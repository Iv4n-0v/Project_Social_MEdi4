"""Contratos de entrada y salida (lo que viaja por HTTP)."""
import datetime
from typing import Optional

from pydantic import BaseModel, Field


class RegisterRequest(BaseModel):
    email: str = Field(max_length=254)
    password: str = Field(max_length=200)
    name: str = Field(min_length=1, max_length=100, pattern=r"\S")
    role: str = "visitor"  # rol inicial: 'visitor' o 'entrepreneur'


class LoginRequest(BaseModel):
    email: str = Field(max_length=254)
    password: str = Field(max_length=200)


class RoleRequest(BaseModel):
    role: str


class ForgotPasswordRequest(BaseModel):
    email: str = Field(max_length=254)


class ResetPasswordRequest(BaseModel):
    token: str = Field(max_length=200)
    new_password: str = Field(max_length=200)


class AccountResponse(BaseModel):
    id: int
    email: str
    name: str
    roles: list[str]
    has_password: bool
    created_at: datetime.datetime


class SessionResponse(BaseModel):
    """El refresh token NO va aqui: viaja en una cookie httpOnly."""

    access_token: str
    token_type: str = "Bearer"
    expires_in: int  # segundos
    account: AccountResponse


class ProvidersResponse(BaseModel):
    google: bool
    facebook: bool


class OAuthStartResponse(BaseModel):
    url: str


class AuditResponse(BaseModel):
    id: int
    action: str
    timestamp: datetime.datetime


class MessageResponse(BaseModel):
    detail: str
    extra: Optional[dict] = None
