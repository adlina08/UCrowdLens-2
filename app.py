import os
import sys
import threading
from flask import Flask

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DEV_DIR = os.path.join(BASE_DIR, "dev")

sys.path.insert(0, DEV_DIR)

from db import init_db
from detection import camera_loop
from public import public_bp
from auth import auth_bp
from admin import admin_bp
from logs import logs_bp
from uploads import upload_bp

app = Flask(
    __name__,
    template_folder=os.path.join(BASE_DIR, "templates"),
    static_folder=os.path.join(BASE_DIR, "static")
)

app.secret_key = os.environ.get("UCROWDLENS_SECRET_KEY", "ucrowdlens-change-me")
app.config["MAX_CONTENT_LENGTH"] = 100 * 1024 * 1024

init_db()

app.register_blueprint(public_bp)
app.register_blueprint(auth_bp)
app.register_blueprint(admin_bp)
app.register_blueprint(logs_bp)
app.register_blueprint(upload_bp)

if __name__ == "__main__":
    threading.Thread(
        target=camera_loop,
        daemon=True
    ).start()

    app.run(
        host="0.0.0.0",
        port=5001,
        threaded=True,
        use_reloader=False
    )