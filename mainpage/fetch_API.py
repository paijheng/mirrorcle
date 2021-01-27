from __future__ import print_function
import requests
import urllib.parse
import configparser
from urllib import parse
import Authorization
import datetime
import numpy as np
import cv2
import time
from PIL import Image, ImageFont, ImageDraw
import pickle
import os.path
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request


def List_Dict_Converter(lst):
    res_dct = {lst[i]: lst[i + 1] for i in range(0, len(lst), 2)}
    return res_dct


def Get_Predic_3Days(functions, location):
    if(functions == "三天預報"):
        # URL for fetching prediction for 3 days.
        Request_URL = config["URL"]["prediction_3days"]\
            + config["settings"]["Authorization"] + "&format=JSON"\
            + "&locationName=" + urllib.parse.quote(location.replace("台", "臺"))

        response = requests.get(Request_URL)

        # requests.codes.ok == 200
        if(response.status_code == requests.codes.ok):
            # filter out which data we need
            raw = response.json()["records"]["locations"][0]
            data = raw["location"][0]["weatherElement"]

            function_type = "Weather"
            description = functions
            list_results = []

            # short form: Wx, PoP, AT
            index = [1, 7, 2]
            # used when coverting list into dict
            dict_output = {
                "Type": function_type,
                "Description": description,
                "Location": location,
                "Prediction": []
            }
            keyname = ["Date", "Time", "Wx", "PoP6h", "AT"]

            # Long form: Wx, PoP, AT, T, RH, CI
            # index = [1, 7, 2, 3, 4, 5]
            # keyname = ["Date", "Time", "Wx", "PoP6h", "AT", "T", "RH", "CI"]

            i = 0
            # Categorize data into strings
            for idx, key in enumerate(index):
                if(idx == 0):
                    for fetch_time in data[key]["time"]:
                        # fetch date
                        date_start = fetch_time["startTime"][5:10]
                        date_end = fetch_time["endTime"][8:10]
                        date = (date_start + "~" + date_end).replace("-", "/")

                        # fetch duration
                        duration_start = fetch_time["startTime"][11:13] + "時"
                        duration_end = fetch_time["endTime"][11:13] + "時"
                        duration = duration_start + "~" + duration_end

                        # fetch value
                        value = fetch_time["elementValue"][0]["value"]
                        output = date + " " + duration + " " + value
                        # save results into list
                        list_results.append(output)

                elif(idx == 1):
                    for fetch_time in data[key]["time"]:
                        value = " " + fetch_time["elementValue"][0]["value"]
                        output = value + "%"
                        list_results[i] = list_results[i] + output
                        list_results[i + 1] = list_results[i + 1] + output
                        i = i + 2

                else:
                    i = 0
                    for fetch_time in data[key]["time"]:
                        value = fetch_time["elementValue"][0]["value"]
                        # output = " " + data[key]["description"] + "：" + value
                        output = " " + value
                        list_results[i] = list_results[i] + output
                        i = i + 1

            # Prepar for the output dict
            # Steps: string > split into list > save into the list in dict
            load = dict_output["Prediction"]
            for order, content in enumerate(list_results):
                # determine how many data to be loaded
                if(order < 4):
                    # split the string into list
                    list_results[order] = content.split(" ")

                    for num in range(0, len(keyname)):
                        list_results[order].insert(num * 2, keyname[num])

                    load.append(List_Dict_Converter(list_results[order]))

            return dict_output

        else:
            print("Request fialed, status_code:", response.status_code)
    else:
        print("功能名稱錯誤")


