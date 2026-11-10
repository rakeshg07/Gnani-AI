# Gnani Evon v3.3 Remote GPU Deployment & Serving Guide

This document provides production-ready instructions for deploying and serving the **Gnani Evon v3.3** open-weight large language model on a dedicated remote Linux GPU instance, and connecting it to the VoiceIQ India FastAPI backend.

---

## 1. Architecture Overview & Model Identification

### Canonical Identities
* **Hugging Face Model Repository**: `gnani/gnani-evon-v3.3-30B-A3B`
* **Official Model Card / Serving Alias**: `gnani/gnani-evon-v3.3`
* **Runtime Served Model Name (`--served-model-name`)**: `evon` (recommended for standard API routing)
* **API Architecture**: OpenAI-compatible HTTP Chat Completions endpoint (`POST /v1/chat/completions`)

```
   VoiceIQ Client (Browser)
             │
             ▼
   FastAPI Backend (VoiceIQ Orchestrator)
             │
      ┌──────┴──────┐
      │             ▼
      │      Gnani Prisma STT (Speech-to-Text)
      │             │ Recognized text
      ▼             ▼
   EvonClient (Async HTTP / Bearer Auth)
             │
             ▼ HTTPS / TLS (Nginx Reverse Proxy)
   Remote Linux GPU Server
   ┌──────────────────────────────────────────────┐
   │ vLLM / SGLang Inference Engine              │
   │ Model: gnani/gnani-evon-v3.3-30B-A3B         │
   │ Served Name: evon                            │
   │ GPU: NVIDIA A100 / H100 / L40S               │
   └──────────────────────────────────────────────┘
```

> **IMPORTANT**: Evon v3.3 is a 30-billion parameter MoE (Mixture of Experts) model with ~3.3B active parameters per token. It **must not** be loaded or executed on local consumer laptops without dedicated data-center grade GPUs.

---

## 2. Hardware & VRAM Requirements

| Precision / Quantization | Minimum GPU VRAM | Recommended GPU Configurations | Throughput / Concurrency |
| :--- | :--- | :--- | :--- |
| **Bfloat16 / FP16 (Native)** | ~64 GB - 72 GB | 1x NVIDIA A100 (80GB SXM/PCIe)<br>1x NVIDIA H100 (80GB)<br>2x NVIDIA L40S (48GB, TP=2) | High (Production default) |
| **FP8 / AWQ (Quantized)** | ~32 GB - 40 GB | 1x NVIDIA A100 (40GB)<br>1x NVIDIA L40 (48GB)<br>2x NVIDIA RTX 4090 / A10G (24GB, TP=2) | High throughput, lower memory |
| **INT4 (GPTQ / AWQ)** | ~18 GB - 24 GB | 1x NVIDIA RTX 3090 / 4090 (24GB)<br>1x NVIDIA A10G (24GB) | Cost-optimized dev/testing |

---

## 3. Remote Server Provisioning & Setup (Ubuntu 22.04 LTS)

### Step 3.1: Install NVIDIA Drivers & CUDA Toolkit
```bash
# Update system
sudo apt-get update && sudo apt-get upgrade -y
sudo apt-get install -y build-essential python3-pip python3-venv git curl jq nginx

# Verify NVIDIA GPU driver and CUDA
nvidia-smi
nvcc --version
```

### Step 3.2: Create Python Virtual Environment
```bash
python3 -m venv /opt/evon-env
source /opt/evon-env/bin/activate
pip install --upgrade pip setuptools wheel
```

### Step 3.3: Install vLLM (Recommended Serving Engine)
```bash
# Install latest vLLM with FlashAttention-2 support
pip install "vllm>=0.12.0" huggingface_hub
```

---

## 4. Serving Evon v3.3 with vLLM

### Production Serving Command (Native BF16 on 1x A100 80GB)
```bash
vllm serve gnani/gnani-evon-v3.3 \
    --served-model-name evon \
    --host 127.0.0.1 \
    --port 8000 \
    --max-model-len 8192 \
    --gpu-memory-utilization 0.92 \
    --trust-remote-code \
    --dtype bfloat16 \
    --api-key "your-secure-internal-evon-api-key"
```

### Alternative: Tensor Parallel on 2x L40S / 2x A10G (2 GPUs)
```bash
vllm serve gnani/gnani-evon-v3.3 \
    --served-model-name evon \
    --host 127.0.0.1 \
    --port 8000 \
    --tensor-parallel-size 2 \
    --max-model-len 8192 \
    --trust-remote-code \
    --api-key "your-secure-internal-evon-api-key"
```

