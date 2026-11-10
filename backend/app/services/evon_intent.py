"""Structured Intent Processing & Pydantic Validation for Gnani Evon v3.3.

Provides strict allowlisted intent schemas, safe parameter extraction,
JSON parsing with markdown fence stripping, and consequential action guards.
"""
import json
import re
from enum import Enum
from typing import Dict, Any, Optional, List, Union
from pydantic import BaseModel, Field, field_validator, model_validator

from app.core.logging import logger


class EvonSupportedIntent(str, Enum):
    """Strict allowlist of customer shopping and support intents."""

    # PRODUCT DISCOVERY
    SEARCH_PRODUCTS = "search_products"
    GET_PRODUCT_DETAILS = "get_product_details"
    COMPARE_PRODUCTS = "compare_products"
    CHECK_PRODUCT_AVAILABILITY = "check_product_availability"

    # CART MANAGEMENT
    ADD_TO_CART = "add_to_cart"
    REMOVE_FROM_CART = "remove_from_cart"
    UPDATE_CART_QUANTITY = "update_cart_quantity"
    GET_CART = "get_cart"

    # ORDER MANAGEMENT
    TRACK_ORDER = "track_order"
    GET_ORDER_DETAILS = "get_order_details"
    REQUEST_CANCELLATION = "request_cancellation"
    REQUEST_RETURN = "request_return"

    # CUSTOMER SUPPORT
    GENERAL_SUPPORT = "general_support"
    PRODUCT_QUESTION = "product_question"
    DELIVERY_QUESTION = "delivery_question"
    PAYMENT_QUESTION = "payment_question"

    # FALLBACK
    UNKNOWN_INTENT = "unknown_intent"


# Intent Aliases Mapping for model variance and legacy compatibility
INTENT_NORMALIZATION_MAP: Dict[str, EvonSupportedIntent] = {
    # Product search aliases
    "search": EvonSupportedIntent.SEARCH_PRODUCTS,
    "search_products": EvonSupportedIntent.SEARCH_PRODUCTS,
    "product_search": EvonSupportedIntent.SEARCH_PRODUCTS,
    "find_products": EvonSupportedIntent.SEARCH_PRODUCTS,
    "browse": EvonSupportedIntent.SEARCH_PRODUCTS,
    "browse_products": EvonSupportedIntent.SEARCH_PRODUCTS,

    # Product details aliases
    "get_product_details": EvonSupportedIntent.GET_PRODUCT_DETAILS,
    "product_details": EvonSupportedIntent.GET_PRODUCT_DETAILS,
    "details": EvonSupportedIntent.GET_PRODUCT_DETAILS,
    "price_query": EvonSupportedIntent.GET_PRODUCT_DETAILS,
    "specs": EvonSupportedIntent.GET_PRODUCT_DETAILS,

    # Product comparison
    "compare_products": EvonSupportedIntent.COMPARE_PRODUCTS,
    "compare": EvonSupportedIntent.COMPARE_PRODUCTS,
    "comparison": EvonSupportedIntent.COMPARE_PRODUCTS,

    # Product availability
    "check_product_availability": EvonSupportedIntent.CHECK_PRODUCT_AVAILABILITY,
    "availability": EvonSupportedIntent.CHECK_PRODUCT_AVAILABILITY,
    "stock_check": EvonSupportedIntent.CHECK_PRODUCT_AVAILABILITY,
    "in_stock": EvonSupportedIntent.CHECK_PRODUCT_AVAILABILITY,

    # Cart operations
    "add_to_cart": EvonSupportedIntent.ADD_TO_CART,
    "add": EvonSupportedIntent.ADD_TO_CART,
    "cart_add": EvonSupportedIntent.ADD_TO_CART,
    "remove_from_cart": EvonSupportedIntent.REMOVE_FROM_CART,
    "cart_remove": EvonSupportedIntent.REMOVE_FROM_CART,
    "delete_cart_item": EvonSupportedIntent.REMOVE_FROM_CART,
    "update_cart_quantity": EvonSupportedIntent.UPDATE_CART_QUANTITY,
    "update_cart": EvonSupportedIntent.UPDATE_CART_QUANTITY,
    "change_quantity": EvonSupportedIntent.UPDATE_CART_QUANTITY,
    "get_cart": EvonSupportedIntent.GET_CART,
    "view_cart": EvonSupportedIntent.GET_CART,
    "cart": EvonSupportedIntent.GET_CART,
    "cart_view": EvonSupportedIntent.GET_CART,

    # Order operations
    "track_order": EvonSupportedIntent.TRACK_ORDER,
    "tracking": EvonSupportedIntent.TRACK_ORDER,
    "order_status": EvonSupportedIntent.TRACK_ORDER,
    "track": EvonSupportedIntent.TRACK_ORDER,
    "where_is_my_order": EvonSupportedIntent.TRACK_ORDER,
    "get_order_details": EvonSupportedIntent.GET_ORDER_DETAILS,
    "order_details": EvonSupportedIntent.GET_ORDER_DETAILS,

    # Consequential actions
    "request_cancellation": EvonSupportedIntent.REQUEST_CANCELLATION,
    "cancel_order": EvonSupportedIntent.REQUEST_CANCELLATION,
    "cancel": EvonSupportedIntent.REQUEST_CANCELLATION,
    "cancellation": EvonSupportedIntent.REQUEST_CANCELLATION,
    "request_return": EvonSupportedIntent.REQUEST_RETURN,
    "return_request": EvonSupportedIntent.REQUEST_RETURN,
    "return_order": EvonSupportedIntent.REQUEST_RETURN,
    "return": EvonSupportedIntent.REQUEST_RETURN,
    "refund": EvonSupportedIntent.REQUEST_RETURN,
    "exchange": EvonSupportedIntent.REQUEST_RETURN,

    # Support
    "general_support": EvonSupportedIntent.GENERAL_SUPPORT,
    "support": EvonSupportedIntent.GENERAL_SUPPORT,
    "help": EvonSupportedIntent.GENERAL_SUPPORT,
    "greeting": EvonSupportedIntent.GENERAL_SUPPORT,
    "faq": EvonSupportedIntent.GENERAL_SUPPORT,
    "product_question": EvonSupportedIntent.PRODUCT_QUESTION,
    "delivery_question": EvonSupportedIntent.DELIVERY_QUESTION,
    "shipping_policy": EvonSupportedIntent.DELIVERY_QUESTION,
    "payment_question": EvonSupportedIntent.PAYMENT_QUESTION,

    # Unknown
    "unknown": EvonSupportedIntent.UNKNOWN_INTENT,
    "unknown_intent": EvonSupportedIntent.UNKNOWN_INTENT,
}

