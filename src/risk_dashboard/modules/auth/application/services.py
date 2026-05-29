from __future__ import annotations

from collections.abc import Callable
from datetime import datetime, timezone

from risk_dashboard.modules.auth.application.google_identity import GoogleIdentity
from risk_dashboard.modules.auth.application.security import (
    Account,
    AccountSession,
    hash_password,
    new_account_id,
    new_session_id,
    normalize_email,
    session_expiry_iso,
    utc_now_iso,
    verify_password,
)
from risk_dashboard.modules.auth.infrastructure.sqlite import (
    SqliteAccountRepository,
    SqliteAccountSessionRepository,
)


class AuthError(Exception):
    """Auth domain error."""


class EmailAlreadyRegistered(AuthError):
    pass


class InvalidCredentials(AuthError):
    pass


class SessionInvalid(AuthError):
    pass


class RegisterAccount:
    def __init__(
        self,
        accounts: SqliteAccountRepository,
        sessions: SqliteAccountSessionRepository,
    ) -> None:
        self.accounts = accounts
        self.sessions = sessions

    def execute(self, *, name: str, email: str, password: str) -> tuple[Account, AccountSession]:
        normalized = normalize_email(email)
        existing = self.accounts.get_by_email(email=normalized)
        if existing is not None:
            raise EmailAlreadyRegistered("Email đã được đăng ký.")
        password_hash, password_salt = hash_password(password)
        now = utc_now_iso()
        account = Account(
            account_id=new_account_id(),
            email=normalized,
            name=name.strip() or normalized.split("@")[0],
            password_hash=password_hash,
            password_salt=password_salt,
            created_at=now,
            updated_at=now,
        )
        self.accounts.save(account)
        session = self._create_session(account_id=account.account_id, now=now)
        return account, session

    def _create_session(self, *, account_id: str, now: str) -> AccountSession:
        session = AccountSession(
            session_id=new_session_id(),
            account_id=account_id,
            status="active",
            created_at=now,
            last_seen_at=now,
            expires_at=session_expiry_iso(),
        )
        self.sessions.save(session)
        return session


class LoginAccount:
    def __init__(
        self,
        accounts: SqliteAccountRepository,
        sessions: SqliteAccountSessionRepository,
    ) -> None:
        self.accounts = accounts
        self.sessions = sessions

    def execute(self, *, email: str, password: str) -> tuple[Account, AccountSession]:
        normalized = normalize_email(email)
        account = self.accounts.get_by_email(email=normalized)
        if account is None:
            raise InvalidCredentials("Email hoặc mật khẩu không đúng.")
        if not verify_password(
            password,
            hash_hex=account.password_hash,
            salt_hex=account.password_salt,
        ):
            raise InvalidCredentials("Email hoặc mật khẩu không đúng.")
        now = utc_now_iso()
        session = AccountSession(
            session_id=new_session_id(),
            account_id=account.account_id,
            status="active",
            created_at=now,
            last_seen_at=now,
            expires_at=session_expiry_iso(),
        )
        self.sessions.save(session)
        return account, session


class LoginWithGoogle:
    def __init__(
        self,
        accounts: SqliteAccountRepository,
        sessions: SqliteAccountSessionRepository,
        verify_credential: Callable[[str], GoogleIdentity],
    ) -> None:
        self.accounts = accounts
        self.sessions = sessions
        self.verify_credential = verify_credential

    def execute(self, *, credential: str) -> tuple[Account, AccountSession]:
        identity = self.verify_credential(credential)
        normalized = normalize_email(identity.email)
        now = utc_now_iso()
        account = self.accounts.get_by_email(email=normalized)
        if account is None:
            password_hash, password_salt = hash_password(new_session_id())
            account = Account(
                account_id=new_account_id(),
                email=normalized,
                name=identity.name.strip() or normalized.split("@")[0],
                password_hash=password_hash,
                password_salt=password_salt,
                created_at=now,
                updated_at=now,
            )
            self.accounts.save(account)
        session = AccountSession(
            session_id=new_session_id(),
            account_id=account.account_id,
            status="active",
            created_at=now,
            last_seen_at=now,
            expires_at=session_expiry_iso(),
        )
        self.sessions.save(session)
        return account, session


class LogoutAccount:
    def __init__(self, sessions: SqliteAccountSessionRepository) -> None:
        self.sessions = sessions

    def execute(self, *, session_id: str) -> None:
        self.sessions.revoke(session_id=session_id)


class ResolveSession:
    def __init__(
        self,
        accounts: SqliteAccountRepository,
        sessions: SqliteAccountSessionRepository,
    ) -> None:
        self.accounts = accounts
        self.sessions = sessions

    def execute(self, *, session_id: str) -> tuple[Account, AccountSession]:
        session = self.sessions.get(session_id=session_id)
        if session is None or session.status != "active":
            raise SessionInvalid("Phiên không hợp lệ hoặc đã hết hạn.")
        try:
            expires_at = datetime.fromisoformat(session.expires_at.replace("Z", "+00:00"))
        except ValueError as exc:  # pragma: no cover - defensive
            raise SessionInvalid("Phiên không hợp lệ.") from exc
        if datetime.now(timezone.utc) >= expires_at:
            self.sessions.revoke(session_id=session_id)
            raise SessionInvalid("Phiên đã hết hạn.")
        account = self.accounts.get_by_id(account_id=session.account_id)
        if account is None:
            raise SessionInvalid("Tài khoản đã bị xoá.")
        self.sessions.touch(session_id=session_id, last_seen_at=utc_now_iso())
        return account, session
