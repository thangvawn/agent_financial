from __future__ import annotations

import hashlib
import hmac
import secrets
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone


SCRYPT_N = 2**14
SCRYPT_R = 8
SCRYPT_P = 1
SCRYPT_DKLEN = 64
SALT_BYTES = 16
SESSION_TTL_HOURS = 24 * 14  # 14 days


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def utc_now_iso() -> str:
    return utc_now().isoformat()


def session_expiry_iso(*, ttl_hours: int = SESSION_TTL_HOURS) -> str:
    return (utc_now() + timedelta(hours=ttl_hours)).isoformat()


def hash_password(password: str, *, salt: bytes | None = None) -> tuple[str, str]:
    """Return (hash_hex, salt_hex) using scrypt."""
    if salt is None:
        salt = secrets.token_bytes(SALT_BYTES)
    derived = hashlib.scrypt(
        password.encode("utf-8"),
        salt=salt,
        n=SCRYPT_N,
        r=SCRYPT_R,
        p=SCRYPT_P,
        dklen=SCRYPT_DKLEN,
    )
    return derived.hex(), salt.hex()


def verify_password(password: str, *, hash_hex: str, salt_hex: str) -> bool:
    try:
        salt = bytes.fromhex(salt_hex)
        expected = bytes.fromhex(hash_hex)
    except ValueError:
        return False
    derived = hashlib.scrypt(
        password.encode("utf-8"),
        salt=salt,
        n=SCRYPT_N,
        r=SCRYPT_R,
        p=SCRYPT_P,
        dklen=len(expected),
    )
    return hmac.compare_digest(derived, expected)


def new_account_id() -> str:
    return f"acc_{secrets.token_hex(8)}"


def new_session_id() -> str:
    return f"sess_{secrets.token_urlsafe(24)}"


def normalize_email(email: str) -> str:
    return email.strip().lower()


@dataclass(frozen=True)
class Account:
    account_id: str
    email: str
    name: str
    password_hash: str
    password_salt: str
    created_at: str
    updated_at: str


@dataclass(frozen=True)
class AccountSession:
    session_id: str
    account_id: str
    status: str
    created_at: str
    last_seen_at: str
    expires_at: str
