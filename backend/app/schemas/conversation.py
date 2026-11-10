"""Pydantic schemas for Conversations and Transcription."""
from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict
from app.schemas.insights import ConversationInsightRead


class ConversationBase(BaseModel):
    filename: str
    file_size_bytes: int = Field(default=0)
    content_type: str = Field(default="audio/wav")
    language_code: str = Field(default="en-IN")


class ConversationCreate(ConversationBase):
    pass


class ConversationUpdate(BaseModel):
    status: Optional[str] = None
    transcript: Optional[str] = None
    confidence_score: Optional[float] = None
    audio_duration_seconds: Optional[float] = None
    error_message: Optional[str] = None


class ConversationRead(ConversationBase):
    id: str
    status: str
    transcript: Optional[str] = None
    confidence_score: Optional[float] = None
    audio_duration_seconds: Optional[float] = None
    error_message: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    insight: Optional[ConversationInsightRead] = None
    model_config = ConfigDict(from_attributes=True)


class ConversationListResponse(BaseModel):
    items: List[ConversationRead]
    total: int
    page: int
    page_size: int
    total_pages: int


class TranscriptionRequest(BaseModel):
    language_code: Optional[str] = Field(default=None, description="Override language code for transcription")
    preferred_language: Optional[str] = Field(default=None, description="Secondary/preferred language code")


class TranscriptionResponse(BaseModel):
    conversation_id: str
    status: str
    transcript: str
    confidence_score: Optional[float] = None
    audio_duration_seconds: Optional[float] = None
    language_code: str
    provider: str = "Gnani Prisma v2.5"
