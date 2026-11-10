# VoiceIQ India — System Architecture

VoiceIQ India is an enterprise-grade multilingual e-commerce voice and text shopping assistant tailored for the Indian retail ecosystem. It couples Gnani Prisma Speech-to-Text (STT) and Gnani Timbre Text-to-Speech (TTS) with high-speed Indic conversational intelligence powered by **Google Gemini 3.8 Flash** (primary) and **Gnani Evon v3.3** (alternative open-weight 30B MoE model).

---

## 1. High-Level System Architecture

```
                       ┌──────────────────────┐
                       │       CUSTOMER       │
                       └──────────┬───────────┘
                                  │
                    Voice (Audio) │ Text / Click
                                  ▼
                    ┌─────────────────────────┐
                    │ REACT + VITE FRONTEND   │
                    │  - VoiceAssistantModal  │
                    │  - Product Grid / Cart  │
                    └────────────┬────────────┘
                                 │ HTTP POST
                                 ▼
                    ┌─────────────────────────┐
                    │     FASTAPI BACKEND     │
                    │   (/api/assistant/...)  │
                    └────────────┬────────────┘
                                 │
                 ┌───────────────┴───────────────┐
                 │ Audio input                   │ Direct text / transcript
                 ▼                               │
      ┌──────────────────────┐                   │
      │   GNANI PRISMA STT   │                   │
      │  (Speech-to-Text)    │                   │
      └──────────┬───────────┘                   │
                 │ Recognized transcript         │
                 └───────────────┬───────────────┘
                                 ▼
                 ┌───────────────────────────────┐
                 │   VOICE ASSISTANT ROUTER      │
                 │   (AI_PROVIDER: gemini/evon)  │
                 └───────┬───────────────┬───────┘
                         │               │
       AI_PROVIDER=gemini│               │AI_PROVIDER=evon
                         ▼               ▼
        ┌──────────────────────┐   ┌──────────────────────┐
        │  GEMINI 3.8 FLASH    │   │   GNANI EVON v3.3    │
        │ (google-genai SDK)   │   │  (30B MoE vLLM/SGLang│
        └──────────┬───────────┘   └──────────┬───────────┘
                   │                          │
                   └─────────────┬────────────┘
                                 │ Structured Intent (JSON)
                                 ▼
                 ┌───────────────────────────────┐
                 │ INTENT VALIDATION & ROUTING   │
                 │   - Intent Allowlist          │
                 │   - Parameter Normalization   │
                 │   - Safety & Injection Shield │
                 │   - Consequential Action Gate │
                 │   - Deterministic Fallback    │
                 └───────────────┬───────────────┘
                                 │
                                 ▼
                 ┌───────────────────────────────┐
                 │  ECOMMERCE BUSINESS SERVICES  │
                 │   - Product Discovery         │
                 │   - Product Comparison        │
                 │   - Cart Management           │
                 │   - Order Tracking & Status   │
                 │   - 2-Step Consequential Gate │
                 └───────┬───────────────┬───────┘
                         │               │
                         ▼               ▼
                 ┌──────────────┐ ┌──────────────┐
                 │ PRODUCT DB   │ │   ORDER DB   │
                 │   (SQLite)   │ │   (SQLite)   │
                 └───────┬──────┘ └──────┬───────┘
                         │ Grounded Data │
                         └───────┬───────┘
                                 ▼
                 ┌───────────────────────────────┐
                 │   RESPONSE BUILDER & LOCALES  │
                 │  (11 Indic Languages Support) │
                 └───────────────┬───────────────┘
                                 │
                 ┌───────────────┴───────────────┐
                 │ Text & Data                   │ Spoken Audio (Optional)
                 ▼                               ▼
       ┌───────────────────┐           ┌───────────────────┐
       │  REACT FRONTEND   │           │ GNANI TIMBRE TTS  │
       │   UI Response     │           │ (Speech Synthesis)│
       └───────────────────┘           └───────────────────┘
```

---

