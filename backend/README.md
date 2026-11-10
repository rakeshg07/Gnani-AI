# VoiceIQ India — Backend Service

FastAPI (Python 3.11+) backend service with SQLite persistence, official Gnani AI Prisma v2.5 STT, Timbre v3.0 TTS, and Evon v3.3 Indic reasoning integration.

---

## 🚀 Quick Start (Run Backend Separately)

### 1. Prerequisites
- Python 3.11+
- Activated virtual environment

### 2. Setup Virtual Environment & Install Dependencies
From within the `backend/` directory:

```bash
# Windows
python -m venv .venv
.\.venv\Scripts\activate

# macOS / Linux
python3 -m venv .venv
source .venv/bin/activate

# Install requirements
pip install -r requirements.txt
```

### 3. Configure Environment Variables
Verify `.env` has your genuine Gnani API key:
```ini
GNANI_API_KEY="vach_your_actual_key"
DATABASE_URL="sqlite:///./voiceiq.db"
```

### 4. Run the Backend Server
You can run using either `python run.py` or `uvicorn`:

```bash
# Option A: Using the convenience runner
python run.py

# Option B: Using uvicorn directly
uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

- **Backend Base URL**: [http://127.0.0.1:8000](http://127.0.0.1:8000)
- **Interactive Swagger Docs**: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- **Health Check**: [http://127.0.0.1:8000/api/health](http://127.0.0.1:8000/api/health)

---

## 📁 Directory Structure
```
backend/
├── app/
│   ├── api/           # Route handlers (/api/ecommerce, /api/assistant, etc.)
│   ├── core/          # Configuration, database engine, logging
│   ├── models/        # SQLAlchemy database models
│   ├── providers/     # Gnani STT/TTS & Evon LLM integration
│   ├── repositories/  # Database access layer
│   ├── schemas/       # Pydantic request/response schemas
│   └── services/      # Business logic & seeding
├── .env               # Local configuration
├── requirements.txt   # Python dependencies
├── run.py             # One-command backend launcher
└── voiceiq.db         # SQLite database
```
