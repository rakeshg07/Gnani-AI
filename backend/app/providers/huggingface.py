"""Official Hugging Face Inference API / Router Provider for VoiceIQ India.

Supports fast, low-latency inference using open-weight models (e.g. Llama-3.2, Qwen-2.5, Mistral)
via Hugging Face's OpenAI-compatible inference router (https://router.huggingface.co/v1)
or dedicated Hugging Face Inference Endpoints.
"""
import asyncio
import json
import re
from typing import Dict, Any, Optional, List, Union, AsyncGenerator
import httpx

from app.core.config import settings
from app.core.logging import logger
from app.services.evon_intent import (
    EVON_INTENT_SYSTEM_PROMPT,
    AssistantStructuredIntent,
    validate_assistant_intent,
    parse_evon_json_output,
)


class HuggingFaceClientException(Exception):
    """Base exception for all Hugging Face inference operations."""
    def __init__(self, message: str, status_code: int = 502, error_code: str = "HF_ERROR"):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.error_code = error_code


class HuggingFaceConfigurationError(HuggingFaceClientException):
    """Raised when Hugging Face API key is missing or invalid."""
    def __init__(self, message: str = "Hugging Face API key is not configured. Set HUGGINGFACE_API_KEY (or HF_TOKEN) in .env"):
        super().__init__(message, status_code=503, error_code="HF_NOT_CONFIGURED")


class HuggingFaceAuthError(HuggingFaceClientException):
    """Raised when Hugging Face authentication fails (HTTP 401/403)."""
    def __init__(self, message: str = "Authentication failed for Hugging Face API. Check HUGGINGFACE_API_KEY."):
        super().__init__(message, status_code=401, error_code="HF_AUTH_FAILED")


class HuggingFaceTimeoutError(HuggingFaceClientException):
    """Raised when Hugging Face inference exceeds timeout."""
    def __init__(self, message: str = "Hugging Face request timed out. Please retry."):
        super().__init__(message, status_code=504, error_code="HF_TIMEOUT")


class HuggingFaceRateLimitError(HuggingFaceClientException):
    """Raised when Hugging Face returns HTTP 429 Too Many Requests."""
    def __init__(self, message: str = "Hugging Face rate limit exceeded. Please retry after a brief delay."):
        super().__init__(message, status_code=429, error_code="HF_RATE_LIMITED")


class HuggingFaceServerError(HuggingFaceClientException):
    """Raised when Hugging Face returns 5xx internal server errors."""
    def __init__(self, message: str = "Hugging Face inference service encountered an internal error."):
        super().__init__(message, status_code=502, error_code="HF_SERVER_ERROR")


class HuggingFaceValidationError(HuggingFaceClientException):
    """Raised when Hugging Face output cannot be parsed into structured intent."""
    def __init__(self, message: str = "Hugging Face structured output validation failed."):
        super().__init__(message, status_code=422, error_code="HF_VALIDATION_FAILED")


