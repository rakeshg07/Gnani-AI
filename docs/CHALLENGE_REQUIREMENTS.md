# Gnani AI Challenge 2026 — Official Challenge Requirements
## VoiceIQ India | Multilingual Voice Customer Support for E-Commerce

**Document Status:** Verified & Active  
**Challenge Edition:** Gnani AI Challenge 2026  
**Project Name:** VoiceIQ India  
**Target Category:** Sovereign Multilingual Voice AI for Indian E-Commerce  

---

## 1. Challenge Overview & Submission Brief

The **Gnani AI Challenge 2026** invites developers and engineering teams to build practical, sovereign voice-first applications powered by **Gnani.ai**'s voice intelligence models and APIs (the **Vachana** platform).

### Core Mission
Demonstrate how real-world Indian businesses can eliminate digital friction, bridge language barriers, and automate customer care through high-accuracy regional language speech recognition, conversational intelligence, and natural voice synthesis.

### Official Submission Checklist
- [x] **Genuine Gnani AI API Integration:** Must use live, non-mocked Gnani API endpoints (`https://api.vachana.ai`) for core speech processing.
- [x] **Verified Account Credentials:** Server-side credential management via `GNANI_API_KEY` (X-API-Key-ID authentication).
- [x] **Working Real-World Application:** A functional, end-to-end product (VoiceIQ India: Mini e-commerce platform inspired by Amazon and Flipkart with integrated voice customer support).
- [x] **Multi-Language Support:** Verification across Indian languages (English-India, Hindi, Tamil, Telugu, Kannada, Malayalam, Marathi, Bengali, Gujarati, Punjabi).
- [x] **End-to-End Business Workflows:** Voice-driven product search, order lookup, delivery tracking, and safe, confirmed cancellations and returns.
- [x] **Automated Test Suite:** Comprehensive backend and frontend automated tests validating both offline logic and provider request construction.
- [x] **Production Build & Reproducible Setup:** Validated TypeScript build, FastAPI deployment readiness, and reproducible environment instructions.
- [x] **Security & Privacy Safeguards:** Zero credential leakage in browser/client code, audio payload validation, sanitized logging, and CSRF/CORS protections.

---

## 2. Mandatory vs. Optional Requirements Matrix

| Requirement | Type | Implementation in VoiceIQ India | Verification Status |
| :--- | :--- | :--- | :--- |
| **Gnani Speech-to-Text (ASR)** | **Mandatory** | `POST https://api.vachana.ai/stt/v3` (Prisma v2.5 model) | **Verified Live** (Request ID: `01a1626e-db73-73db-a363-6de3d1fba7ae`) |
| **Server-Side API Key Storage** | **Mandatory** | `backend/app/providers/gnani.py` via `GNANI_API_KEY` in `.env` | **Verified** (Never exposed to browser clients) |
| **Multilingual Indian Audio Support** | **Mandatory** | 10 Indian language codes (`en-IN`, `hi-IN`, `ta-IN`, `te-IN`, `kn-IN`, etc.) | **Verified** |
| **Working Product Catalog & Orders** | **Mandatory** | SQLite database with Products, Carts, Orders, and Items | **Implemented** |
| **Voice-to-Business Action Execution** | **Mandatory** | Real product search, order tracking, cancellation, and returns | **Implemented** |
| **Consequential Action Safety** | **Mandatory** | Explicit 2-step confirmation for cancellations and return requests | **Implemented** |
| **Audio Format Validation** | **Mandatory** | Magic-byte & MIME checking (WAV, MP3, M4A, OGG, FLAC; max 25MB) | **Verified** (Pytest suite passing) |
| **Gnani Text-to-Speech (TTS)** | Optional/Bonus | `POST https://api.vachana.ai/api/v1/tts/inference` (Timbre v3.0) | **Integrated** (`GnaniSpeechClient.synthesize_speech`) |
| **Admin Analytics Dashboard** | Optional/Bonus | Database-backed KPI metrics (intents, order volume, success rate) | **Implemented** (`/api/admin/analytics`) |
| **Spoken Spoken Response Audio** | Optional/Bonus | HTML5 Audio playback in floating voice assistant | **Implemented** |

---

## 3. Verified Model & API Access Evidence

### Speech-to-Text: Gnani Prisma v2.5
- **Endpoint:** `POST https://api.vachana.ai/stt/v3`
- **Authentication:** `X-API-Key-ID: vach_...`
- **Supported Formats:** WAV, MP3, M4A, OGG, FLAC (16kHz / 8kHz telephony)
- **Live Smoke Test Evidence:**
  ```text
  Initiating Gnani Prisma STT request to https://api.vachana.ai/stt/v3 [lang=en-IN, file=smoke_test_sample.wav]
  Gnani Prisma STT completed successfully (request_id=01a1626e-db73-73db-a363-6de3d1fba7ae)
  Raw Response: {'success': True, 'request_id': '01a1626e-db73-73db-a363-6de3d1fba7ae', 'transcript': '', 'model': 'gnani-prisma-v2.5', 'processing_time': 0.0895, 'end_to_end_latency': 0.0910}
  ```

### Text-to-Speech: Gnani Timbre v3.0 / v2.5
- **Endpoint:** `POST https://api.vachana.ai/api/v1/tts/inference`
- **Available Voices:** `Nalini`, `Shivani`, `Yashvi`, `Avinash`
- **Format:** Binary audio streaming (`audio/wav`)

### Conversational Intent & Dialogue Engine
- **Strategy:** Grounded intent classification combining rule-based deterministic parsing with structured Pydantic schema validation for e-commerce entities (order IDs, item categories, price bounds, return reasons).
- **Guaranteed Isolation:** Business rules and SQL transactions govern all state mutations. AI output never overrides actual database prices or inventory.

---

## 4. Known Risks, Constraints & Mitigations

1. **Microphone Browser Permissions:**
   - *Risk:* In secure contexts or certain browsers, microphone access may be denied.
   - *Mitigation:* The VoiceIQ Assistant offers 3 input modes: live push-to-talk, audio file upload, and text input fallback.
2. **Audio Payload Latency on Mobile Networks:**
   - *Risk:* Uploading large uncompressed audio files can cause latency.
   - *Mitigation:* Audio chunk duration capped to 30 seconds; 90-second timeout configured with user-friendly retry banners.
3. **Accidental Order Cancellation:**
   - *Risk:* Voice transcription error triggering unintentional cancellation.
   - *Mitigation:* Explicit confirmation dialog in assistant and API level requirement for confirmation token before updating order status.