CONSEQUENTIAL_INTENTS = {
    EvonSupportedIntent.REQUEST_CANCELLATION,
    EvonSupportedIntent.REQUEST_RETURN,
}


class IntentParameters(BaseModel):
    """Validated structured parameters for e-commerce intent routing."""
    category: Optional[str] = Field(default=None, description="Category slug e.g. electronics, audio, fashion")
    query: Optional[str] = Field(default=None, description="Cleaned search keywords")
    brand: Optional[str] = Field(default=None, description="Brand name e.g. HP, Samsung, boAt")
    product_id: Optional[str] = Field(default=None, description="Specific product ID e.g. prod_earbuds_01")
    product_ids: Optional[List[str]] = Field(default=None, description="Product IDs for comparison")
    product_name: Optional[str] = Field(default=None, description="Product name or keywords")
    min_price: Optional[float] = Field(default=None, ge=0.0, description="Minimum price filter in INR")
    max_price: Optional[float] = Field(default=None, ge=0.0, description="Maximum budget in INR")
    quantity: int = Field(default=1, ge=1, le=50, description="Item quantity")
    order_id: Optional[str] = Field(default=None, description="Target order ID formatted as VIQ-XXXXX")
    reason: Optional[str] = Field(default=None, description="Customer stated reason for cancellation or return")

    @field_validator("order_id", mode="before")
    @classmethod
    def normalize_order_id(cls, v: Any) -> Optional[str]:
        if not v or not isinstance(v, str):
            return None
        cleaned = v.strip().upper()
        if "XXXXX" in cleaned or cleaned in ("NONE", "NULL", ""):
            return None
        match = re.search(r"\b(?:VIQ-?)?(\d{5})\b", cleaned)
        if match:
            return f"VIQ-{match.group(1)}"
        return cleaned if cleaned.startswith("VIQ-") else None

    @field_validator("max_price", "min_price", mode="before")
    @classmethod
    def parse_price(cls, v: Any) -> Optional[float]:
        if v is None or v == "":
            return None
        if isinstance(v, (int, float)):
            return float(v) if v >= 0 else None
        if isinstance(v, str):
            # Extract digits from e.g. "₹20,000", "20000 rupees"
            clean = re.sub(r"[^\d.]", "", v)
            try:
                val = float(clean)
                return val if val >= 0 else None
            except ValueError:
                return None
        return None

    @field_validator("category", mode="before")
    @classmethod
    def sanitize_category(cls, v: Any) -> Optional[str]:
        if not v or not isinstance(v, str):
            return None
        clean = v.strip().lower()
        if clean in ("mobile", "mobiles", "phone", "phones", "smartphones", "smartphone", "earbuds", "headphones", "speakers", "audio", "smartwatch", "smartwatches", "gadgets"):
            return "electronics"
        if clean in ("tv", "washing machine", "refrigerator", "appliance", "appliances", "mixer", "grinder", "fryer", "fan", "kitchen"):
            return "appliances"
        if clean in ("clothes", "wear", "shirt", "shirts", "saree", "kurta", "kurti", "kurtis", "apparel"):
            return "fashion"
        if clean in ("watch", "watches", "bag", "bags", "backpack", "backpacks"):
            return "accessories"
        return clean


