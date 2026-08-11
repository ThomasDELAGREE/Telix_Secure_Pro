from pydantic import BaseModel, Field, field_validator
from typing import Optional, Literal
from app.core.mac_utils import normalize_mac


class CorporateLoginRequest(BaseModel):
    username: str = Field(..., min_length=1, max_length=255)
    password: str = Field(..., min_length=1)
    provider: Literal["ldap", "azure_ad"] = "ldap"
    mac_address: Optional[str] = Field(
        None, description="Adresse MAC du client, transmise par l'equipement Wi-Fi (redirection captive)"
    )

    @field_validator("mac_address")
    @classmethod
    def validate_mac(cls, v):
        if v is None:
            return None
        normalized = normalize_mac(v)
        if normalized is None:
            raise ValueError("Adresse MAC invalide.")
        return normalized


class OTPRequestSchema(BaseModel):
    phone: str = Field(..., description="Numero E.164 (+33612345678)")
    mac_address: Optional[str] = Field(None, description="Adresse MAC du client")

    @field_validator("mac_address")
    @classmethod
    def validate_mac(cls, v):
        if v is None:
            return None
        normalized = normalize_mac(v)
        if normalized is None:
            raise ValueError("Adresse MAC invalide.")
        return normalized


class OTPVerifySchema(BaseModel):
    phone: str
    otp: str = Field(..., min_length=4, max_length=8)
    mac_address: Optional[str] = Field(None, description="Adresse MAC du client")

    @field_validator("mac_address")
    @classmethod
    def validate_mac(cls, v):
        if v is None:
            return None
        normalized = normalize_mac(v)
        if normalized is None:
            raise ValueError("Adresse MAC invalide.")
        return normalized


class RoomLoginRequest(BaseModel):
    """Authentification visiteur par identifiant de chambre (deploiement hotelier)."""
    room_number: str = Field(..., min_length=1, max_length=50)
    access_code: str = Field(..., min_length=1, max_length=50)
    mac_address: Optional[str] = Field(None, description="Adresse MAC du client")

    @field_validator("mac_address")
    @classmethod
    def validate_mac(cls, v):
        if v is None:
            return None
        normalized = normalize_mac(v)
        if normalized is None:
            raise ValueError("Adresse MAC invalide.")
        return normalized


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user_identifier: str
    auth_type: str


class OTPRequestResponse(BaseModel):
    message: str
    phone: str
    expires_in: int


class ErrorResponse(BaseModel):
    detail: str
    code: Optional[str] = None
