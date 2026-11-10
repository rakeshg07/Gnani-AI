"""Centralized Domain Scope Guard for VoiceIQ India Sovereign Store.

Ensures that the conversational assistant ONLY answers queries related to:
- Store products, categories, specifications, brands, and prices
- Product recommendations, availability, and comparisons
- Shopping cart, checkout, and supported payment methods
- Orders, order tracking, shipping, and delivery
- Order cancellations, 7-day returns, and refunds
- Store policies, services, and application usage

Strictly rejects general-purpose AI tasks (coding, general knowledge, poetry, jokes,
trivia, math, science, politics, personal advice, etc.) using canonical localized responses.
"""
import asyncio
import json
import re
from enum import Enum
from typing import Dict, Any, Optional, List, Tuple
from pydantic import BaseModel, Field

from app.core.config import settings
from app.core.logging import logger
from app.services.assistant_locales import format_msg


class ScopeClassification(str, Enum):
    IN_SCOPE = "in_scope"
    OUT_OF_SCOPE = "out_of_scope"
    NEEDS_CLARIFICATION = "needs_clarification"


class QueryScopeResult(BaseModel):
    """Structured scope evaluation result."""
    classification: ScopeClassification
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    reason: str
    detector: str  # "prompt_shield", "deterministic_rules", "gemini_semantic", or "deterministic_fallback"
    store_topic: Optional[str] = None
    suggested_clarification: Optional[str] = None

    @property
    def is_in_scope(self) -> bool:
        return self.classification == ScopeClassification.IN_SCOPE

    @property
    def is_out_of_scope(self) -> bool:
        return self.classification == ScopeClassification.OUT_OF_SCOPE

    @property
    def needs_clarification(self) -> bool:
        return self.classification == ScopeClassification.NEEDS_CLARIFICATION


# ============================================================================
# STAGE 1: PROMPT INJECTION & JAILBREAK PATTERNS
# ============================================================================

PROMPT_SHIELD_PATTERNS: List[re.Pattern] = [
    re.compile(r"\bignore\s+(?:all\s+)?(?:previous|above|system)\s+(?:instructions|rules|prompts|directions)\b", re.IGNORECASE),
    re.compile(r"\bdisregard\s+(?:all\s+)?(?:previous|above|system)\b", re.IGNORECASE),
    re.compile(r"\byou\s+are\s+now\s+(?:an?\s+)?(?:unrestricted|general|coding|python|dan|jailbroken|unconstrained)\b", re.IGNORECASE),
    re.compile(r"\b(?:pretend|act)\s+as\s+(?:an?\s+)?(?:unrestricted|general|coding|python|dan|jailbroken|chatgpt)\b", re.IGNORECASE),
    re.compile(r"\b(?:reveal|show|print|output)\s+(?:your\s+)?(?:system\s+prompt|developer\s+instructions|initial\s+prompt)\b", re.IGNORECASE),
    re.compile(r"\bdeveloper\s+mode\s+enabled\b", re.IGNORECASE),
]


# ============================================================================
# STAGE 2: DETERMINISTIC REGEX PATTERNS (HIGH CONFIDENCE)
# ============================================================================

