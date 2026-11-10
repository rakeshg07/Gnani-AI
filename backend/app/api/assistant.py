"""API router for Voice Assistant interactions, speech-to-text, and confirmed actions backed by MongoDB."""
from typing import Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Query, status

from app.core.database import get_db
from app.core.config import settings
from app.providers.gnani import GnaniSpeechClient, GnaniClientException
from app.providers.gemini import GeminiClient, GeminiClientException
from app.providers.huggingface import HuggingFaceClient, HuggingFaceClientException
from app.providers.ollama import OllamaClient, OllamaClientException
from app.services.evon_client import EvonClient, EvonClientException
from app.providers.evon import EvonInferenceClient
from app.services.audio_validator import validate_audio_file, AudioValidationError
from app.services.audio_transcoder import transcode_to_wav
from app.services.voice_assistant import VoiceAssistantOrchestrator
from app.services.query_scope import classify_query_scope, QueryScopeResult
from app.services.ecommerce_service import ECommerceService, ECommerceException
from app.services.assistant_locales import format_msg
from app.core.security import get_authenticated_customer, create_customer_session_token
from app.schemas.ecommerce import (
    AssistantMessageIn,
    AssistantMessageOut,
    ConfirmActionIn,
    ProcessTranscriptIn,
    ChatIn,
    OrderOut,
    ReturnRequestOut,
)
from app.core.logging import logger

router = APIRouter(tags=["Voice Assistant"])


@router.post("/voice/transcribe")
async def transcribe_voice(
    file: UploadFile = File(..., description="Customer audio recording (WAV/MP3/M4A/OGG/FLAC)"),
    language_code: str = Form("en-IN", description="BCP-47 Indian language code"),
    preferred_language: Optional[str] = Form(None),
):
    """
    Genuine Gnani Prisma Speech-to-Text endpoint.
    Transcodes browser audio (WebM) to pristine 16-bit PCM WAV at 16kHz, validates format,
    and proxies directly to https://api.vachana.ai/stt/v3.
    """
    logger.info(f"Received voice transcription request: {file.filename} (lang={language_code})")
    audio_bytes = await file.read()

    # Transcode WebM (or non-standard formats) to pristine 16kHz mono WAV for Gnani Prisma STT
    original_name = file.filename or "recording.wav"
    audio_bytes, effective_filename, effective_content_type = transcode_to_wav(
        audio_bytes=audio_bytes,
        original_filename=original_name,
    )

    validate_audio_file(filename=effective_filename, content=audio_bytes, content_type=effective_content_type)

    client = GnaniSpeechClient()
    try:
        result = await client.transcribe_audio(
            audio_bytes=audio_bytes,
            filename=effective_filename,
            language_code=language_code,
            preferred_language=preferred_language,
            content_type=effective_content_type,
        )
        return {
            "success": True,
            "transcript": result.transcript,
            "confidence": result.confidence_score,
            "duration": result.duration_seconds,
            "request_id": result.request_id,
            "language_code": language_code,
        }
    except GnaniClientException as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message)
    except Exception as exc:
        logger.error(f"Unexpected error in transcribe_voice: {exc}")
        raise HTTPException(status_code=500, detail=str(exc))


# ============================================================================
# SECTION 14: STANDARDIZED ASSISTANT ENDPOINTS
# ============================================================================

