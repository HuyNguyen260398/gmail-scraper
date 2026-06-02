"""OAuth2 authentication for the Gmail API.

Handles the interactive consent flow on first run and caches a refresh
token locally so subsequent runs are headless. For production on AWS,
swap the token file for Secrets Manager / SSM Parameter Store.
"""

import os
from pathlib import Path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow

# Read-only is enough to list and read messages. Widen this scope only if
# you later need to modify, send, or delete mail.
SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]

CONFIG_DIR = Path(__file__).resolve().parent.parent / "config"
CREDENTIALS_FILE = CONFIG_DIR / "credentials.json"  # downloaded from Google Cloud Console
TOKEN_FILE = CONFIG_DIR / "token.json"              # generated on first run


def get_credentials() -> Credentials:
    """Return valid user credentials, running the consent flow if needed."""
    creds = None

    if TOKEN_FILE.exists():
        creds = Credentials.from_authorized_user_file(str(TOKEN_FILE), SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not CREDENTIALS_FILE.exists():
                raise FileNotFoundError(
                    f"Missing {CREDENTIALS_FILE}. Download an OAuth client ID "
                    "(Desktop app) from the Google Cloud Console and save it there."
                )
            flow = InstalledAppFlow.from_client_secrets_file(
                str(CREDENTIALS_FILE), SCOPES
            )
            creds = flow.run_local_server(port=0)

        TOKEN_FILE.write_text(creds.to_json())
        os.chmod(TOKEN_FILE, 0o600)

    return creds
