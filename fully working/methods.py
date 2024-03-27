from openai import OpenAI

import os
from datetime import datetime, timedelta
import json

from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import googleapiclient.discovery

from datetime import datetime, timedelta, timezone
import pytz  

# from mistralai.client import MistralClient
# from mistralai.models.chat_completion import ChatMessage


def get_google_calendar_service():
    # Set up the Google Calendar API credentials
    creds = None
    SCOPES = ["https://www.googleapis.com/auth/calendar"]

    if os.path.exists("token.json"):
        creds = Credentials.from_authorized_user_file("token.json")

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file("credentials.json", SCOPES)
            creds = flow.run_local_server(port=0)

        with open("token.json", "w") as token:
            token.write(creds.to_json())

    # Build and return the Google Calendar API service
    service = googleapiclient.discovery.build("calendar", "v3", credentials=creds)
    return service


def extractCalendar(google_calendar):
    service = google_calendar
    now = current_time()
    nextweek = (datetime.now() + timedelta(days=7)).isoformat() + "Z"
    events_result = (
        service.events()
        .list(
            calendarId="primary",
            timeMin=now,
            timeMax=nextweek,
            singleEvents=True,
            orderBy="startTime",
        )
        .execute()
    )

    events = events_result.get("items", [])
    calendar = ""

    for event in events:
        name = event["summary"]
        start = event["start"].get("dateTime", event["start"].get("date"))
        end = event["end"].get("dateTime", event["end"].get("date"))
        id = event["id"]
        event_details = {
            "name": name,
            "datetime_start": start,
            "datetime_end": end,
            "id": id,
        }
        calendar = calendar + f"{event_details}\n"

    return calendar


def get_calendar():
    return extractCalendar(get_google_calendar_service())


def set_up_ChatGPT(calendar):
    os.environ["OPENAI_API_KEY"] = "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"
    client = OpenAI()
    client.api_key = "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"

    stream = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {
                "role": "user",
                "content": "Here's my calendar for the week, store it for your reference. Today's date and time is: "
                + current_time()
                + "\n"
                + calendar
                + "Print the events you see for today. Use 12HR format for time.",
            }
        ],
        stream=True,
    )

    for chunk in stream:
        print(chunk.choices[0].delta.content or "", end="")

    return client

def set_up_MISTRAL(calendar):
    # Assuming current_time() is defined somewhere in your code.
    os.environ["MISTRAL_API_KEY"] = "FZrH3btKf0XO4soOHwxozkDacRKcVixi"
    api_key = os.environ["MISTRAL_API_KEY"]
    client = MistralClient(api_key=api_key)

    # Create ChatMessage objects instead of using dictionaries
    messages = [
        ChatMessage(
            role="user",
            content="Here's my calendar for the week, store it for your reference. Today's date and time is: "
            + current_time()
            + "\n"
            + calendar
            + "Print the events you see for today.",
        )
    ]

    # Use the chat_stream method, which now expects ChatMessage objects
    stream = client.chat_stream(model="open-mistral-7b", messages=messages)

    for chunk in stream:
        print(chunk.choices[0].delta.content or "", end="")

    return client

def move_event(event_details):
    # Function to move an event in Google Calendar
    event_title = event_details.get('name', '')
    date = event_details.get('date', '')
    time = event_details.get('time', '')
    new_date = event_details.get('new_date', '')
    new_time = event_details.get('new_time', '')

    service = get_google_calendar_service()

    try:
        # Parse current datetime
        if date and time:
            current_datetime = datetime.strptime(f'{date} {time}', '%Y-%m-%d %I:%M %p')
        elif time:
            current_datetime = datetime.now().replace(hour=int(time.split(':')[0]))
        elif date:
            current_datetime = datetime.strptime(date, '%Y-%m-%d').replace(hour=0, minute=0, second=0)

        # Parse new datetime
        if new_date and new_time:
            new_datetime = datetime.strptime(f'{new_date} {new_time}', '%Y-%m-%d %I:%M %p')
        elif new_time:
            new_datetime = current_datetime.replace(hour=int(new_time.split(':')[0]), minute=int(new_time.split(':')[1]))
        else:
            raise ValueError('Please specify the time to move the event to.')

        # Check if new datetime is in the future
        if new_datetime < datetime.now():
            raise ValueError('The new date and time should be in the future.')

        # Query events
        events_result = service.events().list(calendarId='primary', timeMin=current_datetime.isoformat()+'Z', 
                                              orderBy='startTime', singleEvents=True, q=event_title.lower()).execute()
        events = events_result.get('items', [])

        if not events:
            raise ValueError(f'Event "{event_title}" not found.')

        event_to_move = events[0]

        # Move event
        event_to_move['start']['dateTime'] = new_datetime.isoformat()
        event_to_move['end']['dateTime'] = (new_datetime + (datetime.fromisoformat(event_to_move['end']['dateTime']) -
                                                             datetime.fromisoformat(event_to_move['start']['dateTime']))).isoformat()

        updated_event = service.events().update(calendarId='primary', eventId=event_to_move['id'], body=event_to_move).execute()

        print(f'Event "{event_title}" moved to {datetime.fromisoformat(updated_event["start"]["dateTime"])}')

    except Exception as e:
        print(f'Error: {e}')



