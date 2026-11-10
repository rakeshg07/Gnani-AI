# VoiceIQ India — E-Commerce Migration & Implementation Plan
## Senior Engineer Mode | Gnani AI Challenge 2026

**Project:** VoiceIQ India  
**Vision:** Mini Indian e-commerce platform inspired by Amazon and Flipkart with integrated sovereign Gnani-powered multilingual voice customer support.  
**Core Models:** Gnani Prisma v2.5 (Speech-to-Text / ASR), Gnani Timbre v3.0 (Text-to-Speech), VoiceIQ Grounded E-Commerce Intent Engine.

---

## 1. Migration Architecture Overview

The VoiceIQ India platform is structured as a decoupled full-stack e-commerce and voice AI architecture:

```
[ Frontend: React 19 + TypeScript + Vite + Tailwind CSS ]
   ├── Storefront (Catalog, Product Details, Filters, Search)
   ├── Cart & Simulated Checkout (Address, Demo Payment, Orders)
   ├── Order History & Live Delivery Tracking
   ├── Floating Multilingual Voice Assistant (Mic, Upload, Text, Spoken TTS)
   └── Admin Voice & Store Analytics Dashboard
         │
         ▼  (Vite Proxy /api -> :8000)
[ Backend: FastAPI (Python 3.11+) + SQLAlchemy + SQLite (voiceiq.db) ]
   ├── /api/products, /api/categories (Catalog & Inventory)
   ├── /api/cart, /api/checkout (Cart & Order Processing)
   ├── /api/orders, /api/orders/{id}/cancel, /api/orders/{id}/returns
   ├── /api/voice/transcribe (Official Gnani Prisma STT proxy)
   ├── /api/assistant/message (Intent parsing & database grounding)
   ├── /api/assistant/confirm-action (2-step safety confirmation)
   ├── /api/tts/synthesize (Official Gnani Timbre TTS proxy)
   └── /api/admin/analytics (Store & voice intelligence metrics)
         │
         ▼
[ Sovereign AI Provider: Gnani.ai Vachana Platform ]
   ├── Prisma v2.5 (POST https://api.vachana.ai/stt/v3)
   └── Timbre v3.0 (POST https://api.vachana.ai/api/v1/tts/inference)
```

---

## 2. Milestones & Execution Phases

### Phase 1: Audit, Requirements & Challenge Compliance [COMPLETED]
- [x] Full repository audit: verified existing FastAPI backend, React frontend, SQLite persistence, and Gnani client.
- [x] Documented challenge requirements in `docs/CHALLENGE_REQUIREMENTS.md`.
- [x] Executed live smoke test against `https://api.vachana.ai/stt/v3` with developer key `vach_...` (Success, Request ID: `01a1626e-db73-73db-a363-6de3d1fba7ae`).
- [x] Verified existing 21 unit/integration tests and TypeScript build.

### Phase 2: E-Commerce Storefront Foundation (Backend & Database) [COMPLETED]
- [x] Designed SQLAlchemy schemas:
  - `Product`: ID, title, description, category_id, price, original_price, rating, reviews_count, stock, image_url, specifications (JSON), return_window_days.
  - `Category`: ID, name, slug, icon, description.
  - `DemoCustomer`: ID, name, email, phone, address, city, state, postal_code.
  - `Cart` & `CartItem`: Persistent demo customer cart with quantity and price validation.
  - `Order` & `OrderItem`: Unique order number (e.g. `VIQ-89214`), status (`processing`, `shipped`, `out_for_delivery`, `delivered`, `cancelled`), shipping details, estimated delivery date, tracking carrier, tracking timeline.
  - `ReturnRequest`: ID, order_id, reason, status (`requested`, `approved`, `rejected`), refund_amount, created_at.
