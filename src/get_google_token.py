"""One-time Google OAuth helper — run locally to obtain a refresh token.

Step-by-step setup:
  1. Go to https://console.cloud.google.com/ and create (or select) a project.
  2. Enable APIs: Google Calendar API and Gmail API.
  3. Configure OAuth consent screen (External, add your email as a test user).
  4. Create OAuth credentials: Desktop app. Download the JSON as client_secret.json
     in this project root (it is gitignored).
  5. Run: python src/get_google_token.py
     A browser window will open; sign in and grant read-only access.
  6. Copy the printed client_id, client_secret, and refresh_token into your
     .env file (or GitHub Actions secrets).

Scopes granted:
  https://www.googleapis.com/auth/calendar.readonly
  https://www.googleapis.com/auth/gmail.readonly
"""

import os
from google_auth_oauthlib.flow import InstalledAppFlow

_SCOPES = [
    "https://www.googleapis.com/auth/calendar.readonly",
    "https://www.googleapis.com/auth/gmail.readonly",
]

_SECRET_FILE = os.path.join(os.path.dirname(__file__), "..", "client_secret.json")


def main():
    flow = InstalledAppFlow.from_client_secrets_file(_SECRET_FILE, _SCOPES)
    creds = flow.run_local_server(port=0)

    print("\n── Google OAuth credentials ──────────────────────────")
    print(f"GOOGLE_CLIENT_ID     = {creds.client_id}")
    print(f"GOOGLE_CLIENT_SECRET = {creds.client_secret}")
    print(f"GOOGLE_REFRESH_TOKEN = {creds.refresh_token}")
    print("─────────────────────────────────────────────────────")
    print("Add these to your .env and/or GitHub Actions secrets.")


if __name__ == "__main__":
    main()
