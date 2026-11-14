
from flask import (
    Flask, render_template, request,
    redirect, url_for, make_response
)
import secrets
import time

app = Flask(__name__)

# Session lifetime in seconds (kept short for the demonstration).
# Used for BOTH the cookie's max_age (client side) and the server check.
SESSION_TIMEOUT = 60

# Temporary server-side session storage:
# session_id -> {"username": str, "created_at": float}
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
        active_sessions[session_id] = {
            "username": username,
            "created_at": time.time(),
        }

        # Send the session ID to the browser as a cookie
        response = make_response(redirect(url_for("dashboard")))

        response.set_cookie(
            "session_id",
            session_id,
            max_age=SESSION_TIMEOUT,
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
    session_data = active_sessions.get(session_id)

    if not session_data:
        return redirect(url_for("home"))

    # Server-side expiry check: do not trust the browser to drop the cookie
    age = time.time() - session_data["created_at"]

    if age > SESSION_TIMEOUT:
        # Session expired: remove it from the server
        del active_sessions[session_id]
        return redirect(url_for("home"))

    return render_template("dashboard.html", username=session_data["username"])


if __name__ == "__main__":
    app.run(debug=True)
