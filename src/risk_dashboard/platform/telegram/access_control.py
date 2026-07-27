"""Access control policy for Telegram bot interactions (with strict group chat rules)."""

from __future__ import annotations

import os
from typing import Set


class TelegramAccessControl:
    def __init__(
        self,
        allowed_chat_ids: Set[str] | None = None,
        admin_user_ids: Set[str] | None = None,
    ) -> None:
        if allowed_chat_ids is not None:
            self.allowed_chat_ids = allowed_chat_ids
        else:
            raw_chats = os.getenv("TELEGRAM_ALLOWED_CHAT_IDS", "").strip()
            self.allowed_chat_ids = {c.strip() for c in raw_chats.split(",") if c.strip()}
            if not self.allowed_chat_ids:
                def_chat = os.getenv("TELEGRAM_DEFAULT_CHAT_ID") or os.getenv("TELEGRAM_CHAT_ID")
                if def_chat:
                    self.allowed_chat_ids.add(def_chat.strip())

        if admin_user_ids is not None:
            self.admin_user_ids = admin_user_ids
        else:
            raw_admins = os.getenv("TELEGRAM_ADMIN_USER_IDS", "").strip()
            self.admin_user_ids = {a.strip() for a in raw_admins.split(",") if a.strip()}
            if not self.admin_user_ids:
                def_chat = os.getenv("TELEGRAM_DEFAULT_CHAT_ID") or os.getenv("TELEGRAM_CHAT_ID")
                if def_chat:
                    self.admin_user_ids.add(def_chat.strip())

    def is_admin(self, user_id: str | int) -> bool:
        str_user = str(user_id).strip()
        return str_user in self.admin_user_ids

    def is_allowed(self, chat_id: str | int, user_id: str | int) -> bool:
        str_chat = str(chat_id).strip()
        str_user = str(user_id).strip()

        # Admin user is always allowed
        if str_user in self.admin_user_ids:
            return True

        if not self.allowed_chat_ids:
            return False

        # Group chat check (starts with '-')
        is_group = str_chat.startswith("-")
        if is_group:
            # Group chat requires BOTH group chat_id allowed AND sender user_id allowed
            return str_chat in self.allowed_chat_ids and str_user in self.allowed_chat_ids

        # Private chat check
        return str_chat in self.allowed_chat_ids or str_user in self.allowed_chat_ids

    def check_access(self, command: str, chat_id: str | int, user_id: str | int) -> bool:
        cmd_clean = command.strip().lower()
        if not cmd_clean.startswith("/"):
            cmd_clean = f"/{cmd_clean}"

        # /status requires explicit admin permission
        if cmd_clean == "/status":
            return self.is_admin(user_id)

        # /help, /market, /news require general allowed access
        return self.is_allowed(chat_id, user_id)
