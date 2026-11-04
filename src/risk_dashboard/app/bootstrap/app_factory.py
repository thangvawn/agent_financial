from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.responses import FileResponse

from dotenv import load_dotenv

from risk_dashboard.api.middleware import APIKeyMiddleware, RequestLoggingMiddleware
from risk_dashboard.app.bootstrap.lifecycle import on_startup
from risk_dashboard.app.config.settings import get_settings
from risk_dashboard.app.registry.registry import get_enabled_modules
from risk_dashboard.modules.news_intelligence.application.social_worker import (
    start_social_worker,
    stop_social_worker,
)
from risk_dashboard.platform.feature_flags.service import FeatureFlagService

load_dotenv()


class SPAStaticFiles(StaticFiles):
    """StaticFiles with SPA fallback — serves index.html for non-file paths.

    Starlette's StaticFiles raises HTTPException(404) rather than returning
    a 404 Response, so we catch the exception and substitute index.html.
    """

    def __init__(self, *, directory: str | Path, fallback: str = "index.html", **kwargs):
        self._fallback = Path(directory) / fallback
        super().__init__(directory=directory, **kwargs)

    async def get_response(self, path: str, scope):
        try:
            response = await super().get_response(path, scope)
            response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
            return response
        except StarletteHTTPException as exc:
            if exc.status_code == 404 and self._fallback.exists():
                resp = FileResponse(str(self._fallback), media_type="text/html")
                resp.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
                return resp
            raise


class LearningAssetStaticFiles(StaticFiles):
    """Serve user assets first, then assets shipped with the frontend."""

    def __init__(self, *, directory: Path, bundled_directories: tuple[Path, ...]):
        super().__init__(directory=directory)
        # Keep Starlette's path traversal/symlink checks and HTTP Range handling.
        self.all_directories.extend(path for path in bundled_directories if path.is_dir())


def create_app() -> FastAPI:
    load_dotenv()
    settings = get_settings()
    feature_flags = FeatureFlagService()

    app = FastAPI(
        title=settings.title,
        version=settings.version,
        description=settings.description,
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_tags=list(settings.openapi_tags),
    )
    app.add_middleware(RequestLoggingMiddleware)
    app.add_middleware(APIKeyMiddleware)

    if settings.frontend_dist.exists():
        app.mount("/dashboard-static", SPAStaticFiles(directory=settings.frontend_dist), name="dashboard-static")
    settings.learning_assets_dir.mkdir(parents=True, exist_ok=True)
    app.mount(
        "/learning-assets",
        LearningAssetStaticFiles(
            directory=settings.learning_assets_dir,
            bundled_directories=(
                settings.frontend_dist / "learning-assets",
                settings.project_root / "frontend" / "public" / "learning-assets",
            ),
        ),
        name="learning-assets",
    )

    app.router.on_startup.append(on_startup)
    for module in get_enabled_modules(feature_flags):
        if module.public_router is not None:
            app.include_router(module.public_router, prefix=module.public_mount_prefix)
        if module.pro_router is not None:
            app.include_router(module.pro_router, prefix=module.pro_mount_prefix)
        if module.admin_router is not None:
            app.include_router(module.admin_router, prefix=module.admin_mount_prefix)
        if module.id == "news_intelligence":
            app.router.on_startup.append(start_social_worker)
            app.router.on_shutdown.append(stop_social_worker)

    from risk_dashboard.modules.auth.api.user_rights import router as user_rights_router
    app.include_router(user_rights_router, prefix="/api/me")
    app.include_router(user_rights_router, prefix="/api/v1/public/me")

    return app
