import os
import time
from datetime import datetime

import cv2
import numpy as np

from db import query

MODEL_PATH = os.path.join("models", "yolov8n.pt")
LOG_EVERY = 5

state = {
    "count": 0,
    "level": "Low",
    "location": 1,
    "frame": None,
    "error": ""
}


def get_level(count):
    thresholds = query(
        "SELECT LOW, MEDIUM FROM THRESHOLD WHERE THRESHOLDID=1"
    )

    if not thresholds:
        return "Low"

    t = thresholds[0]

    if count <= t["LOW"]:
        return "Low"
    elif count <= t["MEDIUM"]:
        return "Medium"
    return "High"


def placeholder():
    img = np.full((480, 640, 3), 50, np.uint8)

    cv2.putText(
        img, "Starting camera...", (170, 245),
        cv2.FONT_HERSHEY_SIMPLEX, 1,
        (255, 255, 255), 2
    )

    return cv2.imencode(".jpg", img)[1].tobytes()


def camera_loop():
    from ultralytics import YOLO


    model = YOLO("yolov8n.pt")

    cap = cv2.VideoCapture(0)
    last_log = 0

    while True:
        ok, frame = cap.read()

        if not ok:
            state["error"] = "Camera not found"
            time.sleep(1)
            cap.open(0)
            continue

        state["error"] = ""
        frame = cv2.resize(frame, (640, 480))

        results = model(frame, conf=0.25, verbose=False)

        count = sum(
            1 for b in results[0].boxes
            if int(b.cls) == 0
        )

        level = get_level(count)

        #blurred = cv2.GaussianBlur(frame, (51, 51), 0)
        state["frame"] = cv2.imencode(".jpg", frame)[1].tobytes()
        state["count"] = count
        state["level"] = level

        if time.time() - last_log >= LOG_EVERY:
            loc = query(
                "SELECT STATUS FROM LOCATION WHERE LOCATIONID=?",
                (state["location"],)
            )

            if loc and loc[0]["STATUS"] == "active":
                query(
                    """INSERT INTO CROWD_LOG
                    (TIMESTAMP, CROWD_COUNT, DENSITY_LEVEL, LOCATIONID)
                    VALUES (?, ?, ?, ?)""",
                    (
                        datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        count,
                        level,
                        state["location"]
                    )
                )

                last_log = time.time()