@router.get("/assistant/health")
async def get_assistant_health():
    """
    Health check for VoiceIQ Assistant, Ollama (Qwen 4B for text), Google Gemini (for voice),
    and Gnani Prisma STT / Timbre TTS platform services.
    """
    ollama_client = OllamaClient()
    ollama_health = await ollama_client.health_check()
    gemini_client = GeminiClient()
    gemini_health = await gemini_client.health_check()
    hf_client = HuggingFaceClient()
    hf_health = await hf_client.health_check()
    evon_client = EvonClient()
    evon_health = await evon_client.health_check()
    gnani_configured = settings.is_gnani_configured()

    return {
        "status": "healthy" if (gnani_configured or gemini_health.get("available") or ollama_health.get("available")) else "degraded",
        "service": "VoiceIQ India Voice Assistant",
        "routing": {
            "text_chat_provider": getattr(settings, "TEXT_CHAT_PROVIDER", "ollama"),
            "voice_chat_provider": getattr(settings, "VOICE_CHAT_PROVIDER", "gemini"),
            "primary_ai_provider": settings.AI_PROVIDER,
        },
        "ollama_llm": {
            "role": "Route 1: Normal Text Conversations",
            "enabled": getattr(settings, "OLLAMA_ENABLED", True),
            "configured": ollama_client.is_configured(),
            "model_name": ollama_client.model_name,
            "base_url": ollama_client.base_url,
            "health": ollama_health,
        },
        "gemini_llm": {
            "role": "Route 2: Real-Time Spoken Conversations",
            "enabled": settings.GEMINI_ENABLED,
            "configured": gemini_client.is_configured(),
            "model_name": gemini_client.model_name,
            "health": gemini_health,
        },
        "huggingface_llm": {
            "role": "Preserved / Inactive",
            "enabled": settings.HUGGINGFACE_ENABLED,
            "configured": hf_client.is_configured(),
            "model_name": hf_client.model_name,
            "base_url": hf_client.base_url,
            "health": hf_health,
        },
        "gnani_speech": {
            "configured": gnani_configured,
            "base_url": settings.GNANI_BASE_URL,
            "stt_endpoint": settings.GNANI_STT_ENDPOINT,
            "tts_endpoint": settings.GNANI_TTS_ENDPOINT,
        },
    }


@router.get("/assistant/ollama/status")
async def get_ollama_status():
    """
    Status and configuration diagnostics for local Ollama / Qwen3 4B runtime.
    """
    client = OllamaClient()
    health = await client.health_check()
    return {
        "enabled": getattr(settings, "OLLAMA_ENABLED", True),
        "model_name": client.model_name,
        "base_url": client.base_url,
        "is_configured": client.is_configured(),
        "health": health,
    }


@router.get("/assistant/huggingface/status")
@router.get("/assistant/hf/status")
async def get_huggingface_status():
    """
    Status and configuration diagnostics for Hugging Face Inference API / Router.
    """
    client = HuggingFaceClient()
    health = await client.health_check()
    return {
        "provider": "huggingface",
        "model_id": client.model_name,
        "configured": client.is_configured(),
        "enabled": settings.HUGGINGFACE_ENABLED,
        "base_url": client.base_url,
        "timeout_seconds": settings.HUGGINGFACE_TIMEOUT_SECONDS,
        "supported_languages": [
            "English", "Hindi", "Bengali", "Telugu", "Tamil",
            "Marathi", "Gujarati", "Kannada", "Malayalam", "Odia", "Punjabi"
        ],
        "health": health,
    }


@router.post("/assistant/check-scope", response_model=QueryScopeResult)
async def check_query_scope(payload: ChatIn):
    """
    Diagnostic endpoint to evaluate domain scope of customer query.
    """
    hf_client = HuggingFaceClient()
    return await classify_query_scope(
        message=payload.message,
        current_page=payload.current_page or "home",
        language_code=payload.language or "en-IN",
        huggingface_client=hf_client if hf_client.is_configured() else None,
    )


@router.get("/assistant/gemini/status")
async def get_gemini_status():
    """
    Status and configuration diagnostics for Google Gemini 3.8 Flash LLM.
    """
    client = GeminiClient()
    health = await client.health_check()
    return {
        "provider": "gemini",
        "model_id": client.model_name,
        "configured": client.is_configured(),
        "enabled": settings.GEMINI_ENABLED,
        "timeout_seconds": settings.GEMINI_TIMEOUT_SECONDS,
        "supported_languages": [
            "English", "Hindi", "Bengali", "Telugu", "Tamil",
            "Marathi", "Gujarati", "Kannada", "Malayalam", "Odia", "Punjabi"
        ],
        "health": health,
    }


