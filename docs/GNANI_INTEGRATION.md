# Gnani AI Integration Guide
## Official Model Specifications, Endpoints, Protocols & Verification

This document records verified specifications, base URLs, authentication mechanisms, supported languages, payload structures, error handling, and live test evidence for Gnani.ai's voice intelligence platform models (Prisma STT and Timbre TTS) used within **VoiceIQ India**.

---

## 1. Provider Overview & Base Infrastructure

- **Platform Name:** Gnani.ai / Vachana Platform
- **Base API URL:** `https://api.vachana.ai`
- **Authentication Header:**
  ```http
  X-API-Key-ID: <your_gnani_api_key>
  ```
  *(Configured server-side in `backend/app/providers/gnani.py` via `GNANI_API_KEY` in `.env`)*
- **Primary Flagship Models:**
  - **Prisma v2.5:** Sovereign Speech-to-Text (ASR) engine optimized for Indian languages, regional accents, telephony audio (8kHz/16kHz), and code-switching (e.g., Hinglish, Tanglish, Kanglish).
  - **Timbre v3.0 / v2.5:** Neural Text-to-Speech (TTS) synthesis with multi-lingual voice personalities, expressiveness audio tags, and adjustable prosody.
  - **Evon / Structured Dialogue Reasoner:** E-commerce intent parsing and structured decision validation.

---

## 2. Speech-to-Text (STT) Integration — Gnani Prisma v2.5

### Endpoint
`POST https://api.vachana.ai/stt/v3`

### Request Format
`multipart/form-data`

### Request Headers
| Header | Value | Description |
| :--- | :--- | :--- |
| `X-API-Key-ID` | `<GNANI_API_KEY>` | Authentication token |

### Multipart Form Fields
| Field Name | Type | Required | Description |
| :--- | :--- | :--- | :--- |
| `audio_file` | Binary (File) | Yes | Audio payload. Supported containers: WAV, MP3, FLAC, OGG, M4A. Recommended sample rate: 16000 Hz or 8000 Hz. |
| `language_code` | String | Yes | BCP-47 language code (e.g. `en-IN`, `hi-IN`, `ta-IN`). |
| `preferred_language` | String | Optional | Secondary language bias or code-switch preference. |
| `format` | String | Optional | `"transcribe"` (default, with Inverse Text Normalization) or `"verbatim"`. |
| `itn_native_numerals` | String ("true"/"false") | Optional | If `"true"`, renders numbers in native script; if `"false"`, renders standard numerals. |

### Verified Indian Language Codes
| Language | BCP-47 Code | Script / Region |
| :--- | :--- | :--- |
| **English (India)** | `en-IN` | Latin / Indian accent |
| **Hindi** | `hi-IN` | Devanagari |
| **Tamil** | `ta-IN` | Tamil Nadu / Sri Lanka |
| **Telugu** | `te-IN` | Andhra Pradesh / Telangana |
| **Kannada** | `kn-IN` | Karnataka |
| **Malayalam** | `ml-IN` | Kerala |
| **Marathi** | `mr-IN` | Maharashtra |
| **Bengali** | `bn-IN` | West Bengal |
| **Gujarati** | `gu-IN` | Gujarat |
| **Punjabi** | `pa-IN` | Punjab (Gurmukhi) |

### Live Verified Response Sample
```json
{
  "success": true,
  "request_id": "01a1626e-db73-73db-a363-6de3d1fba7ae",
  "transcript": "Where is my order VIQ-89214?",
  "model": "gnani-prisma-v2.5",
  "processing_time": 0.0895,
  "end_to_end_latency": 0.0910
}
```

---

## 3. Text-to-Speech (TTS) Integration — Gnani Timbre

### Endpoint
`POST https://api.vachana.ai/api/v1/tts/inference`

### Request Format
`application/json`

### Request Headers
| Header | Value |
| :--- | :--- |
| `Content-Type` | `application/json` |
| `X-API-Key-ID` | `<GNANI_API_KEY>` |

### Request Body Fields
| Field | Type | Required | Description |
| :--- | :--- | :--- | :--- |
| `text` | String | Yes | Plain text to synthesize into spoken audio. |
| `voice` | String | Yes | Character name (`Nalini`, `Shivani`, `Yashvi`, `Avinash`). |
| `model` | String | Yes | `timbre-v3.0` or `timbre-v2.5` |
| `language` | String | No | BCP-47 language code (e.g. `hi-IN`, `en-IN`). |
| `speed` | Float | No | Speed multiplier (default: `1.0`). |

### Response
Binary audio stream (`audio/wav`) converted to Base64 in the `/api/tts/synthesize` endpoint for browser streaming.

---

## 4. HTTP Status Codes & Error Handling Protocol

| HTTP Code | Condition | VoiceIQ Action |
| :--- | :--- | :--- |
| **200 OK** | Successful speech recognition or synthesis | Display transcript in chat / stream audio |
| **400 Bad Request** | Unsupported audio format / missing parameters | Validate audio before sending; return clear user explanation |
| **401 Unauthorized** | Missing or invalid `X-API-Key-ID` | Inform user to check `GNANI_API_KEY` in environment |
| **413 Payload Too Large** | Audio exceeds max size limit (>25MB) | Reject in frontend & backend before upstream transmission |
| **429 Too Many Requests** | Upstream rate limit reached | Exponential backoff (retry up to 3 times) with user notice |
| **500 / 502 / 503** | Upstream Gnani server error | Gracefully surface provider downtime without crashing |
| **Timeout (90s)** | Large file transcription latency | Async task handling with clear timeout alert |

---

## 5. Security & Privacy Guarantees

1. **Server-Side Proxying:** All Gnani API interactions occur exclusively on the backend (`backend/app/providers/gnani.py`). Credentials are never exposed to browser clients.
2. **Sanitized Logs:** Authorization headers and customer transcript contents are redacted in logging pipelines to prevent PII exposure.
3. **Audio Handling:** Temporary audio recordings are cleaned up immediately upon request completion.
