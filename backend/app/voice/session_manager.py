"""Voice Session State & Lifecycle Manager for VoiceIQ Real-Time Conversations."""
import struct
import time
from enum import Enum
from typing import Dict, Optional, Any
from app.core.logging import logger
from app.voice.vad import VoiceActivityDetector
from app.voice.interruption_manager import InterruptionManager


class VoiceSessionState(str, Enum):
    IDLE = "IDLE"
    CONNECTING = "CONNECTING"
    LISTENING = "LISTENING"
    TRANSCRIBING = "TRANSCRIBING"
    THINKING = "THINKING"
    SPEAKING = "SPEAKING"
    INTERRUPTED = "INTERRUPTED"
    ERROR = "ERROR"
    ENDED = "ENDED"


class VoiceSession:
    """Represents a single active continuous voice conversation over WebSocket."""

    def __init__(
        self,
        session_id: str,
        conversation_id: Optional[str] = None,
        language_code: str = "en-IN",
        current_page: str = "home",
    ):
        self.session_id = session_id
        self.conversation_id = conversation_id or f"conv_{session_id[:8]}"
        self.language_code = language_code
        self.current_page = current_page
        self.state = VoiceSessionState.CONNECTING
        self.is_muted = False
        self.created_at = time.time()
        self.last_active_at = time.time()

        # Audio stream buffer for the current turn (16kHz 16-bit mono PCM)
        self.audio_buffer = bytearray()

        # VAD & Interruption controllers
        self.vad = VoiceActivityDetector()
        self.interruption = InterruptionManager(session_id=session_id)

        # Contextual metadata
        self.customer_context: Dict[str, Any] = {
            "current_page": current_page,
            "product_id": None,
            "order_id": None,
        }

    def update_activity(self):
        self.last_active_at = time.time()

    def transition_to(self, new_state: VoiceSessionState) -> VoiceSessionState:
        old_state = self.state
        self.state = new_state
        self.update_activity()
        logger.debug(f"[{self.session_id}] State transition: {old_state.value} -> {new_state.value}")
        return self.state

    def append_audio_chunk(self, pcm_bytes: bytes):
        """Append raw PCM bytes to turn buffer."""
        if not self.is_muted:
            self.audio_buffer.extend(pcm_bytes)
            self.update_activity()

    def clear_audio_buffer(self):
        self.audio_buffer.clear()
        self.vad.reset()

    def get_audio_wav_bytes(self) -> bytes:
        """
        Encodes the accumulated PCM audio buffer into a compliant 16kHz mono WAV file
        with a genuine 44-byte RIFF header for Gnani Prisma STT.
        """
        data_size = len(self.audio_buffer)
        sample_rate = 16000
        num_channels = 1
        bits_per_sample = 16
        byte_rate = sample_rate * num_channels * (bits_per_sample // 8)
        block_align = num_channels * (bits_per_sample // 8)

        header = struct.pack(
            "<4sI4s4sIHHIIHH4sI",
            b"RIFF",
            36 + data_size,
            b"WAVE",
            b"fmt ",
            16,
            1,  # PCM
            num_channels,
            sample_rate,
            byte_rate,
            block_align,
            bits_per_sample,
            b"data",
            data_size,
        )
        return header + bytes(self.audio_buffer)


class VoiceSessionRegistry:
    """Registry maintaining active live voice sessions."""

    def __init__(self):
        self._sessions: Dict[str, VoiceSession] = {}

    def create_session(
        self,
        session_id: str,
        conversation_id: Optional[str] = None,
        language_code: str = "en-IN",
        current_page: str = "home",
    ) -> VoiceSession:
        session = VoiceSession(
            session_id=session_id,
            conversation_id=conversation_id,
            language_code=language_code,
            current_page=current_page,
        )
        self._sessions[session_id] = session
        return session

    def get_session(self, session_id: str) -> Optional[VoiceSession]:
        return self._sessions.get(session_id)

    def remove_session(self, session_id: str) -> Optional[VoiceSession]:
        return self._sessions.pop(session_id, None)

    def active_count(self) -> int:
        return len(self._sessions)


# Global singleton registry
session_registry = VoiceSessionRegistry()

