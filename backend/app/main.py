"""Main FastAPI application entry point for VoiceIQ India."""
import sys
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

# Ensure UTF-8 output on Windows consoles for Indic language support
if sys.platform == "win32" and hasattr(sys.stdout, "isatty") and sys.stdout.isatty():
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

from app.core.config import settings
from app.core.logging import logger
from app.core.database import init_db, get_mongo_db
from app.api import api_router
from app.voice import voice_router
from app.providers.gnani import GnaniClientException
from app.services.audio_validator import AudioValidationError
from app.services.ecommerce_seed import seed_ecommerce_data


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan context for startup initialization and cleanup."""
    logger.info("Initializing VoiceIQ India MongoDB database and models...")
    init_db()
    try:
        db = get_mongo_db()
        seed_ecommerce_data(db)
    except Exception as seed_err:
        logger.warning(f"Initial catalog seeding warning: {seed_err}")
    logger.info(f"VoiceIQ India backend started successfully. Gnani configured: {settings.is_gnani_configured()}")
    yield
    logger.info("VoiceIQ India backend shutting down.")


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="AI-Powered Voice Customer-Support Intelligence Platform optimized for Indian Languages (Gnani AI Challenge 2026).",
    lifespan=lifespan,
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global custom exception handlers
@app.exception_handler(GnaniClientException)
async def gnani_exception_handler(request: Request, exc: GnaniClientException):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "error": {
                "code": exc.error_code,
                "message": exc.message,
            },
        },
    )


@app.exception_handler(AudioValidationError)
async def audio_validation_exception_handler(request: Request, exc: AudioValidationError):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "error": {
                "code": "AUDIO_VALIDATION_ERROR",
                "message": exc.message,
            },
        },
    )


# Include API routes
app.include_router(api_router, prefix=settings.API_V1_STR)
app.include_router(voice_router, prefix=settings.API_V1_STR)
app.include_router(voice_router)


@app.get("/")
def root():
    return {
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "docs": "/docs",
        "health": f"{settings.API_V1_STR}/health",
    }
