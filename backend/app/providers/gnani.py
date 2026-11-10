"""Official Gnani AI Provider Client for Prisma STT and Timbre TTS."""
from typing import Optional, Dict, Any
from dataclasses import dataclass
import httpx
from app.core.config import settings
from app.core.logging import logger


class GnaniClientException(Exception):
    """Base exception for Gnani client errors."""
    def __init__(self, message: str, status_code: int = 502, error_code: str = "GNANI_ERROR"):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.error_code = error_code


class GnaniConfigurationError(GnaniClientException):
    """Raised when GNANI_API_KEY is missing or invalid."""
    def __init__(self, message: str = "Gnani API key is not configured. Please set GNANI_API_KEY in your .env or environment."):
        super().__init__(message, status_code=401, error_code="MISSING_API_KEY")


class GnaniAuthError(GnaniClientException):
    """Raised when Gnani returns 401 or 403."""
    def __init__(self, message: str = "Gnani API authentication failed. Please verify your GNANI_API_KEY."):
        super().__init__(message, status_code=401, error_code="AUTHENTICATION_FAILED")


class GnaniRateLimitError(GnaniClientException):
    """Raised when upstream rate limits are encountered."""
    def __init__(self, message: str = "Gnani API rate limit exceeded. Please wait a moment before trying again."):
        super().__init__(message, status_code=429, error_code="RATE_LIMIT_EXCEEDED")


class GnaniTimeoutError(GnaniClientException):
    """Raised when upstream request times out."""
    def __init__(self, message: str = "Gnani API request timed out during transcription. Please try with a shorter audio segment."):
        super().__init__(message, status_code=504, error_code="UPSTREAM_TIMEOUT")


class GnaniProviderError(GnaniClientException):
    """Raised when Gnani returns an upstream error or malformed payload."""
    pass


@dataclass
class GnaniTranscriptionResult:
    transcript: str
    confidence_score: Optional[float] = None
    duration_seconds: Optional[float] = None
    request_id: Optional[str] = None
    raw_response: Optional[Dict[str, Any]] = None


