"""Official Google Gemini 3.8 Flash LLM Provider.

Primary conversational AI provider for VoiceIQ India e-commerce assistant.
Uses the official google-genai SDK for multilingual Indic reasoning and structured intent extraction.
"""
import asyncio
import json
from typing import Dict, Any, Optional, List
from google import genai
from google.genai import types
from google.genai.errors import APIError

from app.core.config import settings
from app.core.logging import logger
from app.services.evon_intent import (
    AssistantStructuredIntent,
    validate_assistant_intent,
    EVON_INTENT_SYSTEM_PROMPT,
)


class GeminiClientException(Exception):
    """Base exception for all Gemini client operations."""
    def __init__(self, message: str, status_code: int = 502, error_code: str = "GEMINI_ERROR"):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.error_code = error_code


class GeminiConfigurationError(GeminiClientException):
    """Raised when Gemini API key is missing or invalid."""
    def __init__(self, message: str = "Gemini API key is not configured. Set GEMINI_API_KEY."):
        super().__init__(message, status_code=503, error_code="GEMINI_NOT_CONFIGURED")


class GeminiAuthError(GeminiClientException):
    """Raised when Gemini API rejects credentials (HTTP 401/403)."""
    def __init__(self, message: str = "Authentication failed for Google Gemini API. Check GEMINI_API_KEY."):
        super().__init__(message, status_code=401, error_code="GEMINI_AUTH_FAILED")


class GeminiTimeoutError(GeminiClientException):
    """Raised when Gemini API call times out."""
    def __init__(self, message: str = "Google Gemini request timed out."):
        super().__init__(message, status_code=504, error_code="GEMINI_TIMEOUT")


class GeminiRateLimitError(GeminiClientException):
    """Raised when Google Gemini API rate limit is exceeded (HTTP 429)."""
    def __init__(self, message: str = "Gemini API rate limit exceeded. Please retry after a brief delay."):
        super().__init__(message, status_code=429, error_code="GEMINI_RATE_LIMITED")



class GeminiServerError(GeminiClientException):
    """Raised when Google Gemini server returns 5xx error."""
    def __init__(self, message: str = "Google Gemini server encountered an error."):
        super().__init__(message, status_code=502, error_code="GEMINI_SERVER_ERROR")


class GeminiValidationError(GeminiClientException):
    """Raised when Gemini output fails validation against intent schema."""
    def __init__(self, message: str = "Gemini structured output validation failed."):
        super().__init__(message, status_code=422, error_code="GEMINI_VALIDATION_FAILED")


