import secrets
import hashlib

from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import RedirectResponse, JSONResponse
from google_auth_oauthlib.flow import Flow
from google.auth.transport.requests import Request as GoogleRequest
from google.oauth2 import id_token
from sqlalchemy import select
from sqlalchemy.orm import Session

from config.settings import settings
from database import get_db
from models.google_account import GoogleAccount
from models.google_session import GoogleSession
from services.token_crypto import encrypt_token

router = APIRouter()

SCOPES = [
    "openid",
    "https://www.googleapis.com/auth/userinfo.email",
    "https://www.googleapis.com/auth/calendar.events.owned.readonly",
]

CLIENT_CONFIG = {
    "web": {
        "client_id": settings.google_client_id,
        "client_secret": settings.google_client_secret.get_secret_value(),
        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
        "token_uri": "https://oauth2.googleapis.com/token",
        "redirect_uris": [settings.google_redirect_uri],
    }
}

@router.get('/auth/google')
def google_auth() -> RedirectResponse:
    flow = Flow.from_client_config(
        CLIENT_CONFIG,
        scopes=SCOPES,
        redirect_uri=settings.google_redirect_uri,
    )
    authorization_url, state = flow.authorization_url(
        access_type='offline',
        include_granted_scopes='true',
        prompt="consent",
    )

    response = RedirectResponse(authorization_url, status_code=302)
    response.set_cookie(
        key="oauth_state",
        value=state,
        httponly=True,
        secure=False,
        samesite="lax",
        max_age=600,
        path="/auth"
    )

    code_verifier = flow.code_verifier
    if code_verifier is None:
        raise RuntimeError("Code verifier is not set. Ensure that the OAuth flow is properly configured.")

    response.set_cookie(
        key="oauth_code_verifier",
        value=code_verifier,
        httponly=True,
        secure=False,
        samesite="lax",
        max_age=600,
        path="/auth"
    )

    return response

@router.get("/auth/callback")
def google_callback(
    request: Request,
    db: Session = Depends(get_db)
) -> RedirectResponse:
    oauth_error = request.query_params.get("error")
    if oauth_error:
        raise HTTPException(
            status_code=400,
            detail="Google authorization was not granted. Please try again.",
        )

    returned_state = request.query_params.get("state")
    saved_state = request.cookies.get("oauth_state")

    saved_verifier = request.cookies.get("oauth_code_verifier")
    if not saved_verifier:
        raise HTTPException(status_code=400, detail="Code verifier not found in cookies")

    if (
        not returned_state
        or not saved_state
        or not secrets.compare_digest(returned_state, saved_state)
    ):
        raise HTTPException(status_code=400, detail="Invalid OAuth state")

    authorization_code = request.query_params.get("code")
    if not authorization_code:
        raise HTTPException(status_code=400, detail="Authorization code not found")

    flow = Flow.from_client_config(
        CLIENT_CONFIG,
        scopes=SCOPES,
        state=saved_state,
        redirect_uri=settings.google_redirect_uri,
        code_verifier=saved_verifier
    )
    flow.fetch_token(authorization_response=str(request.url))

    id_token_value = flow.credentials.id_token
    if not id_token_value:
        raise HTTPException(status_code=400, detail="Google ID token is missing")

    try:
        claims = id_token.verify_oauth2_token(
            id_token_value,
            GoogleRequest(),
            audience=settings.google_client_id,
        )
    except ValueError as exc:
        raise HTTPException(status_code=401, detail="Invalid Google Id token") from exc

    google_sub = claims.get("sub")

    if not google_sub or claims.get("email_verified") is not True:
        raise HTTPException(status_code=401, detail="Google account could not be verified")

    email = claims.get("email")
    refresh_token = flow.credentials.refresh_token

    account = db.scalar(
        select(GoogleAccount).where(GoogleAccount.google_sub == google_sub)
    )

    if account is None:
        if not refresh_token:
            raise HTTPException(status_code=400, detail="Google refresh token is missing")

        account = GoogleAccount(
            google_sub=google_sub,
            email=email,
            refresh_token_encrypted=encrypt_token(refresh_token),
            granted_scopes=flow.credentials.scopes or [],
        )
        db.add(account)
    else:
        account.email = email
        if refresh_token:
            account.refresh_token_encrypted = encrypt_token(refresh_token)
        account.granted_scopes = flow.credentials.scopes or account.granted_scopes

    db.flush()

    session_token = secrets.token_urlsafe(32)
    db.add(
        GoogleSession(
            token_hash=hashlib.sha256(session_token.encode("utf-8")).hexdigest(),
            account_id=account.id,
            expires_at=datetime.now(timezone.utc) + timedelta(days=7),
        )
    )
    db.commit()

    response = RedirectResponse(settings.frontend_origin, status_code=303)
    response.set_cookie(
        key="session",
        value=session_token,
        httponly=True,
        secure=False,
        samesite="lax",
        max_age=7 * 24 * 60 * 60,
        path="/",
    )
    response.delete_cookie("oauth_state", path="/auth")
    response.delete_cookie("oauth_code_verifier", path="/auth")

    return response

@router.get("/auth/session")
def get_session_status(
    request: Request,
    db: Session = Depends(get_db),
) -> dict[str, bool | str | None]:
    session_token = request.cookies.get("session")
    if not session_token:
        return {"authenticated": False, "email": None}

    token_hash = hashlib.sha256(session_token.encode("utf-8")).hexdigest()
    session = db.get(GoogleSession, token_hash)
    if session is None:
        return {"authenticated": False, "email": None}

    expires_at = session.expires_at
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)

    if expires_at <= datetime.now(timezone.utc):
        db.delete(session)
        db.commit()
        return {"authenticated": False, "email": None}

    account = db.get(GoogleAccount, session.account_id)
    if account is None:
        return {"authenticated": False, "email": None}

    return {"authenticated": True, "email": account.email}

@router.post("/auth/logout")
def logout(
    request: Request,
    db: Session = Depends(get_db)
) -> JSONResponse:
    session_token = request.cookies.get("session")

    if session_token:
        token_hash = hashlib.sha256(session_token.encode("utf-8")).hexdigest()
        session = db.get(GoogleSession, token_hash)

        if session is not None:
            db.delete(session)
            db.commit()

    response = JSONResponse({"authenticated": False})
    response.delete_cookie("session", path="/")
    return response