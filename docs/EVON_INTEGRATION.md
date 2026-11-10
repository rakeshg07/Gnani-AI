# VoiceIQ India — Gnani Evon v3.3 Sovereign Indic LLM Integration Guide

## 1. Overview & Model Architecture

**VoiceIQ India** connects the sovereign **Gnani Prisma Speech-to-Text (STT)** pipeline to **Gnani Evon v3.3**, an open-weights large language model optimized for Indic conversational intelligence, multilingual understanding, and structured intent routing.

- **Hugging Face Model Repository:** [gnani/gnani-evon-v3.3-30B-A3B on Hugging Face](https://huggingface.co/gnani/gnani-evon-v3.3-30B-A3B)
- **Official Model Card / Serving Alias:** `gnani/gnani-evon-v3.3`
- **Runtime Served Model Name:** `evon` (configurable via `EVON_MODEL_NAME`)
- **Model Developer:** Gnani.ai
- **Architecture Type:** Mamba2-Transformer Hybrid Mixture of Experts (MoE)
- **Total Parameters:** 30 Billion
- **Active Parameters:** ~3.3 Billion active per token
- **Maximum Context Length:** 131,072 tokens (128K)
- **Native Precision:** BF16
- **Supported Languages (11):** English (`en`), Hindi (`hi`), Kannada (`kn`), Tamil (`ta`), Telugu (`te`), Malayalam (`ml`), Bengali (`bn`), Marathi (`mr`), Gujarati (`gu`), Odia (`or`), and Punjabi (`pa`).

---

## 2. End-to-End Voice-to-Intent Pipeline Architecture

The unified e-commerce conversational pipeline operates as follows:

```
[Customer Speech / Audio Upload]
               │
               ▼
[Gnani Prisma v2.5 STT (api.vachana.ai/stt/v3)]
  - Audio Format Validation & PCM/WAV/WebM decoding
  - Multi-dialect Indic acoustic decoding
               │
               ▼
   [Recognized Transcript]
               │
               ▼
 [Evon v3.3 Open-Weight LLM Inference Server]
  - OpenAI-compatible /v1/chat/completions (vLLM / SGLang)
  - Temperature: 0.6, Top-P: 0.95
  - Thinking Trace Disabled for Deterministic JSON:
    chat_template_kwargs: {"enable_thinking": false}
               │
               ▼
[Pydantic Structured Output Validation (app.services.evon_intent)]
  - Validates `EvonStructuredIntent`
  - Rejects unsupported intents & sanitizes parameters
  - Enforces `requires_confirmation=True` on consequential actions
               │
               ▼
[FastAPI Action Handler (VoiceAssistantOrchestrator)]
  - search_products          ──► ECommerceService.get_products()
  - get_product_details      ──► ECommerceService.get_product_by_id()
  - compare_products         ──► ECommerceService comparison specs & diff
  - check_product_availability─► ECommerceService stock status check
  - add_to_cart              ──► ECommerceService.add_to_cart()
  - remove_from_cart         ──► ECommerceService.remove_from_cart()
  - get_cart                 ──► ECommerceService.get_or_create_cart()
  - track_order              ──► ECommerceService.get_order_by_tracking_or_id()
  - cancel_order             ──► Propose AssistantActionProposal (Requires User Confirmation)
  - return_request           ──► Propose AssistantActionProposal (Requires User Confirmation)
  - general_support          ──► Returns verified store policies & FAQs
               │
               ▼
   [Authoritative Database Records]
  - SQLite (Products, Stock, INR Prices, Orders, Deliveries)
  - Zero hallucination: all returned entities exist in DB
               │
               ▼
[Optional: Gnani Timbre TTS (api.vachana.ai/api/v1/tts/inference)]
               │
               ▼
[Frontend Response Cards & Audio Stream]
```

---

## 3. Supported E-Commerce Intents & Schemas

| Intent | Description | Consequential Action | Database Action |
| :--- | :--- | :---: | :--- |
| `search_products` | Searches catalog with keyword, category, and INR price budget filters | ❌ No | Queries `products` table |
| `get_product_details` | Inquires about specs, stock, pricing, discount, warranty | ❌ No | Fetches product specifications |
| `compare_products` | Compares 2 products by specs, price, rating, and stock | ❌ No | Queries and diffs product specs |
| `check_product_availability` | Checks stock quantity and estimated delivery | ❌ No | Verifies stock level in inventory |
| `add_to_cart` | Adds items to customer cart with quantity (1-10) | ❌ No | Updates `cart_items` table |
| `remove_from_cart` | Removes items from active shopping cart | ❌ No | Updates `cart_items` table |
| `get_cart` | Views current cart, item quantities, free shipping threshold (₹999) | ❌ No | Computes cart totals |
| `track_order` | Live courier tracking (Delhivery Express, Blue Dart) by order ID | ❌ No | Fetches real order timeline |
| `cancel_order` | Requests order cancellation | ⚠️ **YES** | Proposes confirmation; commits only on explicit confirm |
| `return_request` | Requests 7-day return or exchange | ⚠️ **YES** | Proposes confirmation; commits only on explicit confirm |
| `general_support` | Store policies, free shipping, cash on delivery, warranties | ❌ No | Returns verified policy text |

### Required Structured JSON Contract
```json
{
  "intent": "search_products",
  "language": "en",
  "parameters": {
    "category": "mobile",
    "max_price": 20000,
    "brand": null
  },
  "response_message": "Here are some phones under ₹20,000.",
  "requires_confirmation": false
}
```

Validated by Pydantic schema: `backend/app/services/evon_intent.py`.

---

## 4. Backend Configuration Settings

| Setting | Type | Default | Description |
| :--- | :--- | :--- | :--- |
| `EVON_ENABLED` | bool | `false` | Master switch. Keep false until remote GPU server is configured |
| `EVON_HF_REPO_ID` | str | `gnani/gnani-evon-v3.3-30B-A3B` | Canonical Hugging Face model repository |
| `EVON_BASE_URL` | str | `""` | Remote inference endpoint URL (e.g. `https://gpu.example.com/v1`) |
| `EVON_API_KEY` | str | `""` | Bearer auth token for secured inference servers |
| `EVON_MODEL_NAME` | str | `evon` | Model name exposed by vLLM `--served-model-name` |
| `EVON_TIMEOUT_SECONDS`| float | `60.0` | Timeout before falling back gracefully |
| `EVON_MAX_TOKENS` | int | `512` | Token generation budget for intent JSON |
| `EVON_TEMPERATURE` | float | `0.6` | Generation temperature (official model card) |
| `EVON_TOP_P` | float | `0.95` | Top-P sampling threshold (official model card) |
| `EVON_ENABLE_THINKING`| bool | `false` | Disabled to produce direct, valid JSON |

---

## 5. API Endpoints

- **`POST /api/assistant/voice`**: Multipart audio upload (`file`, `current_page`, `language_code`, `product_id`, `order_id`). Runs Prisma STT, passes recognized transcript to Evon, executes database business action, optionally synthesizes Timbre TTS audio.
- **`POST /api/assistant/chat`**: Direct text chat (`message`, `current_page`, `language_code`, etc.). Directly invokes Evon v3.3 reasoning.
- **`POST /api/assistant/process-transcript`**: JSON endpoint for pre-transcribed text (`transcript`, `language`, `context`).
- **`POST /api/assistant/confirm-action`**: Confirms a proposed consequential action (`action`, `target_id`).
- **`GET /api/assistant/health`**: Comprehensive health check reporting Evon configuration, remote server availability, STT/TTS status, and database health.
- **`GET /api/assistant/evon/status`**: Detailed Evon status, architecture parameters, and supported languages.

---

## 6. Remote GPU Deployment

For instructions on provisioning remote GPU instances (NVIDIA A100 / H100 / L40S) and serving Evon v3.3 with vLLM or SGLang, see [EVON_DEPLOYMENT.md](EVON_DEPLOYMENT.md).
