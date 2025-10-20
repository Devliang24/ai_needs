"""API router configuration."""

from fastapi import APIRouter

from app.api import uploads, sessions, exports, images


api_router = APIRouter()

api_router.include_router(uploads.router, prefix="/uploads", tags=["uploads"])
api_router.include_router(sessions.router, prefix="/sessions", tags=["sessions"])
api_router.include_router(exports.router, prefix="/sessions", tags=["exports"])
api_router.include_router(images.router, tags=["images"])

