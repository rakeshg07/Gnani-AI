"""Analytics and dashboard statistics routes backed by MongoDB."""
from typing import Any
from fastapi import APIRouter, Depends
from app.core.database import get_db
from app.repositories.conversation_repo import conversation_repo
from app.schemas.analytics import DashboardStats

router = APIRouter(prefix="/analytics", tags=["Analytics"])


@router.get("/dashboard", response_model=DashboardStats)
def get_dashboard_metrics(db: Any = Depends(get_db)):
    """Returns database-backed real metrics for the VoiceIQ dashboard."""
    return conversation_repo.get_dashboard_stats(db)