class EvonStructuredIntent(BaseModel):
    """
    Standard application-level contract for Evon v3.3 structured output.
    Guarantees allowlisted intent, sanitized parameters, response message,
    and consequential confirmation enforcement.
    """
    intent: EvonSupportedIntent = Field(..., description="Allowlisted business intent")
    language: str = Field(default="en", description="BCP-47 or ISO language code")
    parameters: IntentParameters = Field(default_factory=IntentParameters, description="Extracted validated parameters")
    response_message: str = Field(default="", description="Natural language response in user's language")
    requires_confirmation: bool = Field(default=False, description="Whether action requires explicit customer confirmation")

    @field_validator("intent", mode="before")
    @classmethod
    def normalize_intent_value(cls, v: Any) -> EvonSupportedIntent:
        if isinstance(v, EvonSupportedIntent):
            return v
        if isinstance(v, str):
            v_clean = v.strip().lower()
            if v_clean in INTENT_NORMALIZATION_MAP:
                return INTENT_NORMALIZATION_MAP[v_clean]
        return EvonSupportedIntent.UNKNOWN_INTENT

    @field_validator("language", mode="before")
    @classmethod
    def normalize_lang(cls, v: Any) -> str:
        if not v or not isinstance(v, str):
            return "en"
        return v.strip().lower()[:10]

    @model_validator(mode="after")
    def enforce_consequential_confirmation(self) -> "EvonStructuredIntent":
        """Consequential actions like cancellation and return MUST always require explicit confirmation."""
        if self.intent in CONSEQUENTIAL_INTENTS:
            self.requires_confirmation = True
        return self


