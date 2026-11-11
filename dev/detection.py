import os
import time
import threading
from datetime import datetime

import cv2
import numpy as np
from ultralytics import YOLO
from db import query

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODEL_PATH = os.path.join(BASE_DIR, 'models', 'best.pt')
IMAGE_SIZE = 960
CONFIDENCE = 0.15
LOG_EVERY = 5

_model = None
_model_lock = threading.Lock()
state = {'count': 0, 'level': 'Low', 'location': 1, 'frame': None, 'error': ''}

def get_model():
    global _model
    with _model_lock:
        if _model is None:
            _model = YOLO(MODEL_PATH)
        return _model

def get_level(count):
    thresholds = query('SELECT LOW, MEDIUM FROM THRESHOLD WHERE THRESHOLDID=1')
    if not thresholds:
        return 'Low'
    t = thresholds[0]
    return 'Low' if count <= t['LOW'] else ('Medium' if count <= t['MEDIUM'] else 'High')

def predict_people(frame):
    # Serialize model access between webcam and uploads.
    model = get_model()
    with _model_lock:
        result = model.predict(source=frame, imgsz=IMAGE_SIZE,
                               conf=CONFIDENCE, verbose=False, device='cpu')[0]
    count = sum(1 for box in result.boxes if int(box.cls.item()) == 0)
    return count, get_level(count)

_privacy_cache = {'enabled': True, 'checked': 0.0}

def privacy_blur_enabled():
    # Avoid a SQLite query on every frame; changes take effect within 1 second.
    now = time.monotonic()
    if now - _privacy_cache['checked'] >= 1:
        rows = query("SELECT SETTING_VALUE FROM SYSTEM_SETTINGS WHERE SETTING_KEY='privacy_blur'")
        _privacy_cache['enabled'] = not rows or rows[0]['SETTING_VALUE'] == '1'
        _privacy_cache['checked'] = now
    return _privacy_cache['enabled']

def private_frame(frame, force=False):
    # This controls the live preview only, not model inference or stored counts.
    if force or privacy_blur_enabled():
        return cv2.GaussianBlur(frame, (51, 51), 0)
    return frame

def placeholder():
    img = np.full((480, 640, 3), 50, np.uint8)
    cv2.putText(img, 'Starting camera...', (150, 245),
                cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
    return cv2.imencode('.jpg', img)[1].tobytes()

def camera_loop():
    cap = cv2.VideoCapture(0)
    last_log = 0
    while True:
        ok, frame = cap.read()
        if not ok:
            state['error'] = 'Camera not found'
            time.sleep(1)
            cap.release()
            cap = cv2.VideoCapture(0)
            continue
        try:
            count, level = predict_people(frame)
            blurred = private_frame(cv2.resize(frame, (640, 480)))
            encoded_ok, jpg = cv2.imencode('.jpg', blurred)
            if encoded_ok:
                state['frame'] = jpg.tobytes()
            state['count'], state['level'], state['error'] = count, level, ''
            if time.time() - last_log >= LOG_EVERY:
                loc = query('SELECT STATUS FROM LOCATION WHERE LOCATIONID=?', (state['location'],))
                if loc and loc[0]['STATUS'] == 'active':
                    query('''INSERT INTO CROWD_LOG
                        (TIMESTAMP, CROWD_COUNT, DENSITY_LEVEL, LOCATIONID)
                        VALUES (?, ?, ?, ?)''',
                        (datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                         count, level, state['location']))
                    last_log = time.time()
        except Exception as exc:
            state['error'] = f'Detection error: {exc}'
            time.sleep(0.5)
