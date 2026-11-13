import json
import unicodedata
from datetime import date, datetime, timezone
from typing import Any
from zoneinfo import ZoneInfo

from fastapi import APIRouter, Depends, HTTPException, Request
from google.auth.exceptions import RefreshError
from googleapiclient.errors import HttpError
from openai import OpenAI
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from config.settings import settings
from database import get_db
from services.google_calendar import get_calendar_events_form_google
from services.session_store import get_account_for_session

router = APIRouter(prefix="/api", tags=["chat"])

class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=2000)


def parse_iso_datetime(value: str | datetime) -> datetime:
    if isinstance(value, datetime):
        parsed = value
    else:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))

    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)

    return parsed


def is_next_event_request(message: str) -> bool:
    normalized = (
        unicodedata.normalize("NFKD", message)
        .encode("ascii", "ignore")
        .decode("ascii")
        .casefold()
    )
    asks_for_next = any(
        term in normalized
        for term in ("najbliz", "nastepne", "kolejne", "next", "upcoming")
    )
    mentions_calendar_item = any(
        term in normalized
        for term in ("wydarzen", "spotkan", "termin", "event", "meeting")
    )
    return asks_for_next and mentions_calendar_item


def format_next_event(events: list[dict[str, Any]], current_time: datetime) -> str:
    for event in events:
        start = event.get("start", {})
        if start.get("dateTime"):
            starts_at = parse_iso_datetime(start["dateTime"]).astimezone(
                current_time.tzinfo
            )
            if starts_at < current_time:
                continue
            when = starts_at.strftime("%d.%m.%Y, %H:%M")
        elif start.get("date"):
            starts_on = date.fromisoformat(start["date"])
            if starts_on < current_time.date():
                continue
            when = f"{starts_on:%d.%m.%Y} (cały dzień)"
        else:
            continue

        title = event.get("summary") or "Bez tytułu"
        return f"Najbliższe wydarzenie: {when} — {title}"

    return "Nie widzę nadchodzących wydarzeń w Twoim kalendarzu."

def validate_calendar_tool_args(raw_args: dict[str, Any]) -> dict[str, str]:
    if not isinstance(raw_args, dict):
        raise ValueError("Calendar tool args must be a JSON object.")

    time_min_raw = raw_args.get("time_min")
    time_max_raw = raw_args.get("time_max")

    if not time_min_raw or not time_max_raw:
        raise ValueError("time_min and time_max are required")

    time_min = parse_iso_datetime(time_min_raw)
    time_max = parse_iso_datetime(time_max_raw)

    if time_min >= time_max:
        raise ValueError("time_min must be earlier than time_max.")

    payload: dict[str, str] = {
        "time_min": time_min.isoformat(),
        "time_max": time_max.isoformat(),
    }

    query = raw_args.get("query")
    if query is not None and str(query).strip():
        payload["query"] = str(query).strip()

    return payload

def build_calendar_tool() -> dict[str, Any]:
    return {
        "type": "function",
        "function": {
            "name": "get_calendar_events",
            "description": "List calendar events for the authenticated user in a specific time window.",
             "parameters": {
                "type": "object",
                "properties": {
                    "time_min": {
                        "type": "string",
                        "format": "date-time",
                        "description": "Earliest time in ISO-8601 format with timezone.",
                    },
                    "time_max": {
                        "type": "string",
                        "format": "date-time",
                        "description": "Latest time in ISO-8601 format with timezone.",
                    },
                    "query": {
                        "type": "string",
                        "description": "Optional natural-language filter describing what events matter to the user.",
                    },
                },
                "required": ["time_min", "time_max"],
                "additionalProperties": False,
            },
        }
    }

def get_calendar_events_tool(account, payload: dict[str, str]) -> list[dict[str, Any]]:
    time_min = parse_iso_datetime(payload["time_min"])
    time_max = parse_iso_datetime(payload["time_max"])
    return get_calendar_events_form_google(account, time_min, time_max)

