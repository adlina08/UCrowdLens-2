"""Temporary uploads. Image/video inputs are not added to CROWD_LOG."""
import base64
import os
import tempfile
import time
import uuid
import threading

import cv2
import numpy as np
from flask import Blueprint, Response, abort, render_template, request
from werkzeug.utils import secure_filename
from detection import predict_people, private_frame

upload_bp = Blueprint('upload', __name__)
VIDEO_JOBS = {}
JOBS_LOCK = threading.Lock()
MAX_VIDEO_SECONDS = 120

@upload_bp.route('/analyze', methods=['POST'])
def analyze():
    file = request.files.get('media')
    if not file or not file.filename:
        return render_template('upload_result.html', error='Please choose an image or video.'), 400
    extension = os.path.splitext(secure_filename(file.filename))[1].lower()
    if extension in {'.jpg', '.jpeg', '.png', '.webp'}:
        raw = file.read()
        frame = cv2.imdecode(np.frombuffer(raw, dtype=np.uint8), cv2.IMREAD_COLOR)
        if frame is None:
            return render_template('upload_result.html', error='Invalid image.'), 400
        count, level = predict_people(frame)
        blurred = private_frame(frame, force=True)
        ok, encoded = cv2.imencode('.jpg', blurred)
        if not ok:
            abort(500)
        image_data = base64.b64encode(encoded.tobytes()).decode('ascii')
        return render_template('upload_result.html', kind='image', count=count,
                               level=level, image_data=image_data)
    if extension in {'.mp4', '.mov', '.avi', '.mkv', '.webm'}:
        with tempfile.NamedTemporaryFile(suffix=extension, delete=False) as temp:
            while True:
                chunk = file.stream.read(1024 * 1024)
                if not chunk:
                    break
                temp.write(chunk)
            path = temp.name
        cap = cv2.VideoCapture(path)
        valid = cap.isOpened()
        cap.release()
        if not valid:
            os.remove(path)
            return render_template('upload_result.html', error='Unable to open video.'), 400
        token = uuid.uuid4().hex
        with JOBS_LOCK:
            VIDEO_JOBS[token] = (path, time.monotonic())
        return render_template('upload_result.html', kind='video', token=token)
    return render_template('upload_result.html', error='Supported: JPG, PNG, WEBP, MP4, MOV, AVI, MKV, WEBM.'), 400

@upload_bp.route('/uploaded-video/<token>')
def uploaded_video(token):
    with JOBS_LOCK:
        job = VIDEO_JOBS.pop(token, None)
    if job is None:
        abort(404)
    path, created = job
    if time.monotonic() - created > 600:
        os.remove(path)
        abort(410)

    def frames():
        cap = cv2.VideoCapture(path)
        start = time.monotonic()
        try:
            while time.monotonic() - start < MAX_VIDEO_SECONDS:
                ok, frame = cap.read()
                if not ok:
                    break
                count, level = predict_people(frame)
                display = private_frame(cv2.resize(frame, (640, 480)), force=True)
                cv2.putText(display, f'Count: {count} | Density: {level}',
                            (15, 35), cv2.FONT_HERSHEY_SIMPLEX, .8,
                            (255, 255, 255), 2)
                success, jpg = cv2.imencode('.jpg', display)
                if success:
                    yield b'--frame\r\nContent-Type: image/jpeg\r\n\r\n' + jpg.tobytes() + b'\r\n'
        finally:
            cap.release()
            try:
                os.remove(path)
            except OSError:
                pass
    return Response(frames(), mimetype='multipart/x-mixed-replace; boundary=frame',
                    headers={'Cache-Control': 'no-store'})
