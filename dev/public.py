import io
import time

from flask import Blueprint, Response, jsonify, render_template, request
from matplotlib.figure import Figure

from db import query
from detection import state, placeholder

public_bp = Blueprint("public", __name__)


@public_bp.route("/")
def dashboard():
    locations = query(
        "SELECT * FROM LOCATION WHERE STATUS='active'"
    )

    ids = [l["LOCATIONID"] for l in locations]
    chosen = request.args.get("loc", type=int)

    if chosen in ids:
        state["location"] = chosen
    elif state["location"] not in ids and ids:
        state["location"] = ids[0]

    name = next(
        (
            l["LOCATION_NAME"] for l in locations
            if l["LOCATIONID"] == state["location"]
        ),
        "-"
    )

    return render_template(
        "dashboard.html",
        locations=locations,
        selected=state["location"],
        name=name
    )


@public_bp.route("/panel")
def panel():
    return render_template(
        "panel.html",
        count=state["count"],
        level=state["level"],
        error=state["error"],
        name=next(
            (
                l["LOCATION_NAME"]
                for l in query(
                    "SELECT * FROM LOCATION WHERE STATUS='active'"
                )
                if l["LOCATIONID"] == state["location"]
            ),
            "-"
        )
    )

@public_bp.route("/video")
def video():
    def stream():
        while True:
            jpg = state["frame"] or placeholder()

            yield (
                b"--frame\r\n"
                b"Content-Type: image/jpeg\r\n\r\n"
                + jpg + b"\r\n"
            )

            time.sleep(0.05)

    return Response(
        stream(),
        mimetype="multipart/x-mixed-replace; boundary=frame"
    )


@public_bp.route("/status")
def status():
    return jsonify(
        count=state["count"],
        level=state["level"],
        error=state["error"]
    )


@public_bp.route("/chart.png")
def chart():
    rows = query(
        """SELECT CAST(strftime('%H', TIMESTAMP) AS INTEGER) AS h,
        AVG(CROWD_COUNT) AS c
        FROM CROWD_LOG
        WHERE LOCATIONID=?
        GROUP BY h ORDER BY h""",
        (state["location"],)
    )

    fig = Figure(figsize=(4, 3), dpi=100)
    ax = fig.subplots()

    if rows:
        ax.bar(
            [r["h"] for r in rows],
            [r["c"] for r in rows],
            color="#4f7df3",
            width=1.0
        )
        ax.set_xlabel("Time (hour of day)")
        ax.set_ylabel("Number of People")
    else:
        ax.text(0.5, 0.5, "No data yet", ha="center", va="center")
        ax.set_axis_off()

    fig.tight_layout()

    buf = io.BytesIO()
    fig.savefig(buf, format="png")

    return Response(
        buf.getvalue(),
        mimetype="image/png",
        headers={"Cache-Control": "no-store"}
    )