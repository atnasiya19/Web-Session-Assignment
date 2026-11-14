# Part 2: Session Expiration

## Objective

This part of the project examines how a web application limits the lifetime of an authenticated session and what happens when a user attempts to continue using a session after that limit has passed. The demonstration application is a Flask server configured with a deliberately short session timeout of 60 seconds, so that expiration can be observed within a single short experiment.

## Client-side and server-side sessions

HTTP is a stateless protocol. Each request is handled independently, and the server has no built-in memory of earlier requests from the same browser. Web applications therefore need a mechanism that associates successive requests with one logged-in user. That mechanism is the session, and there are two broad ways of storing it.

In a client-side session, the session data itself, such as the username, is placed inside a cookie and stored by the browser. The server usually signs the cookie so that it can detect tampering. The server keeps no record of the session, so it cannot revoke an individual session before the cookie expires. It also has to trust any expiry information carried inside the cookie.

In a server-side session, the server keeps the session data in its own storage and sends the browser only a random, meaningless identifier. On every request the browser returns this identifier, and the server looks it up to decide whether the request belongs to a valid session. Because the authoritative record lives on the server, the server alone decides whether a session is still valid, and it can end a session at any time by deleting the record.

The application in this project uses server-side sessions. After a successful login, the server generates a random identifier with `secrets.token_urlsafe(32)`. It stores the username and the creation time in a server-side dictionary, `active_sessions`, and sends the identifier to the browser in a cookie named `session_id`. The cookie contains no user information, only the identifier.

## Session timeout in this application

The session timeout is the maximum length of time a session remains valid. In this application it is set by the constant `SESSION_TIMEOUT = 60` and is enforced at two levels.

At the client level, the cookie is issued with `Max-Age=60`, together with the corresponding `Expires` date. This instructs the browser to delete the cookie 60 seconds after it was set. The cookie is also marked `HttpOnly`, which prevents page scripts from reading it, and `SameSite=Lax`, which restricts it from being sent with most cross-site requests.

At the server level, every request to `/dashboard` looks up the session and compares the current time with the session's recorded `created_at` time. If more than 60 seconds have elapsed, the server deletes the session from `active_sessions` and redirects the user to the login page.

The server-level check is the one that matters for security. Cookie expiry is only an instruction to the browser, and a client can ignore it, either by editing the cookie or by sending the identifier from a tool such as curl. The server check guarantees that an expired identifier is rejected however it is presented.

This timeout is absolute, not idle. It is measured from the moment of login, and activity does not extend it. Reloading or visiting the dashboard does not reset the timer, so a session created at 0 seconds expires at 60 seconds whether the user was active throughout or not. An idle timeout, by contrast, would restart the countdown on each request and expire the session only after a period of inactivity. The absolute model is simpler and puts a firm upper bound on how long a stolen identifier remains useful. Its cost is that an active user is required to log in again.

The page itself does not change when the session expires. The application contains no client-side timer, so the dashboard stays on screen. Expiration is detected only on the next request to the server, which is why the experiment relies on reloading the page.

## Experiment and results

The experiment was carried out in Google Chrome with Developer Tools open and the Network log preserved across navigations. The user logged in as `student01`, reloaded the dashboard immediately, waited more than 60 seconds without interacting, and reloaded again. The times below are taken from the HTTP `Date` response headers.

| Time since login | Request | Cookie sent | Response | Result |
|---|---|---|---|---|
| 0 s (14:59:36 GMT) | POST /login | — | 302 to /dashboard, `Set-Cookie: session_id; Max-Age=60; HttpOnly; SameSite=Lax` | Dashboard displayed |
| 4 s (14:59:40 GMT) | GET /dashboard (reload) | Yes | 200 OK | Dashboard displayed, session active |
| 71 s (15:00:47 GMT) | GET /dashboard (reload) | No | 302 to / | Login page displayed |

These observations are consistent with an earlier command-line test using curl, in which the old cookie was deliberately sent again after expiry. The dashboard returned 200 at 0 and 30 seconds, and 302 to the login page at about 65 seconds even though the identifier was still presented. A fresh login after expiry succeeded and produced a new, valid session.

### Screenshots

| File | Shows |
|---|---|
| [`1_set_cookie_login.png`](screenshots/1_set_cookie_login.png) | `POST /login` returning 302 with `Set-Cookie: … Max-Age=60; HttpOnly; Path=/; SameSite=Lax` |
| [`2_application_session_id.png`](screenshots/2_application_session_id.png) | The `session_id` cookie stored by Chrome, expiring at 15:00:36, HttpOnly, SameSite=Lax |
| [`3_network_dashboard_200.png`](screenshots/3_network_dashboard_200.png) | Reload 4 s after login: `GET /dashboard` 200 OK, with the cookie sent |
| [`3_dashboard_page.png`](screenshots/3_dashboard_page.png) | The dashboard returned by that request ("Your session is currently active.") |
| [`4_network_dashboard_302.png`](screenshots/4_network_dashboard_302.png) | Reload 71 s after login: `GET /dashboard` 302 to `/`, with no cookie sent |

## Behaviour after expiry

The two tests show both layers of the timeout working. In the browser, the cookie's expiry time of 15:00:36 had passed by the time of the final reload. Chrome had therefore already deleted the cookie and sent the request without any `Cookie` header. The server found no session identifier and redirected the user to the login page.

In the curl test, the client kept the old identifier and presented it after the timeout. Here the server's own age check detected that the session was more than 60 seconds old, deleted the session record, and again redirected to the login page. In both cases the expired session could not be used to access the protected page.

After expiry, the user must authenticate again. A successful login creates a new identifier and a new 60-second session, and the expired identifier is never accepted again. One limitation of the current implementation is that an expired session is removed from server memory only when a request presents its identifier. If the browser discards the cookie first, as it did in this experiment, the stale record stays in `active_sessions` until the server restarts. A production system would normally add a periodic clean-up of expired sessions.

## Conclusion

The experiment confirms that the application enforces a 60-second absolute session timeout. Requests made within the timeout are served normally, while requests made after it are redirected to the login page, whether the browser has discarded the cookie or the client still holds and resends it. Because the expiry decision is made on the server from the session's recorded creation time, it does not depend on the browser cooperating, and that independence is what makes server-side session expiration reliable.
