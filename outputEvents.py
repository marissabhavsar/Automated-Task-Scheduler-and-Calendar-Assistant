from datetime import datetime, timedelta

import os.path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# If modifying these scopes, delete the file token.json.
SCOPES = ["https://www.googleapis.com/auth/calendar"]

def convertTime(dateTime):
  date, time_utc = dateTime.split("T")

  if "-" in time_utc:
    time, utc = time_utc.split("-")
  elif "+" in time_utc:
    time, utc = time_utc.split("+")

  return date, time, utc


def createEvent(description, date, time, duration, creds):

  start_datetime = datetime.strptime(f'{date} {time}', '%Y-%m-%d %I:%M %p')
  end_datetime = start_datetime + timedelta(hours=duration)
  start_datetime = start_datetime.isoformat() + 'Z'
  end_datetime = end_datetime.isoformat() + 'Z'
  try:
    service = build("calendar", "v3", credentials=creds)
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

    print(event)

    event = service.events().insert(calendarId="primary", body= event).execute()

  except HttpError as error:
    print("error!", error)


# diff queries: check schedule (overall), check when busy, check when free
def checkSchedule(type, day, week_calendar):
  if type == 'all' or type == 'busy':
    return week_calendar[day]
  # implement a way to check free time


def listEvents(week_calendar):
  return week_calendar




def main():
  """Shows basic usage of the Google Calendar API.
  Prints the start and name of the next 10 events on the user's calendar.
  """
  week_calendar = {}
  name_to_date = {}
  creds = None
  # The file token.json stores the user's access and refresh tokens, and is
  # created automatically when the authorization flow completes for the first
  # time.
  if os.path.exists("token.json"):
    creds = Credentials.from_authorized_user_file("token.json", SCOPES)
  # If there are no (valid) credentials available, let the user log in.
  if not creds or not creds.valid:
    if creds and creds.expired and creds.refresh_token:
      creds.refresh(Request())
    else:
      flow = InstalledAppFlow.from_client_secrets_file(
          "credentials.json", SCOPES
      )
      creds = flow.run_local_server(port=0)
    # Save the credentials for the next run
    with open("token.json", "w") as token:
      token.write(creds.to_json())

  try:
    service = build("calendar", "v3", credentials=creds)

    # Call the Calendar API
    now = datetime.utcnow().isoformat() + "Z"  # 'Z' indicates UTC time
    #now = datetime.now()
    print("Getting the upcoming 10 events")
    events_result = (
        service.events()
        .list(
            calendarId="primary",
            timeMin=now,
            maxResults=10,
            singleEvents=True,
            orderBy="startTime",
        )
        .execute()
    )
    events = events_result.get("items", [])

    if not events:
      print("No upcoming events found.")
      return

    # Prints the start and name of the next 10 events
    # f = open("output.txt", "x")
    for event in events:
      # f.write("Event: " + event["summary"] + " ")
      print(event['summary'])

      start = event["start"].get("dateTime", event["start"].get("date"))
      end = event["end"].get("dateTime", event["end"].get('date'))
      startDate, startTime, startUtc = convertTime(start)
      endDate, endTime, endUtc = convertTime(end)

      datetime_str = datetime.strptime(start, '%Y-%m-%dT%H:%M:%S%z')
      day = datetime_str.strftime('%A')
      event_obj = {}
      event_obj["name"] = event['summary']
      event_obj["startTime"] = startTime
      event_obj["endTime"] = endTime
      event_obj["startDate"] = startDate
      event_obj['endDate'] = endDate

      name_to_date[day] = startDate
      if day in week_calendar:
        week_calendar[day].append(event_obj)
      else:
        week_calendar[day] = []
        week_calendar[day].append(event_obj)


      #print(event["start"].get("dateTime"))
      #print("event: ", event["start"])
      # f.write("Start Date: " + startDate + " ")
      # f.write("Start Time: " + startTime + " ")
      # f.write("End Date: " + endDate + " ")
      # f.write("End Time: "+ endTime + " ")
      #print(start, end, event["summary"])
      #f.write(start, event["summary"])

    print(week_calendar)

    description = "jog"
    day = "2024-03-12"
    time = "12:00 PM"
    duration = 1

    createEvent(description, day, time, duration, creds)

  except HttpError as error:
    print(f"An error occurred: {error}")


if __name__ == "__main__":
  main()