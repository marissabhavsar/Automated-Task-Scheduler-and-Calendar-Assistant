from openai import OpenAI
import os
from datetime import datetime, timedelta
import json

from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import googleapiclient.discovery

def get_google_calendar_service():
    # Set up the Google Calendar API credentials 
    creds = None
    SCOPES = ['https://www.googleapis.com/auth/calendar']

    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json')

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)

        with open('token.json', 'w') as token:
            token.write(creds.to_json())

    # Build and return the Google Calendar API service
    service = googleapiclient.discovery.build('calendar', 'v3', credentials=creds)
    return service

def extractCalendar(google_calendar): 
    service = google_calendar
    now = current_time()
    nextweek = (datetime.now() + timedelta(days=7)).isoformat() + 'Z'
    events_result = service.events().list(calendarId='primary', timeMin=now,
                                        maxResults=10, singleEvents=True,
                                        orderBy='startTime').execute()
    
    events = events_result.get('items', [])
    calendar = ''
    
    for event in events:
        name = event['summary']
        start = event['start'].get('dateTime', event['start'].get('date'))
        end = event['end'].get('dateTime', event['end'].get('date'))
        id = event['id']
        event_details = {'name':name, 'datetime_start':start, 'datetime_end':end, 'id':id}
        calendar = calendar + f'{event_details}\n'

    return calendar

def set_up_ChatGPT(calendar):
    os.environ['OPENAI_API_KEY'] = "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"
    client = OpenAI()
    client.api_key = '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'

    stream = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": "Here's my calendar for the week, store it for your reference. Today's date and time is: " + current_time() + '\n' + calendar + "Print the events events you see for today" }],
        stream=True,
    )
    
    for chunk in stream:
        print(chunk.choices[0].delta.content or "", end="")

    return client

def moveEvent(event_details):
    event_title = event_details.get('name', '')
    date = event_details.get('date', '')
    time = event_details.get('time', '')
    new_date = event_details.get('new_date', '')
    new_time = event_details.get('new_time', '')
    service = get_google_calendar_service()

    
    if date and time: #Eg: move my meeting on 2021-08-20 at 10:00 to 2021-08-21 at 11:00
        current_datetime = datetime.strptime(f'{date} {time}', '%Y-%m-%d %I:%M %p')
    elif time: #Eg: move my meeting at 10:00 to 11:00
        current_datetime = datetime.now().replace(hour=int(time.split(':')[0]))
    elif date: #Eg: move my meeting on 2021-08-20 to 2021-08-21 at 11:00
        current_datetime = datetime.strptime(date, '%Y-%m-%d').replace(hour=0, minute=0, second=0)

    if new_date and new_time: #if both new date and time are provided
        new_datetime = datetime.strptime(f'{new_date} {new_time}', '%Y-%m-%d %I:%M %p')

    elif new_time: #if only new time is provided
        new_datetime = current_datetime.replace(hour=int(time.split(':')[0]), minute=int(time.split(':')[1]))
    else: 
        print('Please specify the time to move the event to.') 
        return
    

    if not date and not time:  #Eg move my meeting to 11:00 
        now = datetime.utcnow().isoformat() + 'Z'
        events_result = service.events().list(calendarId='primary', timeMin=now, orderBy='startTime', singleEvents=True, q=f'{event_title.lower()}').execute() #matches with mispelled event names or lower case
        events = events_result.get('items', [])
        if events:
            event_to_move = events[0]
        else:
            print(f'Event "{event_title}" not found.')
            return
    elif not event_title and not date: #Eg: move my 2pm to monday 11am
        events_result = service.events().list(calendarId='primary', timeMin=current_datetime.isoformat() + 'Z', timeMax= (current_datetime + timedelta(hours=1)).isoformat() + 'Z', orderBy='startTime', singleEvents=True).execute()
        events = events_result.get('items', [])
        if events:
            event_to_move = events[0]
        else:
            print(f'Event not found.')
            return
    else: #Eg: move my meeting on 2021-08-20 at 10:00 to 2021-08-21 at 11:00
        events_result = service.events().list(calendarId='primary', timeMin=current_datetime.isoformat()+'Z', orderBy='startTime', singleEvents=True, q=f'{event_title.lower()}').execute() #matches with mispelled event names or lower case
        events = events_result.get('items', [])
        if events:
            event_to_move = events[0]
        else:
            print(f'Event "{event_title}" not found.')
            return
    
    #check if new date and time is available
    if new_datetime < datetime.now():
        print('The new date and time should be in the future.')
        return
    time_min = new_datetime.isoformat() + 'Z'
    time_max = (new_datetime + timedelta(hours=1)).isoformat() + 'Z'

    check_availability = service.freebusy().query(
        body={
            'timeMin': time_min,
            'timeMax': time_max,
            'items': [{'id': 'primary'}]
        }
    ).execute()
    if check_availability['calendars']['primary']['busy']:
        print(f'The new date and time is not available. Please choose another date and time.')
        return

    print(event_to_move)
    start_datetime = datetime.fromisoformat(event_to_move['start']['dateTime'])  
    end_datetime = datetime.fromisoformat(event_to_move['end']['dateTime'])
    event_duration = end_datetime - start_datetime #to make sure duration of event is maintained when moving 
    new_datetime_end = new_datetime + event_duration
    event_to_move['start']['dateTime'] = new_datetime.isoformat()
    event_to_move['end']['dateTime'] = new_datetime_end.isoformat()

    # Update the event
    updated_event = service.events().update(
    calendarId='primary', eventId=event_to_move['id'], body=event_to_move).execute()

    print(f'Event "{event_title}" moved to {datetime.fromisoformat(updated_event["start"]["dateTime"])}')