@router.post("/assistant/voice", response_model=AssistantMessageOut)
async def process_voice_audio(
    file: UploadFile = File(..., description="Customer voice audio recording"),
    language_code: str = Form("en-IN", description="Target Indian language code"),
    current_page: str = Form("home", description="Current page context"),
    product_id: Optional[str] = Form(None, description="Active product being viewed"),
    order_id: Optional[str] = Form(None, description="Active order context"),
    synthesize_audio: bool = Form(False, description="Optionally synthesize Timbre TTS response"),
    customer_id: str = Query("cust_demo_001"),
    db: Any = Depends(get_db),
):
    """
    End-to-end voice shopping pipeline:
    1. Audio transcode & validation.
    2. Gnani Prisma STT speech recognition.
    3. Recognized transcript routed to Gnani Evon v3.3 for structured intent extraction.
    4. Safe execution against real e-commerce database.
    5. Optional Gnani Timbre TTS speech generation.
    """
    logger.info(f"POST /api/assistant/voice: audio file='{file.filename}', lang='{language_code}'")
    audio_bytes = await file.read()
    original_name = file.filename or "voice_query.wav"

    audio_bytes, effective_filename, effective_content_type = transcode_to_wav(
        audio_bytes=audio_bytes,
        original_filename=original_name,
    )
    validate_audio_file(filename=effective_filename, content=audio_bytes, content_type=effective_content_type)

    gnani_client = GnaniSpeechClient()
    try:
        stt_result = await gnani_client.transcribe_audio(
            audio_bytes=audio_bytes,
            filename=effective_filename,
            language_code=language_code,
            content_type=effective_content_type,
        )
        transcript = stt_result.transcript
    except GnaniClientException as exc:
        raise HTTPException(status_code=exc.status_code, detail=f"Prisma STT failed: {exc.message}")

    if not transcript or not transcript.strip():
        return AssistantMessageOut(
            success=False,
            reply_text="No speech was detected in your recording. Please try speaking clearly or typing your message.",
            intent="unknown_intent",
            detected_language=language_code,
            conversation_id="conv_empty",
            transcript="",
            language=language_code,
            message="No speech was detected in your recording.",
            data={"products": [], "order": None, "cart": None},
            requires_confirmation=False,
        )

    # Dispatch to orchestrator
    payload = AssistantMessageIn(
        message=transcript,
        current_page=current_page,
        product_id=product_id,
        order_id=order_id,
        language_code=language_code,
        synthesize_audio=synthesize_audio,
    )
    gnani_client = GnaniSpeechClient()
    evon_client = EvonClient()
    gemini_client = GeminiClient()
    huggingface_client = HuggingFaceClient()
    return await VoiceAssistantOrchestrator.process_message(
        db=db,
        payload=payload,
        customer_id=customer_id,
        gnani_client=gnani_client,
        evon_client=evon_client,
        gemini_client=gemini_client,
        huggingface_client=huggingface_client,
    )


@router.post("/assistant/chat", response_model=AssistantMessageOut)
async def process_chat_message(
    payload: ChatIn,
    customer_id: str = Query("cust_demo_001"),
    db: Any = Depends(get_db),
):
    """
    Route 1: Normal Text Conversations (Qwen3 4B via Ollama).
    Accepts customer text message, extracts intent via Qwen, executes backend store
    operations against real database, and returns interactive cards.
    If Ollama is unavailable, strictly falls back to deterministic store orchestrator.
    Never invokes Gemini or Hugging Face.
    """
    logger.info(f"POST /api/assistant/chat (Route 1 Text - Qwen): msg='{payload.message[:50]}...', lang='{payload.language}'")
    asst_payload = AssistantMessageIn(
        message=payload.message,
        current_page=payload.current_page or "home",
        product_id=payload.product_id,
        order_id=payload.order_id,
        language_code=payload.language or "en-IN",
        synthesize_audio=payload.synthesize_audio,
    )
    gnani_client = GnaniSpeechClient()
    ollama_client = OllamaClient()
    return await VoiceAssistantOrchestrator.process_message(
        db=db,
        payload=asst_payload,
        customer_id=customer_id,
        gnani_client=gnani_client,
        ollama_client=ollama_client,
        active_provider="ollama",
    )


