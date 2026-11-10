"""Configuration settings for VoiceIQ India backend."""
from pathlib import Path
from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_DIR = Path(__file__).resolve().parent.parent.parent


class Settings(BaseSettings):
    PROJECT_NAME: str = "VoiceIQ India"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api"
    DEBUG: bool = False

    # MongoDB Database Settings
    MONGODB_URI: str = "mongodb://localhost:27017"
    MONGODB_DB_NAME: str = "voiceiq"

    # Gnani AI Provider Settings (STT & TTS)
    GNANI_API_KEY: str = ""
    GNANI_BASE_URL: str = "https://api.vachana.ai"
    GNANI_STT_ENDPOINT: str = "/stt/v3"
    GNANI_TTS_ENDPOINT: str = "/api/v1/tts/inference"
    GNANI_TIMEOUT_SECONDS: float = 90.0

    # Primary AI Provider Routing ('ollama', 'gemini', 'huggingface', 'evon', or 'local')
    AI_PROVIDER: str = "ollama"
    TEXT_CHAT_PROVIDER: str = "ollama"
    VOICE_CHAT_PROVIDER: str = "gemini"

    # Ollama Local LLM Configuration (Qwen3 4B for Text Conversations)
    OLLAMA_ENABLED: bool = True
    OLLAMA_BASE_URL: str = "http://127.0.0.1:11434"
    OLLAMA_MODEL: str = "qwen3:4b"
    OLLAMA_TIMEOUT_SECONDS: float = 30.0
    OLLAMA_TEMPERATURE: float = 0.3

    # Hugging Face Inference API Configuration (Fast Serverless / Dedicated Router)
    HUGGINGFACE_ENABLED: bool = False
    HUGGINGFACE_API_KEY: str = ""       # User Hugging Face Token (starts with hf_...)
    HUGGINGFACE_MODEL: str = "meta-llama/Llama-3.2-3B-Instruct"  # Fast open-weight LLM on HF Router
    HUGGINGFACE_BASE_URL: str = "https://router.huggingface.co/v1"  # Standard OpenAI-compatible HF Router
    HUGGINGFACE_TIMEOUT_SECONDS: float = 30.0
    HUGGINGFACE_MAX_TOKENS: int = 512
    HUGGINGFACE_TEMPERATURE: float = 0.6
    HUGGINGFACE_TOP_P: float = 0.95

    # Hugging Face Aliases for flexible environment names
    HF_API_KEY: str = ""
    HF_TOKEN: str = ""
    HF_MODEL: str = ""
    HF_BASE_URL: str = ""

    # Google Gemini Configuration (Gemini 2.5 Flash for Real-Time Spoken Conversations)
    GEMINI_ENABLED: bool = True
    GEMINI_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-2.5-flash"
    GEMINI_TIMEOUT_SECONDS: float = 60.0
    GEMINI_MAX_OUTPUT_TOKENS: int = 512
    GEMINI_TEMPERATURE: float = 0.6

    # Gnani Evon v3.3 Open-Weight Indic LLM Configuration
    # Official Model: https://huggingface.co/gnani/gnani-evon-v3.3-30B-A3B
    EVON_ENABLED: bool = False
    EVON_HF_REPO_ID: str = "gnani/gnani-evon-v3.3-30B-A3B"
    EVON_BASE_URL: str = ""             # Remote inference server base URL (e.g. https://your-server.example.com/v1)
    EVON_API_KEY: str = ""              # Remote server auth token / Bearer key
    EVON_MODEL_NAME: str = "evon"       # Runtime served model name as configured in vLLM / SGLang
    EVON_TIMEOUT_SECONDS: float = 60.0  # Network timeout in seconds for inference requests
    EVON_MAX_TOKENS: int = 512          # Token generation limit for intent & response
    EVON_TEMPERATURE: float = 0.6       # Official recommended sampling temperature
    EVON_TOP_P: float = 0.95            # Official recommended top-p sampling
    EVON_ENABLE_THINKING: bool = False  # Enable/disable internal reasoning traces

    # Backward compatibility aliases
    EVON_API_BASE: str = ""
    EVON_MODEL_ID: str = "gnani/gnani-evon-v3.3-30B-A3B"

    # Audio Constraints
    MAX_AUDIO_FILE_SIZE_BYTES: int = 25 * 1024 * 1024  # 25 MB
    ALLOWED_AUDIO_EXTENSIONS: List[str] = [".wav", ".mp3", ".m4a", ".ogg", ".flac", ".webm"]
    ALLOWED_MIME_TYPES: List[str] = [
        "audio/wav",
        "audio/x-wav",
        "audio/wave",
        "audio/mpeg",
        "audio/mp3",
        "audio/m4a",
        "audio/x-m4a",
        "audio/mp4",
        "audio/ogg",
        "audio/x-ogg",
        "audio/flac",
        "audio/x-flac",
        "audio/webm",
        "audio/x-webm",
    ]

    # Security & Session Authentication
    SECRET_KEY: str = "voiceiq-sovereign-production-secret-2026-key"
    SESSION_TTL_HOURS: int = 24
    CONFIRMATION_TOKEN_TTL_MINUTES: int = 5

    # Supported Indian Language Codes
    SUPPORTED_LANGUAGES: dict[str, str] = {
        "en-IN": "English (India)",
        "hi-IN": "Hindi (हिंदी)",
        "ta-IN": "Tamil (தமிழ்)",
        "te-IN": "Telugu (తెలుగు)",
        "kn-IN": "Kannada (ಕನ್ನಡ)",
        "ml-IN": "Malayalam (മലയാളം)",
        "mr-IN": "Marathi (मराठी)",
        "bn-IN": "Bengali (বাংলা)",
        "gu-IN": "Gujarati (ગુજરાતી)",
        "pa-IN": "Punjabi (ਪੰਜਾਬੀ)",
        "or-IN": "Odia (ଓଡ଼ିଆ)",
    }

    # CORS
    ALLOWED_ORIGINS: List[str] = [
        "http://localhost:5000",
        "http://127.0.0.1:5000",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "*",
    ]

    model_config = SettingsConfigDict(
        env_file=(".env", "backend/.env", "../.env"),
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    def is_ollama_configured(self) -> bool:
        """
        Check if Ollama local LLM is enabled and configured.
        Requires OLLAMA_ENABLED=true and a non-empty OLLAMA_BASE_URL.
        """
        if not self.OLLAMA_ENABLED:
            return False
        base = (self.OLLAMA_BASE_URL or "").strip()
        return bool(base and not base.startswith("your_"))

    def is_gemini_configured(self) -> bool:
        """
        Check if Google Gemini is enabled with a non-empty, non-placeholder API key.
        """
        if not self.GEMINI_ENABLED:
            return False
        key = (self.GEMINI_API_KEY or "").strip()
        if not key or key.startswith("your_") or "placeholder" in key.lower():
            return False
        return True

    def is_gnani_configured(self) -> bool:
        """Check if a genuine Gnani API key has been populated."""
        return bool(self.GNANI_API_KEY and self.GNANI_API_KEY.strip() and not self.GNANI_API_KEY.startswith("your_"))

    def is_evon_configured(self) -> bool:
        """
        Check if Gnani Evon v3.3 remote inference is enabled and configured.
        Requires EVON_ENABLED=true and a non-empty, non-placeholder EVON_BASE_URL (or legacy EVON_API_BASE).
        """
        if not self.EVON_ENABLED:
            return False
        base = (self.EVON_BASE_URL or self.EVON_API_BASE or "").strip()
        return bool(base and not base.startswith("your_") and not base.startswith("https://your-"))


settings = Settings()