class GeminiClient:
    """
    Asynchronous client for Google Gemini 3.8 Flash using the official google-genai SDK.
    Supports structured intent extraction, configurable parameters, timeout enforcement,
    and automatic error mapping.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        model_name: Optional[str] = None,
        timeout: Optional[float] = None,
        temperature: Optional[float] = None,
        max_output_tokens: Optional[int] = None,
        enabled: Optional[bool] = None,
    ):
        self.api_key = (api_key if api_key is not None else settings.GEMINI_API_KEY).strip()
        self.model_name = (model_name or settings.GEMINI_MODEL or "gemini-3.8-flash").strip()
        self.timeout = timeout if timeout is not None else settings.GEMINI_TIMEOUT_SECONDS
        self.temperature = temperature if temperature is not None else settings.GEMINI_TEMPERATURE
        self.max_output_tokens = max_output_tokens if max_output_tokens is not None else settings.GEMINI_MAX_OUTPUT_TOKENS
        self.enabled = enabled if enabled is not None else settings.GEMINI_ENABLED

        self._client: Optional[genai.Client] = None

    def _get_client(self) -> genai.Client:
        """Lazily initialize genai.Client with configured API key."""
        if self._client is None:
            if not self.api_key:
                raise GeminiConfigurationError()
            self._client = genai.Client(api_key=self.api_key)
        return self._client

    def is_configured(self) -> bool:
        """Check if Gemini API is enabled and has a valid API key."""
        if not self.enabled:
            return False
        if not self.api_key:
            return False
        if self.api_key.startswith("your_") or self.api_key.startswith("test_placeholder"):
            return False
        return True

    async def health_check(self) -> Dict[str, Any]:
        """Check availability and connectivity of Google Gemini API."""
        if not self.is_configured():
            return {
                "available": False,
                "configured": False,
                "model": self.model_name,
                "provider": "google-gemini",
                "error": "Gemini API key is not configured (set GEMINI_API_KEY)",
            }

        try:
            client = self._get_client()
            # Asynchronously get model metadata to verify credentials and connectivity
            model_info = await asyncio.wait_for(
                client.aio.models.get(model=self.model_name),
                timeout=min(self.timeout, 10.0),
            )
            return {
                "available": True,
                "configured": True,
                "model": self.model_name,
                "provider": "google-gemini",
                "display_name": getattr(model_info, "display_name", self.model_name),
            }
        except asyncio.TimeoutError:
            return {
                "available": False,
                "configured": True,
                "model": self.model_name,
                "provider": "google-gemini",
                "error": f"Timeout connecting to Gemini API after {self.timeout}s",
            }
        except APIError as exc:
            return {
                "available": False,
                "configured": True,
                "model": self.model_name,
                "provider": "google-gemini",
                "error": str(exc),
                "code": getattr(exc, "code", 500),
            }
        except Exception as exc:
            return {
                "available": False,
                "configured": True,
                "model": self.model_name,
                "provider": "google-gemini",
                "error": str(exc),
            }

    async def generate_response(
        self,
        messages: List[Dict[str, str]],
        system_instruction: Optional[str] = None,
        temperature: Optional[float] = None,
        max_output_tokens: Optional[int] = None,
    ) -> str:
        """Generate unstructured conversational response from Gemini."""
        if not self.is_configured():
            raise GeminiConfigurationError()

        client = self._get_client()
        temp = temperature if temperature is not None else self.temperature
        tokens = max_output_tokens if max_output_tokens is not None else self.max_output_tokens

        config = types.GenerateContentConfig(
            temperature=temp,
            max_output_tokens=tokens,
            system_instruction=system_instruction,
        )

        # Convert standard message format to prompt
        prompt_parts = []
        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            prompt_parts.append(f"{role.capitalize()}: {content}")
        full_prompt = "\n".join(prompt_parts)

        try:
            response = await asyncio.wait_for(
                client.aio.models.generate_content(
                    model=self.model_name,
                    contents=full_prompt,
                    config=config,
                ),
                timeout=self.timeout,
            )
            return response.text or ""
        except asyncio.TimeoutError:
            raise GeminiTimeoutError()
        except APIError as exc:
            code = getattr(exc, "code", 500)
            if code in (401, 403):
                raise GeminiAuthError(f"Gemini authentication failed: {exc}")
            elif code == 429:
                raise GeminiRateLimitError(f"Gemini rate limit exceeded: {exc}")
            elif code >= 500:
                raise GeminiServerError(f"Gemini server error: {exc}")
            raise GeminiClientException(f"Gemini API error ({code}): {exc}", status_code=code)
        except Exception as exc:
            raise GeminiClientException(f"Unexpected Gemini error: {exc}")

    async def generate_intent(
        self,
        transcript: str,
        language: str = "en-IN",
        context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Extract structured e-commerce shopping intent using Google Gemini 3.8 Flash.
        Employs native JSON schema enforcement with AssistantStructuredIntent.
        """
        if not self.is_configured():
            raise GeminiConfigurationError()

        client = self._get_client()
        ctx = context or {}

        user_content = (
            f"Customer Transcript: {transcript}\n"
            f"Detected Language: {language}\n"
            f"Current Page: {ctx.get('current_page', 'home')}\n"
            f"Active Product ID: {ctx.get('product_id', 'None')}\n"
            f"Active Order ID: {ctx.get('order_id', 'None')}\n"
            f"Recent Conversation History: {ctx.get('recent_history', 'None')}\n"
        )

        config = types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=AssistantStructuredIntent,
            temperature=self.temperature,
            max_output_tokens=self.max_output_tokens,
            system_instruction=EVON_INTENT_SYSTEM_PROMPT,
        )

        try:
            response = await asyncio.wait_for(
                client.aio.models.generate_content(
                    model=self.model_name,
                    contents=user_content,
                    config=config,
                ),
                timeout=self.timeout,
            )

            raw_text = response.text or "{}"
            parsed = json.loads(raw_text)
            return parsed

        except asyncio.TimeoutError:
            raise GeminiTimeoutError()
        except APIError as exc:
            code = getattr(exc, "code", 500)
            if code in (401, 403):
                raise GeminiAuthError(f"Gemini authentication failed: {exc}")
            elif code == 429:
                raise GeminiRateLimitError(f"Gemini rate limit exceeded: {exc}")
            elif code >= 500:
                raise GeminiServerError(f"Gemini server error: {exc}")
            raise GeminiClientException(f"Gemini API error ({code}): {exc}", status_code=code)
        except json.JSONDecodeError as exc:
            logger.warning(f"Failed to parse Gemini JSON output: {exc}. Response text: {raw_text[:120]}")
            raise GeminiValidationError(f"Invalid JSON returned by Gemini: {exc}")
        except Exception as exc:
            if isinstance(exc, GeminiClientException):
                raise
            raise GeminiClientException(f"Unexpected Gemini error: {exc}")

    async def close(self) -> None:
        """Close client resources if necessary."""
        self._client = None

