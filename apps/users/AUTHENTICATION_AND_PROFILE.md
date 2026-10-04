# Users Authentication and Profile API

## Database setup

Apply all database migrations after deployment, including the Simple JWT token blacklist tables:

```powershell
python manage.py migrate
```

## Registration and login

All registration endpoints automatically sign the user in and return an access token, a refresh token, and basic user data. Email verification is not required. Phone users are not created until their OTP is verified.

| Method | Endpoint | Request body |
| --- | --- | --- |
| POST | `/api/users/auth/register/email/` | `{"email":"person@example.com","password":"..."}` |
| POST | `/api/users/auth/login/email/` | `{"email":"person@example.com","password":"..."}` |
| POST | `/api/users/auth/register/phone/request-code/` | `{"phone_number":"09123456789"}` |
| POST | `/api/users/auth/register/phone/verify-code/` | `{"phone_number":"09123456789","code":"123456"}` |
| POST | `/api/users/auth/login/phone/request-code/` | `{"phone_number":"09123456789"}` |
| POST | `/api/users/auth/login/phone/verify-code/` | `{"phone_number":"09123456789","code":"123456"}` |

Email addresses are validated, normalized to lowercase, and unique. Passwords use Django's configured password validators and password hashing; profile updates cannot change account credentials. Use HTTPS for all production requests. `SECURE_SSL_REDIRECT` defaults to enabled when `DEBUG=False`; if TLS ends at a reverse proxy, configure that proxy and Django's deployment settings together.

## Phone OTP behavior

OTP codes contain six digits, expire after five minutes, and allow at most five verification attempts. Only a keyed digest is stored. A new code invalidates the previous unused code. A phone can request a new code once per 60 seconds; request and verification endpoints also have IP rate limits. Unknown and known phone numbers receive the same request response to reduce account discovery. A phone is marked verified only after successful code verification. Existing phone accounts become verified the first time they complete OTP login.

Run `python manage.py cleanup_expired_otps` daily to remove expired OTP records and consumed records older than one day.
Also run `python manage.py flushexpiredtokens` daily to prune expired refresh-token records.

The project has an SMS webhook adapter, but no SMS vendor is configured. Set these values in `.env.local` to enable delivery:

```dotenv
SMS_PROVIDER_URL=https://sms-provider.example/api/messages
SMS_PROVIDER_TOKEN=your-provider-token
```

The HTTPS endpoint must accept `POST` JSON with `phone_number` and `message`, and return a successful HTTP response. When configured, the bearer token is sent in the `Authorization` header. Until this is configured, code requests return `503`; the code is never returned to the client or written to application logs.

## Tokens, sessions, and logout

Send the access token on protected API requests as `Authorization: JWT <access>`. Access tokens last seven minutes and refresh tokens last seven days. Refresh tokens rotate on use; each replaced refresh token is blacklisted. Refresh and verification endpoints are:

- `POST /api/users/auth/token/refresh/` with `{"refresh":"..."}`
- `POST /api/users/auth/token/verify/` with `{"token":"..."}`

The generic `/api/token/` password login endpoint was removed so phone/password authentication cannot bypass the OTP flow. Refresh is accepted only for an active account and an unchanged password. Tokens issued before this change do not contain the password-revocation claim and must be replaced by signing in again.

Multiple devices may be signed in at once. `POST /api/users/auth/logout/` requires the current device's refresh token, checks that it belongs to the authenticated user, then blacklists it. `POST /api/users/auth/logout/all/` blacklists all refresh tokens for that user. After either logout endpoint, the frontend should clear its locally stored access and refresh tokens. Access tokens from a normal logout remain usable until their seven-minute expiration; account deactivation rejects them immediately.

`POST /api/users/auth/change-password/` requires `current_password` and `new_password`. It validates the new password, revokes all refresh tokens, and invalidates old access tokens immediately. Password recovery is not exposed because the project does not yet verify email ownership or have an SMS recovery flow.

The frontend should store the authentication state only after a successful login/registration response. When the access token expires, request a new pair with the refresh endpoint and retry the protected request once. If refresh fails, clear local tokens and show the login screen. This repository contains the backend API only, so it does not include client-side token storage or navigation code.

## Errors and limits

Authentication errors use English messages. Login failures use `401`; inactive accounts use `403`; invalid request data uses `400`; duplicate email uses `409`; OTP attempt exhaustion and rate-limit responses use `429`; unavailable SMS delivery uses `503`. OTP errors distinguish invalid, expired, missing, and exhausted codes. Email login, registration, OTP, refresh, and token verification have IP-based rate limits.
For multi-worker production deployments, configure Django's default cache to use a shared backend so IP limits are shared across workers.

## Profile and presence

`PATCH /api/users/update/` accepts profile fields including first/last name, date of birth, province, city, bio, profile picture, gender, and interests. Use `multipart/form-data` for a profile picture. Email, phone number, and verification state can only be changed through their respective verification flows.

Age is recalculated from date of birth and stored when the user is saved. It is read-only through the API. `GET /api/users/profile/` returns the current user's profile.

While the app is active, call `POST /api/users/presence/heartbeat/` every 60 seconds with the access token. The profile and Discover APIs report `is_online=true` when the last heartbeat is within five minutes.
