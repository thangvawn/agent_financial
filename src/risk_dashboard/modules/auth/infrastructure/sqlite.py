from __future__ import annotations

from risk_dashboard.modules.auth.application.security import Account, AccountSession
from risk_dashboard.platform.database import open_app_state_db


class SqliteAccountRepository:
    def get_by_email(self, *, email: str) -> Account | None:
        with open_app_state_db() as conn:
            row = conn.execute(
                """
                SELECT account_id, email, name, password_hash, password_salt, created_at, updated_at
                FROM accounts WHERE email = ?
                """,
                (email,),
            ).fetchone()
        if row is None:
            return None
        return Account(
            account_id=row["account_id"],
            email=row["email"],
            name=row["name"],
            password_hash=row["password_hash"],
            password_salt=row["password_salt"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )

    def get_by_id(self, *, account_id: str) -> Account | None:
        with open_app_state_db() as conn:
            row = conn.execute(
                """
                SELECT account_id, email, name, password_hash, password_salt, created_at, updated_at
                FROM accounts WHERE account_id = ?
                """,
                (account_id,),
            ).fetchone()
        if row is None:
            return None
        return Account(
            account_id=row["account_id"],
            email=row["email"],
            name=row["name"],
            password_hash=row["password_hash"],
            password_salt=row["password_salt"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )

    def save(self, account: Account) -> Account:
        with open_app_state_db() as conn:
            conn.execute(
                """
                INSERT INTO accounts (account_id, email, password_hash, password_salt, name, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(account_id) DO UPDATE SET
                  password_hash = excluded.password_hash,
                  password_salt = excluded.password_salt,
                  name = excluded.name,
                  updated_at = excluded.updated_at
                """,
                (
                    account.account_id,
                    account.email,
                    account.password_hash,
                    account.password_salt,
                    account.name,
                    account.created_at,
                    account.updated_at,
                ),
            )
        return account


class SqliteAccountSessionRepository:
    def save(self, session: AccountSession) -> AccountSession:
        with open_app_state_db() as conn:
            conn.execute(
                """
                INSERT INTO account_sessions (session_id, account_id, status, created_at, last_seen_at, expires_at)
                VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(session_id) DO UPDATE SET
                  status = excluded.status,
                  last_seen_at = excluded.last_seen_at,
                  expires_at = excluded.expires_at
                """,
                (
                    session.session_id,
                    session.account_id,
                    session.status,
                    session.created_at,
                    session.last_seen_at,
                    session.expires_at,
                ),
            )
        return session

    def get(self, *, session_id: str) -> AccountSession | None:
        with open_app_state_db() as conn:
            row = conn.execute(
                """
                SELECT session_id, account_id, status, created_at, last_seen_at, expires_at
                FROM account_sessions WHERE session_id = ?
                """,
                (session_id,),
            ).fetchone()
        if row is None:
            return None
        return AccountSession(
            session_id=row["session_id"],
            account_id=row["account_id"],
            status=row["status"],
            created_at=row["created_at"],
            last_seen_at=row["last_seen_at"],
            expires_at=row["expires_at"],
        )

    def revoke(self, *, session_id: str) -> None:
        with open_app_state_db() as conn:
            conn.execute(
                "UPDATE account_sessions SET status = 'revoked' WHERE session_id = ?",
                (session_id,),
            )

    def touch(self, *, session_id: str, last_seen_at: str) -> None:
        with open_app_state_db() as conn:
            conn.execute(
                "UPDATE account_sessions SET last_seen_at = ? WHERE session_id = ?",
                (last_seen_at, session_id),
            )