def moveEvent(event_details):
    event_title = event_details.get("name", "")
    date = event_details.get("date", "")
    time = event_details.get("time", "")
    new_date = event_details.get("new_date", "")
    new_time = event_details.get("new_time", "")
    service = get_google_calendar_service()

    if (
        date and time
    ):  # Eg: move my meeting on 2021-08-20 at 10:00 to 2021-08-21 at 11:00
        current_datetime = datetime.strptime(f"{date} {time}", "%Y-%m-%d %I:%M %p")
    elif time:  # Eg: move my meeting at 10:00 to 11:00
        current_datetime = datetime.now().replace(hour=int(time.split(":")[0]))
    elif date:  # Eg: move my meeting on 2021-08-20 to 2021-08-21 at 11:00
        current_datetime = datetime.strptime(date, "%Y-%m-%d").replace(
            hour=0, minute=0, second=0
        )

    if new_date and new_time:  # if both new date and time are provided
        new_datetime = datetime.strptime(f"{new_date} {new_time}", "%Y-%m-%d %I:%M %p")

    elif new_time:  # if only new time is provided
        new_datetime = current_datetime.replace(
            hour=int(time.split(":")[0]), minute=int(time.split(":")[1])
        )
    else:
        print("Please specify the time to move the event to.")
        return

    if not date and not time:  # Eg move my meeting to 11:00
        now = datetime.utcnow().isoformat() + "Z"
        events_result = (
            service.events()
            .list(
                calendarId="primary",
                timeMin=now,
                orderBy="startTime",
                singleEvents=True,
                q=f"{event_title.lower()}",
            )
            .execute()
        )  # matches with mispelled event names or lower case
        events = events_result.get("items", [])
        if events:
            event_to_move = events[0]
        else:
            print(f'Event "{event_title}" not found.')
            return
    elif not event_title and not date:  # Eg: move my 2pm to monday 11am
        events_result = (
            service.events()
            .list(
                calendarId="primary",
                timeMin=current_datetime.isoformat() + "Z",
                timeMax=(current_datetime + timedelta(hours=1)).isoformat() + "Z",
                orderBy="startTime",
                singleEvents=True,
            )
            .execute()
        )
        events = events_result.get("items", [])
        if events:
            event_to_move = events[0]
        else:
            print(f"Event not found.")
            return
    else:  # Eg: move my meeting on 2021-08-20 at 10:00 to 2021-08-21 at 11:00
        events_result = (
            service.events()
            .list(
                calendarId="primary",
                timeMin=current_datetime.isoformat() + "Z",
                orderBy="startTime",
                singleEvents=True,
                q=f"{event_title.lower()}",
            )
            .execute()
        )  # matches with mispelled event names or lower case
        events = events_result.get("items", [])
        if events:
            event_to_move = events[0]
        else:
            print(f'Event "{event_title}" not found.')
            return

    # check if new date and time is available
    if new_datetime < datetime.now():
        print("The new date and time should be in the future.")
        return
    time_min = new_datetime.isoformat() + "Z"
    time_max = (new_datetime + timedelta(hours=1)).isoformat() + "Z"

    check_availability = (
        service.freebusy()
        .query(
            body={
                "timeMin": time_min,
                "timeMax": time_max,
                "items": [{"id": "primary"}],
            }
        )
        .execute()
    )
    if check_availability["calendars"]["primary"]["busy"]:
        print(
            f"The new date and time is not available. Please choose another date and time."
        )
        return

    print(event_to_move)
    start_datetime = datetime.fromisoformat(event_to_move["start"]["dateTime"])
    end_datetime = datetime.fromisoformat(event_to_move["end"]["dateTime"])
    event_duration = (
        end_datetime - start_datetime
    )  # to make sure duration of event is maintained when moving
    new_datetime_end = new_datetime + event_duration
    event_to_move["start"]["dateTime"] = new_datetime.isoformat()
    event_to_move["end"]["dateTime"] = new_datetime_end.isoformat()

    # Update the event
    updated_event = (
        service.events()
        .update(calendarId="primary", eventId=event_to_move["id"], body=event_to_move)
        .execute()
    )

    print(
        f'Event "{event_title}" moved to {datetime.fromisoformat(updated_event["start"]["dateTime"])}'
    )