@router.post("/assistant/process-transcript", response_model=AssistantMessageOut)
async def process_transcript(
    payload: ProcessTranscriptIn,
    customer_id: str = Query("cust_demo_001"),
    db: Any = Depends(get_db),
):
    """
    Direct transcript processing endpoint (Route 1 Text / Transcript):
    Accepts an already recognized transcript string and context, runs Qwen3 4B (Ollama)
    intent extraction, and executes authorized business operations.
    """
    logger.info(f"POST /api/assistant/process-transcript (Qwen): '{payload.transcript[:50]}...'")
    asst_payload = AssistantMessageIn(
        message=payload.transcript,
        current_page=payload.current_page or "home",
        product_id=payload.product_id,
        order_id=payload.order_id,
        language_code=payload.language or "en-IN",
        synthesize_audio=payload.synthesize_audio,
    )
    gnani_client = GnaniSpeechClient()
    ollama_client = OllamaClient()
    return await VoiceAssistantOrchestrator.process_message(
        db=db,
        payload=asst_payload,
        customer_id=customer_id,
        gnani_client=gnani_client,
        ollama_client=ollama_client,
        active_provider="ollama",
    )


@router.get("/assistant/evon/status")
async def get_evon_status():
    """
    Status and configuration diagnostics for Gnani Evon v3.3 open-weight LLM.
    Model card: https://huggingface.co/gnani/gnani-evon-v3.3-30B-A3B
    """
    client = EvonClient()
    health = await client.health_check()
    return {
        "model_id": client.model_name,
        "configured": client.is_configured(),
        "enabled": settings.EVON_ENABLED,
        "endpoint": client.base_url or "Not configured (set EVON_BASE_URL)",
        "hf_repo_id": settings.EVON_HF_REPO_ID,
        "architecture": "Hybrid Mamba2-Transformer MoE (Nemotron Hybrid MoE), 30B total / ~3.5B active",
        "huggingface_repo": f"https://huggingface.co/{settings.EVON_HF_REPO_ID}",
        "supported_languages": [
            "English", "Hindi", "Bengali", "Telugu", "Tamil",
            "Marathi", "Gujarati", "Kannada", "Malayalam", "Odia", "Punjabi"
        ],
        "inference_engine_recommendations": {
            "vllm": f"vllm serve {settings.EVON_HF_REPO_ID} --served-model-name {client.model_name} --max-model-len 8192 --port 8000 --trust-remote-code",
            "sglang": f"python -m sglang.launch_server --model-path {settings.EVON_HF_REPO_ID} --served-model-name {client.model_name} --dtype bfloat16 --context-length 8192 --host 0.0.0.0 --port 30000",
        },
        "health": health,
    }


@router.post("/assistant/message", response_model=AssistantMessageOut)
async def process_assistant_message(
    payload: AssistantMessageIn,
    customer_id: str = Query("cust_demo_001"),
    db: Any = Depends(get_db),
):
    """
    Backward-compatible message endpoint:
    Process shopping query via Qwen (Route 1 Text) or configured provider,
    execute grounded database queries, and return interactive cards.
    """
    gnani_client = GnaniSpeechClient()
    ollama_client = OllamaClient()
    try:
        return await VoiceAssistantOrchestrator.process_message(
            db=db,
            payload=payload,
            customer_id=customer_id,
            gnani_client=gnani_client,
            ollama_client=ollama_client,
            active_provider="ollama",
        )
    except Exception as exc:
        logger.error(f"Error processing assistant message: {exc}")
        raise HTTPException(status_code=500, detail=f"Assistant processing failed: {str(exc)}")


