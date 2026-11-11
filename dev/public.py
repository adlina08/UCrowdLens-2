import io
import time

from flask import Blueprint, Response, jsonify, render_template, request
from matplotlib.figure import Figure
from matplotlib.patches import FancyBboxPatch
from matplotlib.ticker import MaxNLocator

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

    # Dark, responsive-friendly chart rendered from real SQLite hourly averages.
    fig = Figure(figsize=(12, 3.3), dpi=130, facecolor="#0B0E13")
    ax = fig.subplots()
    ax.set_facecolor("#0B0E13")

    hours = list(range(24))
    averages = {int(row["h"]): float(row["c"]) for row in rows}
    values = [averages.get(hour, 0) for hour in hours]

    if rows:
        max_value = max(values)
        upper = max(1.0, max_value * 1.18)
        bar_width = 0.70
        for hour, value in zip(hours, values):
            if value <= 0:
                continue
            bar = FancyBboxPatch(
                (hour - bar_width / 2, 0), bar_width, value,
                boxstyle="round,pad=0,rounding_size=0.10",
                linewidth=0,
                facecolor="#D7FF3C" if hour >= 16 else "#91A928"
            )
            ax.add_patch(bar)
        ax.set_xlim(-0.8, 23.8)
        ax.set_ylim(0, upper)
        ax.set_xticks([0, 4, 8, 12, 16, 20, 23])
        ax.set_xticklabels(["12 AM", "4 AM", "8 AM", "12 PM", "4 PM", "8 PM", "11 PM"])
        ax.yaxis.set_major_locator(MaxNLocator(nbins=4))
        ax.grid(axis="y", color="#303742", linewidth=0.7, alpha=0.55)
        ax.set_axisbelow(True)
        ax.tick_params(colors="#AEB8C7", labelsize=10, length=0, pad=10)
        for spine in ax.spines.values():
            spine.set_visible(False)
        ax.set_ylabel("Average people", color="#AEB8C7", fontsize=10, labelpad=10)
    else:
        ax.text(0.5, 0.5, "No crowd history yet", color="#AEB8C7",
                ha="center", va="center", fontsize=14, transform=ax.transAxes)
        ax.set_axis_off()

    fig.subplots_adjust(left=0.065, right=0.99, top=0.95, bottom=0.18)
    buf = io.BytesIO()
    fig.savefig(buf, format="png", facecolor=fig.get_facecolor())

    return Response(
        buf.getvalue(),
        mimetype="image/png",
        headers={"Cache-Control": "no-store"}
    )