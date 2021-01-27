from __future__ import print_function
import datetime
import pickle
import os.path
import json
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

# If modifying these scopes, delete the file token.pickle.
SCOPES = ["https://www.googleapis.com/auth/calendar.readonly"]

function_type = "Calendar"
description = "最近五項活動"

dict_output_calendar = {
    "Type": function_type,
    "Description": description,
    "Info": []
}

keyname = ["Date", "Start", "End", "Event"]

list_results = []


def List_Dict_Converter(lst):
    res_dct = {lst[i]: lst[i + 1] for i in range(0, len(lst), 2)}
    return res_dct


def main():
    creds = None
    # The file token.pickle stores the user"s access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists("token.pickle"):
        with open("token.pickle", "rb") as token:
            creds = pickle.load(token)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file("credentials.json", SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open("token.pickle", "wb") as token:
            pickle.dump(creds, token)

    service = build("calendar", "v3", credentials=creds)

    # Call the Calendar API
    # "Z" indicates UTC time
    now = datetime.datetime.utcnow().isoformat() + "Z"
    # print("Getting the upcoming 5 events")
    events_result = service.events().list(calendarId="primary", timeMin=now,
        maxResults=5, singleEvents=True, orderBy="startTime").execute()
    events = events_result.get("items", [])

    if not events:
        print("No upcoming events found.")
        token = 0

    else:
        load = dict_output_calendar["Info"]
        for order, event in enumerate(events):
            start = event["start"].get("dateTime", event["start"].get("date"))
            end = event["end"].get("dateTime", event["end"].get("date"))

            event_start = start[5:16].replace("-", "/").replace("T", " ")
            event_end = end[11:16]

            content = event_start + " " + event_end + " " + event["summary"]

            list_results.append(content.split(" "))

            for num in range(0, len(keyname)):
                list_results[order].insert(num * 2, keyname[num])

            load.append(List_Dict_Converter(list_results[order]))


if __name__ == "__main__":
    main()
    # JSON format
    print(json.dumps(dict_output_calendar, indent=4, ensure_ascii=False))

# Result
'''
{
    "Type": "Calendar",
    "Description": "最近五項活動",
    "Info": [
        {
            "Date": "07/16",
            "Start": "09:00",
            "End": "11:00",
            "Event": "上山打老虎"
        },
        {
            "Date": "07/16",
            "Start": "12:00",
            "End": "13:00",
            "Event": "跟周公約會"
        },
        {
            "Date": "07/16",
            "Start": "14:00",
            "End": "17:00",
            "Event": "高雄好七逃"
        },
        {
            "Date": "07/16",
            "Start": "18:00",
            "End": "19:30",
            "Event": "今晚吃一頓大的"
        },
        {
            "Date": "07/16",
            "Start": "20:00",
            "End": "22:00",
            "Event": "看電影"
        }
    ]
}
'''