# Strictly out-of-scope subjects (coding, science, trivia, politics, creative writing)
OUT_OF_SCOPE_REGEXES: List[re.Pattern] = [
    # Coding & Software Engineering (supports common typos like 'whzt is python', 'wat is java')
    re.compile(r"\b(?:wh[a-z]{1,4}\s+is|explain|teach\s+me|syntax\s+for|code\s+for|program\s+in|learn)\s+(?:java|python|c\+\+|c#|rust|golang|javascript|typescript|php|ruby|swift|kotlin|sql|html|css|bash|powershell|react|vue|angular|django|flask|spring\s*boot)\b", re.IGNORECASE),
    re.compile(r"^(?:wh[a-z]{1,4}\s+is\s+|wat\s+is\s+|tell\s+me\s+about\s+)?(?:python|java|c\+\+|javascript|typescript|rust|golang)\s*(?:\?|$)", re.IGNORECASE),
    re.compile(r"\b(?:explain|write\s+(?:a|an)?)\s+(?:python|java|c\+\+|javascript|sql|c#)\s+(?:code|program|script|function|class|query)\b", re.IGNORECASE),
    re.compile(r"\b(?:python|java|c\+\+|c#|rust|golang|javascript|typescript)\s+(?:code|program|script|function|class|query|syntax|programming|basics|tutorial)\b", re.IGNORECASE),
    re.compile(r"\b(?:write|generate|debug|create)\s+(?:a|an|the|some)?\s*(?:program|code|script|function|class|algorithm|regex|sql\s+query|macro|snippet)\b", re.IGNORECASE),
    re.compile(r"\bhow\s+to\s+(?:code|program|compile|debug|write\s+a\s+function|write\s+a\s+loop|declare\s+a\s+variable|import\s+numpy|install\s+python)\b", re.IGNORECASE),
    re.compile(r"\b(?:object\s+oriented\s+programming|recursion|binary\s+tree|dynamic\s+programming|time\s+complexity|big\s+o\s+notation|compiler|interpreter)\b", re.IGNORECASE),

    # General Science, Math & Tech Theory
    re.compile(r"\b(?:what\s+is|explain)\s+(?:artificial\s+intelligence|machine\s+learning|deep\s+learning|neural\s+networks?|llms?|nlp|data\s+science|quantum\s+computing)\b", re.IGNORECASE),
    re.compile(r"\b(?:what\s+is|explain)\s+(?:photosynthesis|gravity|relativity|quantum\s+physics|thermodynamics|chemistry|biology|physics|calculus|algebra|geometry|trigonometry)\b", re.IGNORECASE),
    re.compile(r"\b(?:solve|calculate|evaluate)\s+(?:the\s+equation|for\s+x|integral|derivative|\d+\s*[\+\-\*\/]\s*\d+)\b", re.IGNORECASE),

    # Politics, History & General World Knowledge
    re.compile(r"\bwho\s+is\s+(?:the\s+)?(?:current\s+)?(?:president|prime\s+minister|chief\s+minister|governor|monarch|pope|ceo\s+of\s+google|ceo\s+of\s+microsoft|elon\s+musk)\b", re.IGNORECASE),
    re.compile(r"\bwho\s+won\s+(?:the\s+)?(?:world\s+cup|ipl|elections?|nobel\s+prize|oscar)\b", re.IGNORECASE),
    re.compile(r"\b(?:what\s+is\s+the\s+)?capital\s+of\s+[a-z\s]+\b", re.IGNORECASE),
    re.compile(r"\b(?:history\s+of|tell\s+me\s+about)\s+(?:world\s+war|rome|mughals?|british\s+empire|ancient\s+egypt|french\s+revolution)\b", re.IGNORECASE),

    # Creative Writing, Entertainment & Personal Advice
    re.compile(r"\b(?:tell\s+me|say)\s+(?:a|another)?\s*(?:joke|riddle|funny\s+story)\b", re.IGNORECASE),
    re.compile(r"\b(?:make\s+me\s+laugh|entertain\s+me)\b", re.IGNORECASE),
    re.compile(r"\bwrite\s+(?:a|an)?\s*(?:poem|poetry|song|lyrics|rap|essay|story|novel|speech)\b", re.IGNORECASE),
    re.compile(r"\b(?:sing\s+(?:a|me)?\s*song|recite\s+a\s+poem)\b", re.IGNORECASE),
    re.compile(r"\b(?:give\s+me\s+)?(?:relationship|dating|love|marriage|life|medical|health|legal|financial)\s+advice\b", re.IGNORECASE),
    re.compile(r"\bhow\s+to\s+(?:impress\s+a\s+girl|impress\s+a\s+boy|get\s+a\s+girlfriend|get\s+a\s+boyfriend|make\s+money\s+online|cure\s+fever)\b", re.IGNORECASE),
    re.compile(r"\b(?:horoscope|astrology|zodiac\s+sign|tarot)\b", re.IGNORECASE),
]

