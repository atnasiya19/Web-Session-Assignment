# Part 3: Logout Behavior and Session Invalidation

## Objective
The goal of this experiment is to demonstrate that a secure logout must do more than just navigate the user away from the dashboard or delete the browser cookie. It must invalidate the session on the server side to prevent "Session Hijacking" (where a stolen cookie is reused).

## The Technical Breakdown
When a user clicks "Logout," two things must happen simultaneously:
1. **Client-Side:** The browser must be instructed to delete the session cookie so it stops sending it in HTTP requests.
2. **Server-Side:** The server must delete the session ID from its internal memory (in our app, the `active_sessions` dictionary). 

If the server only deletes the browser cookie but keeps the session alive in memory, an attacker who intercepted the cookie could continue to access the protected dashboard.

## The Experiment (Replay Attack)
To test this, we simulate a stolen cookie attack:
1. Log in to the application and copy the `session_id` cookie from the browser's Developer Tools.
2. Click the Logout button.
3. Use the Developer Console to manually force the old, stolen `session_id` cookie back into the browser.
4. Attempt to access the `/dashboard` route.

## Expected Result
The server must reject the request and redirect the user back to the login page. Even though the browser has the cookie, the server checks its internal `active_sessions` dictionary, sees the session was destroyed, and denies access.

## The Code Evidence
In our `app.py`, the dashboard route includes a critical security check:

```python
@app.route("/dashboard")
def dashboard():
    session_id = request.cookies.get("session_id")
    session_data = active_sessions.get(session_id)
    
    # If the session ID is not in the server's memory, deny access!
    if not session_data:
        return redirect(url_for("home"))

***
