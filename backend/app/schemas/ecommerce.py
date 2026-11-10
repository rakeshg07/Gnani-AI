"""Pydantic schemas for E-Commerce entities and voice assistant interactions."""
from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field


# --- Categories ---
class CategoryOut(BaseModel):
    id: str
    name: str
    slug: str
    icon: str
    description: Optional[str] = None

    class Config:
        from_attributes = True


# --- Products ---
class ProductOut(BaseModel):
    id: str
    title: str
    slug: str
    category_id: str
    price: float
    original_price: float
    rating: float
    reviews_count: int
    stock: int
    image_url: str
    badge: Optional[str] = None
    description: str
    specifications: Dict[str, Any] = Field(default_factory=dict)
    return_window_days: int
    is_featured: bool
    created_at: datetime

    class Config:
        from_attributes = True


class ProductListResponse(BaseModel):
    items: List[ProductOut]
    total: int
    page: int
    page_size: int
    total_pages: int


# --- Cart ---
class CartItemIn(BaseModel):
    product_id: str
    quantity: int = Field(default=1, ge=1)


class CartItemUpdate(BaseModel):
    quantity: int = Field(ge=0)


class CartItemOut(BaseModel):
    id: str
    product_id: str
    product: ProductOut
    quantity: int
    unit_price: float
    total_price: float

    class Config:
        from_attributes = True


class CartOut(BaseModel):
    id: str
    customer_id: str
    items: List[CartItemOut]
    subtotal: float
    shipping_fee: float
    tax_amount: float
    total_amount: float
    item_count: int


# --- Checkout & Orders ---
class ShippingAddress(BaseModel):
    name: str
    phone: str
    address_line: str
    city: str
    state: str
    postal_code: str


class CheckoutIn(BaseModel):
    customer_id: Optional[str] = "cust_demo_001"
    shipping_address: Optional[ShippingAddress] = None
    payment_method: str = "UPI (Simulated)"


class TrackingEvent(BaseModel):
    status: str
    title: str
    timestamp: str
    location: str
    description: str


class OrderItemOut(BaseModel):
    id: str
    product_id: str
    product_title: str
    product_image: str
    unit_price: float
    quantity: int
    total_price: float

    class Config:
        from_attributes = True


class ReturnRequestOut(BaseModel):
    id: str
    order_id: str
    reason: str
    status: str
    refund_amount: float
    created_at: datetime
    resolution_notes: Optional[str] = None

    class Config:
        from_attributes = True


class OrderOut(BaseModel):
    id: str
    customer_id: str
    status: str  # processing, shipped, out_for_delivery, delivered, cancelled
    subtotal: float
    shipping_fee: float
    tax_amount: float
    total_amount: float
    payment_method: str
    payment_status: str
    shipping_address: Dict[str, Any]
    tracking_number: str
    carrier: str
    expected_delivery: Optional[datetime] = None
    delivered_at: Optional[datetime] = None
    cancelled_at: Optional[datetime] = None
    cancellation_reason: Optional[str] = None
    tracking_events: List[Dict[str, Any]] = Field(default_factory=list)
    created_at: datetime
    items: List[OrderItemOut] = Field(default_factory=list)
    returns: List[ReturnRequestOut] = Field(default_factory=list)
    can_cancel: bool = False
    can_return: bool = False

    class Config:
        from_attributes = True


class OrderListResponse(BaseModel):
    items: List[OrderOut]
    total: int


class CancelOrderIn(BaseModel):
    reason: Optional[str] = "Customer requested cancellation via VoiceIQ Support"


class ReturnRequestIn(BaseModel):
    reason: str = Field(min_length=3)


# --- Voice Assistant & Dialogue ---
class AssistantActionProposal(BaseModel):
    action: str  # e.g. "cancel_order", "create_return", "add_to_cart"
    target_id: str  # order_id or product_id
    confirmation_prompt: str
    details: Dict[str, Any] = Field(default_factory=dict)
    confirmation_token: Optional[str] = None
    expires_at: Optional[datetime] = None


class AssistantMessageIn(BaseModel):
    message: str = Field(min_length=1)
    current_page: str = "home"  # "home", "product_detail", "cart", "orders", "checkout"
    product_id: Optional[str] = None
    order_id: Optional[str] = None
    language_code: str = "en-IN"
    synthesize_audio: bool = False
    conversation_id: Optional[str] = None


class AssistantMessageOut(BaseModel):
    success: bool = True
    reply_text: str
    intent: str
    detected_language: str
    action_pending_confirmation: Optional[AssistantActionProposal] = None
    products: Optional[List[ProductOut]] = None
    order: Optional[OrderOut] = None
    cart: Optional[CartOut] = None
    audio_base64: Optional[str] = None
    conversation_id: str
    llm_provider: Optional[str] = "gnani-evon-v3.3"
    intent_confidence: Optional[float] = 1.0
    reasoning: Optional[str] = None
    consequential_action_required: bool = False

    # Section 14 standardized API fields
    transcript: Optional[str] = None
    language: Optional[str] = None
    message: Optional[str] = None
    data: Optional[Dict[str, Any]] = None
    requires_confirmation: bool = False


class ProcessTranscriptIn(BaseModel):
    transcript: str = Field(..., min_length=1, description="Recognized speech transcript or text input")
    language: Optional[str] = Field(default="en-IN", description="Target or detected Indian language code")
    current_page: Optional[str] = Field(default="home", description="Active UI context")
    product_id: Optional[str] = Field(default=None, description="Active product being viewed")
    order_id: Optional[str] = Field(default=None, description="Active order context")
    synthesize_audio: bool = Field(default=False, description="Optionally synthesize Timbre TTS response")


class ChatIn(BaseModel):
    message: str = Field(..., min_length=1, description="Customer text message")
    language: Optional[str] = Field(default="en-IN", description="Language code")
    current_page: Optional[str] = Field(default="home", description="Current page context")
    product_id: Optional[str] = Field(default=None, description="Active product ID")
    order_id: Optional[str] = Field(default=None, description="Active order ID")
    synthesize_audio: bool = Field(default=False, description="Synthesize TTS speech")


class ConfirmActionIn(BaseModel):
    conversation_id: Optional[str] = None
    action: Optional[str] = None  # "cancel_order", "create_return", "add_to_cart"
    target_id: Optional[str] = None
    confirmed: bool = True
    reason: Optional[str] = None
    confirmation_token: Optional[str] = None
