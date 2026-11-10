"""Safe, sanitized logging configuration for VoiceIQ India."""
import logging
import re
import sys

# Ensure UTF-8 output on Windows consoles for Indic language logging (Kannada, Hindi, etc.)
if sys.platform == "win32" and hasattr(sys.stdout, "isatty") and sys.stdout.isatty():
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

_SENSITIVE_PATTERNS = [
    re.compile(r"(X-API-Key-ID:\s*)([^\s,]+)", re.IGNORECASE),
    re.compile(r"(api[_-]?key[\"']?\s*[:=]\s*[\"']?)([^\"'\s,]+)", re.IGNORECASE),
    re.compile(r"(authorization:\s*Bearer\s*)([^\s,]+)", re.IGNORECASE),
]


class RedactingFormatter(logging.Formatter):
    """Custom formatter that automatically redacts API keys and sensitive tokens."""

    def format(self, record: logging.LogRecord) -> str:
        original = super().format(record)
        redacted = original
        for pattern in _SENSITIVE_PATTERNS:
            redacted = pattern.sub(r"\1[REDACTED]", redacted)
        return redacted


def setup_logger(name: str = "voiceiq") -> logging.Logger:
    logger = logging.getLogger(name)
    if not logger.handlers:
        logger.setLevel(logging.INFO)
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(logging.INFO)
        formatter = RedactingFormatter(
            fmt="%(asctime)s [%(levelname)s] [%(name)s] %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.propagate = False
    return logger


logger = setup_logger()
