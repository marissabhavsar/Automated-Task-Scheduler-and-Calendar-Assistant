import json
from datetime import datetime

# Prepare the dynamic part of the description
now = datetime.now()
description_text = "Extract entities from the body of the input text. The current time for your reference is: " + now.strftime("%Y-%m-%d %H:%M:%S") + "."

# Define the JSON structure
moveEvent_format = [
    {
        'name': "moveEvent",
        'description': description_text,
        'parameters': {
            'type': 'object',
            'properties': {
                'name': {
                    'type': 'string',
                    'description': 'Name of the event to be moved.'
                },
                'date': {
                    'type': 'string',
                    'description': 'Current date of the event to be moved. Use YYYY-MM-DD format.'
                },
                'time': {
                    'type': 'string',
                    'description': 'The time of the event to be moved. Use 12HR format, example: 10:00 AM.'
                },
                'new_date': {
                    'type': 'string',
                    'description': 'The date to which the event is to be moved. Use YYYY-MM-DD format.'
                },
                'new_time': {
                    'type': 'string',
                    'description': 'The time to which the event is to be moved. Use 12HR format, example: 10:00 AM.'
                }
            }
        }
    }
]

createEvent_format = [
    {
        'name': "createEvent",
        'description': "Extract entities from the body of the input text to interact with Google Calendar API. The current time for your reference is:" + now.strftime("%Y-%m-%d %H:%M:%S") + ".",
        'parameters': {
            'type': 'object',
            'properties': {
                'description': {
                    'type': 'string',
                    'description': 'Description of the event.'
                },
                'date': {
                    'type': 'string',
                    'description': 'Date of the event. Use YYYY-MM-DD format.'
                },
                'time': {
                    'type': 'string',
                    'description': 'The time at which event should be scheduled. Use 12HR format, example: 10:00 AM. '
                },
                'duration': {
                    'type': 'string',
                    'description': 'Duration of the event.'
                },
                
            }
        }
    }
]

checkSchedule_format = [
    {
        "name": "checkSchedule",
        "description": "Extract entities from the body of the input text to interact with Google Calendar API and check the schedule. The current time for your reference is:"
        + now.strftime("%Y-%m-%d %H:%M:%S")
        + ".",
        "parameters": {
            "type": "object",
            "properties": {
                "type": {
                    "type": "string",
                    "description": "Whether to check free or busy schedule. Use Free or Busy.",
                },
                "start": {
                    "type": "string",
                    "description": 'Start date and time to start checking schedule. Use "%Y-%m-%d %H:%M" format.',
                },
                "end": {
                    "type": "string",
                    "description": 'End date and time at which to stop checking schedule. Use "%Y-%m-%d %H:%M" format.',
                },
            },
        },
    }
]
def getFormat(string):
    if str(string) == "moveEvent_format":
        return moveEvent_format
    else:
        return moveEvent_format
    
