
from flask import Blueprint, flash, redirect, render_template, request, url_for

from db import query
from auth import login_required

admin_bp = Blueprint("admin", __name__)


# =========================
# MANAGE LOCATIONS
# =========================
@admin_bp.route("/locations", methods=["GET", "POST"])
@login_required
def locations():

    if request.method == "POST":
        location_id = request.form.get("id")
        status = request.form.get("status")

        if not location_id or status not in ("active", "inactive"):
            flash("Invalid location status.")
            return redirect(url_for("admin.locations"))

        query(
            "UPDATE LOCATION SET STATUS = ? WHERE LOCATIONID = ?",
            (status, location_id)
        )

        print("UPDATED ROW:", [
            dict(row) for row in query(
                """
                SELECT LOCATIONID, LOCATION_NAME, STATUS
                FROM LOCATION
                WHERE LOCATIONID = ?
                """,
                (location_id,)
            )
        ])

        flash("Location status updated successfully!")
        return redirect(
            url_for("admin.locations", q=request.form.get("q", ""))
        )

    q = request.args.get("q", "").strip()

    rows = query(
        """
        SELECT *
        FROM LOCATION
        WHERE LOCATION_NAME LIKE ?
        ORDER BY LOCATIONID
        """,
        (f"%{q}%",)
    )

    return render_template(
        "locations.html",
        locations=rows,
        q=q
    )


# =========================
# MANAGE CROWD THRESHOLDS
# =========================
@admin_bp.route("/threshold", methods=["GET", "POST"])
@login_required
def threshold():

    if request.method == "POST":
        try:
            low = int(request.form["low"])
            med = int(request.form["medium"])
        except (ValueError, KeyError):
            flash("Please enter valid threshold numbers.")
            return redirect(url_for("admin.threshold"))

        if 0 <= low < med:
            query(
                """
                UPDATE THRESHOLD
                SET LOW = ?, MEDIUM = ?
                WHERE THRESHOLDID = 1
                """,
                (low, med)
            )
            flash("Threshold settings saved successfully!")
        else:
            flash("Medium must be greater than Low.")

        return redirect(url_for("admin.threshold"))

    thresholds = query(
        """
        SELECT LOW, MEDIUM
        FROM THRESHOLD
        WHERE THRESHOLDID = 1
        """
    )

    if not thresholds:
        query(
            """
            INSERT INTO THRESHOLD (THRESHOLDID, LOW, MEDIUM)
            VALUES (1, 10, 20)
            """
        )
        low, med = 10, 20
    else:
        low = thresholds[0]["LOW"]
        med = thresholds[0]["MEDIUM"]

    return render_template(
        "threshold.html",
        low=low,
        medium=med
    )