class HuggingFaceClient:
    """
    Asynchronous client for Hugging Face Inference API / Router.
    Connects to Hugging Face OpenAI-compatible endpoints with support for
    structured intent extraction, streaming, retries, and error mapping.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        model_name: Optional[str] = None,
        base_url: Optional[str] = None,
        timeout: Optional[float] = None,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        top_p: Optional[float] = None,
        enabled: Optional[bool] = None,
        transport: Optional[httpx.AsyncBaseTransport] = None,
    ):
        self.enabled = enabled if enabled is not None else settings.HUGGINGFACE_ENABLED
        resolved_key = (
            api_key
            or settings.HUGGINGFACE_API_KEY
            or settings.HF_API_KEY
            or settings.HF_TOKEN
            or ""
        )
        self.api_key = resolved_key.strip()

        resolved_model = (
            model_name
            or settings.HUGGINGFACE_MODEL
            or settings.HF_MODEL
            or "meta-llama/Llama-3.2-3B-Instruct"
        )
        self.model_name = resolved_model.strip()

        resolved_url = (
            base_url
            or settings.HUGGINGFACE_BASE_URL
            or settings.HF_BASE_URL
            or "https://router.huggingface.co/v1"
        )
        self.base_url = resolved_url.strip().rstrip("/")

        self.timeout = timeout if timeout is not None else settings.HUGGINGFACE_TIMEOUT_SECONDS
        self.max_tokens = max_tokens if max_tokens is not None else settings.HUGGINGFACE_MAX_TOKENS
        self.temperature = temperature if temperature is not None else settings.HUGGINGFACE_TEMPERATURE
        self.top_p = top_p if top_p is not None else settings.HUGGINGFACE_TOP_P
        self.transport = transport
        self._client: Optional[httpx.AsyncClient] = None

    def is_configured(self) -> bool:
        """Check if Hugging Face is enabled and has a valid API key configured."""
        if not self.enabled:
            return False
        if not self.api_key:
            return False
        if self.api_key.startswith("your_") or self.api_key.startswith("test_placeholder"):
            return False
        return True

    def _get_headers(self) -> Dict[str, str]:
        """Construct authorization and content-type headers."""
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        return headers

    def _build_endpoint(self, path: str = "/chat/completions") -> str:
        """Format the endpoint URL cleanly."""
        base = self.base_url
        if path == "/chat/completions":
            if base.endswith("/chat/completions"):
                return base
            if base.endswith("/v1"):
                return f"{base}/chat/completions"
            return f"{base}/v1/chat/completions"
        elif path == "/models":
            if base.endswith("/chat/completions"):
                base = base[:-len("/chat/completions")]
            if base.endswith("/v1"):
                return f"{base}/models"
            return f"{base}/v1/models"
        return f"{base}{path}"

    async def _get_http_client(self) -> httpx.AsyncClient:
        """Provide or create persistent async httpx client."""
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(timeout=self.timeout, transport=self.transport)
        return self._client

    async def close(self) -> None:
        """Cleanly close underlying HTTP connection pool."""
        if self._client is not None and not self._client.is_closed:
            await self._client.aclose()
            self._client = None

    async def health_check(self) -> Dict[str, Any]:
        """
        Verify connectivity to Hugging Face Inference API.
        """
        if not self.is_configured():
            return {
                "available": False,
                "configured": False,
                "model": self.model_name,
                "provider": "huggingface",
                "error": "Hugging Face API key is not configured (set HUGGINGFACE_API_KEY in .env)",
            }

        url = self._build_endpoint("/models")
        client = await self._get_http_client()
        try:
            res = await client.get(url, headers=self._get_headers(), timeout=min(self.timeout, 5.0))
            if res.status_code == 200:
                return {
                    "available": True,
                    "configured": True,
                    "model": self.model_name,
                    "provider": "huggingface",
                    "base_url": self.base_url,
                }
            elif res.status_code in (401, 403):
                return {
                    "available": False,
                    "configured": True,
                    "model": self.model_name,
                    "provider": "huggingface",
                    "error": "Invalid Hugging Face API key (HTTP 401/403).",
                }
            else:
                # Some routers do not implement /models; test a lightweight chat completion probe
                probe = await self.generate_response([{"role": "user", "content": "hi"}], max_tokens=5)
                return {
                    "available": True,
                    "configured": True,
                    "model": self.model_name,
                    "provider": "huggingface",
                    "base_url": self.base_url,
                }
        except Exception as exc:
            return {
                "available": False,
                "configured": True,
                "model": self.model_name,
                "provider": "huggingface",
                "error": str(exc),
            }

    async def generate_response(
        self,
        messages: List[Dict[str, str]],
        system_instruction: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> str:
        """Generate unstructured conversational response from Hugging Face model."""
        if not self.is_configured():
            raise HuggingFaceConfigurationError()

        client = await self._get_http_client()
        temp = temperature if temperature is not None else self.temperature
        tokens = max_tokens if max_tokens is not None else self.max_tokens

        formatted_messages = []
        if system_instruction:
            formatted_messages.append({"role": "system", "content": system_instruction})
        formatted_messages.extend(messages)

        payload = {
            "model": self.model_name,
            "messages": formatted_messages,
            "temperature": temp,
            "max_tokens": tokens,
            "top_p": self.top_p,
            "stream": False,
        }

        url = self._build_endpoint("/chat/completions")
        try:
            res = await client.post(url, headers=self._get_headers(), json=payload)
            if res.status_code == 200:
                data = res.json()
                choices = data.get("choices", [])
                if choices:
                    return choices[0].get("message", {}).get("content", "").strip()
                return ""
            elif res.status_code in (401, 403):
                raise HuggingFaceAuthError(f"Hugging Face authentication failed: {res.text}")
            elif res.status_code == 429:
                raise HuggingFaceRateLimitError(f"Hugging Face rate limit exceeded: {res.text}")
            elif res.status_code >= 500:
                raise HuggingFaceServerError(f"Hugging Face server error ({res.status_code}): {res.text}")
            else:
                raise HuggingFaceClientException(f"Hugging Face error ({res.status_code}): {res.text}", status_code=res.status_code)
        except httpx.TimeoutException:
            raise HuggingFaceTimeoutError()
        except httpx.RequestError as exc:
            raise HuggingFaceServerError(f"Network error connecting to Hugging Face: {exc}")

    async def stream_response(
        self,
        messages: List[Dict[str, str]],
        system_instruction: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> AsyncGenerator[str, None]:
        """
        Progressively stream tokens/deltas from Hugging Face OpenAI-compatible API using Server-Sent Events (SSE).
        Yields text deltas as they arrive from the model.
        """
        if not self.is_configured():
            raise HuggingFaceConfigurationError()

        client = await self._get_http_client()
        temp = temperature if temperature is not None else self.temperature
        tokens = max_tokens if max_tokens is not None else self.max_tokens

        formatted_messages = []
        if system_instruction:
            formatted_messages.append({"role": "system", "content": system_instruction})
        formatted_messages.extend(messages)

        payload = {
            "model": self.model_name,
            "messages": formatted_messages,
            "temperature": temp,
            "max_tokens": tokens,
            "top_p": self.top_p,
            "stream": True,
        }

        url = self._build_endpoint("/chat/completions")
        headers = self._get_headers()
        headers["Accept"] = "text/event-stream"

        try:
            async with client.stream("POST", url, headers=headers, json=payload, timeout=self.timeout) as response:
                if response.status_code in (401, 403):
                    raise HuggingFaceAuthError(f"Hugging Face streaming auth failed (HTTP {response.status_code})")
                elif response.status_code == 429:
                    raise HuggingFaceRateLimitError("Hugging Face streaming rate limit exceeded")
                elif response.status_code >= 400:
                    error_text = await response.aread()
                    raise HuggingFaceClientException(
                        f"Hugging Face streaming error ({response.status_code}): {error_text.decode('utf-8', errors='replace')}",
                        status_code=response.status_code
                    )

                async for line in response.aiter_lines():
                    line = line.strip()
                    if not line:
                        continue
                    if line.startswith("data:"):
                        data_str = line[5:].strip()
                        if data_str == "[DONE]":
                            break
                        try:
                            chunk = json.loads(data_str)
                            choices = chunk.get("choices", [])
                            if choices:
                                delta = choices[0].get("delta", {})
                                content = delta.get("content", "")
                                if content:
                                    yield content
                        except json.JSONDecodeError:
                            continue
        except httpx.TimeoutException:
            raise HuggingFaceTimeoutError("Hugging Face streaming timed out.")
        except httpx.RequestError as exc:
            raise HuggingFaceServerError(f"Network error during Hugging Face streaming: {exc}")

    async def generate_intent(
        self,
        transcript: str,
        language: str = "en-IN",
        context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Extract structured shopping intent from customer transcript using Hugging Face model.
        Returns parsed intent dictionary adhering to AssistantStructuredIntent schema.
        """
        if not self.is_configured():
            raise HuggingFaceConfigurationError()

        ctx = context or {}
        user_content = (
            f"Customer Transcript: {transcript}\n"
            f"Detected Language: {language}\n"
            f"Current Page: {ctx.get('current_page', 'home')}\n"
            f"Active Product ID: {ctx.get('product_id', 'None')}\n"
            f"Active Order ID: {ctx.get('order_id', 'None')}\n"
            f"Recent Conversation History: {ctx.get('recent_history', 'None')}\n\n"
            f"Respond ONLY with a valid JSON object matching the required schema. Do NOT include markdown code fences or explanations."
        )

        messages = [
            {"role": "system", "content": EVON_INTENT_SYSTEM_PROMPT},
            {"role": "user", "content": user_content},
        ]

        raw_text = await self.generate_response(
            messages=messages,
            temperature=self.temperature,
            max_tokens=self.max_tokens,
        )

        parsed = parse_evon_json_output(raw_text)
        return parsed