# Explicit Store Catalog & E-Commerce Keywords (In-Scope Triggers)
IN_SCOPE_STORE_KEYWORDS: List[str] = [
    # Catalog Products
    "earbuds", "earphone", "headphones", "speaker", "soundbar",
    "phone", "smartphone", "mobile", "laptop", "tablet", "computer",
    "mixer", "grinder", "air fryer", "blender", "cooker", "oven", "microwave",
    "tv", "television", "fridge", "refrigerator", "washing machine", "ac", "air conditioner",
    "watch", "smartwatch", "chronograph", "sunglasses",
    "saree", "kurta", "kurti", "shirt", "t-shirt", "jeans", "shoes", "sneakers", "wallet", "apparel",
    # Store Brands
    "boat", "oneplus", "samsung", "apple", "preethi", "philips", "titan", "w for woman",
    "redmi", "realme", "dell", "hp", "lenovo", "sony", "lg",
    # Shopping & Transactions
    "cart", "checkout", "buy", "purchase", "price", "cost", "mrp", "discount", "deal", "offer",
    "order", "orders", "track", "tracking", "shipment", "delivery", "delivered", "courier",
    "delhivery", "blue dart", "ekart",
    "cancel", "cancellation", "return", "returns", "refund", "warranty", "guarantee", "specs", "specification",
    "stock", "available", "availability", "compare", "comparison", "under", "below", "rupees", "rs", "₹",
    # Policies & Methods
    "voiceiq", "store", "sovereign", "upi", "gpay", "phonepe", "paytm", "cod", "cash on delivery",
    "credit card", "debit card", "net banking", "payment", "shipping fee", "free delivery",
    # Common Courteous Greetings / Mic Checks
    "hi", "hello", "hey", "namaste", "vanakkam", "namaskara", "audible", "mic check", "good morning", "good evening",
]

# Indic E-Commerce Signatures
INDIC_IN_SCOPE_PATTERNS: List[str] = [
    # Hindi
    "दिखाओ", "खोजें", "चाहिए", "खरीदना", "मूल्य", "दाम", "कीमत", "सस्ता", "छूट",
    "ऑर्डर", "ट्रैक", "रद्द", "वापसी", "कार्ट", "जोड़ें", "सामान", "वारंटी",
    # Kannada
    "ತೋರಿಸಿ", "ತೋರಿಸು", "ಹುಡುಕು", "ಬೇಕು", "ಖರೀದಿಸಿ", "ಬೆಲೆ", "ದರ", "ರಿಯಾಯಿತಿ",
    "ಆರ್ಡರ್", "ಟ್ರಾಕ್", "ರದ್ದು", "ವಾಪಸ್", "ಕಾರ್ಟ್", "ಸೇರಿಸಿ", "ಉತ್ಪನ್ನ",
    # Tamil
    "காட்டு", "தேடு", "வேண்டும்", "வாங்கு", "விலை", "ஆர்டர்", "ட்ராக்கிங்", "ரத்து", "கார்ட்",
    # Telugu
    "చూపించు", "వెతకండి", "కావాలి", "ధర", "ఆర్డర్", "ట్రాకింగ్", "రద్దు", "కార్ట్",
]


