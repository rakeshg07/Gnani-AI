"""Text-to-Speech routes using Gnani Timbre neural voice synthesis backed by MongoDB."""
import base64
import uuid
from typing import Any
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status
from app.core.database import get_db
from app.core.config import settings
from app.schemas.tts import TTSRequest, TTSResponse
from app.providers.gnani import GnaniSpeechClient, GnaniClientException

router = APIRouter(prefix="/tts", tags=["Text-to-Speech"])


@router.post("/synthesize", response_model=TTSResponse)
async def synthesize_speech(req: TTSRequest, db: Any = Depends(get_db)):
    """
    Synthesizes customer support response text into natural voice audio using Gnani Timbre.
    Returns base64-encoded audio for direct browser playback.
    """
    if not settings.is_gnani_configured():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="GNANI_API_KEY is not configured in .env. Live Timbre TTS voice synthesis requires a valid Gnani API key.",
        )

    gnani_client = GnaniSpeechClient()
    try:
        audio_bytes = await gnani_client.synthesize_speech(
            text=req.text,
            voice=req.voice,
            language=req.language,
            model=req.model,
            speed=req.speed,
        )
    except GnaniClientException as g_err:
        raise HTTPException(status_code=g_err.status_code, detail=f"Timbre TTS Error: {g_err.message}")
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Speech synthesis failure: {str(exc)}",
        )

    audio_b64 = base64.b64encode(audio_bytes).decode("utf-8")
    resp_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc)

    # If associated with a conversation, record the spoken response in MongoDB
    if req.conversation_id:
        spoken_rec = {
            "_id": resp_id,
            "id": resp_id,
            "conversation_id": req.conversation_id,
            "text": req.text,
            "voice_name": req.voice,
            "language_code": req.language,
            "created_at": now,
        }
        db.spoken_responses.insert_one(spoken_rec)
        db.conversations.update_one(
            {"$or": [{"id": req.conversation_id}, {"_id": req.conversation_id}]},
            {"$push": {"spoken_responses": spoken_rec}},
        )

    return TTSResponse(
        id=resp_id,
        conversation_id=req.conversation_id,
        voice_name=req.voice,
        language_code=req.language,
        audio_base64=audio_b64,
        media_type="audio/wav",
        created_at=now,
    )
