"""Official Ollama Local LLM Provider for VoiceIQ India (Route 1: Text Conversations).

Connects to local Ollama runtime (default: http://127.0.0.1:11434) using Qwen3 4B (qwen3:4b).
Provides async HTTP requests, NDJSON streaming parser, health checks, structured intent extraction,
and strict fallback handling.
"""
import asyncio
import json
from typing import Dict, Any, Optional, List, AsyncGenerator
import httpx

from app.core.config import settings
from app.core.logging import logger
from app.services.evon_intent import (
    EVON_INTENT_SYSTEM_PROMPT,
    AssistantStructuredIntent,
    validate_assistant_intent,
)


class OllamaClientException(Exception):
    """Base exception for all Ollama client operations."""
    def __init__(self, message: str, status_code: int = 502, error_code: str = "OLLAMA_ERROR"):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.error_code = error_code


class OllamaConnectionError(OllamaClientException):
    """Raised when Ollama local server cannot be reached."""
    def __init__(self, message: str = "Cannot connect to Ollama server at http://127.0.0.1:11434"):
        super().__init__(message, status_code=503, error_code="OLLAMA_CONNECTION_ERROR")


class OllamaModelNotFoundError(OllamaClientException):
    """Raised when specified model is not pulled in Ollama."""
    def __init__(self, message: str = "Model 'qwen3:4b' not found in Ollama."):
        super().__init__(message, status_code=404, error_code="OLLAMA_MODEL_NOT_FOUND")


class OllamaTimeoutError(OllamaClientException):
    """Raised when an Ollama request times out."""
    def __init__(self, message: str = "Ollama request timed out."):
        super().__init__(message, status_code=504, error_code="OLLAMA_TIMEOUT")


class OllamaServerError(OllamaClientException):
    """Raised when Ollama returns a 5xx error."""
    def __init__(self, message: str = "Ollama server error."):
        super().__init__(message, status_code=502, error_code="OLLAMA_SERVER_ERROR")


