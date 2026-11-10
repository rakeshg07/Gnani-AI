"""Pydantic schemas for Timbre Text-to-Speech (TTS)."""
from typing import Optional
from pydantic import BaseModel, Field
from datetime import datetime


class TTSRequest(BaseModel):
    conversation_id: Optional[str] = Field(default=None, description="Associated conversation ID")
    text: str = Field(..., min_length=1, max_length=2000, description="Support agent response text to synthesize")
    voice: str = Field(default="Nalini", description="Production voice: Nalini, Shivani, Yashvi, Avinash")
    language: str = Field(default="en-IN", description="BCP-47 language code: en-IN, hi-IN, ta-IN, etc.")
    model: str = Field(default="timbre-v3.0", description="Timbre model: timbre-v3.0 or timbre-v2.5")
    speed: float = Field(default=1.0, ge=0.5, le=2.0, description="Speech rate speed multiplier")


class TTSResponse(BaseModel):
    id: str
    conversation_id: Optional[str] = None
    voice_name: str
    language_code: str
    audio_base64: str = Field(..., description="Base64 encoded audio string for instant browser playback")
    media_type: str = "audio/wav"
    created_at: datetime
