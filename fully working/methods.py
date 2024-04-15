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

from mistralai.client import MistralClient
from mistralai.models.chat_completion import ChatMessage

# def google_tasks_api():
#     creds = None
#     SCOPES = ['https://www.googleapis.com/auth/tasks.readonly']
#     # Check for existing credentials
#     if os.path.exists('token.pickle'):
#         with open('token.pickle', 'rb') as token:
#             creds = pickle.load(token)

#     # If there are no (valid) credentials, perform OAuth flow
#     if not creds or not creds.valid:
#         if creds and creds.expired and creds.refresh_token:
#             creds.refresh(Request())
#         else:
#             flow = InstalledAppFlow.from_client_secrets_file(
#                 'credentials.json', SCOPES)
#             creds = flow.run_local_server(port=0)
#         # Save the credentials for the next run
#         with open('token.pickle', 'wb') as token:
#             pickle.dump(creds, token)

#     service = build('tasks', 'v1', credentials=creds)

#     # Call the Tasks API
#     results = service.tasks().list(tasklist='@default').execute()
#     items = results.get('items', [])

#     all_tasks = []
#     if not items:
#         print('No tasks found.')
#     else:
#         for item in items:
#             task_name = item.get('title', 'No Title')
#             task_due_date = item.get('due', None)  # Use None if no due date is provided
#             if task_due_date:
#                 task_due_date = task_due_date[:10]  # Extract only the date part

#             all_tasks.append({'title': task_name, 'due_date': task_due_date})

#     return all_tasks

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


def get_task_service():
    creds = None
    SCOPES = ["https://www.googleapis.com/auth/tasks"]

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
    service = googleapiclient.discovery.build("tasks", "v1", credentials=creds)
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

def extractTasks(tasks_service):
    tasks_output = []
    task_lists = tasks_service.tasklists().list().execute()

    for task_list in task_lists['items']:

        tasks = tasks_service.tasks().list(tasklist=task_list['id']).execute()
        if 'items' in tasks:
            for task in tasks['items']:
                if 'due' in task:
                    due_date_str = task['due']
                    current_date_str = datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ")
                    if due_date_str > current_date_str:
                        description = task['title']
                        tasks_output.append((description, due_date_str))
        else:
            print("No tasks in this list.")


    return f"{tasks_output}\n"

def get_calendar():
    return extractCalendar(get_google_calendar_service())

def get_tasks():
    return extractTasks(get_task_service())

def set_up_ChatGPT(calendar, tasks):
    os.environ["OPENAI_API_KEY"] = "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"
    client = OpenAI()
    client.api_key = "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"


    stream = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {
                "role": "user",
                "content": "Here's my calendar and tasks for the week, store it for your reference. Today's date and time is: "
                + current_time()
                + "\n"
                + "calendar: " + calendar + "\n"
                + "tasks: " + tasks + "\n"
                + "Print the events and tasks you see for the week. Use 12HR format for time.",
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
    
    chat_response = client.chat(model='mistral-large-latest',messages=messages)

    print(chat_response.choices[0].message.content)

    return client

def moveEvent(event_id, new_date, new_time):

    service = get_google_calendar_service()
    try:
        # Parse current datetime

        # if new_date and new_time:
        #     current_datetime = datetime.strptime(f'{new_date} {new_time}', '%Y-%m-%d %I:%M %p')
        # elif new_time:
        #     current_datetime = datetime.now().replace(hour=int(new_time.split(':')[0]))
        # elif new_date:
        #     current_datetime = datetime.strptime(new_date, '%Y-%m-%d').replace(hour=0, minute=0, second=0)

        # Check if new datetime is in the future
        # if new_datetime < datetime.now():
        #     raise ValueError('The new date and time should be in the future.')

        # Retrieve event from Google Calendar

        # Retrieve event from Google Calendar

        event_id = event_id.strip('"')
        new_date = new_date.strip('"')
        new_time = new_time.strip('"')
        event_id = event_id.strip("'")
        new_date = new_date.strip("'")
        new_time = new_time.strip("'")


        event = service.events().get(calendarId='primary', eventId=event_id).execute()

        # Adjust the datetime parsing to match the incoming data
        naive_start_datetime = datetime.strptime(f"{new_date} {new_time}", "%Y-%m-%d %H:%M")

        # Assuming input time is in the local timezone
        local_timezone = pytz.timezone('America/New_York')
        local_start_datetime = local_timezone.localize(naive_start_datetime)

        # Convert local time to UTC (Zulu Time)
        utc_start_datetime = local_start_datetime.astimezone(pytz.utc)
        duration = (datetime.strptime(event['end']['dateTime'], "%Y-%m-%dT%H:%M:%S%z") -
                                                    datetime.strptime(event['start']['dateTime'], "%Y-%m-%dT%H:%M:%S%z"))

        print('duration: ', duration)
        utc_end_datetime = utc_start_datetime + duration

        print("UTC start time: ", utc_start_datetime, "UTC end time: ", utc_end_datetime)

        # Convert the datetime back to RFC3339 format for the Google Calendar API call
        start_iso = utc_start_datetime.isoformat()
        end_iso = utc_end_datetime.isoformat()


       # Parse new datetime
        # new_datetime = datetime.strptime(new_date + " " + new_time, "%Y-%m-%d %H:%M")

        # # Get timezone
        # print('new datetime reg: ', new_datetime)
        # print('event timezone: ', event['start']['timeZone'])
        # event_timezone = pytz.timezone(event['start']['timeZone'])
        # print('timezone: ', event_timezone)

        # # Convert new datetime to event timezone
        # new_datetime = event_timezone.localize(new_datetime)
        # new_datetime_utc = new_datetime.astimezone(pytz.utc)
        # print('new datetime utc: ', new_datetime_utc)
        # # Update event start and end time
        # duration = (datetime.strptime(event['end']['dateTime'], "%Y-%m-%dT%H:%M:%S%z") -
        #                                             datetime.strptime(event['start']['dateTime'], "%Y-%m-%dT%H:%M:%S%z"))

        # event['start']['dateTime'] = new_datetime_utc.isoformat()
        # event['end']['dateTime'] = (new_datetime_utc + duration).isoformat()

        event['start']['dateTime'] = start_iso
        event['end']['dateTime'] = end_iso


        # Update event in Google Calendar
        updated_event = service.events().update(calendarId='primary', eventId=event_id, body=event).execute()
        #print('Event updated: %s' % updated_event.get('htmlLink'))

        print(f'Event "{event}" moved to {datetime.fromisoformat(updated_event["start"]["dateTime"])}')
    except Exception as e:
        print(f'Error: {e}')



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


def updateEvent(event_id, new_description, new_duration, new_location):
    service = get_google_calendar_service()

    try:
        event_id = event_id.strip('"')
        event_id = event_id.strip("'")

        event = service.events().get(calendarId='primary', eventId=event_id).execute()
        print(event_id)
        if new_description:
            event['description'] = new_description

        # if new_duration:
        #     print(new_duration)
        #     event['end']['dateTime'] = event['start']['dateTime'] + timedelta(hours=int(new_duration))

        if new_location:
            event['location'] = new_location
        #print('event: ', event)
        updated_event = service.events().update(calendarId='primary', eventId=event_id, body=event).execute()
        #print('created event: ', updated_event)
    except Exception as e:
        print(f'Error: {e}')


def deleteEvent(event_id):
    service = get_google_calendar_service()

    event_id = event_id.strip("'")
    event_id = event_id.strip('"')

    try:
        service.events().delete(calendarId='primary', eventId=event_id).execute()
    except Exception as e:
        print(f'Error: {e}')






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
