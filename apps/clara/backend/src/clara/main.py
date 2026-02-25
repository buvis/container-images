from collections.abc import Callable, Coroutine
from typing import Any

from pathlib import Path

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse

from clara.config import get_settings
from clara.exceptions import (
    ConflictError,
    ForbiddenError,
    InvalidCredentialsError,
    NotFoundError,
)
from clara.middleware import CSRFMiddleware, RequestSizeLimitMiddleware


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title="CLARA",
        version="0.1.0",
        docs_url="/docs" if settings.debug else None,
        redoc_url="/redoc" if settings.debug else None,
    )

    from clara.logging import setup_logging
    setup_logging(debug=settings.debug)

    if settings.debug:
        from clara.metrics import instrumentator
        instrumentator.instrument(app).expose(app, endpoint="/metrics")

    app.add_middleware(CSRFMiddleware)
    app.add_middleware(RequestSizeLimitMiddleware)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.exception_handler(NotFoundError)
    async def not_found_handler(request: Request, exc: NotFoundError) -> JSONResponse:
        return JSONResponse(status_code=404, content={"detail": str(exc)})

    @app.exception_handler(ForbiddenError)
    async def forbidden_handler(request: Request, exc: ForbiddenError) -> JSONResponse:
        return JSONResponse(status_code=403, content={"detail": str(exc)})

    @app.exception_handler(ConflictError)
    async def conflict_handler(request: Request, exc: ConflictError) -> JSONResponse:
        return JSONResponse(status_code=409, content={"detail": exc.detail})

    @app.exception_handler(InvalidCredentialsError)
    async def invalid_credentials_handler(
        request: Request, exc: InvalidCredentialsError
    ) -> JSONResponse:
        return JSONResponse(status_code=401, content={"detail": "Invalid credentials"})

    import time

    import structlog
    logger = structlog.get_logger()

    @app.middleware("http")
    async def log_requests(
        request: Request,
        call_next: Callable[
            [Request], Coroutine[Any, Any, Response]
        ],
    ) -> Response:
        start = time.monotonic()
        response = await call_next(request)
        duration_ms = round((time.monotonic() - start) * 1000, 1)
        logger.info(
            "request_handled",
            method=request.method,
            path=request.url.path,
            status=response.status_code,
            duration_ms=duration_ms,
        )
        return response

    @app.get("/api/v1/health")
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    from clara.auth.api import router as auth_router
    app.include_router(auth_router, prefix="/api/v1/auth", tags=["auth"])
    from clara.auth.vault_api import router as vault_router
    app.include_router(vault_router, prefix="/api/v1/vaults", tags=["vaults"])
    from clara.contacts.api import router as contacts_router
    app.include_router(
        contacts_router,
        prefix="/api/v1/vaults/{vault_id}/contacts",
        tags=["contacts"],
    )
    from clara.contacts.sub_api import (
        addresses_router,
        contact_tags_router,
        methods_router,
        pets_router,
        relationships_router,
        vault_tags_router,
    )
    app.include_router(
        methods_router,
        prefix="/api/v1/vaults/{vault_id}/contacts/{contact_id}/methods",
        tags=["contacts"],
    )
    app.include_router(
        addresses_router,
        prefix="/api/v1/vaults/{vault_id}/contacts/{contact_id}/addresses",
        tags=["contacts"],
    )
    app.include_router(
        relationships_router,
        prefix="/api/v1/vaults/{vault_id}/contacts/{contact_id}/relationships",
        tags=["contacts"],
    )
    app.include_router(
        pets_router,
        prefix="/api/v1/vaults/{vault_id}/contacts/{contact_id}/pets",
        tags=["contacts"],
    )
    app.include_router(
        contact_tags_router,
        prefix="/api/v1/vaults/{vault_id}/contacts/{contact_id}/tags",
        tags=["contacts"],
    )
    app.include_router(
        vault_tags_router,
        prefix="/api/v1/vaults/{vault_id}/tags",
        tags=["contacts"],
    )
    from clara.contacts.relationship_type_api import router as rel_types_router
    app.include_router(
        rel_types_router,
        prefix="/api/v1/vaults/{vault_id}/relationship-types",
        tags=["contacts"],
    )
    from clara.activities.api import router as activities_router
    app.include_router(
        activities_router,
        prefix="/api/v1/vaults/{vault_id}/activities",
        tags=["activities"],
    )
    from clara.notes.api import router as notes_router
    app.include_router(
        notes_router,
        prefix="/api/v1/vaults/{vault_id}/notes",
        tags=["notes"],
    )
    from clara.reminders.api import router as reminders_router
    app.include_router(
        reminders_router,
        prefix="/api/v1/vaults/{vault_id}/reminders",
        tags=["reminders"],
    )
    from clara.reminders.stay_in_touch_api import router as sit_router
    app.include_router(
        sit_router,
        prefix="/api/v1/vaults/{vault_id}/contacts/{contact_id}/stay_in_touch",
        tags=["stay-in-touch"],
    )
    from clara.tasks.api import router as tasks_router
    app.include_router(
        tasks_router,
        prefix="/api/v1/vaults/{vault_id}/tasks",
        tags=["tasks"],
    )
    from clara.journal.api import router as journal_router
    app.include_router(
        journal_router,
        prefix="/api/v1/vaults/{vault_id}/journal",
        tags=["journal"],
    )
    from clara.finance.gift_api import router as gifts_router
    app.include_router(
        gifts_router,
        prefix="/api/v1/vaults/{vault_id}/gifts",
        tags=["gifts"],
    )
    from clara.finance.debt_api import router as debts_router
    app.include_router(
        debts_router,
        prefix="/api/v1/vaults/{vault_id}/debts",
        tags=["debts"],
    )
    from clara.files.api import router as files_router
    app.include_router(
        files_router,
        prefix="/api/v1/vaults/{vault_id}/files",
        tags=["files"],
    )
    from clara.customization.template_api import router as templates_router
    app.include_router(
        templates_router,
        prefix="/api/v1/vaults/{vault_id}/templates",
        tags=["templates"],
    )
    from clara.customization.custom_field_api import router as custom_fields_router
    app.include_router(
        custom_fields_router,
        prefix="/api/v1/vaults/{vault_id}/custom-fields",
        tags=["custom-fields"],
    )
    from clara.integrations.api import router as import_export_router
    app.include_router(
        import_export_router,
        prefix="/api/v1/vaults/{vault_id}",
        tags=["import-export"],
    )
    from clara.notifications.api import router as notifications_router
    app.include_router(
        notifications_router,
        prefix="/api/v1/vaults/{vault_id}/notifications",
        tags=["notifications"],
    )
    from clara.dav_sync.api import router as dav_sync_router
    app.include_router(
        dav_sync_router,
        prefix="/api/v1/vaults/{vault_id}/dav-sync",
        tags=["dav-sync"],
    )
    from clara.git_sync.api import router as git_sync_router
    app.include_router(
        git_sync_router,
        prefix="/api/v1/vaults/{vault_id}/git-sync",
        tags=["git-sync"],
    )

    spa_dir = Path("/app/static")
    if spa_dir.is_dir():
        spa_root = spa_dir.resolve()

        @app.get("/{path:path}")
        async def serve_spa(path: str) -> Response:
            file = (spa_dir / path).resolve()
            if file.is_file() and str(file).startswith(str(spa_root)):
                return FileResponse(file)
            return FileResponse(spa_dir / "200.html")

    return app


app = create_app()
