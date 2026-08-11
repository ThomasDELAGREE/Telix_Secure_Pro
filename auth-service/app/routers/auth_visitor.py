import logging
from fastapi import APIRouter, HTTPException, Request, Depends, status
from sqlalchemy.orm import Session
from datetime import timedelta, datetime, timezone

from app.core.config import settings
from app.core.security import create_access_token
from app.core.database import get_db
from app.models.session import AuthSession
from app.schemas.auth import OTPRequestSchema, OTPVerifySchema, TokenResponse, OTPRequestResponse
from app.services.otp_service import otp_service

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/visitor/request-otp", response_model=OTPRequestResponse, summary="Envoi OTP SMS visiteur")
async def request_otp(
    payload: OTPRequestSchema,
    request: Request,
    db: Session = Depends(get_db),
):
    ip = request.client.host if request.client else "unknown"

    try:
        sent = await otp_service.send_otp(payload.phone)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))

    if not sent:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Impossible d'envoyer le SMS. Veuillez reessayer.",
        )

    db.add(AuthSession(
        user_identifier=payload.phone,
        auth_type="sms_otp_request",
        ip_address=ip,
        success=True,
    ))
    db.commit()

    return OTPRequestResponse(
        message="Code OTP envoye par SMS.",
        phone=payload.phone,
        expires_in=settings.OTP_EXPIRY_SECONDS,
    )


@router.post("/visitor/verify-otp", response_model=TokenResponse, summary="Validation OTP visiteur")
async def verify_otp(
    payload: OTPVerifySchema,
    request: Request,
    db: Session = Depends(get_db),
):
    ip = request.client.host if request.client else "unknown"
    user_agent = request.headers.get("user-agent", "")
    valid = otp_service.verify_otp(payload.phone, payload.otp)

    db.add(AuthSession(
        user_identifier=payload.phone,
        auth_type="sms_otp",
        ip_address=ip,
        user_agent=user_agent,
        success=valid,
        failure_reason=None if valid else "OTP invalide ou expire",
        expires_at=(
            datetime.now(timezone.utc) + timedelta(minutes=settings.JWT_EXPIRY_MINUTES)
            if valid else None
        ),
    ))
    db.commit()

    if not valid:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Code OTP invalide ou expire.")

    token = create_access_token(subject=payload.phone, extra_claims={"auth_type": "sms_otp"})
    return TokenResponse(
        access_token=token,
        expires_in=settings.JWT_EXPIRY_MINUTES * 60,
        user_identifier=payload.phone,
        auth_type="sms_otp",
    )