EVON_INTENT_SYSTEM_PROMPT = """You are Evon v3.3, a sovereign Indic large language model for the VoiceIQ India e-commerce platform.
Your task is to analyze customer shopping speech transcripts across Indian languages (English, Hindi, Kannada, Tamil, Telugu, Malayalam, Bengali, Marathi, Gujarati, Odia, Punjabi) and extract a STRICT JSON object conforming to the schema below.

ALLOWLISTED INTENTS:
- "search_products": Search or browse items (parameters: query, category, brand, min_price, max_price).
- "get_product_details": Inquire about specs, price, features of a specific product.
- "compare_products": Compare two or more products or brands (parameters: product_ids, product_name).
- "check_product_availability": Check stock status of an item.
- "add_to_cart": Add item to shopping cart (parameters: product_name, product_id, quantity).
- "remove_from_cart": Remove item from cart (parameters: product_name, product_id).
- "update_cart_quantity": Update quantity in cart (parameters: product_id, quantity).
- "get_cart": View cart contents and total.
- "track_order": Track delivery or courier status (parameters: order_id formatted as VIQ-XXXXX).
- "get_order_details": View past order summary (parameters: order_id).
- "request_cancellation": Cancel an order (requires_confirmation MUST be true, parameters: order_id, reason).
- "request_return": Return/refund an order (requires_confirmation MUST be true, parameters: order_id, reason).
- "general_support": General store policies (7-day returns, cash on delivery, warranties).
- "product_question": Specific question about a product line.
- "delivery_question": Questions about delivery times or courier partners (Delhivery, Blue Dart).
- "payment_question": Questions regarding UPI, cards, EMI, or refund timelines.
- "unknown_intent": Use when input is unclear or unrelated.

SAFETY & INTEGRITY RULES:
1. Never generate SQL queries, shell commands, or arbitrary code.
2. Never invent fake prices, order IDs, or delivery dates.
3. For cancellations and returns, ALWAYS set "requires_confirmation": true.
4. If an order number is mentioned (e.g. 89214 or VIQ-89214), extract it as "VIQ-XXXXX".
5. Provide a helpful, concise "response_message" in the customer's language.
6. Output ONLY a valid JSON object. No preamble, no markdown formatting outside of JSON.

REQUIRED JSON FORMAT:
{
  "intent": "search_products",
  "language": "en",
  "parameters": {
    "category": "electronics",
    "query": "mobile phones",
    "brand": null,
    "product_id": null,
    "product_ids": null,
    "product_name": null,
    "min_price": null,
    "max_price": 20000,
    "quantity": 1,
    "order_id": null,
    "reason": null
  },
  "response_message": "Here are some mobile phones under ₹20,000.",
  "requires_confirmation": false
}
"""


def parse_evon_json_output(raw_output: str) -> Dict[str, Any]:
    """
    Safely extract and parse JSON from model output, handling code fences,
    extraneous text, or missing brackets.
    """
    if not raw_output or not raw_output.strip():
        return {
            "intent": "unknown_intent",
            "language": "en",
            "parameters": {},
            "response_message": "I could not understand the input.",
            "requires_confirmation": False,
        }

    cleaned = raw_output.strip()

    # Strip markdown code fences if present: ```json ... ```
    fence_match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", cleaned, re.DOTALL)
    if fence_match:
        json_str = fence_match.group(1)
    else:
        # Match outermost curly braces
        brace_match = re.search(r"(\{.*\})", cleaned, re.DOTALL)
        if brace_match:
            json_str = brace_match.group(1)
        else:
            json_str = cleaned

    try:
        return json.loads(json_str)
    except json.JSONDecodeError:
        # Controlled fix for trailing commas or single quotes
        fixed = re.sub(r",\s*([}\]])", r"\1", json_str)
        try:
            return json.loads(fixed)
        except Exception as exc:
            logger.warning(f"Could not parse Evon JSON: {exc}. Raw: {raw_output[:150]}")
            return {
                "intent": "unknown_intent",
                "language": "en",
                "parameters": {},
                "response_message": cleaned[:300],
                "requires_confirmation": False,
            }


def validate_evon_intent(raw_dict: Dict[str, Any], fallback_language: str = "en") -> EvonStructuredIntent:
    """
    Validates a parsed model dictionary against the strict EvonStructuredIntent schema.
    If validation fails, returns safe unknown_intent fallback.
    """
    try:
        # Handle flat parameters format if model returned parameters directly at root
        if "parameters" not in raw_dict and any(
            k in raw_dict for k in ("category", "query", "max_price", "order_id", "product_name")
        ):
            params = {
                k: raw_dict.get(k)
                for k in ("category", "query", "brand", "product_id", "product_ids", "product_name", "min_price", "max_price", "quantity", "order_id", "reason")
            }
            raw_dict["parameters"] = params

        if "language" not in raw_dict or not raw_dict["language"]:
            raw_dict["language"] = fallback_language

        return EvonStructuredIntent.model_validate(raw_dict)
    except Exception as exc:
        logger.error(f"Intent validation failure: {exc}. Falling back to unknown_intent.")
        return EvonStructuredIntent(
            intent=EvonSupportedIntent.UNKNOWN_INTENT,
            language=fallback_language,
            parameters=IntentParameters(),
            response_message="I'm sorry, I couldn't process your request. How can I assist you?",
            requires_confirmation=False,
        )


# Generalized Aliases for Multi-Model Support (Gemini 3.8 Flash, Evon v3.3)
AssistantStructuredIntent = EvonStructuredIntent
SupportedIntent = EvonSupportedIntent
validate_assistant_intent = validate_evon_intent

