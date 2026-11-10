"""Voice Assistant Dialogue and E-Commerce Intent Orchestration Engine.
Powered by Gnani Prisma STT, Evon v3.3 (Open-Weight 30B MoE LLM), and Timbre TTS.
"""
import re
import base64
import uuid
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Optional, List, Tuple, Union

def generate_uuid() -> str:
    return str(uuid.uuid4())
from app.schemas.ecommerce import (
    AssistantMessageIn,
    AssistantMessageOut,
    AssistantActionProposal,
    ProductOut,
    OrderOut,
    CartOut,
)
from app.services.ecommerce_service import ECommerceService, ECommerceException, get_utc_now
from app.core.config import settings
from app.providers.gnani import GnaniSpeechClient, GnaniClientException
from app.providers.gemini import (
    GeminiClient,
    GeminiClientException,
    GeminiConfigurationError,
    GeminiAuthError,
    GeminiRateLimitError,
    GeminiTimeoutError,
    GeminiServerError,
    GeminiValidationError,
)
from app.providers.ollama import (
    OllamaClient,
    OllamaClientException,
    OllamaConnectionError,
    OllamaTimeoutError,
    OllamaModelNotFoundError,
    OllamaServerError,
)
from app.providers.huggingface import (
    HuggingFaceClient,
    HuggingFaceClientException,
    HuggingFaceConfigurationError,
    HuggingFaceAuthError,
    HuggingFaceRateLimitError,
    HuggingFaceTimeoutError,
    HuggingFaceServerError,
    HuggingFaceValidationError,
)
from app.services.query_scope import (
    classify_query_scope,
    QueryScopeGuard,
    QueryScopeResult,
    ScopeClassification,
)
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
    AssistantStructuredIntent,
    validate_evon_intent,
    validate_assistant_intent,
    IntentParameters,
    CONSEQUENTIAL_INTENTS,
)
from app.providers.evon import EvonInferenceClient
from app.services.assistant_locales import format_msg, get_locale
from app.core.logging import logger


