from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.responses import FileResponse

from risk_dashboard.api.middleware import APIKeyMiddleware, RequestLoggingMiddleware
from risk_dashboard.app.bootstrap.lifecycle import on_startup
from risk_dashboard.app.config.settings import get_settings
from risk_dashboard.app.registry.registry import get_enabled_modules
from risk_dashboard.platform.feature_flags.service import FeatureFlagService


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
            return await super().get_response(path, scope)
        except StarletteHTTPException as exc:
            if exc.status_code == 404 and self._fallback.exists():
                return FileResponse(str(self._fallback), media_type="text/html")
            raise


def create_app() -> FastAPI:
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
    app.mount("/learning-assets", StaticFiles(directory=settings.learning_assets_dir), name="learning-assets")

    for module in get_enabled_modules(feature_flags):
        if module.public_router is not None:
            app.include_router(module.public_router, prefix=module.public_mount_prefix)
        if module.pro_router is not None:
            app.include_router(module.pro_router, prefix=module.pro_mount_prefix)
        if module.admin_router is not None:
            app.include_router(module.admin_router, prefix=module.admin_mount_prefix)

    app.router.on_startup.append(on_startup)
    return app
