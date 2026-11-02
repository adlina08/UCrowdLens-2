
from functools import wraps

from flask import (
    Blueprint,
    flash,
    redirect,
    render_template,
    request,
    session,
    url_for
)

from db import query

auth_bp = Blueprint("auth", __name__)


# =========================
# LOGIN REQUIRED
# =========================
def login_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if not session.get("admin"):
            return redirect(url_for("auth.login"))

        return f(*args, **kwargs)

    return wrapper


# =========================
# ADMIN LOGIN
# =========================
@auth_bp.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":
        rows = query(
            "SELECT * FROM ADMIN WHERE USERNAME = ?",
            (request.form["username"],)
        )

        if rows and rows[0]["PASSWORD"] == request.form["password"]:
            session["admin"] = True

            flash("Login successful!")

            return redirect(url_for("public.dashboard"))

        flash("Wrong username or password.")

    return render_template("login.html")


# =========================
# ADMIN LOGOUT
# =========================
@auth_bp.route("/logout")
def logout():

    session.clear()

    return """
    <script>
        alert("You have successfully logged out!");
        window.location.href = "/";
    </script>
    """