def createEvent(description, date, time, duration):
    print("Create event called")

    # Adjust date parsing to match incoming data
    description = description.strip('"')
    date = date.strip('"')
    time = time.strip('"')
    print("The data and time is ", date, "/", time)

    # Adjust the datetime parsing to match the incoming data
    naive_start_datetime = datetime.strptime(f"{date} {time}", "%Y-%m-%d %H:%M")
    
    # Assuming input time is in the local timezone
    local_timezone = pytz.timezone('America/New_York')  
    local_start_datetime = local_timezone.localize(naive_start_datetime)

    # Convert local time to UTC (Zulu Time)
    utc_start_datetime = local_start_datetime.astimezone(pytz.utc)
    utc_end_datetime = utc_start_datetime + timedelta(hours=int(duration))

    print("UTC start time: ", utc_start_datetime, "UTC end time: ", utc_end_datetime)

    # Convert the datetime back to RFC3339 format for the Google Calendar API call
    start_iso = utc_start_datetime.isoformat()
    end_iso = utc_end_datetime.isoformat()

    service = get_google_calendar_service()
    calendar = service.calendars().get(calendarId="primary").execute()
    timezone = calendar.get("timeZone")

    event = {
        "summary": description,
        "start": {"dateTime": start_iso, "timeZone": "UTC"},  # Set timezone explicitly to UTC
        "end": {"dateTime": end_iso, "timeZone": "UTC"},      # Set timezone explicitly to UTC
    }

    created_event = service.events().insert(calendarId="primary", body=event).execute()
    print(
        f"Event created: {description} on {date} at {time} for duration of {duration} hours."
    )


def checkSchedule(type, start, end):
    service = get_google_calendar_service()
    now = datetime.now().isoformat()
    nextweek = (datetime.now() + timedelta(days=7)).isoformat()
    time_min = datetime.strptime(start, "%Y-%m-%d %H:%M")
    time_max = datetime.strptime(end, "%Y-%m-%d %H:%M")
    start_datetime = datetime.strptime(start, "%Y-%m-%d %H:%M").replace(
        tzinfo=timezone.utc
    )
    end_datetime = datetime.strptime(end, "%Y-%m-%d %H:%M").replace(tzinfo=timezone.utc)

    if type == "Free":
        events_result = (
            service.freebusy()
            .query(
                body={
                    "timeMin": time_min.isoformat() + "Z",
                    "timeMax": time_max.isoformat() + "Z",
                    "items": [{"id": "primary"}],
                }
            )
            .execute()
        )
        busy_periods = events_result["calendars"]["primary"]["busy"]
        free_periods = []
        last_end_time = start_datetime

        for busy_period in busy_periods:
            start_time = datetime.fromisoformat(busy_period["start"]).replace(
                tzinfo=timezone.utc
            )
            end_time = datetime.fromisoformat(busy_period["end"]).replace(
                tzinfo=timezone.utc
            )

            # Check if there is a gap between the last busy period and the current one
            if last_end_time < start_time:
                free_periods.append({"start": last_end_time, "end": start_time})

            last_end_time = max(last_end_time, end_time)

        # Check if there is a gap between the last busy period and the end of the specified time range
        if last_end_time < end_datetime:
            free_periods.append({"start": last_end_time, "end": end_datetime})

        # Print the free periods
        if not free_periods:
            print("You are busy all day!")
        else:
            print("You are free in these time periods:")
            for free_period in free_periods:
                start_time = free_period["start"].strftime("%I:%M %p")
                end_time = free_period["end"].strftime("%I:%M %p")
                print(f"{start_time} to {end_time}")
    else:
        # The rest of your code for handling non-Free events
        pass


"""
# Assuming get_google_calendar_service is defined somewhere in your code
entities = {
    "type": "Free",
    "start": "2024-03-13 00:00",
    "end": "2024-03-14 00:00",
}
checkSchedule(entities)
"""


def current_time():
    now = datetime.now().isoformat() + "Z"
    return now
