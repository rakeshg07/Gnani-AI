"""API router for User Authentication (Registration, Login, Profile) using MongoDB."""
import uuid
from typing import Any
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status, Header

from app.core.database import get_db
from app.core.security import (
    hash_password,
    verify_password,
    create_customer_session_token,
    verify_customer_session_token,
)
from app.schemas.auth import UserRegisterIn, UserLoginIn, UserOut, AuthResponse

router = APIRouter(prefix="/auth", tags=["Authentication"])


def get_utc_now() -> datetime:
    return datetime.now(timezone.utc)


@router.post("/register", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
def register_user(payload: UserRegisterIn, db: Any = Depends(get_db)):
    """Register a new customer account in MongoDB and return session token."""
    email_clean = payload.email.lower().strip()

    # Check duplicate
    existing = db.users.find_one({"email": email_clean})
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="An account with this email address already exists. Please sign in.",
        )

    user_id = f"cust_{uuid.uuid4().hex[:10]}"
    now = get_utc_now()
    user_doc = {
        "_id": user_id,
        "id": user_id,
        "name": payload.name.strip(),
        "email": email_clean,
        "phone": payload.phone or "+91 98450 12345",
        "password_hash": hash_password(payload.password),
        "address_line": payload.address_line or "Flat 101, Green View",
        "city": payload.city or "Bengaluru",
        "state": payload.state or "Karnataka",
        "postal_code": payload.postal_code or "560001",
        "created_at": now,
    }

    db.users.insert_one(user_doc)
    # Also mirror in customers collection for backward compatibility
    db.customers.update_one({"_id": user_id}, {"$set": user_doc}, upsert=True)

    # Initialize empty cart for user
    db.carts.update_one(
        {"customer_id": user_id},
        {
            "$setOnInsert": {
                "_id": f"cart_{user_id}",
                "id": f"cart_{user_id}",
                "customer_id": user_id,
                "items": [],
                "created_at": now,
                "updated_at": now,
            }
        },
        upsert=True,
    )

    token = create_customer_session_token(
        customer_id=user_id,
        extra_claims={"name": user_doc["name"], "email": user_doc["email"]},
    )

    user_out = UserOut(
        id=user_id,
        name=user_doc["name"],
        email=user_doc["email"],
        phone=user_doc["phone"],
        address_line=user_doc["address_line"],
        city=user_doc["city"],
        state=user_doc["state"],
        postal_code=user_doc["postal_code"],
        created_at=user_doc["created_at"],
    )

    return AuthResponse(
        token=token,
        user=user_out,
        message="Account created successfully! Welcome to VoiceIQ India.",
    )


@router.post("/login", response_model=AuthResponse)
def login_user(payload: UserLoginIn, db: Any = Depends(get_db)):
    """Authenticate with email and password and return session token."""
    email_clean = payload.email.lower().strip()
    user = db.users.find_one({"email": email_clean})

    if not user:
        # Check if user is trying with demo credentials
        if email_clean in ["demo@voiceiq.in", "rahul.sharma@example.in", "demo"]:
            user = db.users.find_one({"id": "cust_demo_001"})

    if not user or not verify_password(payload.password, user.get("password_hash", "")):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password. Please try again.",
        )

    user_id = user.get("id") or str(user.get("_id", ""))
    token = create_customer_session_token(
        customer_id=user_id,
        extra_claims={"name": user.get("name"), "email": user.get("email")},
    )

    user_out = UserOut(
        id=user_id,
        name=user.get("name", "User"),
        email=user.get("email", email_clean),
        phone=user.get("phone"),
        address_line=user.get("address_line"),
        city=user.get("city"),
        state=user.get("state"),
        postal_code=user.get("postal_code"),
        created_at=user.get("created_at"),
    )

    return AuthResponse(
        token=token,
        user=user_out,
        message=f"Welcome back, {user_out.name}!",
    )


@router.get("/me", response_model=UserOut)
def get_current_user(
    authorization: str = Header(None),
    x_customer_token: str = Header(None),
    db: Any = Depends(get_db),
):
    """Retrieve currently authenticated user profile from token."""
    token = None
    if authorization and authorization.lower().startswith("bearer "):
        token = authorization[7:].strip()
    elif x_customer_token:
        token = x_customer_token.strip()

    if not token:
        # Fallback to demo user if unauthenticated
        demo = db.users.find_one({"id": "cust_demo_001"})
        if demo:
            return UserOut(
                id=demo["id"],
                name=demo["name"],
                email=demo["email"],
                phone=demo.get("phone"),
                address_line=demo.get("address_line"),
                city=demo.get("city"),
                state=demo.get("state"),
                postal_code=demo.get("postal_code"),
                created_at=demo.get("created_at"),
            )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication token required.",
        )

    payload = verify_customer_session_token(token)
    if not payload or not payload.get("sub"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session expired or invalid. Please sign in again.",
        )

    user_id = payload["sub"]
    user = db.users.find_one({"$or": [{"id": user_id}, {"_id": user_id}]})
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User account not found.",
        )

    return UserOut(
        id=user.get("id") or str(user.get("_id")),
        name=user.get("name"),
        email=user.get("email"),
        phone=user.get("phone"),
        address_line=user.get("address_line"),
        city=user.get("city"),
        state=user.get("state"),
        postal_code=user.get("postal_code"),
        created_at=user.get("created_at"),
    )


@router.post("/logout")
def logout_user():
    """Client-side token clearing acknowledgement."""
    return {"success": True, "message": "Successfully logged out."}

