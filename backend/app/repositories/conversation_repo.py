"""Database repository for conversations, insights, and analytics backed by MongoDB."""
import uuid
import re
from datetime import datetime, timezone
from typing import Optional, List, Tuple, Dict, Any

from app.schemas.conversation import ConversationCreate, ConversationUpdate
from app.schemas.insights import ConversationInsightCreate


def get_utc_now() -> datetime:
    return datetime.now(timezone.utc)


class ConversationRepository:
    """Encapsulates all database operations for conversations using MongoDB."""

    def create(self, db: Any, obj_in: ConversationCreate) -> Dict[str, Any]:
        conv_id = str(uuid.uuid4())
        now = get_utc_now()
        doc = {
            "_id": conv_id,
            "id": conv_id,
            "filename": obj_in.filename,
            "file_size_bytes": obj_in.file_size_bytes,
            "content_type": obj_in.content_type,
            "language_code": obj_in.language_code,
            "status": "uploaded",
            "transcript": None,
            "confidence_score": None,
            "audio_duration_seconds": None,
            "error_message": None,
            "customer_id": "cust_demo_001",
            "order_id": None,
            "product_id": None,
            "source": "voice_widget",
            "detected_intent": None,
            "created_at": now,
            "updated_at": now,
            "insight": None,
            "spoken_responses": [],
        }
        db.conversations.insert_one(doc)
        return doc

    def get_by_id(self, db: Any, conversation_id: str) -> Optional[Dict[str, Any]]:
        doc = db.conversations.find_one({"$or": [{"id": conversation_id}, {"_id": conversation_id}]})
        if doc:
            doc["id"] = doc.get("id") or str(doc.get("_id", ""))
            # Attach insight if stored in conversation_insights
            if not doc.get("insight"):
                insight = db.conversation_insights.find_one({"conversation_id": doc["id"]})
                if insight:
                    doc["insight"] = insight
        return doc

    def get_multi(
        self,
        db: Any,
        skip: int = 0,
        limit: int = 20,
        search: Optional[str] = None,
        status: Optional[str] = None,
        language_code: Optional[str] = None,
    ) -> Tuple[List[Dict[str, Any]], int]:
        filters: Dict[str, Any] = {}

        if search and search.strip():
            regex = re.compile(re.escape(search.strip()), re.IGNORECASE)
            filters["$or"] = [
                {"filename": {"$regex": regex}},
                {"transcript": {"$regex": regex}},
            ]

        if status and status.strip() and status != "all":
            filters["status"] = status.strip()

        if language_code and language_code.strip() and language_code != "all":
            filters["language_code"] = language_code.strip()

        total = db.conversations.count_documents(filters)
        items = list(db.conversations.find(filters).sort("created_at", -1).skip(skip).limit(limit))

        for it in items:
            it["id"] = it.get("id") or str(it.get("_id", ""))
            if not it.get("insight"):
                it["insight"] = db.conversation_insights.find_one({"conversation_id": it["id"]})

        return items, total

    def update(
        self,
        db: Any,
        conversation_id: str,
        obj_in: ConversationUpdate,
    ) -> Optional[Dict[str, Any]]:
        update_data = {k: v for k, v in obj_in.model_dump(exclude_unset=True).items() if v is not None}
        update_data["updated_at"] = get_utc_now()

        db.conversations.update_one(
            {"$or": [{"id": conversation_id}, {"_id": conversation_id}]},
            {"$set": update_data},
        )
        return self.get_by_id(db, conversation_id)

    def create_insight(
        self,
        db: Any,
        conversation_id: str,
        obj_in: ConversationInsightCreate,
    ) -> Dict[str, Any]:
        insight_id = str(uuid.uuid4())
        now = get_utc_now()
        doc = {
            "_id": insight_id,
            "id": insight_id,
            "conversation_id": conversation_id,
            "summary": obj_in.summary,
            "customer_intent": obj_in.customer_intent,
            "primary_issue": obj_in.primary_issue,
            "action_items": obj_in.action_items,
            "commitments": obj_in.commitments,
            "resolution_status": obj_in.resolution_status,
            "escalation_level": obj_in.escalation_level,
            "escalation_reason": obj_in.escalation_reason,
            "sentiment_label": obj_in.sentiment_label,
            "sentiment_score": obj_in.sentiment_score,
            "frustration_index": obj_in.frustration_index,
            "created_at": now,
        }

        db.conversation_insights.update_one(
            {"conversation_id": conversation_id},
            {"$set": doc},
            upsert=True,
        )
        db.conversations.update_one(
            {"$or": [{"id": conversation_id}, {"_id": conversation_id}]},
            {"$set": {"insight": doc, "updated_at": now}},
        )
        return doc

    def save_spoken_response(
        self,
        db: Any,
        conversation_id: str,
        text: str,
        voice_name: str,
        language_code: str,
        audio_duration_seconds: float,
        synthesis_latency_ms: float,
    ) -> Dict[str, Any]:
        resp_id = str(uuid.uuid4())
        doc = {
            "_id": resp_id,
            "id": resp_id,
            "conversation_id": conversation_id,
            "text": text,
            "voice_name": voice_name,
            "language_code": language_code,
            "audio_duration_seconds": audio_duration_seconds,
            "synthesis_latency_ms": synthesis_latency_ms,
            "created_at": get_utc_now(),
        }
        db.spoken_responses.insert_one(doc)
        db.conversations.update_one(
            {"$or": [{"id": conversation_id}, {"_id": conversation_id}]},
            {"$push": {"spoken_responses": doc}},
        )
        return doc

    def get_dashboard_stats(self, db: Any) -> Dict[str, Any]:
        total_convs = db.conversations.count_documents({})
        processed_convs = db.conversations.count_documents({"status": "completed"})

        insights = list(db.conversation_insights.find())
        avg_frustration = (
            sum(i.get("frustration_index", 0) for i in insights) / len(insights)
            if insights else 0.0
        )
        escalations = sum(1 for i in insights if i.get("escalation_level") in ["high", "critical"])

        return {
            "total_conversations": total_convs,
            "processed_conversations": processed_convs,
            "average_frustration_index": round(avg_frustration, 2),
            "escalated_conversations": escalations,
        }

    def delete(self, db: Any, conversation_id: str) -> bool:
        res = db.conversations.delete_one({"$or": [{"id": conversation_id}, {"_id": conversation_id}]})
        db.conversation_insights.delete_many({"conversation_id": conversation_id})
        db.spoken_responses.delete_many({"conversation_id": conversation_id})
        return res.deleted_count > 0


conversation_repo = ConversationRepository()
