"""Admin analytics and business operations endpoints backed by MongoDB."""
from typing import Any
from fastapi import APIRouter, Depends
from app.core.database import get_db
from app.services.ecommerce_service import ECommerceService
from app.repositories.conversation_repo import conversation_repo

router = APIRouter(prefix="/admin", tags=["Admin & Store Analytics"])


@router.get("/analytics")
def get_admin_analytics(db: Any = Depends(get_db)):
    """
    Returns real database-backed metrics for store performance and voice support operations:
    - Order counts and simulated revenue
    - Return requests
    - Support conversations volume and transcription success rate
    - Customer intent breakdown
    - Language distribution
    - Recent interactions
    """
    store_stats = ECommerceService.get_store_analytics(db)
    conv_stats = conversation_repo.get_dashboard_stats(db)
    recent_convs, _ = conversation_repo.get_multi(db, skip=0, limit=5)

    return {
        "store": store_stats,
        "support": conv_stats,
        "recent_conversations": recent_convs,
    }
