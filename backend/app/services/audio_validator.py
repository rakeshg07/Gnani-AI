"""Audio file validation service: validates size, extension, and binary magic bytes."""
import os
from typing import Tuple
from app.core.config import settings


class AudioValidationError(Exception):
    """Exception raised when an uploaded audio file fails validation."""
    def __init__(self, message: str, status_code: int = 400):
        super().__init__(message)
        self.message = message
        self.status_code = status_code


def validate_audio_file(filename: str, content: bytes, content_type: str = "") -> Tuple[bool, str]:
    """
    Validates uploaded audio data against:
    1. Empty file checks
    2. File size limits (<= 25MB)
    3. Allowed extension checks (.wav, .mp3, .m4a, .ogg, .flac)
    4. Magic byte signatures to verify genuine audio container binary headers
    """
    if not content or len(content) == 0:
        raise AudioValidationError("Audio file is completely empty (0 bytes).", status_code=400)

    if len(content) > settings.MAX_AUDIO_FILE_SIZE_BYTES:
        max_mb = settings.MAX_AUDIO_FILE_SIZE_BYTES // (1024 * 1024)
        raise AudioValidationError(
            f"Audio file size ({len(content) / (1024*1024):.2f} MB) exceeds maximum allowed limit of {max_mb} MB.",
            status_code=413,
        )

    _, ext = os.path.splitext(filename.lower())
    if ext not in settings.ALLOWED_AUDIO_EXTENSIONS:
        raise AudioValidationError(
            f"Unsupported file extension '{ext}'. Allowed extensions: {', '.join(settings.ALLOWED_AUDIO_EXTENSIONS)}",
            status_code=400,
        )

    # Magic byte verification
    header = content[:16]
    detected_format = None

    if len(content) >= 12 and header[:4] == b"RIFF" and content[8:12] == b"WAVE":
        detected_format = "wav"
    elif header[:3] == b"ID3" or (len(content) >= 2 and header[0] == 0xFF and (header[1] & 0xE0) == 0xE0):
        detected_format = "mp3"
    elif header[:4] == b"fLaC":
        detected_format = "flac"
    elif header[:4] == b"OggS":
        detected_format = "ogg"
    elif len(content) >= 8 and content[4:8] == b"ftyp":
        detected_format = "m4a"
    elif len(content) >= 4 and header[:4] == b"\x1a\x45\xdf\xa3":
        detected_format = "webm"

    if detected_format is None:
        # If magic bytes do not match recognized audio headers, reject spoofed/corrupted files
        raise AudioValidationError(
            f"Corrupted or invalid audio file: '{filename}' does not contain recognized audio stream signatures.",
            status_code=400,
        )

    return True, detected_format
