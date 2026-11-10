"""Aggregate API router for VoiceIQ India backend."""
from fastapi import APIRouter
from app.api.auth import router as auth_router
from app.api.health import router as health_router
from app.api.ecommerce import router as ecommerce_router
from app.api.assistant import router as assistant_router
from app.api.admin import router as admin_router
from app.api.conversations import router as conversations_router
from app.api.analytics import router as analytics_router
from app.api.tts import router as tts_router

api_router = APIRouter()

api_router.include_router(auth_router)
api_router.include_router(health_router)
api_router.include_router(ecommerce_router)
api_router.include_router(assistant_router)
api_router.include_router(admin_router)
api_router.include_router(conversations_router)
api_router.include_router(analytics_router)
api_router.include_router(tts_router)
