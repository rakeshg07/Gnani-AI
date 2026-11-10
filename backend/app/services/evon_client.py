"""Official Gnani Evon v3.3 Open-Weight LLM Inference Client.

Connects to a remote OpenAI-compatible inference server (such as vLLM or SGLang)
serving the sovereign Gnani Evon v3.3 Indic model.

Model Reference: https://huggingface.co/gnani/gnani-evon-v3.3-30B-A3B
Architecture: Hybrid Mamba2-Transformer Mixture of Experts (MoE), 30B total / ~3.5B active
Specialized for Indian Languages: English, Hindi, Tamil, Telugu, Kannada, Bengali,
Marathi, Gujarati, Malayalam, Odia, and Punjabi.
"""
import asyncio
import json
import re
from typing import Dict, Any, Optional, List, Union
import httpx

from app.core.config import settings
from app.core.logging import logger


class EvonClientException(Exception):
    """Base exception for all Evon client operations."""
    def __init__(self, message: str, status_code: int = 502, error_code: str = "EVON_ERROR"):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.error_code = error_code


class EvonConfigurationError(EvonClientException):
    """Raised when Evon inference is disabled or missing required remote configuration."""
    def __init__(self, message: str = "Evon v3.3 inference is not configured. Set EVON_ENABLED=true and EVON_BASE_URL to your remote GPU server."):
        super().__init__(message, status_code=503, error_code="EVON_NOT_CONFIGURED")


class EvonConnectionError(EvonClientException):
    """Raised when network connection to the remote Evon inference server fails."""
    def __init__(self, message: str = "Unable to connect to remote Evon inference server. Ensure vLLM/SGLang is running and reachable."):
        super().__init__(message, status_code=503, error_code="EVON_CONNECTION_FAILED")


class EvonAuthError(EvonClientException):
    """Raised when inference server rejects credentials (HTTP 401/403)."""
    def __init__(self, message: str = "Authentication failed for remote Evon inference server. Check EVON_API_KEY."):
        super().__init__(message, status_code=401, error_code="EVON_AUTH_FAILED")


class EvonTimeoutError(EvonClientException):
    """Raised when inference request exceeds configured timeout."""
    def __init__(self, message: str = "Evon inference request timed out. Check GPU host load or increase EVON_TIMEOUT_SECONDS."):
        super().__init__(message, status_code=504, error_code="EVON_TIMEOUT")


class EvonRateLimitError(EvonClientException):
    """Raised when remote inference server returns HTTP 429 Too Many Requests."""
    def __init__(self, message: str = "Evon inference rate limit exceeded. Please retry after a brief delay."):
        super().__init__(message, status_code=429, error_code="EVON_RATE_LIMITED")


class EvonServerError(EvonClientException):
    """Raised when remote inference server returns 5xx internal server errors."""
    def __init__(self, message: str = "Remote Evon inference server encountered an internal error."):
        super().__init__(message, status_code=502, error_code="EVON_SERVER_ERROR")


class EvonValidationError(EvonClientException):
    """Raised when Evon output does not conform to the expected format or schema."""
    def __init__(self, message: str = "Evon structured output validation failed."):
        super().__init__(message, status_code=422, error_code="EVON_VALIDATION_FAILED")


