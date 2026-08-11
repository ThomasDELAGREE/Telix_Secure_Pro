import logging
from fastapi import APIRouter, HTTPException, Request, Depends, status
from sqlalchemy.orm import Session
from datetime import timedelta, datetime, timezone

from app.core.config import settings
from app.core.security import create_access_token
from app.core.database import get_db
from app.models.session import AuthSession
from app.schemas.auth import CorporateLoginRequest, TokenResponse
from app.services.ldap_service import ldap_service

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/corporate", response_model=TokenResponse, summary="Auth corporate (AD/LDAP ou Azure AD)")
async def corporate_login(
    payload: CorporateLoginRequest,
    request: Request,
    db: Session = Depends(get_db),
):
    ip = request.client.host if request.client else "unknown"
    user_agent = request.headers.get("user-agent", "")
    user_info = None
    failure_reason = None

    try:
        if payload.provider == "ldap":
            user_info = ldap_service.authenticate(payload.username, payload.password)
        elif payload.provider == "azure_ad":
            from app.services.azure_ad_service import azure_ad_service
            user_info = await azure_ad_service.authenticate(payload.username, payload.password)
        else:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Provider non supporté.")
    except Exception as e:
        logger.error(f"Erreur auth corporate: {e}")
        failure_reason = str(e)

    db.add(AuthSession(
        user_identifier=payload.username,
        auth_type=payload.provider,
        ip_address=ip,
        user_agent=user_agent,
        success=user_info is not None,
        failure_reason=failure_reason,
        expires_at=(
            datetime.now(timezone.utc) + timedelta(minutes=settings.JWT_EXPIRY_MINUTES)
            if user_info else None
        ),
    ))
    db.commit()

    if not user_info:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Identifiants invalides ou compte non autorisé.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = create_access_token(
        subject=user_info["username"],
        extra_claims={"auth_type": payload.provider, "email": user_info.get("email"), "display_name": user_info.get("display_name")},
    )

    return TokenResponse(
        access_token=token,
        expires_in=settings.JWT_EXPIRY_MINUTES * 60,
        user_identifier=user_info["username"],
        auth_type=payload.provider,
    )
