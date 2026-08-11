from pydantic import BaseModel, Field
from typing import Optional, Literal


class CorporateLoginRequest(BaseModel):
    username: str = Field(..., min_length=1, max_length=255)
    password: str = Field(..., min_length=1)
    provider: Literal["ldap", "azure_ad"] = "ldap"


class OTPRequestSchema(BaseModel):
    phone: str = Field(..., description="Numéro E.164 (+33612345678)")


class OTPVerifySchema(BaseModel):
    phone: str
    otp: str = Field(..., min_length=4, max_length=8)


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