class EvonClient:
    """
    Reusable, asynchronous OpenAI-compatible HTTP client for Gnani Evon v3.3.
    Provides request timeouts, controlled retries, authorization headers,
    health checks, and structured intent extraction.
    """

    def __init__(
        self,
        base_url: Optional[str] = None,
        model_name: Optional[str] = None,
        api_key: Optional[str] = None,
        timeout: Optional[float] = None,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        top_p: Optional[float] = None,
        enabled: Optional[bool] = None,
        enable_thinking: Optional[bool] = None,
        max_retries: int = 2,
        transport: Optional[httpx.AsyncBaseTransport] = None,
    ):
        self.enabled = enabled if enabled is not None else settings.EVON_ENABLED
        self.base_url = (base_url or settings.EVON_BASE_URL or settings.EVON_API_BASE or "").strip().rstrip("/")
        self.model_name = (model_name or settings.EVON_MODEL_NAME or settings.EVON_MODEL_ID or "evon").strip()
        self.api_key = (api_key if api_key is not None else settings.EVON_API_KEY).strip()
        self.timeout = timeout or settings.EVON_TIMEOUT_SECONDS
        self.max_tokens = max_tokens or settings.EVON_MAX_TOKENS
        self.temperature = temperature if temperature is not None else settings.EVON_TEMPERATURE
        self.top_p = top_p if top_p is not None else settings.EVON_TOP_P
        self.enable_thinking = enable_thinking if enable_thinking is not None else settings.EVON_ENABLE_THINKING
        self.max_retries = max(0, max_retries)
        self.transport = transport
        self._client: Optional[httpx.AsyncClient] = None

    def is_configured(self) -> bool:
        """Check if remote inference is enabled and a valid base URL is configured."""
        if not self.enabled:
            return False
        if not self.base_url:
            return False
        if self.base_url.startswith("your_") or self.base_url.startswith("https://your-"):
            return False
        return True

    def _get_headers(self) -> Dict[str, str]:
        """Construct request headers, injecting Bearer token when configured."""
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        return headers

    def _build_endpoint(self, path: str = "/chat/completions") -> str:
        """Format the full endpoint URL cleanly from the configured base URL."""
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

    async def close(self):
        """Cleanly close underlying HTTP connection pool."""
        if self._client is not None and not self._client.is_closed:
            await self._client.aclose()
            self._client = None

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()

    async def health_check(self) -> Dict[str, Any]:
        """
        Verify connectivity to the remote Evon inference endpoint via GET /models.
        Returns a diagnostic status dictionary without leaking secrets.
        """
        if not self.is_configured():
            return {
                "available": False,
                "enabled": self.enabled,
                "configured": False,
                "endpoint": self.base_url or None,
                "model": self.model_name,
                "reason": "Evon remote inference is disabled or EVON_BASE_URL is not configured.",
            }

        url = self._build_endpoint("/models")
        client = await self._get_http_client()
        try:
            res = await client.get(url, headers=self._get_headers(), timeout=5.0)
            if res.status_code == 200:
                try:
                    data = res.json()
                    models = [m.get("id") for m in data.get("data", [])] if isinstance(data, dict) else []
                    return {
                        "available": True,
                        "enabled": True,
                        "configured": True,
                        "endpoint": self.base_url,
                        "model": self.model_name,
                        "available_models": models,
                    }
                except Exception:
                    return {
                        "available": True,
                        "enabled": True,
                        "configured": True,
                        "endpoint": self.base_url,
                        "model": self.model_name,
                    }
            elif res.status_code in (401, 403):
                return {
                    "available": False,
                    "enabled": True,
                    "configured": True,
                    "endpoint": self.base_url,
                    "status_code": res.status_code,
                    "reason": "Authentication failed on inference server (HTTP 401/403).",
                }
            else:
                return {
                    "available": False,
                    "enabled": True,
                    "configured": True,
                    "endpoint": self.base_url,
                    "status_code": res.status_code,
                    "reason": f"Remote server returned HTTP {res.status_code}.",
                }
        except httpx.TimeoutException:
            return {
                "available": False,
                "enabled": True,
                "configured": True,
                "endpoint": self.base_url,
                "reason": "Health check timed out after 5.0s.",
            }
        except Exception as exc:
            return {
                "available": False,
                "enabled": True,
                "configured": True,
                "endpoint": self.base_url,
                "reason": f"Connection error: {type(exc).__name__}",
            }

    async def generate_response(
        self,
        messages: List[Dict[str, str]],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        top_p: Optional[float] = None,
        enable_thinking: Optional[bool] = None,
    ) -> str:
        """
        Sends an OpenAI-compatible Chat Completions request to the remote Evon v3.3 server.
        Follows official model card hyperparameters (temp=0.6, top_p=0.95, repetition_penalty=1.1).
        Implements controlled retries for transient failures.
        """
        if not self.is_configured():
            raise EvonConfigurationError()

        url = self._build_endpoint("/chat/completions")
        temp = temperature if temperature is not None else self.temperature
        tokens = max_tokens if max_tokens is not None else self.max_tokens
        tp = top_p if top_p is not None else self.top_p
        thinking = enable_thinking if enable_thinking is not None else self.enable_thinking

        request_body: Dict[str, Any] = {
            "model": self.model_name,
            "messages": messages,
            "temperature": temp,
            "top_p": tp,
            "max_tokens": tokens,
            "stream": False,
            "repetition_penalty": 1.1,
        }
        if thinking is not None:
            request_body["chat_template_kwargs"] = {"enable_thinking": thinking}

        logger.info(f"Dispatching Evon v3.3 inference request to {url} (model={self.model_name})")

        last_exception: Optional[Exception] = None
        client = await self._get_http_client()

        for attempt in range(self.max_retries + 1):
            try:
                res = await client.post(url, headers=self._get_headers(), json=request_body)

                if res.status_code in (401, 403):
                    logger.error(f"Evon authentication failure: HTTP {res.status_code}")
                    raise EvonAuthError()

                if res.status_code == 429:
                    logger.warning(f"Evon rate limited: HTTP 429 on attempt {attempt + 1}")
                    if attempt < self.max_retries:
                        await asyncio.sleep(1.0 * (attempt + 1))
                        continue
                    raise EvonRateLimitError()

                if res.status_code >= 500:
                    logger.error(f"Evon server error: HTTP {res.status_code}")
                    if attempt < self.max_retries:
                        await asyncio.sleep(1.0 * (attempt + 1))
                        continue
                    raise EvonServerError(f"Evon inference server returned HTTP {res.status_code}.")

                if res.status_code != 200:
                    logger.error(f"Evon unexpected status: HTTP {res.status_code} - {res.text[:200]}")
                    raise EvonClientException(
                        f"Evon inference server returned HTTP {res.status_code}: {res.text[:200]}",
                        status_code=res.status_code,
                    )

                data = res.json()
                choices = data.get("choices", [])
                if not choices:
                    raise EvonClientException("Evon returned empty choices array.")

                reply_content = choices[0].get("message", {}).get("content", "")
                return reply_content.strip()

            except (httpx.ConnectError, httpx.ConnectTimeout) as exc:
                last_exception = exc
                logger.warning(f"Connection failed to Evon server (attempt {attempt + 1}/{self.max_retries + 1}): {exc}")
                if attempt < self.max_retries:
                    await asyncio.sleep(1.0 * (attempt + 1))
                    continue
                raise EvonConnectionError(f"Connection refused or timed out connecting to Evon at {self.base_url}.")

            except httpx.TimeoutException as exc:
                last_exception = exc
                logger.warning(f"Evon request timed out after {self.timeout}s (attempt {attempt + 1})")
                if attempt < self.max_retries:
                    await asyncio.sleep(1.0 * (attempt + 1))
                    continue
                raise EvonTimeoutError(f"Evon inference request timed out after {self.timeout}s.")

            except EvonClientException:
                raise
            except Exception as exc:
                last_exception = exc
                logger.error(f"Unexpected error in Evon inference: {exc}")
                raise EvonClientException(f"Unexpected Evon client error: {str(exc)}")

        if last_exception:
            raise EvonClientException(f"Evon call failed after retries: {str(last_exception)}")
        raise EvonClientException("Evon call failed.")

    async def generate_intent(
        self,
        transcript: str,
        language: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Sends transcript to Evon v3.3 with prompt instructions to produce structured intent JSON.
        Returns the parsed dictionary. Validation against Pydantic schema is handled in evon_intent.py.
        """
        from app.services.evon_intent import EVON_INTENT_SYSTEM_PROMPT, parse_evon_json_output

        if not transcript or not transcript.strip():
            return {
                "intent": "unknown_intent",
                "language": language or "en",
                "parameters": {},
                "response_message": "No voice transcript was detected. How can I help you?",
                "requires_confirmation": False,
            }

        context_str = ""
        if context:
            if context.get("current_page"):
                context_str += f"Current Page: {context['current_page']}. "
            if context.get("product_id"):
                context_str += f"Active Product ID: {context['product_id']}. "
            if context.get("order_id"):
                context_str += f"Active Order ID: {context['order_id']}. "
            if context.get("recent_history"):
                context_str += f"Recent Dialogue Context: {context['recent_history']}. "

        user_content = (
            f"{context_str.strip()}\n"
            f"Language: {language or 'auto-detect'}\n"
            f"Customer Input: \"{transcript.strip()}\"\n"
            f"Produce the structured JSON response:"
        )

        messages = [
            {"role": "system", "content": EVON_INTENT_SYSTEM_PROMPT},
            {"role": "user", "content": user_content},
        ]

        raw_output = await self.generate_response(messages)
        return parse_evon_json_output(raw_output)
