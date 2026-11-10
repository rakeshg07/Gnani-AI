"""Health and readiness check endpoints."""
from typing import Any
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status
from app.core.config import settings
from app.core.database import get_db

router = APIRouter(tags=["Health"])


@router.get("/health", summary="Service health status")
async def health_check():
    """Returns basic system health, version, and provider configuration status."""
    return {
        "status": "healthy",
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "gnani_configured": settings.is_gnani_configured(),
        "provider": "Gnani.ai (Prisma v2.5 / Timbre v3.0)",
    }


@router.get("/ready", summary="Service readiness check")
async def readiness_check(db: Any = Depends(get_db)):
    """Verifies that the MongoDB database and internal dependencies are functional."""
    try:
        db.list_collection_names()
    except Exception as db_err:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Database readiness check failed: {str(db_err)}",
        )

    return {
        "status": "ready",
        "database": "connected",
        "gnani_api_endpoint": f"{settings.GNANI_BASE_URL}{settings.GNANI_STT_ENDPOINT}",
        "gnani_configured": settings.is_gnani_configured(),
        "supported_languages": list(settings.SUPPORTED_LANGUAGES.keys()),
    }