class GnaniSpeechClient:
    """
    Dedicated client for Gnani.ai's voice intelligence APIs.
    Communicates with Prisma (STT) and Timbre (TTS).
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        timeout: Optional[float] = None,
    ):
        self.api_key = api_key if api_key is not None else settings.GNANI_API_KEY
        self.base_url = (base_url or settings.GNANI_BASE_URL).rstrip("/")
        self.timeout = timeout or settings.GNANI_TIMEOUT_SECONDS

    def _get_auth_headers(self) -> Dict[str, str]:
        if not self.api_key or not self.api_key.strip() or self.api_key.startswith("your_"):
            raise GnaniConfigurationError()
        return {
            "X-API-Key-ID": self.api_key.strip(),
        }

    async def transcribe_audio(
        self,
        audio_bytes: bytes,
        filename: str,
        language_code: str = "en-IN",
        preferred_language: Optional[str] = None,
        content_type: str = "audio/wav",
    ) -> GnaniTranscriptionResult:
        """
        Sends audio bytes to Gnani Prisma STT (POST /stt/v3).
        Validates response and extracts transcript and metrics.
        """
        headers = self._get_auth_headers()
        url = f"{self.base_url}{settings.GNANI_STT_ENDPOINT}"

        # Prepare multipart/form-data
        files = {
            "audio_file": (filename, audio_bytes, content_type),
        }
        data = {
            "language_code": language_code,
            "preferred_language": preferred_language or language_code,
            "format": "transcribe",
            "itn_native_numerals": "false",
        }

        logger.info(f"Initiating Gnani Prisma STT request to {url} [lang={language_code}, file={filename}]")

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(url, headers=headers, data=data, files=files)

            if response.status_code in (401, 403):
                logger.error(f"Gnani authentication failure (HTTP {response.status_code})")
                raise GnaniAuthError(
                    f"Gnani API rejected credentials (HTTP {response.status_code}). Please verify GNANI_API_KEY."
                )

            if response.status_code == 429:
                logger.warning("Gnani API rate limit hit (HTTP 429)")
                raise GnaniRateLimitError()

            if response.status_code >= 500:
                logger.error(f"Gnani upstream server error (HTTP {response.status_code})")
                raise GnaniProviderError(
                    f"Gnani upstream speech service is temporarily unavailable (HTTP {response.status_code}).",
                    status_code=503,
                )

            if response.status_code != 200:
                logger.error(f"Gnani returned unexpected status {response.status_code}: {response.text}")
                raise GnaniProviderError(
                    f"Gnani speech recognition returned HTTP {response.status_code}: {response.text[:200]}",
                    status_code=response.status_code,
                )

            try:
                res_json = response.json()
            except Exception as json_err:
                logger.error(f"Failed to parse Gnani response as JSON: {json_err}")
                raise GnaniProviderError("Malformed JSON response returned by Gnani API.")

            # Validate response schema
            # Gnani STT response may include 'transcript', 'text', or 'data.transcript'
            transcript = ""
            if isinstance(res_json, dict):
                transcript = (
                    res_json.get("transcript")
                    or res_json.get("text")
                    or (res_json.get("data", {}).get("transcript") if isinstance(res_json.get("data"), dict) else "")
                    or ""
                )

            if not transcript and res_json.get("success") is False:
                err_msg = res_json.get("error", {}).get("message", "Gnani API indicated transcription failure.")
                raise GnaniProviderError(f"Gnani transcription error: {err_msg}")

            confidence = res_json.get("confidence") or res_json.get("confidence_score")
            duration = res_json.get("duration") or res_json.get("audio_duration")
            request_id = res_json.get("request_id")

            logger.info(f"Gnani Prisma STT completed successfully for {filename} (request_id={request_id})")

            return GnaniTranscriptionResult(
                transcript=transcript.strip(),
                confidence_score=float(confidence) if confidence is not None else 0.95,
                duration_seconds=float(duration) if duration is not None else None,
                request_id=request_id,
                raw_response=res_json,
            )

        except httpx.TimeoutException:
            logger.error(f"Gnani STT timed out after {self.timeout}s")
            raise GnaniTimeoutError()
        except httpx.RequestError as req_err:
            logger.error(f"Network error connecting to Gnani API: {req_err}")
            raise GnaniProviderError(f"Network error connecting to Gnani service: {str(req_err)}", status_code=503)

    async def synthesize_speech(
        self,
        text: str,
        voice: str = "Shivani",
        language: str = "en-IN",
        model: str = "timbre-v3.0",
        speed: float = 1.0,
    ) -> bytes:
        """
        Synthesizes spoken audio from text using Gnani Timbre TTS (POST /api/v1/tts/inference).
        Guarantees returned audio has a valid RIFF/WAVE header for standard browser playback.
        """
        import struct

        headers = self._get_auth_headers()
        headers["Content-Type"] = "application/json"
        url = f"{self.base_url}{settings.GNANI_TTS_ENDPOINT}"

        payload = {
            "text": text,
            "voice": voice,
            "language": language,
            "model": model,
            "speed": speed,
            "audio_config": {
                "sample_rate": 24000,
                "num_channels": 1,
                "sample_width": 2,
                "encoding": "linear_pcm",
                "container": "wav",
            },
        }

        logger.info(f"Initiating Gnani Timbre TTS request to {url} [voice={voice}, lang={language}]")

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(url, headers=headers, json=payload)

            if response.status_code in (401, 403):
                raise GnaniAuthError("Gnani API rejected credentials for Timbre TTS.")

            if response.status_code == 429:
                raise GnaniRateLimitError()

            if response.status_code != 200:
                raise GnaniProviderError(
                    f"Gnani Timbre TTS returned HTTP {response.status_code}: {response.text[:200]}",
                    status_code=response.status_code,
                )

            raw_audio = response.content

            # Verify and ensure genuine RIFF/WAVE header for browser compatibility
            if len(raw_audio) >= 12 and raw_audio[:4] == b"RIFF" and raw_audio[8:12] == b"WAVE":
                return raw_audio

            # If raw linear PCM was returned without RIFF header, construct standard 44-byte WAV header
            sample_rate = 24000
            num_channels = 1
            bits_per_sample = 16
            byte_rate = sample_rate * num_channels * (bits_per_sample // 8)
            block_align = num_channels * (bits_per_sample // 8)
            data_size = len(raw_audio)

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
            logger.info(f"Attached standard WAV header to {data_size} bytes of raw PCM from Gnani Timbre")
            return header + raw_audio

        except httpx.TimeoutException:
            raise GnaniTimeoutError("Gnani Timbre TTS timed out.")
        except httpx.RequestError as req_err:
            raise GnaniProviderError(f"Network error during TTS synthesis: {str(req_err)}", status_code=503)
