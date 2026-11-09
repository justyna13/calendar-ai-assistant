from datetime import datetime
from typing import Any

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

from config.settings import settings
from models.google_account import GoogleAccount
from services.token_crypto import decrypt_token


def list_events(
    account: GoogleAccount,
    time_min: datetime,
    time_max: datetime
) -> list[dict[str, Any]]:
    credentials = Credentials(
        token=None,
        refresh_token=decrypt_token(account.refresh_token_encrypted),
        token_uri="https://oauth2.googleapis.com/token",
        client_id=settings.google_client_id,
        client_secret=settings.google_client_secret.get_secret_value(),
        scopes=account.granted_scopes,
    )

    calendar = build(
        "calendar",
        "v3",
        credentials=credentials,
        cache_discovery=False,
    )

    results = (
        calendar.events()
        .list(
            calendarId="primary",
            timeMin=time_min.isoformat(),
            timeMax=time_max.isoformat(),
            maxResults=100,
            singleEvents=True,
            orderBy="startTime"
        )
        .execute()
    )

    return results.get("items", [])