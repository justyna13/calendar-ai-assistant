from datetime import datetime
from typing import Any

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

from config.settings import settings
from models.google_account import GoogleAccount
from services.token_crypto import decrypt_token


def get_calendar_events_form_google(
    account: GoogleAccount,
    time_min: datetime,
    time_max: datetime | None = None,
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

    list_arguments: dict[str, Any] = {
        "calendarId": "primary",
        "timeMin": time_min.isoformat(),
        "maxResults": 100,
        "singleEvents": True,
        "orderBy": "startTime",
    }
    if time_max is not None:
        list_arguments["timeMax"] = time_max.isoformat()

    results = calendar.events().list(**list_arguments).execute()

    return results.get("items", [])