- [x] Implemented backend API routes:
  - `GET /api/products` (search, category filter, price filter, sorting, pagination).
  - `GET /api/products/{id}`.
  - `GET /api/categories`.
  - `GET /api/cart`, `POST /api/cart/items`, `PATCH /api/cart/items/{id}`, `DELETE /api/cart/items/{id}`.
  - `POST /api/checkout` (creates demo order from cart with realistic validation).
  - `GET /api/orders`, `GET /api/orders/{id}`.
  - `POST /api/orders/{id}/cancel` (cancellation policy validation).
  - `POST /api/orders/{id}/returns` (return eligibility window validation).
- [x] Seeded realistic Indian e-commerce catalog (Smartphones, Wireless Earbuds, Smartwatches, Kitchen Appliances, Ethnic Wear, Travel Gear) with demo orders in varying tracking states.

### Phase 3: E-Commerce Voice Assistant Orchestration (Backend) [COMPLETED]
- [x] Implemented `POST /api/voice/transcribe`:
  - Validates audio using magic bytes and size check.
  - Passes audio directly to `GnaniSpeechClient.transcribe_audio`.
  - Returns raw transcript, duration, confidence, and request ID.
- [x] Implemented `POST /api/assistant/message`:
  - Accepts user voice transcript or direct text.
  - Ingests page context (current route, active product ID, order ID).
  - Classifies intent using validated schema (`product_search`, `product_details`, `price_query`, `stock_check`, `cart_add`, `order_status`, `delivery_tracking`, `cancel_order`, `return_eligibility`, `refund_status`, `shipping_policy`).
  - Executes grounded database queries (actual product prices, stock, real order status).
  - Produces structured action proposals for consequential operations (`action_pending_confirmation`).
  - Synthesizes spoken audio via Gnani Timbre TTS when enabled.
- [x] Implemented `POST /api/assistant/confirm-action`:
  - Validates confirmation token, executes state mutation (order cancellation or return creation), and returns updated entity.

### Phase 4: Storefront Frontend Experience [COMPLETED]
- [x] Modern Indian e-commerce layout inspired by Amazon & Flipkart:
  - `StoreHeader`: delivery location, category search bar, language pill, orders link, cart drawer badge, and voice trigger.
  - `HeroBanner`: promotional banners ("Great Indian Voice Sale", "Shop in Hindi, Tamil, Telugu, Kannada & more").
  - Category navigation cards (Electronics, Home Appliances, Fashion, Accessories).
  - Product catalog grid with filter drawer (price sliders, brand, stock, rating).
  - `ProductDetailModal`: high-res photos, specs table, return policy badge, quantity selector, and "Ask Assistant about this product".
  - `CartDrawer`: interactive shopping cart with item quantity controls, delivery cost calculation, and free delivery progress.
  - `CheckoutModal`: address selection, simulated UPI/Card/COD options, and realistic order confirmation.
  - `OrdersView`: tracking timeline with live delivery progress steps, delivery date, cancel button, and return button.

### Phase 5: Floating Multilingual Voice Assistant [COMPLETED]
- [x] Persistent floating microphone button across all views.
- [x] Push-to-talk recording with MediaRecorder and recording timer.
- [x] Audio file upload and text fallback.
- [x] Language selector with 10 verified Indian languages.
- [x] Dynamic in-chat interactive cards (Product recommendations, Order tracking status card, Action confirmation card).
- [x] Spoken response playback with audio player controls.

### Phase 6: Admin Dashboard & Support Analytics [COMPLETED]
- [x] Implemented `AdminAnalyticsView` driven by `/api/admin/analytics`:
  - Total store orders and simulated revenue.
  - Voice query metrics: volume, transcription accuracy, intent distribution, language breakdown.
  - Support conversation audit log.
- [x] Header toggle to switch seamlessly between "Storefront" and "Admin Hub".

### Phase 7: Automated Testing, Hardening & Documentation [COMPLETED]
- [x] Pytest suite: 31 automated tests passing at 100% across catalog, cart, checkout, orders, returns, cancellations, and assistant actions.
- [x] TypeScript verification (`npm run check`): 0 errors.
- [x] Production build verification (`npm run build`): compiled successfully in 21s.
- [x] Updated `README.md`, `docs/CHALLENGE_REQUIREMENTS.md`, `docs/GNANI_INTEGRATION.md`.