def createEvent(entities):
    now = datetime.now()

    description = entities.get('description', '')
    date = entities.get('date', now.strftime("%Y-%m-%d"))
    time = entities.get('time', '')
    duration = entities.get('duration', 1)
    if not time:
        print('Please specify the time of the event.')
        return
    
    start_datetime = datetime.strptime(f'{date} {time}', '%Y-%m-%d %I:%M %p')
    print(start_datetime)
    end_datetime = start_datetime + timedelta(hours=duration)
    start_datetime = start_datetime.isoformat() 
    end_datetime = end_datetime.isoformat() 
    
    service = get_google_calendar_service()
    calendar = service.calendars().get(calendarId='primary').execute()
    timezone = calendar.get("timeZone")
    #print(timezone)

    event = {
        'summary': description,

        'start': {
        'dateTime': start_datetime,
        'timeZone': timezone
        },
        'end': {
        'dateTime': end_datetime,
        'timeZone': timezone
        }

    }

    event = service.events().insert(calendarId="primary", body= event).execute()
    print(f'Event created: {description} on {date} at {time} for {duration} hours.')

from datetime import datetime, timedelta, timezone


def checkSchedule(entities):
    type = entities.get("type", "")
    start = entities.get("start", "")
    end = entities.get("end", "")
    service = get_google_calendar_service()
    now = datetime.now().isoformat()
    nextweek = (datetime.now() + timedelta(days=7)).isoformat()
    time_min = datetime.strptime(start, "%Y-%m-%d %H:%M")
    time_max = datetime.strptime(end, "%Y-%m-%d %H:%M")
    start_datetime = datetime.strptime(start, "%Y-%m-%d %H:%M").replace(tzinfo=timezone.utc)
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
            start_time = datetime.fromisoformat(busy_period['start']).replace(tzinfo=timezone.utc)
            end_time = datetime.fromisoformat(busy_period['end']).replace(tzinfo=timezone.utc)

            # Check if there is a gap between the last busy period and the current one
            if last_end_time < start_time:
                free_periods.append({'start': last_end_time, 'end': start_time})
    
            last_end_time = max(last_end_time, end_time)

        # Check if there is a gap between the last busy period and the end of the specified time range
        if last_end_time < end_datetime:
            free_periods.append({'start': last_end_time, 'end': end_datetime})

        # Print the free periods
        if not free_periods:
            print("You are busy all day!")
        else:
            print("You are free in these time periods:")
            for free_period in free_periods:
                start_time = free_period['start'].strftime("%I:%M %p")
                end_time = free_period['end'].strftime("%I:%M %p")
                print(f"{start_time} to {end_time}")   
    else:
        # The rest of your code for handling non-Free events
        pass

'''
# Assuming get_google_calendar_service is defined somewhere in your code
entities = {
    "type": "Free",
    "start": "2024-03-13 00:00",
    "end": "2024-03-14 00:00",
}
checkSchedule(entities)
'''

def current_time():
    now = datetime.now().isoformat() + 'Z'
    return now
    
