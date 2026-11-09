import hashlib
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from models.google_account import GoogleAccount
from models.google_session import GoogleSession

def get_account_for_session(
    session_token: str | None,
    db: Session
) -> GoogleAccount | None:
    if not session_token:
        return None

    token_hash = hashlib.sha256(session_token.encode("utf-8")).hexdigest()
    session = db.get(GoogleSession, token_hash)
    if session is None:
        return None

    expires_at = session.expires_at
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)

    if expires_at <= datetime.now(timezone.utc):
        db.delete(session)
        db.commit()
        return None

    return db.get(GoogleAccount, session.account_id)