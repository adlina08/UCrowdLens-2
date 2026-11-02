
import csv
import io
import math
from datetime import datetime

from flask import Blueprint, Response, render_template, request
from db import query
from auth import login_required

logs_bp = Blueprint("logs", __name__)


# =========================
# FORMAT TIMESTAMP
# =========================
def fmt_time(value):
    if not value:
        return "-"

    try:
        return datetime.fromisoformat(
            str(value)
        ).strftime("%d %b %Y, %I:%M %p")
    except (ValueError, TypeError):
        return str(value)


logs_bp.add_app_template_filter(fmt_time, "fmt_time")


# =========================
# GET FILTERED LOGS
# =========================
def get_logs():
    sql = (
        "SELECT L.TIMESTAMP, N.LOCATION_NAME, "
        "L.CROWD_COUNT, L.DENSITY_LEVEL "
        "FROM CROWD_LOG L "
        "JOIN LOCATION N ON N.LOCATIONID = L.LOCATIONID "
        "WHERE 1=1"
    )

    args = []
    f = request.args

    if f.get("date_from"):
        sql += " AND L.TIMESTAMP >= ?"
        args.append(f["date_from"] + " 00:00:00")

    if f.get("date_to"):
        sql += " AND L.TIMESTAMP <= ?"
        args.append(f["date_to"] + " 23:59:59")

    if f.get("location"):
        sql += " AND L.LOCATIONID = ?"
        args.append(f["location"])

    if f.get("density"):
        sql += " AND L.DENSITY_LEVEL = ?"
        args.append(f["density"])

    return query(sql + " ORDER BY L.TIMESTAMP DESC", args)



# =========================
# VIEW LOGS - LATEST 100, 20 PER PAGE
# =========================
@logs_bp.route("/logs")
@login_required
def logs():
    all_logs = get_logs()[:100]

    per_page = 20
    total = len(all_logs)
    total_pages = max(1, math.ceil(total / per_page))

    page = request.args.get("page", 1, type=int)
    page = max(1, min(page, total_pages))

    start = (page - 1) * per_page
    page_logs = all_logs[start:start + per_page]

    return render_template(
        "logs.html",
        logs=page_logs,
        f=request.args,
        locations=query("SELECT * FROM LOCATION"),
        page=page,
        total_pages=total_pages,
        total=total
    )



# =========================
# DOWNLOAD CSV
# =========================
@logs_bp.route("/download")
@login_required
def download():
    out = io.StringIO()
    writer = csv.writer(out)

    writer.writerow(["Time", "Location", "Count", "Density"])
    writer.writerows([list(row) for row in get_logs()])

    return Response(
        out.getvalue(),
        mimetype="text/csv",
        headers={
            "Content-Disposition":
                "attachment; filename=crowd_logs.csv"
        }
    )
