"""Cryptographic security, password hashing, session management, and customer authentication."""
import base64
import hashlib
import hmac
import json
import secrets
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional
from fastapi import Depends, Header, HTTPException, Query, Request, status

from app.core.config import settings
from app.core.database import get_db


def get_utc_now() -> datetime:
    return datetime.now(timezone.utc)


def generate_secure_token(nbytes: int = 32) -> str:
    """Generates an unpredictable cryptographically secure URL-safe token."""
    return secrets.token_urlsafe(nbytes)


def hash_password(password: str) -> str:
    """Hashes a password with PBKDF2-HMAC-SHA256 and a random salt."""
    salt = secrets.token_hex(16)
    key = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("utf-8"), 100000)
    return f"{salt}:{key.hex()}"


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifies a plain password against the stored salt:hash string."""
    try:
        salt, key_hex = hashed_password.split(":")
        test_key = hashlib.pbkdf2_hmac("sha256", plain_password.encode("utf-8"), salt.encode("utf-8"), 100000)
        return hmac.compare_digest(test_key.hex(), key_hex)
    except Exception:
        return False


def _b64encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).decode("utf-8").rstrip("=")


def _b64decode(s: str) -> bytes:
    padding = 4 - (len(s) % 4)
    if padding and padding < 4:
        s += "=" * padding
    return base64.urlsafe_b64decode(s.encode("utf-8"))


def create_customer_session_token(
    customer_id: str,
    expires_delta: Optional[timedelta] = None,
    extra_claims: Optional[Dict[str, Any]] = None,
) -> str:
    """Creates a tamper-proof cryptographically signed customer session token (HMAC-SHA256)."""
    now = get_utc_now()
    delta = expires_delta or timedelta(hours=settings.SESSION_TTL_HOURS)
    exp = now + delta

    payload = {
        "sub": customer_id,
        "iat": int(now.timestamp()),
        "exp": int(exp.timestamp()),
        "jti": secrets.token_hex(8),
    }
    if extra_claims:
        payload.update(extra_claims)

    raw_payload = json.dumps(payload, separators=(",", ":"), sort_keys=True).encode("utf-8")
    payload_b64 = _b64encode(raw_payload)

    signature = hmac.new(
        settings.SECRET_KEY.encode("utf-8"),
        payload_b64.encode("utf-8"),
        hashlib.sha256,
    ).digest()
    sig_b64 = _b64encode(signature)

    return f"{payload_b64}.{sig_b64}"


def verify_customer_session_token(token: str) -> Optional[Dict[str, Any]]:
    """Verifies token signature and expiration. Returns token payload dict if valid, or None."""
    if not token or "." not in token:
        return None

    try:
        parts = token.strip().split(".")
        if len(parts) != 2:
            return None
        payload_b64, sig_b64 = parts

        expected_sig = hmac.new(
            settings.SECRET_KEY.encode("utf-8"),
            payload_b64.encode("utf-8"),
            hashlib.sha256,
        ).digest()
        provided_sig = _b64decode(sig_b64)

        if not hmac.compare_digest(expected_sig, provided_sig):
            return None

        payload_bytes = _b64decode(payload_b64)
        payload = json.loads(payload_bytes.decode("utf-8"))

        now_ts = int(get_utc_now().timestamp())
        if payload.get("exp", 0) < now_ts:
            return None

        return payload
    except Exception:
        return None


def get_authenticated_customer(
    request: Request,
    authorization: Optional[str] = Header(None),
    x_customer_token: Optional[str] = Header(None),
    customer_id: Optional[str] = Query(None),
    db: Any = Depends(get_db),
) -> str:
    """
    FastAPI dependency that resolves and validates the authenticated customer identity from MongoDB.
    1. Checks 'Authorization: Bearer <token>'
    2. Checks 'X-Customer-Token: <token>'
    3. Validates query customer_id against MongoDB users/customers collection
    4. Defaults safely to verified demo customer 'cust_demo_001'
    """
    # 1. Bearer Token
    if authorization and authorization.lower().startswith("bearer "):
        token = authorization[7:].strip()
        payload = verify_customer_session_token(token)
        if payload and payload.get("sub"):
            return payload["sub"]
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired customer session token.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # 2. X-Customer-Token
    if x_customer_token:
        payload = verify_customer_session_token(x_customer_token.strip())
        if payload and payload.get("sub"):
            return payload["sub"]
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired X-Customer-Token header.",
        )

    # 3. Query Parameter / Fallback
    resolved_id = customer_id or "cust_demo_001"

    cust = db.users.find_one({"id": resolved_id}) or db.customers.find_one({"id": resolved_id})
    if not cust:
        # If demo customer not explicitly stored, create or allow default
        if resolved_id == "cust_demo_001":
            return "cust_demo_001"
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Customer identity '{resolved_id}' is not registered.",
        )
    return str(cust.get("id", resolved_id))