class VoiceAssistantOrchestrator:
    """
    Connects multilingual customer speech or text queries directly to backend
    e-commerce database logic using Gnani Evon v3.3 structured reasoning
    with consequential action safety guards and automatic fallback.
    """

    @staticmethod
    def resolve_language(payload: AssistantMessageIn) -> str:
        """
        Determine target language code.
        Prioritizes selected language in widget or detected Indic Unicode scripts.
        Supports 11 languages: en, hi, ta, te, kn, ml, mr, bn, gu, pa, or.
        """
        msg = payload.message or ""
        # Check for Odia Unicode script (0x0B00 to 0x0B7F)
        if any("\u0B00" <= c <= "\u0B7F" for c in msg):
            return "or-IN"
        # Check for Kannada Unicode script (0x0C80 to 0x0CFF)
        if any("\u0C80" <= c <= "\u0CFF" for c in msg):
            return "kn-IN"
        # Check for Tamil Unicode script (0x0B80 to 0x0BFF)
        if any("\u0B80" <= c <= "\u0BFF" for c in msg):
            return "ta-IN"
        # Check for Telugu Unicode script (0x0C00 to 0x0C7F)
        if any("\u0C00" <= c <= "\u0C7F" for c in msg):
            return "te-IN"
        # Check for Malayalam Unicode script (0x0D00 to 0x0D7F)
        if any("\u0D00" <= c <= "\u0D7F" for c in msg):
            return "ml-IN"
        # Check for Bengali Unicode script (0x0980 to 0x09FF)
        if any("\u0980" <= c <= "\u09FF" for c in msg):
            return "bn-IN"
        # Check for Gujarati Unicode script (0x0A80 to 0x0AFF)
        if any("\u0A80" <= c <= "\u0AFF" for c in msg):
            return "gu-IN"
        # Check for Gurmukhi / Punjabi Unicode script (0x0A00 to 0x0A7F)
        if any("\u0A00" <= c <= "\u0A7F" for c in msg):
            return "pa-IN"
        # Check for Devanagari Unicode script (0x0900 to 0x097F) - Hindi / Marathi
        if any("\u0900" <= c <= "\u097F" for c in msg):
            if (payload.language_code or "").startswith("mr") or any(
                w in msg for w in ["माझी", "दाखवा", "पाहिजे", "आहे", "करा", "कुठे", "रद्द करा", "माझा"]
            ):
                return "mr-IN"
            return "hi-IN"

        code = (payload.language_code or "").strip().lower()
        lang_prefixes = [
            ("kn", "kn-IN"),
            ("hi", "hi-IN"),
            ("ta", "ta-IN"),
            ("te", "te-IN"),
            ("ml", "ml-IN"),
            ("mr", "mr-IN"),
            ("bn", "bn-IN"),
            ("gu", "gu-IN"),
            ("pa", "pa-IN"),
            ("or", "or-IN"),
            ("en", "en-IN"),
        ]
        for prefix, lang in lang_prefixes:
            if code.startswith(prefix):
                return lang

        return payload.language_code or "en-IN"

    @staticmethod
    def detect_intent(
        message: str, current_page: str = "home", has_product_context: bool = False
    ) -> Tuple[str, Dict[str, Any]]:
        """
        Deterministic semantic fallback intent parser supporting Indian languages.
        Used when remote LLMs are unconfigured or temporarily unreachable.
        """
        text = message.lower().strip()
        entities: Dict[str, Any] = {}

        # 0. Centralized Domain Scope check: reject non-store questions immediately
        scope_det = QueryScopeGuard.evaluate_deterministic(
            message, current_page=current_page, has_product_context=has_product_context
        )
        if scope_det.is_out_of_scope and scope_det.detector in ("prompt_shield", "deterministic_rules"):
            return "out_of_scope", entities

        # Pre-extract common entities (price, order_id, top-level category, query)
        price_match = re.search(
            r"(?:under|below|less than|within|upto|kam|kamti|ಒಳಗೆ|ಕೆಳಗೆ|లోపు|உள்)\s*(?:rs\.?|inr|₹)?\s*([0-9,]+)",
            text,
            re.IGNORECASE,
        )
        if not price_match:
            price_match = re.search(r"(?:rs\.?|inr|₹)\s*([0-9,]+)", text, re.IGNORECASE)
        if price_match:
            try:
                entities["max_price"] = float(price_match.group(1).replace(",", ""))
            except ValueError:
                pass

        order_match = re.search(r"\b(?:viq-?)?(\d{5})\b", text, re.IGNORECASE)
        if order_match:
            entities["order_id"] = f"VIQ-{order_match.group(1)}"

        top_categories_map = {
            "electronics": ["electronics", "electronic", "gadget", "gadgets"],
            "appliances": ["appliances", "appliance", "kitchen", "home & kitchen"],
            "fashion": ["fashion", "apparel", "clothes", "clothing"],
            "accessories": ["accessories", "accessory", "bags & watches"],
        }
        for cat, kw_list in top_categories_map.items():
            if any(re.search(rf"\b{re.escape(k)}\b", text) for k in kw_list):
                entities["category"] = cat
                break

        entities["query"] = message.strip()

        # 1. Product comparison
        if any(w in text for w in ["compare", "vs", "versus", "ತುಲನೆ", "तुलना", "ஒப்பிடு", "పోల్చండి"]):
            return "compare_products", entities

        # 2. Order Tracking

        tracking_keywords = [
            "track", "tracking", "status", "where is", "delivery", "delivered",
            "kahan hai", "kab aayega", "order status", "kahaan hai",
            "எங்கே", "ఎక్కడ", "ಎಲ್ಲಿದೆ", "എവിടെ", "कुठे आहे", "কোথায়", "ક્યાં છે", "ਕਿੱਥੇ ਹੈ",
        ]
        if any(k in text for k in tracking_keywords) and not any(k in text for k in ["cancel", "radd", "band", "return", "refund", "vapas"]):
            return "track_order", entities

        # 4. Cancellation (Consequential Action)
        non_prod_text = re.sub(r"noise[- ]cancell?(?:ing|ation)?", "", text)
        cancel_keywords = [
            "cancel my order", "cancel order", "cancel the order", "radd karo", "band karo",
            "cancellation",
            "cancel" if "to cart" not in text and "add" not in text else "cancel order",
            "ರದ್ದು", "ரத்து", "రద్దు", "റദ്ദാക്കുക", "रद्द करा", "বাতিল", "રદ કરો", "ਰੱਦ ਕਰੋ", "ବାତିଲ",
        ]
        if any(k in text for k in cancel_keywords):
            return "request_cancellation", entities

        # 5. Return / Refund (Consequential Action)
        return_keywords = [
            "return", "refund", "exchange", "vapas", "wapas", "replacement",
            "ಹಿಂತಿರುಗಿಸು", "திருப்பி", "తిరిగి", "തിരികെ", "परत", "ফেরত", "પાછા", "ਵਾਪਸ", "ଫେରସ୍ତ",
        ]
        if any(k in text for k in return_keywords):
            return "request_return", entities

        # 6. Cart Management
        remove_keywords = ["remove from cart", "delete from cart", "remove item", "ಕಾರ್ಟ್‌ನಿಂದ ತೆಗೆ", "कार्ट से हटाएं"]
        if any(k in text for k in remove_keywords):
            return "remove_from_cart", entities

        add_cart_keywords = [
            "add to cart", "buy this", "purchase", "add this", "khareedna",
            "ಕಾರ್ಟ್‌ಗೆ ಸೇರಿಸು", "ಕಾರ್ಟ್ ಗೆ ಹಾಕು", "கார்ட்டில் சேர்", "కార్ట్‌కి జోడించు",
            "കാർട്ടിലേക്ക് ചേർക്കുക", "कार्टमध्ये जोडा", "কার্টে যোগ করুন", "કાર્ટમાં ઉમેરો", "ਕਾਰਟ ਵਿੱਚ ਸ਼ਾਮਲ ਕਰੋ",
        ]
        if (
            any(k in text for k in add_cart_keywords)
            or re.search(r"\badd\b.+\bto\s+cart\b", text)
            or (current_page == "product_detail" and any(k in text for k in ["add", "buy", "cart"]))
        ):
            qty_match = re.search(r"\b(\d+)\s*(?:quantity|pieces|items|units)?\b", text)
            entities["quantity"] = int(qty_match.group(1)) if qty_match and int(qty_match.group(1)) <= 10 else 1
            return "add_to_cart", entities

        view_cart_keywords = [
            "view cart", "show cart", "my cart", "open cart", "cart total",
            "ನನ್ನ ಕಾರ್ಟ್", "என் கார்ட்", "నా కార్ట్", "എന്റെ കാർട്ട്", "माझी कार्ट", "আমার কার্ট", "મારું કાર્ટ", "ਮੇਰਾ ਕਾਰਟ",
        ]
        if any(k in text for k in view_cart_keywords) or text in ["cart", "tokri", "jhola", "bag"]:
            return "get_cart", entities

        # 7. Support & FAQs
        if any(w in text for w in ["delivery partner", "shipping time", "how long delivery", "courier", "delhivery"]):
            return "delivery_question", entities
        if any(w in text for w in ["payment", "upi", "credit card", "cod", "cash on delivery", "refund time"]):
            return "payment_question", entities

        # 8. Catalog Search vs Single-Product Availability vs Details
        search_triggers = [
            "show", "find", "search", "list", "browse", "looking for", "want", "need",
            "recommend", "suggest", "all", "brand", "brands", "dikhao", "dhoondo",
            "ತೋರಿಸಿ", "ತೋರಿಸು", "ಹುಡುಕು", "காட்டு", "చూపించు", "കാണിക്കുക", "दाखवा", "দেখান", "બતાવો", "ਦਿਖਾਓ", "ଦେଖାନ୍ତୁ",
        ]
        product_item_keywords = [
            "mobile", "mobiles", "smartphone", "smartphones", "phone", "phones",
            "earbud", "earbuds", "earphone", "earphones", "headphone", "headphones", "headset",
            "watch", "watches", "smartwatch", "smartwatches", "bag", "bags", "backpack",
            "shirt", "shirts", "kurti", "kurtis", "kurta", "mixer", "grinder", "fryer", "fan",
            "oneplus", "boat", "sony", "noise", "preethi", "philips", "havells", "titan", "tourister", "louis philippe",
            "ಫೋನ್", "ಮೊಬೈಲ್", "फोन", "मोबाईल", "इयरबड्स",
        ]
        has_search_trigger = any(re.search(rf"\b{re.escape(t)}\b", text) if t.isascii() else t in text for t in search_triggers)
        has_product_kw = any(k in text for k in product_item_keywords)
        has_avail_kw = any(w in text for w in ["available", "in stock", "stock", "ಲಭ್ಯವಿದೆಯೇ", "स्टॉक में है", "இருக்கிறதா", "ఉందా"])

        if has_search_trigger or entities.get("category") or entities.get("max_price"):
            return "search_products", entities

        if has_avail_kw:
            if has_product_context or has_product_kw:
                return "check_product_availability", entities
            return "search_products", entities

        if has_product_context or any(k in text for k in ["spec", "battery", "price of this", "warranty", "details of this"]):
            return "get_product_details", entities

        if has_product_kw:
            return "search_products", entities

        # If clearly out of scope, do not guess general support
        if scope_det.is_out_of_scope:
            return "out_of_scope", entities

        return "general_support", entities

    @classmethod
    async def process_message(
        cls,
        db: Any,
        payload: AssistantMessageIn,
        customer_id: str = "cust_demo_001",
        gnani_client: Optional[GnaniSpeechClient] = None,
        evon_client: Optional[Union[EvonClient, EvonInferenceClient]] = None,
        gemini_client: Optional[GeminiClient] = None,
        huggingface_client: Optional[HuggingFaceClient] = None,
        ollama_client: Optional[OllamaClient] = None,
        active_provider: Optional[str] = None,
    ) -> AssistantMessageOut:
        """
        Orchestrates VoiceIQ customer query through:
        1. Multi-turn dialogue context ingestion.
        2. Domain scope evaluation (only store queries allowed).
        3. Qwen (Route 1 Text) or Gemini (Route 2 Voice) / deterministic fallback reasoning.
        4. Strict Pydantic intent & safety validation.
        5. Real MongoDB database operations (catalog, cart, orders).
        6. Consequential action proposals for cancellations & returns.
        7. Optional Gnani Timbre TTS speech synthesis.
        """
        target_lang = cls.resolve_language(payload)
        if active_provider is None:
            if gemini_client is not None:
                active_provider = "gemini"
            elif ollama_client is not None:
                active_provider = "ollama"
            elif evon_client is not None:
                active_provider = "evon"
            elif huggingface_client is not None and getattr(settings, "HUGGINGFACE_ENABLED", False):
                active_provider = "huggingface"
            else:
                active_provider = (settings.TEXT_CHAT_PROVIDER or settings.AI_PROVIDER or "ollama").strip().lower()
        active_provider = active_provider.strip().lower()

        llm_provider = "local-rule-engine"
        intent_confidence = 0.90
        reasoning: Optional[str] = None
        consequential_action_required = False

        intent = "general_support"
        entities: Dict[str, Any] = {}

        # -----------------------------------------------------------------
        # STEP 1: Multi-Turn Conversation Context Resolution
        # -----------------------------------------------------------------
        recent_history = ""
        last_product_id = payload.product_id
        last_order_id = payload.order_id
        inherited_category = None
        inherited_brand = None

        try:
            prev_convs = list(
                db.conversations.find({"customer_id": customer_id})
                .sort("created_at", -1)
                .limit(3)
            )
            if prev_convs:
                recent_history = " | ".join(
                    f"Customer: {c.get('transcript')} -> Assistant: {c.get('detected_intent')}"
                    for c in reversed(prev_convs)
                    if c.get("transcript")
                )
                for c in prev_convs:
                    if not last_product_id and c.get("product_id"):
                        last_product_id = c.get("product_id")
                    if not last_order_id and c.get("order_id"):
                        last_order_id = c.get("order_id")
                        last_order_id = c.order_id
        except Exception as ctx_err:
            logger.debug(f"Multi-turn context lookup skipped: {ctx_err}")

        # -----------------------------------------------------------------
        # STEP 1.5: Centralized Domain Scope Guard
        # -----------------------------------------------------------------
        scope_res = await classify_query_scope(
            message=payload.message,
            current_page=payload.current_page,
            language_code=target_lang,
            has_product_context=bool(last_product_id),
            has_order_context=bool(last_order_id),
            gemini_client=gemini_client or (GeminiClient() if active_provider == "gemini" else None),
            huggingface_client=huggingface_client or (HuggingFaceClient() if active_provider in ("huggingface", "hf") else None),
        )

        if scope_res.is_out_of_scope or scope_res.needs_clarification:
            guard_intent = "out_of_scope" if scope_res.is_out_of_scope else "needs_clarification"
            reply_text = format_msg(target_lang, guard_intent)
            audio_b64: Optional[str] = None
            if payload.synthesize_audio and gnani_client:
                try:
                    audio_bytes = await gnani_client.synthesize_speech(
                        text=reply_text,
                        language=target_lang,
                        voice="Nalini" if "hi" in target_lang else "Shivani",
                    )
                    if audio_bytes:
                        audio_b64 = base64.b64encode(audio_bytes).decode("ascii")
                except Exception as tts_err:
                    logger.debug(f"TTS skipped for {guard_intent} response: {tts_err}")

            conv_id = payload.conversation_id or generate_uuid()
            return AssistantMessageOut(
                success=True,
                reply_text=reply_text,
                intent=guard_intent,
                detected_language=target_lang,
                audio_base64=audio_b64,
                conversation_id=conv_id,
                llm_provider=f"domain-scope-guard ({scope_res.detector})",
                intent_confidence=scope_res.confidence,
                reasoning=scope_res.reason,
                consequential_action_required=False,
                transcript=payload.message,
                language=target_lang,
                message=reply_text,
                data={"products": [], "order": None, "cart": None, "action_proposal": None},
                requires_confirmation=False,
            )

        # -----------------------------------------------------------------
        # STEP 2: Intent Extraction via Primary AI Provider (Hugging Face / Gemini / Evon / fallback)
        # -----------------------------------------------------------------
        context_payload = {
            "current_page": payload.current_page,
            "product_id": last_product_id,
            "order_id": last_order_id,
            "recent_history": recent_history,
        }

        if active_provider in ("ollama", "qwen"):
            ollama = ollama_client or OllamaClient()
            if ollama.is_configured():
                try:
                    raw_intent_dict = await ollama.generate_intent(
                        transcript=payload.message,
                        language=target_lang,
                        context=context_payload,
                    )
                    ollama_structured = validate_assistant_intent(
                        raw_intent_dict, fallback_language=target_lang
                    )
                    intent = ollama_structured.intent.value
                    entities = ollama_structured.parameters.model_dump()
                    entities["direct_response"] = ollama_structured.response_message
                    consequential_action_required = ollama_structured.requires_confirmation
                    llm_provider = f"qwen-ollama ({ollama.model_name})"
                    intent_confidence = 0.95
                    reasoning = f"Qwen3 4B structured reasoning: intent='{intent}', params={entities}"
                    logger.info(f"Qwen3 4B successfully classified intent: {intent}")
                except OllamaClientException as exc:
                    logger.warning(
                        f"Ollama Qwen inference warning ({exc.error_code}): {exc.message}. "
                        "Gracefully recovering with deterministic semantic orchestrator."
                    )
                    intent, entities = cls.detect_intent(
                        payload.message,
                        payload.current_page,
                        has_product_context=bool(payload.product_id),
                    )
                    llm_provider = f"fallback-semantic-engine ({exc.error_code})"
                    reasoning = f"Ollama Qwen unavailable: {exc.message}. Gracefully recovered."
            else:
                intent, entities = cls.detect_intent(
                    payload.message,
                    payload.current_page,
                    has_product_context=bool(payload.product_id),
                )
                llm_provider = "local-semantic-engine (Ollama unconfigured)"
                reasoning = "Local semantic engine. Set OLLAMA_ENABLED=true to connect local Ollama runtime."

        elif active_provider in ("huggingface", "hf"):
            hf = huggingface_client or HuggingFaceClient()
            if hf.is_configured():
                try:
                    raw_intent_dict = await hf.generate_intent(
                        transcript=payload.message,
                        language=target_lang,
                        context=context_payload,
                    )
                    hf_structured = validate_assistant_intent(
                        raw_intent_dict, fallback_language=target_lang
                    )
                    intent = hf_structured.intent.value
                    entities = hf_structured.parameters.model_dump()
                    entities["direct_response"] = hf_structured.response_message
                    consequential_action_required = hf_structured.requires_confirmation
                    llm_provider = f"huggingface ({hf.model_name})"
                    intent_confidence = 0.96
                    reasoning = f"Hugging Face structured reasoning: intent='{intent}', params={entities}"
                    logger.info(f"Hugging Face successfully classified intent: {intent}")
                except HuggingFaceClientException as exc:
                    logger.warning(
                        f"Hugging Face inference warning ({exc.error_code}): {exc.message}. "
                        "Gracefully recovering with deterministic semantic orchestrator."
                    )
                    intent, entities = cls.detect_intent(
                        payload.message,
                        payload.current_page,
                        has_product_context=bool(payload.product_id),
                    )
                    llm_provider = f"fallback-semantic-engine ({exc.error_code})"
                    reasoning = f"Hugging Face unavailable: {exc.message}. Gracefully recovered."
            else:
                intent, entities = cls.detect_intent(
                    payload.message,
                    payload.current_page,
                    has_product_context=bool(payload.product_id),
                )
                llm_provider = "local-semantic-engine (Hugging Face unconfigured)"
                reasoning = "Local semantic engine. Set HUGGINGFACE_API_KEY to connect Hugging Face Inference."

        elif active_provider == "gemini":
            gemini = gemini_client or GeminiClient()
            if gemini.is_configured():
                try:
                    raw_intent_dict = await gemini.generate_intent(
                        transcript=payload.message,
                        language=target_lang,
                        context=context_payload,
                    )
                    gemini_structured = validate_assistant_intent(
                        raw_intent_dict, fallback_language=target_lang
                    )
                    intent = gemini_structured.intent.value
                    entities = gemini_structured.parameters.model_dump()
                    entities["direct_response"] = gemini_structured.response_message
                    consequential_action_required = gemini_structured.requires_confirmation
                    llm_provider = f"google-gemini ({gemini.model_name})"
                    intent_confidence = 0.96
                    reasoning = f"Google Gemini 3.8 Flash structured reasoning: intent='{intent}', params={entities}"
                    logger.info(f"Gemini 3.8 Flash successfully classified intent: {intent}")
                except GeminiClientException as exc:
                    logger.warning(
                        f"Gemini 3.8 Flash inference warning ({exc.error_code}): {exc.message}. "
                        "Gracefully recovering with deterministic semantic orchestrator."
                    )
                    intent, entities = cls.detect_intent(
                        payload.message,
                        payload.current_page,
                        has_product_context=bool(payload.product_id),
                    )
                    llm_provider = f"fallback-semantic-engine ({exc.error_code})"
                    reasoning = f"Gemini 3.8 Flash unavailable: {exc.message}. Gracefully recovered."
            else:
                intent, entities = cls.detect_intent(
                    payload.message,
                    payload.current_page,
                    has_product_context=bool(payload.product_id),
                )
                llm_provider = "local-semantic-engine (Gemini unconfigured)"
                reasoning = "Local semantic engine. Set GEMINI_API_KEY to connect Google Gemini 3.8 Flash."

        elif active_provider == "evon":
            evon = evon_client or EvonClient()
            if evon.is_configured():
                try:
                    raw_intent_dict = await evon.generate_intent(
                        transcript=payload.message,
                        language=target_lang,
                        context=context_payload,
                    )
                    evon_structured: EvonStructuredIntent = validate_evon_intent(
                        raw_intent_dict, fallback_language=target_lang
                    )
                    intent = evon_structured.intent.value
                    entities = evon_structured.parameters.model_dump()
                    entities["direct_response"] = evon_structured.response_message
                    consequential_action_required = evon_structured.requires_confirmation
                    model_name = getattr(evon, "model_name", getattr(evon, "model_id", "evon"))
                    llm_provider = f"gnani-evon-v3.3 ({model_name})"
                    intent_confidence = 0.95
                    reasoning = f"Evon v3.3 Indic classification: intent='{intent}', params={entities}"
                    logger.info(f"Evon v3.3 successfully classified intent: {intent}")
                except EvonClientException as exc:
                    logger.warning(
                        f"Evon v3.3 remote inference warning ({exc.error_code}): {exc.message}. "
                        "Gracefully recovering with deterministic semantic orchestrator."
                    )
                    intent, entities = cls.detect_intent(
                        payload.message,
                        payload.current_page,
                        has_product_context=bool(payload.product_id),
                    )
                    llm_provider = f"fallback-semantic-engine ({exc.error_code})"
                    reasoning = f"Evon v3.3 unavailable: {exc.message}. Gracefully recovered."
            else:
                intent, entities = cls.detect_intent(
                    payload.message,
                    payload.current_page,
                    has_product_context=bool(payload.product_id),
                )
                llm_provider = "local-semantic-engine (Evon remote unconfigured)"
                reasoning = "Local semantic engine. Set EVON_ENABLED=true and EVON_BASE_URL to connect remote GPU server."
        else:
            intent, entities = cls.detect_intent(
                payload.message,
                payload.current_page,
                has_product_context=bool(payload.product_id),
            )
            llm_provider = "local-semantic-engine"
            reasoning = "Local deterministic semantic engine."

        # Normalize intent aliases
        if intent in ("product_search", "find_products"):
            intent = "search_products"
        elif intent in ("product_details", "price_query"):
            intent = "get_product_details"
        elif intent in ("cart_add", "add"):
            intent = "add_to_cart"
        elif intent in ("cart_view", "view_cart"):
            intent = "get_cart"
        elif intent in ("order_status", "tracking"):
            intent = "track_order"
        elif intent in ("cancel_order", "cancel"):
            intent = "request_cancellation"
        elif intent in ("return_request", "return", "refund"):
            intent = "request_return"
        elif intent == "unknown":
            intent = "unknown_intent"

        # Consequential safety guard enforcement
        if intent in ("request_cancellation", "request_return", "cancel_order", "return_request"):
            consequential_action_required = True

        reply_text = ""
        action_pending: Optional[AssistantActionProposal] = None
        products_out: Optional[List[ProductOut]] = None
        order_out: Optional[OrderOut] = None
        cart_out: Optional[CartOut] = None
        target_order_id = entities.get("order_id") or payload.order_id or last_order_id

        # -----------------------------------------------------------------
        # STEP 3: Execute Validated Action Handler against Real Database
        # -----------------------------------------------------------------

        # 1. SEARCH PRODUCTS
        if intent == "search_products":
            search_query = entities.get("query") or entities.get("product_name") or payload.message
            for filler in [
                "show me", "find", "search for", "looking for", "i want", "dikhao", "please",
                "list out all", "list out", "list all", "can you search", "can you",
                "ತೋರಿಸಿ", "ತೋರಿಸು", "ಹುಡುಕು", "ದರ್ಶಿಸು", "ಬೇಕು", "चाहिए", "दीजिए",
            ]:
                search_query = re.sub(rf"\b{re.escape(filler)}\b", " ", search_query, flags=re.IGNORECASE)

            max_p = entities.get("max_price")
            min_p = entities.get("min_price")
            category_filter = entities.get("category")
            brand_filter = entities.get("brand")

            # Combine brand filter if query doesn't already contain it
            if brand_filter and brand_filter.lower() not in search_query.lower():
                search_query = f"{brand_filter} {search_query}".strip()

            items, total = ECommerceService.get_products(
                db,
                search=search_query.strip(),
                category_id=category_filter,
                min_price=min_p,
                max_price=max_p,
                page_size=4,
            )

            # Retry across all categories if category_filter narrowed out a valid product search
            if not items and category_filter and search_query.strip():
                items, total = ECommerceService.get_products(
                    db,
                    search=search_query.strip(),
                    min_price=min_p,
                    max_price=max_p,
                    page_size=4,
                )

            if not items and max_p:
                items, total = ECommerceService.get_products(db, max_price=max_p, page_size=4)

            if items:
                products_out = [ProductOut.model_validate(p) for p in items]
                price_suffix = f" under ₹{int(max_p):,}" if max_p else ""
                if target_lang == "en-IN":
                    if len(products_out) == 1:
                        p0 = products_out[0]
                        stock_note = f"{p0.stock} units in stock" if p0.stock > 0 else "currently out of stock"
                        reply_text = (
                            f"I found 1 matching product{price_suffix}: {p0.title} — ₹{p0.price:,.0f} ({stock_note}). "
                            "You can check its specs below or ask me to add it to your cart."
                        )
                    else:
                        item_summaries = "; ".join(
                            f"{p.title} (₹{p.price:,.0f}, {p.stock} in stock)" for p in products_out
                        )
                        reply_text = f"I found {len(products_out)} matching products{price_suffix}: {item_summaries}."
                else:
                    price_clause = " " + format_msg(target_lang, "search_under", price=int(max_p)) if max_p else ""
                    base_msg = format_msg(target_lang, "search_found", count=len(products_out), price_clause=price_clause)
                    names_list = ", ".join(f"{p.title} (₹{p.price:,.0f})" for p in products_out[:3])
                    reply_text = f"{base_msg} {names_list}"
            else:
                if target_lang == "en-IN":
                    reply_text = (
                        f"I couldn't find any exact products matching '{payload.message.strip()}' in our store catalog. "
                        "Currently we carry OnePlus (smartphones), boAt & Sony (audio), Noise & Titan (watches), "
                        "Preethi, Philips & Havells (appliances), and W / Louis Philippe / American Tourister."
                    )
                else:
                    reply_text = format_msg(target_lang, "search_empty", query=payload.message.strip())

        # 2. GET PRODUCT DETAILS
        elif intent == "get_product_details":
            raw_product = None
            if payload.product_id:
                raw_product = ECommerceService.get_product_by_id(db, payload.product_id)
            if not raw_product:
                prod_term = entities.get("product_name") or entities.get("query") or payload.message
                items, _ = ECommerceService.get_products(db, search=prod_term, page_size=1)
                if items:
                    raw_product = items[0]

            if raw_product:
                product = ProductOut.model_validate(raw_product)
                products_out = [product]
                discount_pct = int(round((1 - product.price / product.original_price) * 100)) if product.original_price else 0
                specs_summary = ", ".join(f"{k}: {v}" for k, v in list((product.specifications or {}).items())[:3])
                stock_status = (
                    format_msg(target_lang, "prod_in_stock", count=product.stock)
                    if product.stock > 0
                    else format_msg(target_lang, "prod_out_of_stock")
                )
                reply_text = format_msg(
                    target_lang,
                    "prod_details",
                    title=product.title,
                    price=product.price,
                    discount=discount_pct,
                    original_price=product.original_price,
                    stock_status=stock_status,
                    specs=specs_summary,
                )
            else:
                reply_text = format_msg(target_lang, "prod_prompt")

        # 3. COMPARE PRODUCTS
        elif intent == "compare_products":
            prod_terms = entities.get("product_ids") or []
            raw_items: List[Dict[str, Any]] = []
            if not prod_terms:
                raw_q = entities.get("query") or entities.get("product_name") or payload.message
                clean_q = re.sub(r"(?i)\b(compare|vs|versus|and|between|with|the|to|two|products)\b", ",", raw_q)
                parts = [p.strip() for p in clean_q.split(",") if p.strip() and len(p.strip()) > 1]
                for part in parts:
                    sub_items, _ = ECommerceService.get_products(db, search=part, page_size=1)
                    if sub_items and sub_items[0]["id"] not in [it["id"] for it in raw_items]:
                        raw_items.append(sub_items[0])
                if len(raw_items) < 2:
                    sub_items, _ = ECommerceService.get_products(db, search=raw_q, page_size=2)
                    for sit in sub_items:
                        if sit["id"] not in [it["id"] for it in raw_items] and len(raw_items) < 2:
                            raw_items.append(sit)
                if len(raw_items) < 2:
                    all_items, _ = ECommerceService.get_products(db, page_size=2)
                    for ait in all_items:
                        if ait["id"] not in [it["id"] for it in raw_items] and len(raw_items) < 2:
                            raw_items.append(ait)
            else:
                for pid in prod_terms[:2]:
                    found_p = ECommerceService.get_product_by_id(db, pid)
                    if found_p:
                        raw_items.append(found_p)

            items_out = [ProductOut.model_validate(p) for p in raw_items]
            if len(items_out) >= 2:
                p1, p2 = items_out[0], items_out[1]
                products_out = [p1, p2]
                specs1 = list((p1.specifications or {}).items())
                diff_parts = []
                for k, v in specs1[:2]:
                    v2 = (p2.specifications or {}).get(k, "N/A")
                    diff_parts.append(f"{k}: {p1.title.split()[0]}={v} vs {p2.title.split()[0]}={v2}")
                diff_str = "; ".join(diff_parts) if diff_parts else f"Price diff: Rs. {abs(p1.price - p2.price):,.2f}"

                reply_text = format_msg(
                    target_lang,
                    "compare_summary",
                    title1=p1.title,
                    price1=p1.price,
                    rating1=p1.rating,
                    title2=p2.title,
                    price2=p2.price,
                    rating2=p2.rating,
                    diff=diff_str,
                )
            elif len(items_out) == 1:
                p0 = items_out[0]
                products_out = [p0]
                reply_text = format_msg(
                    target_lang,
                    "prod_details",
                    title=p0.title,
                    price=p0.price,
                    discount=10,
                    original_price=p0.original_price,
                    stock_status=f"{p0.stock} units in stock",
                    specs=str(p0.specifications),
                )
            else:
                reply_text = format_msg(target_lang, "compare_prompt")

        # 4. CHECK PRODUCT AVAILABILITY
        elif intent == "check_product_availability":
            raw_items: List[Dict[str, Any]] = []
            if payload.product_id:
                found_p = ECommerceService.get_product_by_id(db, payload.product_id)
                if found_p:
                    raw_items = [found_p]
            if not raw_items:
                p_name = entities.get("product_name") or entities.get("query") or payload.message
                raw_items, _ = ECommerceService.get_products(db, search=p_name, page_size=4)

            if raw_items:
                products_out = [ProductOut.model_validate(p) for p in raw_items]
                if len(products_out) == 1:
                    target_prod = products_out[0]
                    if target_prod.stock > 0:
                        del_date = (get_utc_now() + timedelta(days=2)).strftime("%d %B, %A")
                        reply_text = format_msg(
                            target_lang,
                            "avail_in_stock",
                            title=target_prod.title,
                            count=target_prod.stock,
                            price=target_prod.price,
                            date=del_date,
                        )
                    else:
                        reply_text = format_msg(target_lang, "avail_out_of_stock", title=target_prod.title)
                else:
                    in_stock_list = "; ".join(
                        f"{p.title} (₹{p.price:,.0f}, {p.stock} in stock)" for p in products_out
                    )
                    reply_text = f"Yes, here are the matching items currently available: {in_stock_list}."
            else:
                reply_text = format_msg(target_lang, "prod_prompt")

        # 5. ADD TO CART
        elif intent == "add_to_cart":
            target_prod_id = payload.product_id
            if not target_prod_id:
                prod_term = entities.get("product_name") or entities.get("query") or payload.message
                items, _ = ECommerceService.get_products(db, search=prod_term, page_size=1)
                if items:
                    target_prod_id = items[0]["id"]

            qty = int(entities.get("quantity", 1) or 1)
            if target_prod_id:
                try:
                    updated_cart = ECommerceService.add_to_cart(db, customer_id, target_prod_id, quantity=qty)
                    cart_out = CartOut.model_validate(updated_cart)
                    product = ECommerceService.get_product_by_id(db, target_prod_id)
                    prod_title = product["title"] if product else target_prod_id
                    reply_text = format_msg(
                        target_lang,
                        "cart_add_success",
                        title=prod_title,
                        qty=qty,
                        count=cart_out.item_count,
                        total=cart_out.total_amount,
                    )
                except ECommerceException as exc:
                    reply_text = format_msg(target_lang, "cart_add_error", error=exc.message)
            else:
                reply_text = format_msg(target_lang, "cart_add_prompt")

        # 6. REMOVE FROM CART
        elif intent == "remove_from_cart":
            cart_dict = ECommerceService.get_cart(db, customer_id)
            cart_items = cart_dict.get("items", [])
            target_item = None
            target_pid = entities.get("product_id") or payload.product_id
            p_name = (entities.get("product_name") or entities.get("query") or "").lower()

            for item in cart_items:
                if target_pid and item["product_id"] == target_pid:
                    target_item = item
                    break
                if p_name and p_name in item["product"]["title"].lower():
                    target_item = item
                    break

            if not target_item and cart_items:
                target_item = cart_items[-1]

            if target_item:
                item_title = target_item["product"]["title"]
                updated_cart = ECommerceService.remove_cart_item(db, customer_id, target_item["product_id"])
                cart_out = CartOut.model_validate(updated_cart)
                reply_text = format_msg(
                    target_lang,
                    "cart_remove_success",
                    title=item_title,
                    count=cart_out.item_count,
                    total=cart_out.total_amount,
                )
            else:
                reply_text = format_msg(target_lang, "cart_empty")

        # 7. UPDATE CART QUANTITY
        elif intent == "update_cart_quantity":
            cart_dict = ECommerceService.get_cart(db, customer_id)
            cart_items = cart_dict.get("items", [])
            target_item = None
            target_pid = entities.get("product_id") or payload.product_id
            p_name = (entities.get("product_name") or entities.get("query") or "").lower()
            new_qty = int(entities.get("quantity", 1) or 1)

            for item in cart_items:
                if target_pid and item["product_id"] == target_pid:
                    target_item = item
                    break
                if p_name and p_name in item["product"]["title"].lower():
                    target_item = item
                    break

            if not target_item and cart_items:
                target_item = cart_items[0]

            if target_item:
                try:
                    updated_cart = ECommerceService.update_cart_item(db, customer_id, target_item["product_id"], new_qty)
                    cart_out = CartOut.model_validate(updated_cart)
                    reply_text = format_msg(
                        target_lang,
                        "cart_update_success",
                        title=target_item["product"]["title"],
                        qty=new_qty,
                        count=cart_out.item_count,
                        total=cart_out.total_amount,
                    )
                except ECommerceException as exc:
                    reply_text = f"Could not update quantity: {exc.message}"
            else:
                reply_text = format_msg(target_lang, "cart_empty")

        # 8. GET CART
        elif intent == "get_cart":
            cart_dict = ECommerceService.get_cart(db, customer_id)
            cart_out = CartOut.model_validate(cart_dict)
            if cart_out.item_count == 0:
                reply_text = format_msg(target_lang, "cart_empty")
            else:
                reply_text = format_msg(
                    target_lang,
                    "cart_summary",
                    count=cart_out.item_count,
                    subtotal=cart_out.subtotal,
                    total=cart_out.total_amount,
                )

        # 9. TRACK ORDER
        elif intent == "track_order":
            raw_order: Optional[Dict[str, Any]] = None
            if target_order_id:
                try:
                    raw_order = ECommerceService.get_order_by_id(db, target_order_id, customer_id)
                except ECommerceException:
                    raw_order = None
            if not raw_order:
                orders = ECommerceService.get_orders(db, customer_id)
                if orders:
                    raw_order = orders[0]

            if raw_order:
                order_out = OrderOut.model_validate(raw_order)
                order_out.can_cancel = order_out.status in ("processing", "shipped")
                order_out.can_return = order_out.status == "delivered"

                items_summary = ", ".join(item.product_title for item in order_out.items[:2])
                status_key = f"status_{order_out.status}"
                date_str = order_out.delivered_at.strftime('%d %b %Y') if order_out.delivered_at else ""
                status_desc = format_msg(
                    target_lang,
                    status_key,
                    carrier=order_out.carrier,
                    tracking=order_out.tracking_number,
                    date=date_str,
                )
                arrival_desc = (
                    format_msg(target_lang, "track_arrival", date=order_out.expected_delivery.strftime('%d %B, %A'))
                    if order_out.expected_delivery and order_out.status not in ("delivered", "cancelled")
                    else ""
                )
                if order_out.status == "cancelled":
                    reply_text = format_msg(target_lang, "track_cancelled", order_id=order_out.id, items=items_summary)
                else:
                    reply_text = format_msg(
                        target_lang,
                        "track_status",
                        order_id=order_out.id,
                        items=items_summary,
                        status_desc=status_desc,
                        arrival_desc=arrival_desc,
                    )
            else:
                reply_text = format_msg(target_lang, "track_empty")

        # 10. GET ORDER DETAILS
        elif intent == "get_order_details":
            raw_order = None
            if target_order_id:
                try:
                    raw_order = ECommerceService.get_order_by_id(db, target_order_id, customer_id)
                except ECommerceException:
                    raw_order = None
            if not raw_order:
                orders = ECommerceService.get_orders(db, customer_id)
                if orders:
                    raw_order = orders[0]

            if raw_order:
                order_out = OrderOut.model_validate(raw_order)
                items_str = ", ".join(f"{it.product_title} (x{it.quantity})" for it in order_out.items)
                reply_text = f"Order #{order_out.id}: {items_str}. Total: Rs. {order_out.total_amount:,.2f}. Status: {order_out.status.upper()} with {order_out.carrier}."
            else:
                reply_text = format_msg(target_lang, "track_empty")

        # 11. REQUEST CANCELLATION (Consequential Action Safety Guard)
        elif intent in ("request_cancellation", "cancel_order"):
            raw_order = None
            if target_order_id:
                try:
                    raw_order = ECommerceService.get_order_by_id(db, target_order_id, customer_id)
                except ECommerceException:
                    raw_order = None
            if not raw_order:
                orders = ECommerceService.get_orders(db, customer_id)
                for o in orders:
                    if o.get("status") in ("processing", "shipped"):
                        raw_order = o
                        break

            if raw_order:
                order_out = OrderOut.model_validate(raw_order)
                order_out.can_cancel = order_out.status in ("processing", "shipped")

                if order_out.status == "delivered":
                    reply_text = format_msg(target_lang, "cancel_already_delivered", order_id=order_out.id)
                elif order_out.status == "cancelled":
                    reply_text = format_msg(target_lang, "cancel_already_cancelled", order_id=order_out.id)
                else:
                    confirm_prompt = format_msg(
                        target_lang,
                        "cancel_confirm_prompt",
                        order_id=order_out.id,
                        total=order_out.total_amount,
                    )
                    reply_text = format_msg(
                        target_lang,
                        "cancel_confirm_body",
                        order_id=order_out.id,
                        total=order_out.total_amount,
                    )

                    pending_rec = ECommerceService.create_pending_action(
                        db=db,
                        customer_id=customer_id,
                        action_type="cancel_order",
                        order_id=order_out.id,
                        details={
                            "order_id": order_out.id,
                            "total_amount": order_out.total_amount,
                            "items": [item.product_title for item in order_out.items],
                        },
                    )
                    action_pending = AssistantActionProposal(
                        action="cancel_order",
                        target_id=order_out.id,
                        confirmation_prompt=confirm_prompt,
                        confirmation_token=pending_rec["confirmation_token"],
                        expires_at=pending_rec["expires_at"],
                        details={
                            "order_id": order_out.id,
                            "total_amount": order_out.total_amount,
                            "items": [item.product_title for item in order_out.items],
                            "confirmation_token": pending_rec["confirmation_token"],
                            "expires_at": pending_rec["expires_at"].isoformat(),
                        },
                    )
            else:
                reply_text = format_msg(target_lang, "cancel_not_found")

        # 12. REQUEST RETURN (Consequential Action Safety Guard)
        elif intent in ("request_return", "return_request"):
            raw_order = None
            if target_order_id:
                try:
                    raw_order = ECommerceService.get_order_by_id(db, target_order_id, customer_id)
                except ECommerceException:
                    raw_order = None
            if not raw_order:
                orders = ECommerceService.get_orders(db, customer_id)
                for o in orders:
                    if o.get("status") == "delivered" and not o.get("returns"):
                        raw_order = o
                        break

            if raw_order:
                order_out = OrderOut.model_validate(raw_order)
                if order_out.status != "delivered":
                    reply_text = format_msg(target_lang, "return_not_delivered", order_id=order_out.id)
                elif order_out.returns:
                    reply_text = format_msg(target_lang, "return_already_requested", order_id=order_out.id)
                else:
                    confirm_prompt = format_msg(
                        target_lang,
                        "return_confirm_prompt",
                        order_id=order_out.id,
                        total=order_out.total_amount,
                    )
                    reply_text = format_msg(
                        target_lang,
                        "return_confirm_body",
                        order_id=order_out.id,
                        carrier=order_out.carrier,
                    )

                    pending_rec = ECommerceService.create_pending_action(
                        db=db,
                        customer_id=customer_id,
                        action_type="create_return",
                        order_id=order_out.id,
                        details={
                            "order_id": order_out.id,
                            "refund_amount": order_out.total_amount,
                            "items": [item.product_title for item in order_out.items],
                        },
                    )
                    action_pending = AssistantActionProposal(
                        action="create_return",
                        target_id=order_out.id,
                        confirmation_prompt=confirm_prompt,
                        confirmation_token=pending_rec["confirmation_token"],
                        expires_at=pending_rec["expires_at"],
                        details={
                            "order_id": order_out.id,
                            "refund_amount": order_out.total_amount,
                            "items": [item.product_title for item in order_out.items],
                            "confirmation_token": pending_rec["confirmation_token"],
                            "expires_at": pending_rec["expires_at"].isoformat(),
                        },
                    )
            else:
                reply_text = format_msg(target_lang, "return_not_found")

        # 13. CUSTOMER SUPPORT: DELIVERY
        elif intent in ("delivery_question", "shipping_policy"):
            reply_text = format_msg(target_lang, "delivery_support")

        # 14. CUSTOMER SUPPORT: PAYMENT
        elif intent == "payment_question":
            reply_text = format_msg(target_lang, "payment_support")

        # 15. CUSTOMER SUPPORT: PRODUCT QUESTIONS
        elif intent == "product_question":
            direct_ans = entities.get("direct_response")
            if direct_ans and len(direct_ans.strip()) > 5:
                reply_text = direct_ans.strip()
            else:
                reply_text = "All products on VoiceIQ India are 100% genuine, backed by brand warranty, with 7-day easy returns and replacement support."

        # 16. GENERAL SUPPORT, OUT OF SCOPE & UNKNOWN
        else:
            if intent == "out_of_scope":
                reply_text = format_msg(target_lang, "out_of_scope")
            elif intent == "needs_clarification":
                reply_text = format_msg(target_lang, "needs_clarification")
            else:
                direct_ans = entities.get("direct_response")
                if direct_ans and len(direct_ans.strip()) > 5:
                    reply_text = direct_ans.strip()
                else:
                    reply_text = format_msg(target_lang, "general_support")

        # -----------------------------------------------------------------
        # STEP 4: Optional Gnani Timbre TTS Speech Synthesis
        # -----------------------------------------------------------------
        audio_b64: Optional[str] = None
        if payload.synthesize_audio and gnani_client:
            try:
                tts_text = reply_text
                # Convert currency signs to spoken words in Indic languages
                if "kn" in target_lang:
                    tts_text = re.sub(r"₹\s*([0-9,]+(?:\.[0-9]+)?)", r"\1 ರೂಪಾಯಿ", tts_text)
                    tts_text = re.sub(r"Rs\.?\s*([0-9,]+(?:\.[0-9]+)?)", r"\1 ರೂಪಾಯಿ", tts_text)
                elif "hi" in target_lang or "mr" in target_lang:
                    tts_text = re.sub(r"₹\s*([0-9,]+(?:\.[0-9]+)?)", r"\1 रुपये", tts_text)
                    tts_text = re.sub(r"Rs\.?\s*([0-9,]+(?:\.[0-9]+)?)", r"\1 रुपये", tts_text)
                elif "ta" in target_lang:
                    tts_text = re.sub(r"₹\s*([0-9,]+(?:\.[0-9]+)?)", r"\1 ரூபாய்", tts_text)
                    tts_text = re.sub(r"Rs\.?\s*([0-9,]+(?:\.[0-9]+)?)", r"\1 ரூபாய்", tts_text)
                elif "te" in target_lang:
                    tts_text = re.sub(r"₹\s*([0-9,]+(?:\.[0-9]+)?)", r"\1 రూపాయలు", tts_text)
                    tts_text = re.sub(r"Rs\.?\s*([0-9,]+(?:\.[0-9]+)?)", r"\1 రూపాయలు", tts_text)
                elif "ml" in target_lang:
                    tts_text = re.sub(r"₹\s*([0-9,]+(?:\.[0-9]+)?)", r"\1 രൂപ", tts_text)
                    tts_text = re.sub(r"Rs\.?\s*([0-9,]+(?:\.[0-9]+)?)", r"\1 രൂപ", tts_text)
                elif "bn" in target_lang:
                    tts_text = re.sub(r"₹\s*([0-9,]+(?:\.[0-9]+)?)", r"\1 টাকা", tts_text)
                    tts_text = re.sub(r"Rs\.?\s*([0-9,]+(?:\.[0-9]+)?)", r"\1 টাকা", tts_text)
                elif "gu" in target_lang:
                    tts_text = re.sub(r"₹\s*([0-9,]+(?:\.[0-9]+)?)", r"\1 રૂપિયા", tts_text)
                    tts_text = re.sub(r"Rs\.?\s*([0-9,]+(?:\.[0-9]+)?)", r"\1 રૂપિયા", tts_text)
                elif "pa" in target_lang:
                    tts_text = re.sub(r"₹\s*([0-9,]+(?:\.[0-9]+)?)", r"\1 ਰੁਪਏ", tts_text)
                    tts_text = re.sub(r"Rs\.?\s*([0-9,]+(?:\.[0-9]+)?)", r"\1 ਰੁਪਏ", tts_text)
                else:
                    tts_text = re.sub(r"Rs\.\s*", "Rupees ", tts_text)
                    tts_text = re.sub(r"₹\s*", "Rupees ", tts_text)

                audio_bytes = await gnani_client.synthesize_speech(
                    text=tts_text,
                    language=target_lang,
                    voice="Nalini" if "hi" in target_lang else "Shivani",
                )
                audio_b64 = base64.b64encode(audio_bytes).decode("ascii")
            except Exception as tts_err:
                logger.warning(f"VoiceAssistant TTS synthesis skipped/failed: {tts_err}")

        # -----------------------------------------------------------------
        # STEP 5: Persist Conversation Audit Record in MongoDB
        # -----------------------------------------------------------------
        conv_id = payload.conversation_id or generate_uuid()
        now = get_utc_now()
        existing_conv = db.conversations.find_one({"$or": [{"id": conv_id}, {"_id": conv_id}]})
        if existing_conv:
            updated_transcript = (existing_conv.get("transcript") or "") + f"\nUser: {payload.message}\nAI: {reply_text}"
            db.conversations.update_one(
                {"_id": existing_conv["_id"]},
                {
                    "$set": {
                        "transcript": updated_transcript,
                        "detected_intent": intent,
                        "language_code": target_lang,
                        "updated_at": now,
                    }
                },
            )
        else:
            conv_doc = {
                "_id": conv_id,
                "id": conv_id,
                "filename": f"voice_msg_{conv_id[:8]}",
                "content_type": "text/plain",
                "language_code": target_lang,
                "status": "completed",
                "transcript": f"User: {payload.message}\nAI: {reply_text}",
                "customer_id": customer_id,
                "order_id": target_order_id,
                "product_id": payload.product_id,
                "source": "voice_widget",
                "detected_intent": intent,
                "created_at": now,
                "updated_at": now,
            }
            db.conversations.insert_one(conv_doc)

        insight_doc = {
            "conversation_id": conv_id,
            "summary": reply_text[:250],
            "customer_intent": intent,
            "primary_issue": intent.replace("_", " ").title(),
            "action_items": [{"task": f"Process {intent}", "assignee": "Evon v3.3 AI", "priority": "medium", "status": "completed"}],
            "commitments": [],
            "resolution_status": "resolved",
            "escalation_level": "low",
            "sentiment_label": "neutral",
            "sentiment_score": 0.1,
            "frustration_index": 0.0,
            "updated_at": now,
        }
        db.conversation_insights.update_one(
            {"conversation_id": conv_id},
            {"$set": insight_doc, "$setOnInsert": {"_id": f"ins_{conv_id}", "id": f"ins_{conv_id}", "created_at": now}},
            upsert=True,
        )

        # Section 14 standardized data dictionary
        data_block: Dict[str, Any] = {
            "products": [p.model_dump() for p in products_out] if products_out else [],
            "order": order_out.model_dump() if order_out else None,
            "cart": cart_out.model_dump() if cart_out else None,
            "action_proposal": action_pending.model_dump() if action_pending else None,
        }

        return AssistantMessageOut(
            success=True,
            reply_text=reply_text,
            intent=intent,
            detected_language=target_lang,
            action_pending_confirmation=action_pending,
            products=products_out,
            order=order_out,
            cart=cart_out,
            audio_base64=audio_b64,
            conversation_id=conv_id,
            llm_provider=llm_provider,
            intent_confidence=intent_confidence,
            reasoning=reasoning,
            consequential_action_required=consequential_action_required,
            # Section 14 standardized contract fields
            transcript=payload.message,
            language=target_lang,
            message=reply_text,
            data=data_block,
            requires_confirmation=consequential_action_required,
        )
