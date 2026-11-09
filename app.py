
from flask import (
    Flask, render_template, request,
    redirect, url_for, make_response
)
import secrets

app = Flask(__name__)

# Temporary server-side session storage
active_sessions = {}

# Demonstration account
TEST_USERNAME = "student01"
TEST_PASSWORD = "demo123"


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/login", methods=["POST"])
def login():
    username = request.form.get("username")
    password = request.form.get("password")

    # Verify login credentials
    if username == TEST_USERNAME and password == TEST_PASSWORD:

        # Generate a random session identifier
        session_id = secrets.token_urlsafe(32)

        # Store the session on the server
        active_sessions[session_id] = username

        # Send the session ID to the browser as a cookie
        response = make_response(redirect(url_for("dashboard")))

        response.set_cookie(
            "session_id",
            session_id,
            max_age=600,
            httponly=True,
            secure=False,
            samesite="Lax",
            path="/"
        )

        return response

    return render_template(
        "index.html",
        error="Invalid username or password."
    )


@app.route("/dashboard")
def dashboard():

    # Read the session cookie sent by the browser
    session_id = request.cookies.get("session_id")

    # Check whether the session exists on the server
    username = active_sessions.get(session_id)

    if not username:
        return redirect(url_for("home"))

    return render_template("dashboard.html", username=username)


if __name__ == "__main__":
    app.run(debug=True)
