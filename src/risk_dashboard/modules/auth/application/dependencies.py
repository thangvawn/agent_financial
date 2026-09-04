from __future__ import annotations

from fastapi import Header, HTTPException

from risk_dashboard.modules.auth.application.security import utc_now_iso
from risk_dashboard.modules.auth.application.services import ResolveSession, SessionInvalid
from risk_dashboard.modules.auth.infrastructure.sqlite import (
    SqliteAccountConsentRepository,
    SqliteAccountRepository,
    SqliteAccountSessionRepository,
)
from risk_dashboard.modules.auth.schemas.principal import AuthPrincipal


DEFAULT_ACCOUNT_SCOPES: tuple[str, ...] = (
    "account:market_portfolio:read",
    "me:home_journey:read",
    "me:home_journey:feedback",
)


def resolve_principal(
    authorization: str | None = Header(default=None),
) -> AuthPrincipal:
    if authorization is None or len(authorization) > 256:
        raise HTTPException(status_code=401, detail="Thông tin xác thực không hợp lệ.")
    scheme, _, session_id = authorization.partition(" ")
    if scheme.lower() != "bearer" or not 8 <= len(session_id) <= 128:
        raise HTTPException(status_code=401, detail="Thông tin xác thực không hợp lệ.")
    service = ResolveSession(
        accounts=SqliteAccountRepository(),
        sessions=SqliteAccountSessionRepository(),
    )
    try:
        account, session = service.execute(session_id=session_id)
    except SessionInvalid as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc

    consent = SqliteAccountConsentRepository().get(account_id=account.account_id)

    return AuthPrincipal(
        account_id=account.account_id,
        session_id=session.session_id,
        scopes=DEFAULT_ACCOUNT_SCOPES,
        consent=consent,
        resolved_at=utc_now_iso(),
    )

