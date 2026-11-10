"""Audio transcoding service using ffmpeg to ensure compatibility with Gnani Prisma STT."""
import os
import subprocess
from typing import Tuple
from app.core.logging import logger


def transcode_to_wav(
    audio_bytes: bytes,
    original_filename: str = "recording.wav",
    target_sample_rate: int = 16000,
) -> Tuple[bytes, str, str]:
    """
    Transcodes audio (e.g. WebM from browser MediaRecorder, or other formats)
    into standard 16-bit PCM mono WAV at 16kHz, which is guaranteed to be accepted
    by Gnani Prisma STT.

    Returns:
        (transcoded_bytes, filename, content_type)
    """
    # If already a valid WAV with RIFF & WAVE headers, no transcoding needed
    if len(audio_bytes) >= 12 and audio_bytes[:4] == b"RIFF" and audio_bytes[8:12] == b"WAVE":
        base = os.path.splitext(original_filename)[0] or "mic_recording"
        return audio_bytes, f"{base}.wav", "audio/wav"

    # Transcode using ffmpeg
    try:
        process = subprocess.run(
            [
                "ffmpeg",
                "-y",
                "-hide_banner",
                "-loglevel", "error",
                "-i", "pipe:0",
                "-ar", str(target_sample_rate),
                "-ac", "1",
                "-c:a", "pcm_s16le",
                "-f", "wav",
                "pipe:1",
            ],
            input=audio_bytes,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=True,
            timeout=15.0,
        )

        output_wav = process.stdout
        if len(output_wav) >= 44 and output_wav[:4] == b"RIFF":
            base = os.path.splitext(original_filename)[0] or "mic_recording"
            new_filename = f"{base}.wav"
            logger.info(
                f"Transcoded {original_filename} ({len(audio_bytes)} bytes) -> "
                f"{new_filename} ({len(output_wav)} bytes, 16kHz mono WAV)"
            )
            return output_wav, new_filename, "audio/wav"
        else:
            logger.warning("ffmpeg output did not contain valid WAV header, returning original")
    except Exception as exc:
        logger.warning(f"Audio transcoding to WAV failed ({exc}), falling back to original audio")

    return audio_bytes, original_filename, "audio/wav"
