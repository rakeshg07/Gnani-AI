"""Official Gnani Evon v3.3 Open-Weight LLM Provider.

Re-exports core services from app.services.evon_client and app.services.evon_intent
maintaining full backward compatibility for existing imports across VoiceIQ India.
"""
from typing import Optional, Dict, Any, List
from app.services.evon_client import (
    EvonClient,
    EvonClientException,
    EvonConfigurationError,
    EvonConnectionError,
    EvonAuthError,
    EvonTimeoutError,
    EvonRateLimitError,
    EvonServerError,
    EvonValidationError,
)
from app.services.evon_intent import (
    EvonSupportedIntent,
    EvonStructuredIntent,
    validate_evon_intent,
    IntentParameters,
    EVON_INTENT_SYSTEM_PROMPT,
    parse_evon_json_output,
)


# Legacy alias for EvonStructuredIntent
EvonIntentPayload = EvonStructuredIntent


class EvonInferenceClient(EvonClient):
    """
    Subclass of EvonClient providing backward compatibility for existing references.
    """
    def __init__(
        self,
        api_base: Optional[str] = None,
        model_id: Optional[str] = None,
        api_key: Optional[str] = None,
        timeout: Optional[float] = None,
        temperature: Optional[float] = None,
        top_p: Optional[float] = None,
        max_tokens: Optional[int] = None,
        enable_thinking: Optional[bool] = None,
    ):
        super().__init__(
            base_url=api_base,
            model_name=model_id,
            api_key=api_key,
            timeout=timeout,
            temperature=temperature,
            top_p=top_p,
            max_tokens=max_tokens,
            enable_thinking=enable_thinking,
        )

    @property
    def api_base(self) -> str:
        return self.base_url

    @property
    def model_id(self) -> str:
        return self.model_name

    async def check_health(self) -> Dict[str, Any]:
        return await self.health_check()

    async def generate_chat_completion(
        self,
        messages: List[Dict[str, str]],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        enable_thinking: Optional[bool] = None,
    ) -> str:
        return await self.generate_response(
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            enable_thinking=enable_thinking,
        )

    async def extract_intent(
        self,
        transcript: str,
        current_page: str = "home",
        context: Optional[Dict[str, Any]] = None,
    ) -> EvonStructuredIntent:
        ctx = dict(context or {})
        ctx["current_page"] = current_page
        raw_dict = await self.generate_intent(transcript, context=ctx)
        return validate_evon_intent(raw_dict)
