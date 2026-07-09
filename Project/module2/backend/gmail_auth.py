import asyncio
from pathlib import Path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

SCOPES = [
    "https://www.googleapis.com/auth/gmail.send",
    "https://www.googleapis.com/auth/gmail.readonly",
]

STORAGE_DIR = Path(__file__).parent / "storage"
CREDENTIALS_PATH = STORAGE_DIR / "credentials.json"
TOKEN_PATH = STORAGE_DIR / "token.json"


def load_credentials() -> Credentials:
    STORAGE_DIR.mkdir(parents=True, exist_ok=True)

    creds = None
    if TOKEN_PATH.exists():
        creds = Credentials.from_authorized_user_file(str(TOKEN_PATH), SCOPES)

    if creds and creds.valid:
        return creds

    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())
        TOKEN_PATH.write_text(creds.to_json())
        return creds

    if not CREDENTIALS_PATH.exists():
        raise FileNotFoundError(
            f"Missing {CREDENTIALS_PATH}. Follow the Google Cloud OAuth setup steps in "
            "README.md to download your OAuth client credentials and place them there."
        )

    flow = InstalledAppFlow.from_client_secrets_file(str(CREDENTIALS_PATH), SCOPES)
    creds = flow.run_local_server(port=0)
    TOKEN_PATH.write_text(creds.to_json())
    return creds


async def get_credentials() -> Credentials:
    return await asyncio.to_thread(load_credentials)


def build_gmail_service(creds: Credentials):
    return build("gmail", "v1", credentials=creds)
