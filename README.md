# VoiceIQ India 🇮🇳
### Mini E-Commerce Platform with Multilingual Voice Customer Support Powered by Sovereign Gnani AI
**Gnani AI Challenge 2026 | Senior Developer & Autonomous Engineering Showcase**

---

## 1. Executive Summary & Product Vision

**VoiceIQ India** is a mini online shopping platform inspired by the shopping experiences of **Amazon** and **Flipkart**, integrated with a sovereign **Gnani-powered multilingual voice assistant**.

The platform demonstrates how Indian businesses can eliminate digital friction and make online shopping accessible to the next billion users by allowing customers to:
- Browse and search a rich catalog across **Electronics, Home & Kitchen, Fashion & Apparel, and Accessories**.
- Add products to a persistent shopping cart with automatic **Free Delivery threshold calculation** (orders > ₹999).
- Complete a **simulated checkout** with delivery address validation and demo payment options (UPI, Cards, Net Banking, Cash on Delivery).
- Track their demo orders in real time with visual shipping timelines (`Delhivery Express`, `Blue Dart`, `Ekart Logistics`).
- Interact with a persistent **floating voice assistant** available across all pages.
- Speak in **10 verified Indian languages** (English, Hindi, Tamil, Telugu, Kannada, Malayalam, Marathi, Bengali, Gujarati, Punjabi) using real **Gnani Prisma v2.5 STT**.
- Receive grounded, factual responses based on **actual database inventory and live order data**—not decorative chatbots or fabricated mock responses.
- Safely execute consequential customer actions such as **order cancellations** and **7-day return requests** through a validated 2-step confirmation workflow.
- Hear spoken responses aloud synthesized via **Gnani Timbre TTS** (`Nalini`, `Shivani`, `Yashvi`, `Avinash`).
- Inspect business performance in an **Admin & Voice Intelligence Hub** driven by real database analytics.

---

## 2. Platform Architecture

```
                                      VOICEIQ INDIA
                                            │
        ┌───────────────────────────────────┴───────────────────────────────────┐
        ▼                                                                       ▼
[ Frontend: React 19 + TypeScript + Vite + Tailwind CSS ]           [ Backend: FastAPI (Python 3.11+) + SQLite ]
├── Storefront (Catalog, Deals, Categories, Badges)                 ├── Catalog & Inventory (/api/products, /api/categories)
├── Product Details (Specs, Warranty, 7-Day Returns)                ├── Cart & Checkout Engine (/api/cart, /api/checkout)
├── Cart & Free Delivery Meter (₹999 threshold)                     ├── Order Tracking & Actions (/api/orders, /cancel, /returns)
├── Simulated Checkout (Address, UPI/COD, Tracking ID)              ├── Official Gnani Prisma STT Client (/api/voice/transcribe)
├── Orders View (Shipment Timeline, Delhivery/BlueDart)             ├── Grounded Voice Assistant Dialogue (/api/assistant/message)
├── Floating Multilingual Voice Assistant (Mic, Upload, Text)       ├── 2-Step Consequential Safety Guard (/api/assistant/confirm-action)
└── Admin & Voice Intelligence Hub (/api/admin/analytics)           └── Official Gnani Timbre TTS Client (/api/tts/synthesize)
                                                                                │
                                                                                ▼
                                                            [ Sovereign AI: Gnani.ai Platform & Models ]
                                                            ├── Prisma v2.5 STT (POST https://api.vachana.ai/stt/v3)
                                                            ├── Evon v3.3 Indic LLM (Hugging Face: gnani/gnani-evon-v3.3-30B-A3B)
                                                            └── Timbre v3.0 TTS (POST https://api.vachana.ai/api/v1/tts/inference)
```

---

## 3. Verified Official Gnani AI Integration

The integration with official Gnani.ai technologies has been audited and verified:

| Capability | Flagship Model | API / Runtime Endpoint | Authentication / Framework | Verification Status |
| :--- | :--- | :--- | :--- | :--- |
| **Primary Conversational AI** | **Google Gemini 3.8 Flash** | `google-genai` SDK (`gemini-3.8-flash`) | `GEMINI_API_KEY` | **Integrated (Structured Intent & Safety Gates)** |
| **Speech-to-Text (ASR)** | **Gnani Prisma v2.5** | `POST https://api.vachana.ai/stt/v3` | `X-API-Key-ID: <GNANI_API_KEY>` | **Verified Live** (Request ID: `01a1626e-db73-73db-a363-6de3d1fba7ae`) |
| **Alternative Indic LLM** | **Gnani Evon v3.3** (30B MoE) | OpenAI-Compatible `/v1/chat/completions` | vLLM / SGLang / Remote GPU | **Integrated (Standby)** |
| **Text-to-Speech (TTS)** | **Gnani Timbre v3.0** | `POST https://api.vachana.ai/api/v1/tts/inference` | `X-API-Key-ID: <GNANI_API_KEY>` | **Integrated & Verified** |

