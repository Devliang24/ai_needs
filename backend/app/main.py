"""FastAPI application entrypoint."""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import api_router, websocket
from app.config import settings
from app.db import init_models
from app.utils.logger import configure_logging


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan to prepare and teardown resources."""

    configure_logging("DEBUG" if settings.debug else "INFO")
    _ = settings.resolved_upload_dir
    await init_models()
    yield


def create_app() -> FastAPI:
    """Application factory."""

    app = FastAPI(title="智能分析平台", lifespan=lifespan)

    app.include_router(api_router, prefix="/api")
    app.include_router(websocket.router)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/healthz", tags=["system"], summary="Health check")
    async def healthcheck():
        return {"status": "ok"}

    return app


app = create_app()
