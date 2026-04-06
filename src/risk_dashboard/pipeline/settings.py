from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


def _env_path(key: str, default: str) -> Path:
    return Path(os.environ.get(key, default)).expanduser().resolve()


@dataclass(frozen=True)
class PipelinePaths:
    """Đường dẫn chuẩn — override bằng biến môi trường hoặc tham số CLI."""

    cache_dir: Path
    sqlite_path: Path

    @classmethod
    def defaults(cls, project_root: Path | None = None) -> PipelinePaths:
        root = project_root or Path.cwd()
        cache = _env_path("RISK_DASHBOARD_CACHE", str(root / "data" / "cache"))
        db = _env_path("RISK_DASHBOARD_SQLITE", str(root / "data" / "risk_dashboard.db"))
        return cls(cache_dir=cache, sqlite_path=db)
