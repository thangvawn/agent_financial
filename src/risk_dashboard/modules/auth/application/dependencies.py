from __future__ import annotations

from datetime import datetime, timezone
import uuid
from fastapi import Header, HTTPException, Query

from risk_dashboard.modules.auth.application.scope_resolver import BASE_SCOPES, resolve_scopes
from risk_dashboard.modules.auth.application.security import utc_now_iso
from risk_dashboard.modules.auth.application.services import ResolveSession, SessionInvalid
from risk_dashboard.modules.auth.infrastructure.sqlite import (
    SqliteAccountConsentRepository,
    SqliteAccountRepository,
    SqliteAccountSessionRepository,
)
from risk_dashboard.modules.auth.schemas.principal import AuthPrincipal, ConsentSnapshot

DEFAULT_ACCOUNT_SCOPES = BASE_SCOPES


def _determine_assurance(created_at_iso: str) -> str:
    try:
        dt = datetime.fromisoformat(created_at_iso.replace("Z", "+00:00"))
        if (datetime.now(timezone.utc) - dt).total_seconds() <= 900:
            return "recent_auth"
    except Exception:
        pass
    return "session"


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
    assurance = _determine_assurance(session.created_at)

    return AuthPrincipal(
        account_id=account.account_id,
        session_id=session.session_id,
        assurance=assurance,
        scopes=resolve_scopes(tier="community", role="user"),
        consent=consent,
        resolved_at=utc_now_iso(),
    )


def resolve_principal_relaxed(
    authorization: str | None = Header(default=None),
) -> AuthPrincipal:
    if authorization is not None:
        return resolve_principal(authorization=authorization)

    ephemeral_id = f"anon_{uuid.uuid4().hex[:8]}"
    return AuthPrincipal(
        account_id=ephemeral_id,
        session_id=f"anon_sess_{uuid.uuid4().hex[:12]}",
        assurance="anonymous",
        scopes=BASE_SCOPES,
        is_anonymous=True,
        consent=ConsentSnapshot(memory=False, analytics=False, policy_version="1.0.0"),
        resolved_at=utc_now_iso(),
    )


def resolve_surface_principal(
    authorization: str | None = Header(default=None),
    session_id: str | None = Query(default=None),
) -> AuthPrincipal:
    if authorization is not None:
        return resolve_principal(authorization=authorization)

    if session_id:
        sessions_repo = SqliteAccountSessionRepository()
        session = sessions_repo.get(session_id=session_id)
        if session and session.status == "active":
            accounts_repo = SqliteAccountRepository()
            account = accounts_repo.get_by_id(account_id=session.account_id)
            if account:
                consent = SqliteAccountConsentRepository().get(account_id=account.account_id)
                return AuthPrincipal(
                    account_id=account.account_id,
                    session_id=session.session_id,
                    assurance=_determine_assurance(session.created_at),
                    scopes=resolve_scopes(tier="community", role="user"),
                    consent=consent,
                    resolved_at=utc_now_iso(),
                )

        # Legacy test session or anonymous
        return AuthPrincipal(
            account_id=session_id,
            session_id=session_id,
            assurance="anonymous",
            scopes=BASE_SCOPES,
            is_anonymous=True,
            consent=ConsentSnapshot(memory=False, analytics=False, policy_version="1.0.0"),
            resolved_at=utc_now_iso(),
        )

    return resolve_principal_relaxed(authorization=None)