@router.post("/auth/token")
def create_auth_token(
    customer_id: str = Query("cust_demo_001", description="Customer ID to issue signed session token for"),
    db: Any = Depends(get_db),
):
    """
    Issues a cryptographically signed HMAC-SHA256 session token for a customer.
    Allows testing and production clients to authenticate securely without hardcoded IDs.
    """
    cust = db.users.find_one({"id": customer_id}) or db.customers.find_one({"id": customer_id})
    if not cust:
        cust = {"id": customer_id, "name": "Valued Customer"}
    c_id = cust.get("id", customer_id)
    token = create_customer_session_token(customer_id=c_id)
    return {
        "customer_id": c_id,
        "name": cust.get("name", "Customer"),
        "access_token": token,
        "token_type": "bearer",
        "expires_in_hours": settings.SESSION_TTL_HOURS,
    }


@router.post("/assistant/confirm-action")
def confirm_assistant_action(
    payload: ConfirmActionIn,
    customer_id: str = Depends(get_authenticated_customer),
    db: Any = Depends(get_db),
):
    """
    Executes a consequential action (e.g. cancellation or return) after customer confirmation.
    Enforces production security:
    1. Requires a cryptographically verified server-side pending confirmation token.
    2. Validates token expiration (5 minutes TTL).
    3. Enforces authenticated customer identity and order ownership.
    4. Atomically consumes token to prevent replay attacks and race conditions.
    5. Revalidates order state in database before committing.
    """
    logger.info(f"Confirming assistant action: {payload.action} on {payload.target_id} by customer {customer_id}")

    # Check original conversation language if available
    lang = "en-IN"
    if payload.conversation_id:
        conv = db.conversations.find_one({"id": payload.conversation_id})
        if conv and conv.get("language_code"):
            lang = conv["language_code"]

    if not payload.confirmed:
        token = (payload.confirmation_token or "").strip()
        if token:
            db.pending_actions.update_one(
                {"confirmation_token": token, "customer_id": customer_id},
                {"$set": {"status": "cancelled"}},
            )

        cancel_msg = format_msg(lang, "cancel_action_cancelled")
        return {
            "success": True,
            "action": payload.action or "action",
            "target_id": payload.target_id or "order",
            "confirmed": False,
            "message": cancel_msg,
        }

    token = (payload.confirmation_token or "").strip()
    if not token:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing confirmation token. Consequential actions require a cryptographically verified server-side pending confirmation token.",
        )

    try:
        pending_rec, result = ECommerceService.consume_pending_action(
            db=db,
            confirmation_token=token,
            customer_id=customer_id,
            action=payload.action,
            target_id=payload.target_id,
            reason=payload.reason,
        )

        if pending_rec.get("action_type") in ("cancel_order", "request_cancellation"):
            success_msg = format_msg(lang, "cancel_action_confirmed", order_id=result.get("id"), total=result.get("total_amount", 0))
            return {
                "success": True,
                "action": "cancel_order",
                "target_id": result.get("id"),
                "confirmed": True,
                "message": success_msg,
                "order": OrderOut.model_validate(result),
                "token_consumed": True,
            }
        else:
            success_msg = format_msg(lang, "return_action_confirmed", order_id=result.get("order_id"), carrier="our courier partner")
            return {
                "success": True,
                "action": "create_return",
                "target_id": result.get("order_id"),
                "confirmed": True,
                "message": success_msg,
                "return_request": ReturnRequestOut.model_validate(result),
                "token_consumed": True,
            }

    except ECommerceException as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message)