class OllamaClient:
    """
    Asynchronous client for Qwen3 4B hosted locally on Ollama.
    Processes normal text shopping queries with backend-controlled tool integration
    and NDJSON streaming.
    """

    def __init__(
        self,
        base_url: Optional[str] = None,
        model_name: Optional[str] = None,
        timeout: Optional[float] = None,
        temperature: Optional[float] = None,
        enabled: Optional[bool] = None,
    ):
        self.base_url = (base_url or settings.OLLAMA_BASE_URL or "http://127.0.0.1:11434").rstrip("/")
        self.model_name = (model_name or settings.OLLAMA_MODEL or "qwen3:4b").strip()
        self.timeout = timeout if timeout is not None else settings.OLLAMA_TIMEOUT_SECONDS
        self.temperature = temperature if temperature is not None else settings.OLLAMA_TEMPERATURE
        self.enabled = enabled if enabled is not None else settings.OLLAMA_ENABLED

    def is_configured(self) -> bool:
        """Check if Ollama provider is enabled with a valid base URL."""
        if not self.enabled:
            return False
        return bool(self.base_url and not self.base_url.startswith("your_"))

    async def health_check(self) -> Dict[str, Any]:
        """
        Check connectivity to the local Ollama server and verify model availability.
        Does NOT automatically pull the model.
        """
        if not self.is_configured():
            return {
                "available": False,
                "configured": False,
                "provider": "ollama",
                "model": self.model_name,
                "error": "Ollama is disabled in configuration.",
            }

        endpoint = f"{self.base_url}/api/tags"
        try:
            async with httpx.AsyncClient(timeout=4.0) as client:
                res = await client.get(endpoint)
                if res.status_code == 200:
                    data = res.json()
                    available_models = [m.get("name", "") for m in data.get("models", [])]
                    model_found = any(self.model_name in m for m in available_models)
                    return {
                        "available": True,
                        "configured": True,
                        "connected": True,
                        "provider": "ollama",
                        "model": self.model_name,
                        "model_installed": model_found,
                        "available_models": available_models,
                        "base_url": self.base_url,
                    }
                return {
                    "available": False,
                    "configured": True,
                    "connected": False,
                    "provider": "ollama",
                    "model": self.model_name,
                    "status_code": res.status_code,
                    "error": f"Ollama HTTP {res.status_code}",
                }
        except httpx.ConnectError:
            return {
                "available": False,
                "configured": True,
                "connected": False,
                "provider": "ollama",
                "model": self.model_name,
                "error": f"Connection refused at {self.base_url}. Ensure 'ollama serve' is running.",
            }
        except Exception as exc:
            return {
                "available": False,
                "configured": True,
                "connected": False,
                "provider": "ollama",
                "model": self.model_name,
                "error": str(exc),
            }

    async def generate_response(
        self,
        messages: List[Dict[str, str]],
        system_instruction: Optional[str] = None,
        temperature: Optional[float] = None,
    ) -> str:
        """
        Generate non-streaming text response from Qwen3 4B via Ollama /api/chat.
        """
        if not self.is_configured():
            raise OllamaClientException("Ollama provider is disabled or unconfigured.")

        endpoint = f"{self.base_url}/api/chat"
        temp = temperature if temperature is not None else self.temperature

        formatted_messages = []
        if system_instruction:
            formatted_messages.append({"role": "system", "content": system_instruction})

        for msg in messages:
            formatted_messages.append({
                "role": msg.get("role", "user"),
                "content": msg.get("content", ""),
            })

        payload = {
            "model": self.model_name,
            "messages": formatted_messages,
            "stream": False,
            "think": False,  # Top-level Ollama flag to disable Qwen3 thinking trace for low latency
            "options": {
                "temperature": temp,
            },
        }

        client_timeout = httpx.Timeout(self.timeout, connect=2.0)
        try:
            async with httpx.AsyncClient(timeout=client_timeout) as client:
                res = await client.post(endpoint, json=payload)

                if res.status_code == 404:
                    raise OllamaModelNotFoundError(
                        f"Model '{self.model_name}' not found in Ollama. Pull it with: ollama run {self.model_name}"
                    )
                elif res.status_code >= 500:
                    raise OllamaServerError(f"Ollama server error (HTTP {res.status_code}): {res.text}")
                elif res.status_code != 200:
                    raise OllamaClientException(
                        f"Ollama returned HTTP {res.status_code}: {res.text}",
                        status_code=res.status_code,
                    )

                data = res.json()
                return data.get("message", {}).get("content", "").strip()

        except httpx.ConnectError as exc:
            raise OllamaConnectionError(
                f"Failed to connect to Ollama at {self.base_url}. Is Ollama running? Error: {exc}"
            )
        except httpx.TimeoutException:
            raise OllamaTimeoutError(f"Ollama request timed out after {self.timeout}s.")
        except OllamaClientException:
            raise
        except Exception as exc:
            raise OllamaClientException(f"Unexpected error communicating with Ollama: {exc}")

    async def stream_response(
        self,
        messages: List[Dict[str, str]],
        system_instruction: Optional[str] = None,
        temperature: Optional[float] = None,
    ) -> AsyncGenerator[str, None]:
        """
        Generate streaming text response from Qwen3 4B parsing Ollama's NDJSON output stream.
        """
        if not self.is_configured():
            raise OllamaClientException("Ollama provider is disabled or unconfigured.")

        endpoint = f"{self.base_url}/api/chat"
        temp = temperature if temperature is not None else self.temperature

        formatted_messages = []
        if system_instruction:
            formatted_messages.append({"role": "system", "content": system_instruction})

        for msg in messages:
            formatted_messages.append({
                "role": msg.get("role", "user"),
                "content": msg.get("content", ""),
            })

        payload = {
            "model": self.model_name,
            "messages": formatted_messages,
            "stream": True,
            "think": False,
            "options": {
                "temperature": temp,
            },
        }

        client_timeout = httpx.Timeout(self.timeout, connect=2.0)
        try:
            async with httpx.AsyncClient(timeout=client_timeout) as client:
                async with client.stream("POST", endpoint, json=payload) as response:
                    if response.status_code != 200:
                        body = await response.aread()
                        raise OllamaClientException(
                            f"Ollama stream failed with HTTP {response.status_code}: {body.decode('utf-8', errors='ignore')}"
                        )

                    async for line in response.aiter_lines():
                        line_clean = line.strip()
                        if not line_clean:
                            continue
                        try:
                            chunk = json.loads(line_clean)
                            content = chunk.get("message", {}).get("content", "")
                            if content:
                                yield content
                            if chunk.get("done", False):
                                break
                        except json.JSONDecodeError:
                            continue
        except httpx.ConnectError as exc:
            raise OllamaConnectionError(f"Ollama stream connection error: {exc}")
        except httpx.TimeoutException:
            raise OllamaTimeoutError(f"Ollama stream timed out after {self.timeout}s.")

    async def generate_intent(
        self,
        transcript: str,
        language: str = "en-IN",
        context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Extract structured e-commerce shopping intent using Qwen3 4B.
        Instructs the model to output strict JSON adhering to AssistantStructuredIntent schema.
        """
        ctx = context or {}
        user_prompt = (
            f"Customer Transcript: {transcript}\n"
            f"Detected Language: {language}\n"
            f"Current Page: {ctx.get('current_page', 'home')}\n"
            f"Active Product ID: {ctx.get('product_id', 'None')}\n"
            f"Active Order ID: {ctx.get('order_id', 'None')}\n"
            f"Recent Conversation History: {ctx.get('recent_history', 'None')}\n"
            "\n"
            "Respond ONLY with a valid JSON object matching this schema:\n"
            "{\n"
            '  "intent": "product_search" | "product_details" | "compare_products" | "add_to_cart" | "cart_summary" | "checkout" | "track_order" | "cancel_order" | "return_order" | "greeting" | "help",\n'
            '  "parameters": {\n'
            '    "query": string | null,\n'
            '    "category": string | null,\n'
            '    "brand": string | null,\n'
            '    "product_id": string | null,\n'
            '    "product_name": string | null,\n'
            '    "min_price": number | null,\n'
            '    "max_price": number | null,\n'
            '    "quantity": integer,\n'
            '    "order_id": string | null,\n'
            '    "reason": string | null\n'
            '  },\n'
            '  "language": string,\n'
            '  "response_message": string,\n'
            '  "requires_confirmation": boolean\n'
            "}"
        )

        raw_output = await self.generate_response(
            messages=[{"role": "user", "content": user_prompt}],
            system_instruction=EVON_INTENT_SYSTEM_PROMPT,
            temperature=0.1,  # Lower temperature for deterministic schema adherence
        )

        # Parse JSON from model output (handling optional markdown code blocks)
        cleaned = raw_output.strip()
        if "```json" in cleaned:
            cleaned = cleaned.split("```json", 1)[1].split("```", 1)[0].strip()
        elif "```" in cleaned:
            cleaned = cleaned.split("```", 1)[1].split("```", 1)[0].strip()

        try:
            parsed = json.loads(cleaned)
            return parsed
        except json.JSONDecodeError as json_err:
            logger.warning(f"Failed to parse Qwen JSON output: {json_err}. Output was: {raw_output[:120]}")
            # Try to find { ... } within output
            start = raw_output.find("{")
            end = raw_output.rfind("}")
            if start != -1 and end != -1 and end > start:
                try:
                    return json.loads(raw_output[start:end+1])
                except Exception:
                    pass
            raise OllamaClientException(f"Qwen did not return valid JSON schema: {json_err}")