class QueryScopeGuard:
    """
    Evaluates whether user input is strictly within VoiceIQ Sovereign Store scope.
    """

    @classmethod
    def evaluate_deterministic(
        cls,
        text: str,
        current_page: str = "home",
        has_product_context: bool = False,
        has_order_context: bool = False,
    ) -> QueryScopeResult:
        """
        Fast, zero-latency deterministic scope classification without calling external APIs.
        Handles prompt injections, coding queries, general trivia, and unmistakable store actions.
        """
        cleaned = text.strip()
        lower_text = cleaned.lower()

        # Rule 1: Empty or whitespace
        if not cleaned:
            return QueryScopeResult(
                classification=ScopeClassification.NEEDS_CLARIFICATION,
                confidence=1.0,
                reason="Empty query received.",
                detector="deterministic_rules",
                suggested_clarification="How can I assist you with VoiceIQ Store today?",
            )

        # Rule 2: Prompt Injection / System Jailbreak Guard
        for pattern in PROMPT_SHIELD_PATTERNS:
            if pattern.search(lower_text):
                logger.warning(f"Scope Guard: Prompt injection attempt detected: '{cleaned[:60]}'")
                return QueryScopeResult(
                    classification=ScopeClassification.OUT_OF_SCOPE,
                    confidence=1.0,
                    reason="Prompt injection / system jailbreak attempt blocked.",
                    detector="prompt_shield",
                )

        # Rule 3: Check for explicit Store Context Overrides
        # (e.g. if customer asks "Do you sell python programming books?" or has active product context)
        store_match_found = any(k in lower_text for k in IN_SCOPE_STORE_KEYWORDS) or any(k in cleaned for k in INDIC_IN_SCOPE_PATTERNS)
        order_id_present = bool(re.search(r"\b(?:viq-?)?\d{5}\b", lower_text))

        # Rule 4: Match Explicit Out-Of-Scope Patterns
        for out_regex in OUT_OF_SCOPE_REGEXES:
            if out_regex.search(lower_text):
                # If it's a coding or trivia question, even if it contains "python" or "java",
                # it's out of scope unless explicitly asking to buy/search products
                shopping_verbs = ["buy", "sell", "do you have", "price of", "cost of", "in stock", "available"]
                is_genuine_shopping = any(v in lower_text for v in shopping_verbs) and ("book" in lower_text or "course" in lower_text or "tshirt" in lower_text)

                if not is_genuine_shopping:
                    logger.info(f"Scope Guard: Deterministic rule matched out-of-scope query: '{cleaned[:60]}'")
                    return QueryScopeResult(
                        classification=ScopeClassification.OUT_OF_SCOPE,
                        confidence=0.98,
                        reason=f"Query matched out-of-scope pattern: {out_regex.pattern[:30]}",
                        detector="deterministic_rules",
                    )

        # Rule 5: Explicit In-Scope Store Actions & Keywords
        if store_match_found or order_id_present or has_product_context or has_order_context:
            topic = "orders" if order_id_present else ("cart" if "cart" in lower_text else "products")
            return QueryScopeResult(
                classification=ScopeClassification.IN_SCOPE,
                confidence=0.95,
                reason="Query contains store products, cart, order, or policy keywords.",
                detector="deterministic_rules",
                store_topic=topic,
            )

        # Rule 6: Check for general knowledge interrogatives without any store context
        # e.g., "What is gravity?", "Who is Barack Obama?", "Tell me about France"
        gk_interrogatives = [
            r"^what\s+is\s+", r"^who\s+is\s+", r"^who\s+was\s+", r"^explain\s+",
            r"^tell\s+me\s+about\s+", r"^how\s+does\s+", r"^why\s+is\s+", r"^where\s+is\s+(?!my\s+order)",
        ]
        for gk_pat in gk_interrogatives:
            if re.search(gk_pat, lower_text):
                return QueryScopeResult(
                    classification=ScopeClassification.OUT_OF_SCOPE,
                    confidence=0.90,
                    reason="General knowledge question unrelated to VoiceIQ Store.",
                    detector="deterministic_rules",
                )

        # Rule 7: Very short or ambiguous queries (< 3 words)
        words = lower_text.split()
        if len(words) <= 2 and not store_match_found:
            return QueryScopeResult(
                classification=ScopeClassification.NEEDS_CLARIFICATION,
                confidence=0.85,
                reason="Short ambiguous query with no store context.",
                detector="deterministic_rules",
                suggested_clarification="Could you please clarify your request? I can help you search products, track orders, or view deals.",
            )

        # Default fallback for unclassified non-store queries
        return QueryScopeResult(
            classification=ScopeClassification.OUT_OF_SCOPE,
            confidence=0.85,
            reason="Query does not relate to VoiceIQ Sovereign Store products, orders, or services.",
            detector="deterministic_rules",
        )

    @classmethod
    async def evaluate_with_gemini(
        cls,
        text: str,
        gemini_client: Any,
        current_page: str = "home",
        timeout: float = 4.0,
    ) -> QueryScopeResult:
        """
        Invokes Google Gemini 3.8 Flash for semantic domain scope classification.
        Constrained by a tight timeout (4.0s) and validated by backend rules.
        """
        prompt = (
            "You are a strict domain scope gatekeeper for VoiceIQ Sovereign Store, an Indian e-commerce platform "
            "selling electronics (phones, audio, laptops, TVs), kitchen appliances, fashion apparel, and watches.\n"
            "Classify the following customer user message into exactly ONE category:\n"
            "- 'in_scope': Directly relates to products, brands, prices, deals, stock, cart, checkout, payments (UPI/Cards/COD), "
            "orders, shipping/tracking, returns, refunds, store policies, application navigation, or friendly greetings.\n"
            "- 'out_of_scope': General knowledge, coding/programming, technical tutorials, poetry, jokes, politics, math, science, "
            "personal advice, or topics unrelated to the VoiceIQ store.\n"
            "- 'needs_clarification': The user input is too ambiguous or fragmented to determine intent.\n\n"
            f"User Message: {text}\n"
            f"Current Page Context: {current_page}\n\n"
            "Respond ONLY with valid JSON in this exact structure:\n"
            '{"classification": "in_scope" | "out_of_scope" | "needs_clarification", "confidence": 0.95, "reason": "reason", "store_topic": "topic"}'
        )

        try:
            client = gemini_client._get_client()
            from google.genai import types

            config = types.GenerateContentConfig(
                response_mime_type="application/json",
                temperature=0.1,
                max_output_tokens=150,
            )

            response = await asyncio.wait_for(
                client.aio.models.generate_content(
                    model=gemini_client.model_name,
                    contents=prompt,
                    config=config,
                ),
                timeout=timeout,
            )

            raw = response.text or "{}"
            parsed = json.loads(raw)

            classification_str = (parsed.get("classification") or "out_of_scope").lower().strip()
            if classification_str == "in_scope":
                # CRITICAL RULE: Backend Validation Guard
                # Even if Gemini says 'in_scope', verify it didn't miss obvious coding / trivia
                deterministic_check = cls.evaluate_deterministic(text, current_page=current_page)
                if deterministic_check.is_out_of_scope and deterministic_check.detector in ("prompt_shield", "deterministic_rules"):
                    logger.warning(f"Backend Guard: Overruled Gemini 'in_scope' classification for: '{text}'")
                    return deterministic_check

                return QueryScopeResult(
                    classification=ScopeClassification.IN_SCOPE,
                    confidence=float(parsed.get("confidence", 0.95)),
                    reason=parsed.get("reason", "Gemini semantic classification: in-scope store query."),
                    detector="gemini_semantic",
                    store_topic=parsed.get("store_topic", "ecommerce"),
                )
            elif classification_str == "needs_clarification":
                return QueryScopeResult(
                    classification=ScopeClassification.NEEDS_CLARIFICATION,
                    confidence=float(parsed.get("confidence", 0.85)),
                    reason=parsed.get("reason", "Gemini identified query as needing clarification."),
                    detector="gemini_semantic",
                    suggested_clarification="Could you please clarify your request regarding VoiceIQ Store?",
                )
            else:
                return QueryScopeResult(
                    classification=ScopeClassification.OUT_OF_SCOPE,
                    confidence=float(parsed.get("confidence", 0.95)),
                    reason=parsed.get("reason", "Gemini semantic classification: out-of-scope query."),
                    detector="gemini_semantic",
                )

        except asyncio.TimeoutError:
            logger.info("Scope Guard: Gemini semantic evaluation timed out. Using deterministic fallback.")
            res = cls.evaluate_deterministic(text, current_page=current_page)
            res.detector = "deterministic_fallback (gemini_timeout)"
            return res
        except Exception as exc:
            logger.info(f"Scope Guard: Gemini classification skipped ({exc}). Using deterministic fallback.")
            res = cls.evaluate_deterministic(text, current_page=current_page)
            res.detector = "deterministic_fallback (gemini_error)"
            return res

    @classmethod
    async def evaluate_with_huggingface(
        cls,
        text: str,
        hf_client: Any,
        current_page: str = "home",
        timeout: float = 4.0,
    ) -> QueryScopeResult:
        """
        Invokes Hugging Face model for fast semantic domain scope classification.
        """
        prompt = (
            "You are a strict domain scope gatekeeper for VoiceIQ Sovereign Store, an Indian e-commerce platform "
            "selling electronics, kitchen appliances, fashion apparel, and watches.\n"
            "Classify the following customer message into exactly ONE category:\n"
            "- 'in_scope': Products, brands, prices, deals, stock, cart, checkout, payments, orders, shipping, returns, store services, or greetings.\n"
            "- 'out_of_scope': General knowledge, coding/programming, trivia, jokes, poems, politics, science, math, or personal advice.\n"
            "- 'needs_clarification': The query is too ambiguous or fragmented.\n\n"
            f"User Message: {text}\n"
            f"Current Page Context: {current_page}\n\n"
            "Respond ONLY with valid JSON in this exact structure: "
            '{"classification": "in_scope" | "out_of_scope" | "needs_clarification", "confidence": 0.95, "reason": "reason"}'
        )

        try:
            raw = await asyncio.wait_for(
                hf_client.generate_response(
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.1,
                    max_tokens=150,
                ),
                timeout=timeout,
            )
            from app.services.evon_intent import parse_evon_json_output
            parsed = parse_evon_json_output(raw)

            classification_str = (parsed.get("classification") or "out_of_scope").lower().strip()
            if classification_str == "in_scope":
                # Backend Validation Guard
                deterministic_check = cls.evaluate_deterministic(text, current_page=current_page)
                if deterministic_check.is_out_of_scope and deterministic_check.detector in ("prompt_shield", "deterministic_rules"):
                    logger.warning(f"Backend Guard: Overruled HF 'in_scope' classification for: '{text}'")
                    return deterministic_check

                return QueryScopeResult(
                    classification=ScopeClassification.IN_SCOPE,
                    confidence=float(parsed.get("confidence", 0.95)),
                    reason=parsed.get("reason", "Hugging Face semantic classification: in-scope store query."),
                    detector="huggingface_semantic",
                    store_topic=parsed.get("store_topic", "ecommerce"),
                )
            elif classification_str == "needs_clarification":
                return QueryScopeResult(
                    classification=ScopeClassification.NEEDS_CLARIFICATION,
                    confidence=float(parsed.get("confidence", 0.85)),
                    reason=parsed.get("reason", "Hugging Face identified query as needing clarification."),
                    detector="huggingface_semantic",
                    suggested_clarification="Could you please clarify your request regarding VoiceIQ Store?",
                )
            else:
                return QueryScopeResult(
                    classification=ScopeClassification.OUT_OF_SCOPE,
                    confidence=float(parsed.get("confidence", 0.95)),
                    reason=parsed.get("reason", "Hugging Face semantic classification: out-of-scope query."),
                    detector="huggingface_semantic",
                )
        except Exception as exc:
            logger.info(f"Scope Guard: Hugging Face classification skipped ({exc}). Using deterministic fallback.")
            res = cls.evaluate_deterministic(text, current_page=current_page)
            res.detector = "deterministic_fallback (hf_error)"
            return res