@router.post("/chat")
def chat_with_calendar(
    payload: ChatRequest,
    request: Request,
    db: Session = Depends(get_db)
) -> dict[str, str]:
    account = get_account_for_session(request.cookies.get("session"), db)
    if account is None:
        raise HTTPException(status_code=401, detail="Not authenticated")

    client = OpenAI(base_url=settings.ollama_base_url, api_key="ollama")

    tools = [build_calendar_tool()]

    current_time = datetime.now(ZoneInfo("Europe/Warsaw"))

    if is_next_event_request(payload.message):
        try:
            events = get_calendar_events_form_google(account, current_time)
        except RefreshError as exc:
            raise HTTPException(
                status_code=502,
                detail="Google authorization could not be refreshed. Please sign in again.",
            ) from exc
        except HttpError as exc:
            google_status = getattr(exc.resp, "status", None)
            detail = (
                "Google Calendar denied access. Check the app's Calendar permissions."
                if google_status == 403
                else "Google Calendar is temporarily unavailable."
            )
            raise HTTPException(status_code=502, detail=detail) from exc

        return {"reply": format_next_event(events, current_time)}

    system_message = (
        f"Aktualna data i godzina to {current_time.isoformat()}. "
        "Względne określenia dat, takie jak «dzisiaj», «jutro» i «w tym tygodniu», "
        "interpretuj względem tej daty i strefy Europe/Warsaw. "
        "Tydzień trwa od poniedziałku do niedzieli. "
        "Jesteś pomocnym asystentem kalendarza. "
        "Odpowiadaj zawsze po polsku, chyba że użytkownik prosi o inny język. "
        "Używaj narzędzia get_calendar_events, gdy użytkownik pyta o nadchodzące wydarzenia, dostępność lub planowanie. "
        "Jeśli korzystasz z narzędzia, opieraj odpowiedź na danych z kalendarza. "
        "Odpowiedzi mają być krótkie, konkretne i przyjazne. "
        "Listę wydarzeń zapisuj jako zwykły tekst, po jednym wydarzeniu w każdym wierszu, bez Markdown, pogrubień i emoji. "
        "Dla każdego wydarzenia podaj datę, godzinę (jeśli jest) i tytuł; wydarzenia całodniowe oznacz jako całodniowe. "
        "W danych Google Calendar end.date jest datą końcową wyłączną: nie pokazuj jej jako dnia wydarzenia. "
        "Dla wydarzenia jednodniowego pokaż tylko datę startu, a dla wielodniowego zakończ na dniu poprzedzającym end.date."
    )

    messages = [
        {"role": "system", "content": system_message},
        {"role": "user", "content": "Odpowiedz po polsku. " + payload.message}
    ]

    try:
        first_response = client.chat.completions.create(
            model=settings.ollama_model,
            messages=messages,
            tools=tools,
            temperature=0.2
        )
        assistant_message = first_response.choices[0].message
    except Exception as exc:
        raise HTTPException(
            status_code=502,
            detail="The local Ollama model is unavailable. Please ensure it is running"
        ) from exc

    if not assistant_message.tool_calls:
        reply = assistant_message.content or "I can help with your calendar, but I need a question about planned events or availbility."
        return {"reply": reply}

    tool_results = []
    assistant_tool_calls = []

    for tool_call in assistant_message.tool_calls:
        assistant_tool_calls.append(
            {
                "id": tool_call.id,
                "type": tool_call.type,
                "function": {
                    "name": tool_call.function.name,
                    "arguments": tool_call.function.arguments,
                },
            }
        )

        if tool_call.function.name != "get_calendar_events":
            tool_results.append(
                {
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "name": tool_call.function.name,
                    "content": json.dumps({"error": "Unsupported tool requested."}),
                }
            )
            continue

        try:
            arguments = json.loads(tool_call.function.arguments or "{}")
            validate_args = validate_calendar_tool_args(arguments)
            events = get_calendar_events_tool(account, validate_args)

            tool_results.append(
                {
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "name": tool_call.function.name,
                    "content": json.dumps(events),
                }
            )
        except (TypeError, ValueError, json.JSONDecodeError) as exc:
            tool_results.append(
                {
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "name": tool_call.function.name,
                    "content": json.dumps({"error": str(exc)}),
                }
            )

    follow_up_message = messages + [
        {
            "role": "assistant",
            "content": assistant_message.content or "",
            "tool_calls": assistant_tool_calls,
        },
        *tool_results,
    ]

    try:
        final_response = client.chat.completions.create(
            model=settings.ollama_model,
            messages=follow_up_message,
            temperature=0.2
        )
    except Exception as exc:
        raise HTTPException(
            status_code=502,
            detail="The local Ollama model rejected the tool results. Please try again.",
        ) from exc

    reply = final_response.choices[0].message.content or "I could not produce a final answer from the model."
    return {"reply": reply}