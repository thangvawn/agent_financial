from __future__ import annotations

import os
from dataclasses import dataclass

DEFAULT_GOOGLE_OAUTH_CLIENT_ID = (
    "483150503670-hd2qvbcvaq0qqre21qn94mgq21o9559k.apps.googleusercontent.com"
)


class GoogleAuthConfigurationError(Exception):
    pass


class GoogleTokenInvalid(Exception):
    pass


@dataclass(frozen=True)
class GoogleIdentity:
    email: str
    name: str
    subject: str
    email_verified: bool


def google_oauth_client_id() -> str:
    return (
        os.getenv("GOOGLE_OAUTH_CLIENT_ID", "").strip()
        or os.getenv("VITE_GOOGLE_CLIENT_ID", "").strip()
        or DEFAULT_GOOGLE_OAUTH_CLIENT_ID
    )


def verify_google_credential(credential: str) -> GoogleIdentity:
    client_id = google_oauth_client_id()
    if not client_id:
        raise GoogleAuthConfigurationError("Google OAuth client ID chưa được cấu hình.")
    try:
        from google.auth.transport import requests
        from google.oauth2 import id_token
    except ImportError as exc:  # pragma: no cover - dependency guard
        raise GoogleAuthConfigurationError(
            "Thiếu dependency google-auth. Cài đặt `google-auth` rồi thử lại."
        ) from exc

    try:
        claims = id_token.verify_oauth2_token(
            credential,
            requests.Request(),
            audience=client_id,
        )
    except ValueError as exc:
        raise GoogleTokenInvalid("Google token không hợp lệ hoặc đã hết hạn.") from exc

    email = str(claims.get("email") or "").strip().lower()
    subject = str(claims.get("sub") or "").strip()
    email_verified = bool(claims.get("email_verified"))
    if not email or not subject or not email_verified:
        raise GoogleTokenInvalid("Google account chưa có email đã xác minh.")
    return GoogleIdentity(
        email=email,
        name=str(claims.get("name") or email.split("@")[0]).strip(),
        subject=subject,
        email_verified=email_verified,
    )
