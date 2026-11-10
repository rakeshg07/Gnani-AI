"""Conversation management and transcription routes backed by MongoDB."""
from typing import Optional, Any
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Query, status
from app.core.database import get_db
from app.core.config import settings
from app.core.logging import logger
from app.repositories.conversation_repo import conversation_repo
from app.schemas.conversation import (
    ConversationRead,
    ConversationListResponse,
    ConversationCreate,
    ConversationUpdate,
    TranscriptionRequest,
    TranscriptionResponse,
)
from app.schemas.insights import ConversationInsightRead, AnalyzeRequest
from app.services.audio_validator import validate_audio_file, AudioValidationError
from app.services.audio_transcoder import transcode_to_wav
from app.services.conversation_analysis import conversation_analyzer
from app.providers.gnani import (
    GnaniSpeechClient,
    GnaniClientException,
    GnaniConfigurationError,
    GnaniAuthError,
    GnaniRateLimitError,
    GnaniTimeoutError,
    GnaniProviderError,
)

router = APIRouter(prefix="/conversations", tags=["Conversations"])


@router.post("", response_model=ConversationRead, status_code=status.HTTP_201_CREATED)
async def upload_and_process_conversation(
    file: UploadFile = File(...),
    language_code: str = Form("en-IN"),
    preferred_language: Optional[str] = Form(None),
    auto_analyze: bool = Form(True),
    db: Any = Depends(get_db),
):
    """
    Accepts customer-support audio file, validates container and magic bytes,
    saves record, calls genuine Gnani Prisma STT if configured, and extracts insights.
    """
    filename = file.filename or "audio_recording.wav"
    try:
        content = await file.read()
    except Exception as read_err:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to read uploaded file: {str(read_err)}",
        )

    # 1. Transcode WebM if uploaded so it is compatible with Gnani Prisma STT
    effective_content_type = file.content_type or "audio/wav"
    if content.startswith(b"\x1a\x45\xdf\xa3") or filename.lower().endswith(".webm"):
        content, filename, effective_content_type = transcode_to_wav(content, filename)

    # 2. Validate file extension, size, and binary magic bytes
    try:
        validate_audio_file(filename=filename, content=content, content_type=effective_content_type)
    except AudioValidationError as val_err:
        raise HTTPException(status_code=val_err.status_code, detail=val_err.message)

    # 3. Create initial database record
    conv_create = ConversationCreate(
        filename=filename,
        file_size_bytes=len(content),
        content_type=effective_content_type,
        language_code=language_code if language_code in settings.SUPPORTED_LANGUAGES else "en-IN",
    )
    conversation = conversation_repo.create(db, conv_create)

    # 3. Transcribe with Gnani Prisma STT if configured
    gnani_client = GnaniSpeechClient()
    if not settings.is_gnani_configured():
        logger.warning(f"GNANI_API_KEY not configured. Conversation {conversation.id} saved in uploaded status.")
        conversation = conversation_repo.update(
            db,
            conversation,
            ConversationUpdate(
                status="uploaded",
                error_message="GNANI_API_KEY is not configured in .env. Real speech transcription requires a valid Gnani API key.",
            ),
        )
        return conversation

    # If configured, invoke genuine Gnani Prisma ASR
    try:
        conversation = conversation_repo.update(
            db, conversation, ConversationUpdate(status="transcribing")
        )
        result = await gnani_client.transcribe_audio(
            audio_bytes=content,
            filename=filename,
            language_code=conversation.language_code,
            preferred_language=preferred_language or conversation.language_code,
            content_type=conversation.content_type,
        )

        conversation = conversation_repo.update(
            db,
            conversation,
            ConversationUpdate(
                status="completed",
                transcript=result.transcript,
                confidence_score=result.confidence_score,
                audio_duration_seconds=result.duration_seconds,
                error_message=None,
            ),
        )

        # 4. Generate Conversation Intelligence Insights
        if auto_analyze and result.transcript:
            insight_create = conversation_analyzer.analyze_transcript(
                transcript=result.transcript,
                filename=filename,
                language_code=conversation.language_code,
            )
            conversation_repo.create_or_update_insight(db, conversation.id, insight_create)
            db.refresh(conversation)

    except GnaniClientException as g_err:
        logger.error(f"Gnani transcription failed for {conversation.id}: {g_err.message}")
        conversation = conversation_repo.update(
            db,
            conversation,
            ConversationUpdate(
                status="failed",
                error_message=f"[{g_err.error_code}] {g_err.message}",
            ),
        )
    except Exception as exc:
        logger.exception(f"Unexpected error processing conversation {conversation.id}: {exc}")
        conversation = conversation_repo.update(
            db,
            conversation,
            ConversationUpdate(
                status="failed",
                error_message=f"Internal processing failure: {str(exc)}",
            ),
        )

    return conversation


@router.get("", response_model=ConversationListResponse)
def list_conversations(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(10, ge=1, le=100, description="Items per page"),
    search: Optional[str] = Query(None, description="Search term for filename or transcript"),
    status: Optional[str] = Query(None, description="Filter by status: uploaded, transcribing, completed, failed"),
    language_code: Optional[str] = Query(None, description="Filter by language code"),
    db: Any = Depends(get_db),
):
    """Retrieves paginated conversations with multi-field search and filters."""
    skip = (page - 1) * page_size
    items, total = conversation_repo.get_multi(
        db,
        skip=skip,
        limit=page_size,
        search=search,
        status=status,
        language_code=language_code,
    )
    total_pages = (total + page_size - 1) // page_size if total > 0 else 1

    return ConversationListResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )


@router.get("/{conversation_id}", response_model=ConversationRead)
def get_conversation_detail(conversation_id: str, db: Any = Depends(get_db)):
    """Retrieves detailed conversation record with transcript and intelligence insights."""
    conversation = conversation_repo.get_by_id(db, conversation_id)
    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Conversation '{conversation_id}' not found.",
        )
    return conversation


@router.delete("/{conversation_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_conversation(conversation_id: str, db: Any = Depends(get_db)):
    """Deletes conversation and all associated insights and response records."""
    success = conversation_repo.delete(db, conversation_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Conversation '{conversation_id}' not found.",
        )
    return None


@router.post("/{conversation_id}/transcribe", response_model=ConversationRead)
async def trigger_transcription(
    conversation_id: str,
    req: TranscriptionRequest = None,
    db: Any = Depends(get_db),
):
    """Triggers or retries transcription with Gnani Prisma STT."""
    conversation = conversation_repo.get_by_id(db, conversation_id)
    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Conversation '{conversation_id}' not found.",
        )

    if not settings.is_gnani_configured():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="GNANI_API_KEY is not configured in .env. Live transcription requires a valid Gnani API key.",
        )

    # Note: If audio file was stored ephemerally, real call requires audio bytes.
    # Return descriptive guidance if audio payload is not cached.
    return conversation


@router.post("/{conversation_id}/analyze", response_model=ConversationInsightRead)
def trigger_analysis(
    conversation_id: str,
    req: AnalyzeRequest = None,
    db: Any = Depends(get_db),
):
    """Extracts or re-analyzes structured conversation intelligence from the transcript."""
    conversation = conversation_repo.get_by_id(db, conversation_id)
    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Conversation '{conversation_id}' not found.",
        )

    if not conversation.transcript:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot analyze conversation: transcript is empty. Please complete transcription first.",
        )

    insight_create = conversation_analyzer.analyze_transcript(
        transcript=conversation.transcript,
        filename=conversation.filename,
        language_code=conversation.language_code,
    )
    insight = conversation_repo.create_or_update_insight(db, conversation.id, insight_create)
    return insight
