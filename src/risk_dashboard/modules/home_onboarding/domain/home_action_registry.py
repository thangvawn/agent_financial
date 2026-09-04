from __future__ import annotations

import re
from typing import Final

ACTION_TYPE_PREFIX_MAP: Final[dict[str, str]] = {
    "open_lesson": "/learn",
    "continue_lesson": "/learn",
    "view_research_memo": "/bctc",
    "refresh_artifact": "/simulation",
    "read_market_education": "/market",
    "read_news_brief": "/news",
}

ALLOWED_ACTION_TYPES: Final[frozenset[str]] = frozenset(ACTION_TYPE_PREFIX_MAP.keys())

ALLOWED_CTA_PREFIXES: Final[frozenset[str]] = frozenset(
    set(ACTION_TYPE_PREFIX_MAP.values())
)

_SAFE_PATH_REGEX: Final[re.Pattern[str]] = re.compile(
    r"^/[a-zA-Z0-9_\-\?&=%/\.]*$"
)


def _is_path_bounded(path: str, prefix: str) -> bool:
    if path == prefix:
        return True
    return path.startswith(prefix + "/") or path.startswith(prefix + "?")


def is_action_allowed(action_type: str, cta_path: str) -> bool:
    expected_prefix = ACTION_TYPE_PREFIX_MAP.get(action_type)
    if expected_prefix is None:
        return False
    if not cta_path or not _SAFE_PATH_REGEX.match(cta_path):
        return False
    return _is_path_bounded(cta_path, expected_prefix)


def validate_action(action_type: str, cta_path: str) -> None:
    if not is_action_allowed(action_type, cta_path):
        raise ValueError(
            f"Action type '{action_type}' or CTA path '{cta_path}' not allowed by server registry."
        )

