from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from risk_dashboard.platform.database.config import get_db_path, project_root


def _env_path(key: str, default: str) -> Path:
    return Path(os.environ.get(key, default)).expanduser().resolve()


@dataclass(frozen=True)
class PipelinePaths:
    """Đường dẫn chuẩn — override bằng biến môi trường hoặc tham số CLI."""

    cache_dir: Path
    sqlite_path: Path

    @classmethod
    def defaults(cls, project_root_override: Path | None = None) -> PipelinePaths:
        root = project_root_override or project_root()
        cache = _env_path("RISK_DASHBOARD_CACHE", str(root / "data" / "cache"))
        # Same transactional DB as the app (compat: RISK_DASHBOARD_SQLITE still honored via get_db_path)
        db = get_db_path()
        return cls(cache_dir=cache, sqlite_path=db)
