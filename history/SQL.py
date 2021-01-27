import mysql.connector
import csv
import codecs
import os
import numpy as np
import cv2
import time
import upload
from datetime import datetime
from PIL import Image, ImageFont, ImageDraw


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


def fetch_data():
    task = "SELECT * FROM heart_rate"
    cursor.execute(task)
    count = cursor.fetchall()
    length = len(count)
    if (length - 20) < 0:
        length = 0
    task = "SELECT bpm, now FROM heart_rate WHERE id > %s" % (length - 20)
    cursor.execute(task)
    data = cursor.fetchall()
    return data


def history():
    img = np.zeros((1080, 1920, 3), np.uint8)
    now = datetime.now()

    FONT_COLOR = (255, 255, 255)
    CURRENT_TIME = now.strftime("%H:%M")
    CURRENT_DATE = now.strftime("%m/%d")
    CURRENT_WEEK = str.upper(now.strftime("%a"))

    img = cv_text_zh(img, CURRENT_TIME, (20, -10), FONT_COLOR, 100)
    img = cv_text_zh(img, CURRENT_DATE, (300, 10), FONT_COLOR, 40)
    img = cv_text_zh(img, CURRENT_WEEK, (300, 60), FONT_COLOR, 40)

    y0, dy = 200, 40
    j = 0
    for i in fetch_data():
        y = y0 + j * dy
        cv2.putText(img, i[1] + " | " + str(i[0]), (10, y), cv2.FONT_HERSHEY_DUPLEX, 1, (255, 255, 255), 1, cv2.LINE_AA)
        cv2.putText(img, "bpm", (550, y), cv2.FONT_HERSHEY_DUPLEX, 1, (255, 255, 255), 1, cv2.LINE_AA)
        j += 1
    return img


def export_record():
    with codecs.open("heart_rate_record.csv", mode="w", encoding="utf-8") as f:
        write = csv.writer(f, dialect="excel")
        task = "SELECT * FROM heart_rate"
        cursor.execute(task)
        all_data = cursor.fetchall()
        for row in all_data:
            # print(row)
            write.writerow(row)


if __name__ == '__main__':
    maxdb = mysql.connector.connect(
        host="127.0.0.1",
        user="root",
        password="fantamirror",  # 換成你的密碼
        database="maxdb",
    )
    cursor = maxdb.cursor()

    while True:
        cv2.imwrite("history.jpg", history())
        print("history image saved successgully!")
        export_record()
        upload.main(is_update_file_function=bool(True), update_drive_service_name="heart_rate_record.csv", update_file_path=os.getcwd() + '/')
        time.sleep(5)
