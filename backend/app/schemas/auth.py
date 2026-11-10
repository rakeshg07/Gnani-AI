"""Pydantic schemas for User Authentication and Account management."""
from typing import Optional
from datetime import datetime
from pydantic import BaseModel, EmailStr, Field


class UserRegisterIn(BaseModel):
    name: str = Field(min_length=2, max_length=100)
    email: EmailStr
    password: str = Field(min_length=6, max_length=128)
    phone: Optional[str] = Field(default="+91 98450 12345")
    address_line: Optional[str] = Field(default="")
    city: Optional[str] = Field(default="Bengaluru")
    state: Optional[str] = Field(default="Karnataka")
    postal_code: Optional[str] = Field(default="560001")


class UserLoginIn(BaseModel):
    email: str
    password: str


class UserOut(BaseModel):
    id: str
    name: str
    email: str
    phone: Optional[str] = None
    address_line: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    postal_code: Optional[str] = None
    created_at: Optional[datetime] = None


class AuthResponse(BaseModel):
    token: str
    user: UserOut
    message: str