## 2. Key Architectural Pillars

### 1. Dual-AI Intelligence with Pluggable Routing (`AI_PROVIDER`)
- **Primary Provider**: **Google Gemini 3.8 Flash (`gemini-3.8-flash`)** using the official modern `google-genai` SDK. Delivers sub-second latency, Indic script comprehension, and schema-constrained JSON extraction.
- **Alternative Provider**: **Gnani Evon v3.3 (`gnani/gnani-evon-v3.3-30B-A3B`)**, sovereign 30B Mixture-of-Experts (MoE) hosted via remote vLLM / SGLang.
- **Deterministic Semantic Fallback**: If LLM API keys or endpoints are unavailable, requests automatically fall back to rule-based keyword & entity extraction with clear diagnostic labeling.

### 2. Strict LLM Boundary & Grounded Execution
- The LLM **never** has direct access to execute raw SQL, shell commands, or arbitrary network calls.
- The LLM only classifies the intent and extracts entities into a typed Pydantic schema (`AssistantStructuredIntent`).
- Authoritative execution is performed exclusively by backend SQLAlchemy services querying SQLite (`voiceiq.db`).

### 3. Consequential Action Security Guard (2-Step Verification)
- Critical actions (cancellations and returns) cannot be executed in a single shot by the LLM or client boolean flags.
- **Step 1 (Proposal)**: Backend validates authenticated customer ownership and order eligibility, then creates a server-side `PendingAction` record with a cryptographically secure token (`secrets.token_urlsafe(32)`) and a 5-minute expiration.
- **Step 2 (Execution)**: The customer must submit the token to `POST /api/assistant/confirm-action`. The backend revalidates customer identity, order status, and atomicity within a database transaction before marking the token as consumed to prevent replay attacks.

### 4. End-to-End Multilingual Speech Pipeline
- **Speech-to-Text (STT)**: Browser audio (WebM) is transcoded to 16kHz 16-bit PCM WAV and sent to **Gnani Prisma v2.5** (`https://api.vachana.ai/stt/v3`).
- **Text-to-Speech (TTS)**: Response text is optionally synthesized aloud using **Gnani Timbre v3.0** (`https://api.vachana.ai/api/v1/tts/inference`).
- **11 Supported Indian Languages**: English, Hindi, Kannada, Tamil, Telugu, Malayalam, Bengali, Marathi, Gujarati, Punjabi, and Odia.

---

## 3. Technology Stack & Component Matrix

| Layer | Technology | Primary Functionality |
| :--- | :--- | :--- |
| **Frontend** | React 18, TypeScript, Vite, Tailwind CSS, Lucide Icons | Responsive e-commerce UI, product catalog, cart, simulated checkout, interactive voice modal |
| **Backend Framework** | FastAPI (Python 3.11+), Uvicorn | High-performance asynchronous REST API, route handlers, session authentication |
| **Primary LLM** | Google Gemini 3.8 Flash (`google-genai` SDK) | Multilingual Indic conversational reasoning and structured JSON intent extraction |
| **Alternative LLM** | Gnani Evon v3.3 (30B MoE via vLLM/SGLang) | Sovereign Indic open-weight model integration |
| **Speech STT/TTS** | Gnani Prisma STT & Gnani Timbre TTS | Audio speech recognition and regional speech generation |
| **Data Validation** | Pydantic v2 | Strict request/response schemas, JSON schema enforcement, sanitization |
| **ORM & Database** | SQLAlchemy 2.0, SQLite (`voiceiq.db`) | ACID transactional operations across products, categories, orders, carts, and pending actions |
| **Security & Auth** | HMAC-SHA256, Python `secrets` | Cryptographically signed customer session tokens, 5-minute single-use confirmation tokens |
| **Audio Processing** | Python `wave`, `audioop` | Browser audio transcoding, WAV 16kHz PCM normalization |
| **Testing** | Pytest, pytest-asyncio, HTTPX | 58 unit and integration tests covering security, clients, intent schemas, and fallback |