async def classify_query_scope(
    message: str,
    current_page: str = "home",
    language_code: str = "en-IN",
    has_product_context: bool = False,
    has_order_context: bool = False,
    gemini_client: Optional[Any] = None,
    huggingface_client: Optional[Any] = None,
) -> QueryScopeResult:
    """
    High-level entry point for domain scope classification across all channels.
    Combines fast deterministic filters with optional LLM semantic verification.
    """
    # Step 1: Run deterministic fast evaluation
    det_result = QueryScopeGuard.evaluate_deterministic(
        text=message,
        current_page=current_page,
        has_product_context=has_product_context,
        has_order_context=has_order_context,
    )

    # If deterministic filter found prompt injection or unambiguous out-of-scope pattern, return immediately
    if det_result.is_out_of_scope and det_result.detector in ("prompt_shield", "deterministic_rules"):
        return det_result

    # If unambiguous store query with high confidence, return immediately
    if det_result.is_in_scope and det_result.confidence >= 0.95:
        return det_result

    # Step 2: Semantic check via Hugging Face if configured
    if huggingface_client and getattr(huggingface_client, "is_configured", lambda: False)():
        return await QueryScopeGuard.evaluate_with_huggingface(
            text=message,
            hf_client=huggingface_client,
            current_page=current_page,
            timeout=4.0,
        )

    # Step 3: Semantic check via Gemini if configured
    if gemini_client and getattr(gemini_client, "is_configured", lambda: False)():
        return await QueryScopeGuard.evaluate_with_gemini(
            text=message,
            gemini_client=gemini_client,
            current_page=current_page,
            timeout=4.0,
        )

    # Step 4: Return deterministic fallback result
    return det_result

