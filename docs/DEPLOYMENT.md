# VoiceIQ India — Production Deployment Guide
## Senior Engineer Mode | Gnani AI Challenge 2026

This guide covers deployment workflows for **VoiceIQ India**, including local deployment, containerization with Docker, and cloud hosting configurations.

---

## 1. System Architecture & Prerequisites

- **Frontend:** React 19, TypeScript, Vite, Tailwind CSS (Single Page Application, port 5000 in dev or static build)
- **Backend:** Python 3.11+, FastAPI, Uvicorn, SQLAlchemy, SQLite (port 8000)
- **AI Core:** Gnani.ai Vachana Platform (`https://api.vachana.ai`)
  - Prisma v2.5 STT (`/stt/v3`)
  - Timbre v3.0 / v2.5 TTS (`/api/v1/tts/inference`)

---

## 2. Environment Variables Configuration

Copy `.env.example` to `.env` in the project root:

```ini
# Application Core
PROJECT_NAME="VoiceIQ India"
VERSION="1.0.0"
DEBUG=false

# Persistence
DATABASE_URL="sqlite:///./voiceiq.db"

# Gnani AI API Credentials
# Replace with your official Gnani API key from the challenge portal
GNANI_API_KEY="your_actual_gnani_api_key_here"
GNANI_BASE_URL="https://api.vachana.ai"
GNANI_STT_ENDPOINT="/stt/v3"
GNANI_TTS_ENDPOINT="/api/v1/tts/inference"
GNANI_TIMEOUT_SECONDS=90.0

# Server Binding
HOST="127.0.0.1"
PORT=8000
```

---

## 3. Local Development & Verification

### Step 1: Backend Setup
```bash
# 1. Create virtual environment
py -3.11 -m venv backend/.venv

# 2. Activate virtual environment
# Windows PowerShell:
backend\.venv\Scripts\Activate.ps1
# Linux / macOS:
# source backend/.venv/bin/activate

# 3. Install dependencies
pip install -r backend/requirements.txt

# 4. Launch FastAPI backend
uvicorn app.main:app --app-dir backend --host 127.0.0.1 --port 8000
```

### Step 2: Frontend Setup
```bash
# 1. Install Node dependencies
npm install

# 2. Verify TypeScript typing
npm run check

# 3. Start Vite development server
npm run dev:client
```
The application will be accessible at `http://localhost:5000/`.

---

## 4. Production Build & Serving

### Step 1: Build Frontend Static Bundle
```bash
npm run build
```
This generates the optimized static assets in `dist/public`.

### Step 2: Production ASGI Server
In production environments, serve the FastAPI backend with multiple worker processes using Uvicorn:

```bash
uvicorn app.main:app --app-dir backend --host 0.0.0.0 --port 8000 --workers 4
```

---

## 5. Docker Deployment

### Multi-Stage Dockerfile (`Dockerfile`)

```dockerfile
# Stage 1: Build Frontend
FROM node:20-alpine AS frontend-builder
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

# Stage 2: Production Python Backend
FROM python:3.11-slim
WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app/backend

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install python dependencies
COPY backend/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend application
COPY backend/app ./backend/app

# Copy built frontend assets
COPY --from=frontend-builder /app/dist/public ./dist/public

EXPOSE 8000

# Health check probe
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:8000/api/health || exit 1

CMD ["uvicorn", "app.main:app", "--app-dir", "backend", "--host", "0.0.0.0", "--port", "8000"]
```

---

## 6. Health & Readiness Probes

| Endpoint | Method | Success Response | Purpose |
| :--- | :--- | :--- | :--- |
| `/api/health` | `GET` | `{"status":"healthy", "gnani_configured": true}` | Kubernetes Liveness Probe / Monitoring |
| `/api/ready` | `GET` | `{"status":"ready", "database":"connected"}` | Kubernetes Readiness Probe |