def get_Estimated(routename, location, direction, dict_output):

    if(direction == "去程"):
        direction = 0  # 去程
    elif(direction == "回程"):
        direction = 1  # 返程
    else:
        direction = 2  # 迴圈

    # urllib.parse.quote() URL encode
    QUERY_OPTIONS = parse.quote(routename) + "?$format=JSON"
    RESOURCE_PATH = RESOURCE + QUERY_OPTIONS

    # fetch json data from the api
    response = requests.get(RESOURCE_PATH, headers=auth.get_auth_header())

    # requests.codes.ok == 200
    if(response.status_code == requests.codes.ok):
        data = response.json()["N1Datas"]
        # print(json.dumps(data, indent=4, ensure_ascii=False))  # for testing
        keyname = ["Routename", "Location", "EstimateTime", "Destination"]
        list_results = []
        token = 0

        # if the route exists
        if(data):
            # traverse the data dictionary
            for x in data:
                # print(json.dumps(x, indent=4, ensure_ascii=False))
                # check if the stop name exists, if so, token = 1
                if(x["StopName"]["Zh_tw"] == location):
                    if("SubRouteUID" in x and (x["Direction"] == direction or x["SubRouteUID"].endswith(str(direction + 1)))):
                        token = 1
                        if("EstimateTime" in x and x["EstimateTime"] > 0):
                            if(x["EstimateTime"] // 60 > 3):
                                minute = str(x["EstimateTime"] // 60) + "分"
                            else:
                                minute = "即將進站"

                            estimate = minute
                            if(x["DestinationStopName"]):
                                last_stop = x["DestinationStopName"]
                                destination = "往" + last_stop["Zh_tw"]
                            else:
                                last_stop = x["SubRouteName"]
                                destination = "往" + last_stop["Zh_tw"][4:]

                            if(len(destination) > 6):
                                destination = destination.replace(destination[5:], "…")

                            list_results = [routename, location, estimate, destination]

                        elif(x["StopStatus"] == 1 and x["EstimateTime"] > 0):
                            estimate = "尚未發車"
                            destination = ""
                            list_results = [routename, location, estimate, destination]

                    else:
                        estimate = "尚未發車"
                        destination = estimate
                        list_results = [routename, location, estimate, destination]

                    # steps: list with keynames > dict output
                    # insert keynames into the list
                    for num in range(0, len(keyname)):
                        list_results.insert(num * 2, keyname[num])

                    # convert list to dict
                    final_output = List_Dict_Converter(list_results)
                    return final_output

            if(token == 0):
                final_output = "No such stop"
                return final_output
        else:
            final_output = "No such routename"
            return final_output
    else:
        final_output = "Request fialed, status_code:" + response.status_code
        return final_output


def get_calendar():
    dict_output_calendar["Info"].clear()
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

            list_results_calendar.append(content.split(" "))

            for num in range(0, len(keyname_calendar)):
                list_results_calendar[order].insert(num * 2, keyname_calendar[num])

            load.append(List_Dict_Converter(list_results_calendar[order]))


def print_icon(img, weather, pos):
    icon = cv2.imread('./icon/' + weather + '.png')
    icon = cv2.resize(icon, None, fx=0.08, fy=0.08)  # 圖片縮小70%
    rows, cols, channels = icon.shape
    for i in range(rows):
        for j in range(0, cols):
            img[pos[1] + i, pos[0] + j] = icon[i, j]  # 行列互調了
    return img


def cv_text_zh(im, chinese, pos, color, size):
    # font = "PingFang-TC-Regular-2.otf"
    font_sources = "D:/GitHub/Fantamirror/font/" + "NotoSansCJKtc-Light.otf"
    img_PIL = Image.fromarray(cv2.cvtColor(im, cv2.COLOR_BGR2RGB))
    font = ImageFont.truetype(font_sources, size)
    fillColor = color  # (255,0,0)
    position = pos  # (100,100)
    draw = ImageDraw.Draw(img_PIL)
    draw.text(position, chinese, font=font, fill=fillColor)
    img = cv2.cvtColor(np.asarray(img_PIL), cv2.COLOR_RGB2BGR)
    return img


def mainpage(weather, bus, calendar):
    img = np.zeros((1080, 1920, 3), np.uint8)
    now = datetime.datetime.now()
    FONT_COLOR = (255, 255, 255)
    CURRENT_TIME = now.strftime("%H:%M")
    CURRENT_DATE = now.strftime("%m/%d")
    CURRENT_WEEK = str.upper(now.strftime("%a"))

    WEATHER = weather['Prediction']
    BUS = bus['Info']
    CALENDAR = calendar['Info']

    pos_weather = [1250, 20]  # (x, y)
    pos_bus = [1250, 900]
    pos_calendar = [30, 800]

    offset_weather = [225, 50]
    offset_bus = [120, 50]
    offset_calendar = [60, 50]

    date = []

    img = cv_text_zh(img, CURRENT_TIME, (20, -10), FONT_COLOR, 100)
    img = cv_text_zh(img, CURRENT_DATE, (300, 10), FONT_COLOR, 40)
    img = cv_text_zh(img, CURRENT_WEEK, (300, 60), FONT_COLOR, 40)

    wthr_dict = {
        '晴': 'sun',
        '多雲': 'cloud',
        '午後短暫雷陣雨': 'rain',
        '雨': 'rain',
        '雨天': 'rain',
        '雷陣雨': 'storm',
        '雷雨': 'storm'
    }

    for i in range(0, 3):
        # Time duration of the weather prediction
        img = cv_text_zh(img, WEATHER[i]['Time'],
            (pos_weather[0] + i * offset_weather[0], pos_weather[1]), FONT_COLOR, 25)
        # Wx of the weather prediction
        print_icon(img, wthr_dict[WEATHER[i]['Wx']], (pos_weather[0] + 125 + i * offset_weather[0], pos_weather[1] - 5))
        # PoP6h of the weather prediction
        img = cv_text_zh(img, "降雨機率：" + WEATHER[i]['PoP6h'],
            (pos_weather[0] + i * offset_weather[0], pos_weather[1] + offset_weather[1] * 1), FONT_COLOR, 25)
        # RealFeel temperature of the weather prediction
        img = cv_text_zh(img, "體感溫度：" + WEATHER[i]['AT'] + "℃",
            (pos_weather[0] + i * offset_weather[0], pos_weather[1] + offset_weather[1] * 2), FONT_COLOR, 25)
        # Routename of the bus
        img = cv_text_zh(img, BUS[i]['Routename'],
            (pos_bus[0], pos_bus[1] + i * offset_bus[1]), FONT_COLOR, 25)
        # StopName of the bus
        img = cv_text_zh(img, BUS[i]['Location'],
            (pos_bus[0] + offset_bus[0], pos_bus[1] + i * offset_bus[1]), FONT_COLOR, 25)
        # Direction of the bus
        img = cv_text_zh(img, BUS[i]['Destination'],
            (pos_bus[0] + offset_bus[0] * 3, pos_bus[1] + i * offset_bus[1]), FONT_COLOR, 25)
        # Estimated time of the bus
        img = cv_text_zh(img, BUS[i]['EstimateTime'],
            (pos_bus[0] + offset_bus[0] * 4.55, pos_bus[1] + i * offset_bus[1]), FONT_COLOR, 25)
    # Calendar

    for i in range(0, 5):
        if(CALENDAR[i]['Date'][3:] == now.strftime("%d")):
            date.append("今天")
        else:
            date.append("明天")

    date_backup = date.copy()

    for i in range(1, 5):
        if(date[i] == date[i - 1]):
            date_backup[i] = ""

    for i in range(0, 5):
        img = cv_text_zh(img, date_backup[i],
            (pos_calendar[0], pos_calendar[1] + i * offset_calendar[1]), FONT_COLOR, 25)
        img = cv_text_zh(img, CALENDAR[i]['Start'] + "~" + CALENDAR[i]['End'],
            (pos_calendar[0] + offset_bus[0], pos_calendar[1] + i * offset_calendar[1]), FONT_COLOR, 25)
        img = cv_text_zh(img, CALENDAR[i]['Event'],
            (pos_calendar[0] + offset_bus[0] * 2.5, pos_calendar[1] + i * offset_calendar[1]), FONT_COLOR, 25)

    return img


if __name__ == "__main__":
    # initial settings of data to be searched
    route_list = ["紅幹線", "18", "綠幹線"]
    stop_list = ["臺南火車站(北站)", "和順", "臺南轉運站"]
    dir_list = ["去程", "去程", "去程"]

    config = configparser.ConfigParser()
    config.read("config.ini")

    APP_ID = config["AUTH"]["APP_ID"]
    APP_KEY = config["AUTH"]["APP_KEY"]
    RESOURCE = config["URL"]["Estimated_TNN"]

    # fetch the authorization headers
    auth = Authorization.Auth(APP_ID, APP_KEY)

    # initialize the output format
    dict_output = {
        "Info": []
    }

    dict_output_calendar = {
        "Info": []
    }

    # Calendar
    # If modifying these scopes, delete the file token.pickle.
    SCOPES = ["https://www.googleapis.com/auth/calendar.readonly"]

    keyname_calendar = ["Date", "Start", "End", "Event"]

    list_results_calendar = []

    while True:
        dict_output["Info"].clear()
        list_results_calendar.clear()
        output = Get_Predic_3Days("三天預報", "台北市")

        for i in range(0, len(route_list)):
            output2 = get_Estimated(route_list[i], stop_list[i], dir_list[i], dict_output)
            dict_output["Info"].append(output2)

        get_calendar()

        cv2.imwrite("mainpage.jpg", mainpage(output, dict_output, dict_output_calendar))
        print("mainpage image saved successgully!")
        time.sleep(5)
