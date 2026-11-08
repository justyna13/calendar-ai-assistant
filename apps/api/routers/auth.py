import secrets

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import RedirectResponse, JSONResponse
from google_auth_oauthlib.flow import Flow

from config.settings import settings

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
def google_callback(request: Request) -> JSONResponse:
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

    response = JSONResponse({"message": "Google authorization successful"})
    response.delete_cookie("oauth_state", path="/auth")

    return response