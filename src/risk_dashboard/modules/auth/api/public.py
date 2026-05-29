from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query

from risk_dashboard.modules.auth.application.google_identity import (
    GoogleAuthConfigurationError,
    GoogleTokenInvalid,
    verify_google_credential,
)
from risk_dashboard.modules.auth.application.services import (
    AuthError,
    EmailAlreadyRegistered,
    InvalidCredentials,
    LoginAccount,
    LoginWithGoogle,
    LogoutAccount,
    RegisterAccount,
    ResolveSession,
    SessionInvalid,
)
from risk_dashboard.modules.auth.infrastructure.sqlite import (
    SqliteAccountRepository,
    SqliteAccountSessionRepository,
)
from risk_dashboard.modules.auth.schemas.auth import (
    AccountProfile,
    AuthLogoutResponse,
    AuthMeResponse,
    AuthSessionResponse,
    GoogleLoginRequest,
    LoginRequest,
    LogoutRequest,
    RegisterRequest,
)

router = APIRouter(prefix="/auth", tags=["Auth"])


def _accounts() -> SqliteAccountRepository:
    return SqliteAccountRepository()


def _sessions() -> SqliteAccountSessionRepository:
    return SqliteAccountSessionRepository()


def _to_profile(account) -> AccountProfile:
    return AccountProfile(email=account.email, name=account.name)


@router.post("/register", response_model=AuthSessionResponse)
def register(req: RegisterRequest) -> AuthSessionResponse:
    service = RegisterAccount(accounts=_accounts(), sessions=_sessions())
    try:
        account, session = service.execute(name=req.name, email=req.email, password=req.password)
    except EmailAlreadyRegistered as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except AuthError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return AuthSessionResponse(session_id=session.session_id, profile=_to_profile(account))


@router.post("/login", response_model=AuthSessionResponse)
def login(req: LoginRequest) -> AuthSessionResponse:
    service = LoginAccount(accounts=_accounts(), sessions=_sessions())
    try:
        account, session = service.execute(email=req.email, password=req.password)
    except InvalidCredentials as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc
    return AuthSessionResponse(session_id=session.session_id, profile=_to_profile(account))


@router.post("/google", response_model=AuthSessionResponse)
def google_login(req: GoogleLoginRequest) -> AuthSessionResponse:
    service = LoginWithGoogle(
        accounts=_accounts(),
        sessions=_sessions(),
        verify_credential=verify_google_credential,
    )
    try:
        account, session = service.execute(credential=req.credential)
    except GoogleAuthConfigurationError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except GoogleTokenInvalid as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc
    return AuthSessionResponse(session_id=session.session_id, profile=_to_profile(account))


@router.post("/logout", response_model=AuthLogoutResponse)
def logout(req: LogoutRequest) -> AuthLogoutResponse:
    LogoutAccount(sessions=_sessions()).execute(session_id=req.session_id)
    return AuthLogoutResponse(status="ok")


@router.get("/me", response_model=AuthMeResponse)
def me(session_id: str = Query(..., min_length=8, max_length=128)) -> AuthMeResponse:
    service = ResolveSession(accounts=_accounts(), sessions=_sessions())
    try:
        account, session = service.execute(session_id=session_id)
    except SessionInvalid as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc
    return AuthMeResponse(session_id=session.session_id, profile=_to_profile(account))