### Verified Indian Languages Supported (11 Languages)
1. **English (India)** — `en-IN`
2. **Hindi (हिंदी)** — `hi-IN`
3. **Tamil (தமிழ்)** — `ta-IN`
4. **Telugu (తెలుగు)** — `te-IN`
5. **Kannada (ಕನ್ನಡ)** — `kn-IN`
6. **Malayalam (മലയാളം)** — `ml-IN`
7. **Marathi (मराठी)** — `mr-IN`
8. **Bengali (বাংলা)** — `bn-IN`
9. **Gujarati (ગુજરાતી)** — `gu-IN`
10. **Punjabi (ਪੰਜਾਬੀ)** — `pa-IN`
11. **Odia (ଓଡ଼ିଆ)** — `or-IN`

Detailed endpoint schemas, error handling, and audio specifications are documented in [`docs/GNANI_INTEGRATION.md`](file:///c:/Users/Rakesh%20G/OneDrive/Desktop/GNANI%20AI/docs/GNANI_INTEGRATION.md), [`docs/EVON_INTEGRATION.md`](file:///c:/Users/Rakesh%20G/OneDrive/Desktop/GNANI%20AI/docs/EVON_INTEGRATION.md), and [`docs/EVON_DEPLOYMENT.md`](file:///c:/Users/Rakesh%20G/OneDrive/Desktop/GNANI%20AI/docs/EVON_DEPLOYMENT.md).

---

## 4. Key E-Commerce & Voice Features

### A. Storefront & Product Catalog
- **Top Promotional Banner:** Indian delivery guarantee and sovereign AI voice badges.
- **Search & Filters:** Search by product title, brand, category, price range, and sorting (Featured, Price: Low-to-High, Rating, Newest).
- **Product Cards:** Image with zoom hover effect, price in INR (₹), discount tags, star ratings with verified review counts, stock status, and "Ask AI" voice shortcuts.
- **Product Details Modal:** High-resolution preview, full specifications table (battery, display, motor wattage, fabric), return window guarantee, and direct "Buy Now" simulated checkout.

### B. Persistent Cart & Simulated Checkout
- **Free Delivery Meter:** Live progress bar calculating how much more to add to qualify for free shipping (> ₹999).
- **Stock Validation:** Backend prevents adding more items than available in inventory.
- **Simulated Checkout:** Delivery address inputs (pre-filled with default demo customer Aarav Sharma in Bengaluru), simulated payment selection (UPI, Credit/Debit, Net Banking, Cash on Delivery), order creation with unique ID (e.g., `VIQ-89214`), and immediate tracking number generation.

### C. Demo Orders & Real Delivery Tracking
- **Order Tracking Milestones:** Visual shipment progress bar (Ordered → Packed → In Transit → Out for Delivery → Delivered).
- **Logistics Partners:** Delhivery Express, Blue Dart, Ekart Logistics.
- **Safety-Guarded Actions:**
  - Active orders can be cancelled with a full simulated refund.
  - Delivered orders within 7 days are eligible for return/replacement requests.
  - Expired or already cancelled orders enforce strict policy validation.

### D. Integrated Floating Voice Assistant
- **Global Availability:** Floating circular microphone widget accessible across all pages.
- **3 Interaction Modes:**
  1. *Push-to-Talk:* Browser microphone audio recorded via HTML5 MediaRecorder and streamed to Gnani Prisma STT.
  2. *Audio Upload:* Dropzone for pre-recorded WAV/MP3 files.
  3. *Text Fallback:* Accessible text input for quiet or unsupported environments.
- **Grounded E-Commerce Intents:**
  - `product_search`: "Show me wireless earbuds under 2000 rupees" → displays interactive product cards.
  - `product_details` / `price_query` / `stock_check`: "What is the battery life?" → reads specifications from database.
  - `order_status`: "Where is my order VIQ-89214?" → reads real tracking events from database.
  - `cancel_order`: "Cancel my order" → triggers a 2-step confirmation proposal card before updating database state.
  - `return_request`: "I want to return order VIQ-73910" → checks 7-day return window and proposes return pickup.
- **Spoken Spoken Response:** Generates natural voice audio via Gnani Timbre TTS with in-chat play/pause controls.

### E. Admin & Voice Intelligence Hub (Terminal Portal)
- The Admin & Intelligence Hub is operated directly inside your **terminal** to keep the customer-facing storefront clean and focused on shopping.
- Real-time KPIs computed live from the SQLite database:
  - **Orders & Revenue:** Total Orders, Active Shipments, Delivered Orders, 7-Day Returns, Gross Simulated Revenue (₹).
  - **Voice Intelligence:** Total voice queries, Gnani Prisma STT transcription success rate (%).
  - **Intent Distribution:** Visual ASCII/ANSI breakdown of customer intents (`product_search`, `order_status`, `cancel_order`, etc.).
  - **Multilingual Indian Audio:** Real-time BCP-47 language breakdown (`kn-IN`, `hi-IN`, `en-IN`, `ta-IN`, `te-IN`).
  - **Customer Speech Logs:** Recent voice interactions with timestamps, BCP-47 codes, status, and transcripts in vernacular scripts (Kannada, Hindi, etc.).

---

## 5. Getting Started & Running Separately

This project is organized into two independent, standalone directories:
- **`backend/`** — Python 3.11+ FastAPI service (Port 8000)
- **`client/`** — React 19 + TypeScript + Vite frontend (Port 5000)

```
GNANI AI/
├── backend/                  # Standalone FastAPI Python Backend
│   ├── app/                  # REST API & Gnani AI provider services
│   ├── requirements.txt      # Python dependencies
│   ├── run.py                # One-line backend launcher
│   ├── .env                  # Backend credentials & config
│   ├── voiceiq.db            # SQLite database with seeded catalog
│   └── README.md             # Dedicated backend documentation
├── client/                   # Standalone Vite React Frontend
│   ├── src/                  # React components, hooks, pages, styles
│   ├── package.json          # Frontend dependencies & npm scripts
│   ├── vite.config.ts        # Vite configuration & /api proxy to :8000
│   ├── tsconfig.json         # TypeScript configuration
│   └── README.md             # Dedicated client documentation
├── script/                   # Node.js CLI tools
│   └── admin-hub.ts          # Terminal Admin Hub (TypeScript)
├── admin.py                  # Terminal Admin Hub (Python CLI)
├── run-backend.bat           # Windows 1-click launcher for backend
├── run-client.bat            # Windows 1-click launcher for client
└── README.md
```

---

### Option A: Running in Two Separate Terminals (Recommended)

#### Terminal 1 — Start the Backend Server (Port 8000)
```bash

cd backend
.\.venv\Scripts\activate
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```
- **Backend API**: [http://127.0.0.1:8000](http://127.0.0.1:8000)
- **Interactive Swagger Docs**: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

#### Terminal 2 — Start the Client Frontend (Port 5000)
```bash
cd client

# 1. Start development server
npm run dev
```
- **Storefront & Voice Assistant**: [http://localhost:5000](http://localhost:5000)
- Vite automatically proxies `/api/*` requests to the FastAPI backend at `http://127.0.0.1:8000`.

---

### Option B: Windows 1-Click Launchers
Simply double-click:
1. `run-backend.bat` — opens a terminal running the FastAPI backend on port 8000.
2. `run-client.bat` — opens a terminal running the Vite frontend on port 5000.

---

### Option C: Run from Root using NPM Scripts
From the project root directory:
```bash
# Start backend
npm run backend

# Start client (in another terminal)
npm run client

# Run client typecheck
npm run check:client
```

---

### Option D: Open Admin Portal in Terminal (CLI Commands) 📊

The Admin & Voice Intelligence Portal can be launched anytime in your terminal using either **npm** or **Python**:

#### 1. Using NPM (Node.js / TypeScript)
```bash
# Snapshot report
npm run admin

# Real-time live monitoring dashboard (auto-refreshes every 3 seconds)
npm run admin:watch
```

#### 2. Using Python
```bash
# Snapshot report
python admin.py

# Real-time live monitoring dashboard (auto-refreshes every 3 seconds)
python admin.py --watch

# Direct SQLite offline mode (reads directly from voiceiq.db without server running)
python admin.py --db
```

#### Terminal Dashboard Preview:
```text
  ╔════════════════════════════════════════════════════════════════════════════╗
  ║      VOICEIQ INDIA — ADMIN & VOICE INTELLIGENCE TERMINAL HUB        ║
  ╚════════════════════════════════════════════════════════════════════════════╝
  Source: FastAPI Backend (http://127.0.0.1:8000)  •  Refreshed: 12:02:55 PM 

  KEY PERFORMANCE METRICS
  ──────────────────────────────────────────────────────────────────────────
  Total Orders:    6 (0 active)         Simulated Rev:   ₹8,394.75
  Voice Queries:   69 (100.0% accuracy) 7-Day Returns:   0 requests (1 delivered)
  ──────────────────────────────────────────────────────────────────────────

  📊 CUSTOMER VOICE INTENTS BREAKDOWN
  ORDER DELIVERY & TRACKING ██░░░░░░░░░░░░░░░░░░  11% (2)
  SEARCH PRODUCTS           █████████████████░░░  84% (16)
  CANCEL ORDER              ██████░░░░░░░░░░░░░░  32% (6)
  GENERAL SUPPORT           █████████████████░░░  84% (16)
  TRACK ORDER               ████████████████████ 100% (19)
  GET PRODUCT DETAILS       ███░░░░░░░░░░░░░░░░░  16% (3)

  🌐 MULTILINGUAL INDIAN AUDIO DISTRIBUTION (BCP-47)
  hi-IN                     █░░░░░░░░░░░░░░░░░░░   6% (2 recordings)
  en-IN                     ██████████████████░░  91% (30 recordings)
  kn-IN                     ████████████████████ 100% (33 recordings)
  te-IN                     ██░░░░░░░░░░░░░░░░░░   9% (3 recordings)

  🎙 RECENT CUSTOMER VOICE SUPPORT LOGS
  TIMESTAMP          LANG       STATUS       TRANSCRIPT
  ──────────────────────────────────────────────────────────────────────────
  2026-10-27 05:23   en-IN      COMPLETED    "Track my order"
  2026-10-26 11:54   kn-IN      COMPLETED    "ನಾನು ಆರ್ಡರನ್ನು ಕ್ಯಾನ್ಸಲ್ ಮಾಡಬೇಕು"
  2026-10-26 11:53   kn-IN      COMPLETED    "ನನಗೆ 1 ಬಟ್ಟೆ ಬೇಕು"
  2026-10-26 10:44   en-IN      COMPLETED    "Earbuds under ₹2000"
  ──────────────────────────────────────────────────────────────────────────
```

---

## 6. Challenge Submission Checklist

- [x] Full source code committed to repository.
- [x] Genuine Gnani AI API integration for core voice speech recognition (`https://api.vachana.ai/stt/v3`).
- [x] End-to-end working e-commerce storefront with catalog, details, cart, checkout, and tracking.
- [x] Multilingual voice assistant with push-to-talk, audio upload, and text fallback across 10 Indian languages.
- [x] Consequential action safety confirmation for cancellations and returns.
- [x] Database-backed admin analytics dashboard in terminal (`npm run admin` / `python admin.py`).
- [x] Zero API keys or secrets exposed in frontend or Git tracking.
- [x] Complete documentation:
  - [`docs/CHALLENGE_REQUIREMENTS.md`](file:///c:/Users/Rakesh%20G/OneDrive/Desktop/GNANI%20AI/docs/CHALLENGE_REQUIREMENTS.md)
  - [`docs/ARCHITECTURE.md`](file:///c:/Users/Rakesh%20G/OneDrive/Desktop/GNANI%20AI/docs/ARCHITECTURE.md)
  - [`docs/EVON_DEPLOYMENT.md`](file:///c:/Users/Rakesh%20G/OneDrive/Desktop/GNANI%20AI/docs/EVON_DEPLOYMENT.md)
  - [`docs/EVON_INTEGRATION.md`](file:///c:/Users/Rakesh%20G/OneDrive/Desktop/GNANI%20AI/docs/EVON_INTEGRATION.md)
  - [`docs/GNANI_INTEGRATION.md`](file:///c:/Users/Rakesh%20G/OneDrive/Desktop/GNANI%20AI/docs/GNANI_INTEGRATION.md)
  - [`docs/IMPLEMENTATION_PLAN.md`](file:///c:/Users/Rakesh%20G/OneDrive/Desktop/GNANI%20AI/docs/IMPLEMENTATION_PLAN.md)
- [x] Complete test suite passing: `pytest backend/tests` (45 passed, 1 skipped real inference test pending remote GPU deployment).