### Alternative: SGLang Serving Engine
```bash
pip install "sglang[all]>=0.4.0"

python3 -m sglang.launch_server \
    --model-path gnani/gnani-evon-v3.3 \
    --host 127.0.0.1 \
    --port 8000 \
    --chat-template chatml \
    --context-length 8192 \
    --api-key "your-secure-internal-evon-api-key"
```

---

## 5. Systemd Daemon Service Setup

To keep Evon running reliably across reboots:

Create `/etc/systemd/system/evon-inference.service`:
```ini
[Unit]
Description=Gnani Evon v3.3 vLLM Inference Engine
After=network.target nvidia-persistenced.service

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/opt/evon-env
Environment="PATH=/opt/evon-env/bin:/usr/local/cuda/bin:/usr/bin"
Environment="CUDA_VISIBLE_DEVICES=0"
ExecStart=/opt/evon-env/bin/vllm serve gnani/gnani-evon-v3.3 \
    --served-model-name evon \
    --host 127.0.0.1 \
    --port 8000 \
    --max-model-len 8192 \
    --gpu-memory-utilization 0.92 \
    --trust-remote-code \
    --dtype bfloat16 \
    --api-key "YOUR_PRODUCTION_API_KEY"
Restart=always
RestartSec=10
LimitNOFILE=65536

[Install]
WantedBy=multi-user.target
```

Enable and start the service:
```bash
sudo systemctl daemon-reload
sudo systemctl enable evon-inference
sudo systemctl start evon-inference
sudo systemctl status evon-inference
```

---

## 6. Nginx HTTPS Reverse Proxy with TLS

Never expose vLLM directly on port 8000 without TLS and authentication.

Configure `/etc/nginx/sites-available/evon`:
```nginx
server {
    server_name evon-inference.yourcompany.com;

    client_max_body_size 64M;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # Timeouts for generative inference
        proxy_connect_timeout 60s;
        proxy_send_timeout 120s;
        proxy_read_timeout 120s;
    }

    listen 443 ssl http2;
    ssl_certificate /etc/letsencrypt/live/evon-inference.yourcompany.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/evon-inference.yourcompany.com/privkey.pem;
    include /etc/letsencrypt/options-ssl-nginx.conf;
    ssl_dhparam /etc/letsencrypt/ssl-dhparams.pem;
}

server {
    listen 80;
    server_name evon-inference.yourcompany.com;
    return 301 https://$host$request_uri;
}
```

---

## 7. Verifying Remote Inference with `curl`

### Health & Models Check:
```bash
curl -X GET https://evon-inference.yourcompany.com/v1/models \
  -H "Authorization: Bearer YOUR_PRODUCTION_API_KEY"
```
**Expected response**:
```json
{
  "object": "list",
  "data": [
    {
      "id": "evon",
      "object": "model",
      "owned_by": "gnani"
    }
  ]
}
```

### Chat Completions Test:
```bash
curl -X POST https://evon-inference.yourcompany.com/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_PRODUCTION_API_KEY" \
  -d '{
    "model": "evon",
    "messages": [
      {"role": "system", "content": "You are VoiceIQ sovereign Indic assistant."},
      {"role": "user", "content": "Show me wireless earbuds under 2000 rupees"}
    ],
    "temperature": 0.6,
    "max_tokens": 256
  }'
```

---

## 8. Connecting VoiceIQ FastAPI Backend

In your backend `.env` file (e.g., `backend/.env` or root `.env`):

```bash
# Enable Evon remote inference
EVON_ENABLED=true

# Canonical Hugging Face model
EVON_HF_REPO_ID=gnani/gnani-evon-v3.3-30B-A3B

# Remote inference endpoint
EVON_BASE_URL=https://evon-inference.yourcompany.com/v1

# Secure API Key
EVON_API_KEY=YOUR_PRODUCTION_API_KEY

# Model name served by vLLM
EVON_MODEL_NAME=evon

# Sizing & Hyperparameters
EVON_TIMEOUT_SECONDS=60
EVON_MAX_TOKENS=512
EVON_TEMPERATURE=0.6
EVON_TOP_P=0.95
EVON_ENABLE_THINKING=false
```

Once configured:
1. Verify with health endpoint: `GET http://localhost:8000/api/assistant/health`
2. Run automated real inference verification:
   ```bash
   pytest backend/tests/test_evon_real_inference.py -v
   ```

