import logging
import random
import string
import httpx
import phonenumbers
from phonenumbers import NumberParseException
from app.core.config import settings
from app.core.redis_client import get_redis

logger = logging.getLogger(__name__)
OTP_KEY_PREFIX = "telix:otp:"


class OTPService:
    """
    Gestion des OTP visiteurs :
    - Generation code aleatoire
    - Envoi SMS via Kannel
    - Stockage Redis avec TTL
    - Validation usage unique
    """

    def _normalize_phone(self, phone: str) -> str:
        try:
            parsed = phonenumbers.parse(phone, None)
            if not phonenumbers.is_valid_number(parsed):
                raise ValueError(f"Numero invalide : {phone}")
            return phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.E164)
        except NumberParseException:
            raise ValueError(f"Format invalide : {phone}")

    def _generate_otp(self) -> str:
        return "".join(random.choices(string.digits, k=settings.OTP_LENGTH))

    async def send_otp(self, phone: str) -> bool:
        normalized = self._normalize_phone(phone)
        otp = self._generate_otp()
        r = get_redis()
        key = f"{OTP_KEY_PREFIX}{normalized}"
        r.setex(key, settings.OTP_EXPIRY_SECONDS, otp)

        message = (
            f"Telix Secure Pro - Votre code : {otp} "
            f"(valable {settings.OTP_EXPIRY_SECONDS // 60} min)"
        )
        sent = await self._send_via_kannel(normalized, message)

        if not sent:
            r.delete(key)
            return False

        logger.info(f"OTP envoye au {normalized}.")
        return True

    async def _send_via_kannel(self, phone: str, message: str) -> bool:
        params = {
            "user": settings.KANNEL_USER,
            "pass": settings.KANNEL_PASSWORD,
            "to": phone,
            "text": message,
            "from": settings.SMS_SENDER,
            "coding": 0,
        }
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.get(settings.KANNEL_URL, params=params)
            if resp.status_code == 202:
                return True
            logger.error(f"Kannel: reponse {resp.status_code} - {resp.text}")
            return False
        except httpx.RequestError as e:
            logger.error(f"Kannel: erreur connexion - {e}")
            return False

    def verify_otp(self, phone: str, otp: str) -> bool:
        try:
            normalized = self._normalize_phone(phone)
        except ValueError:
            return False

        r = get_redis()
        key = f"{OTP_KEY_PREFIX}{normalized}"
        stored = r.get(key)

        if stored is None:
            logger.warning(f"OTP: aucun code pour {normalized} (expire ou inexistant).")
            return False

        if stored != otp:
            logger.warning(f"OTP: code incorrect pour {normalized}.")
            return False

        r.delete(key)
        logger.info(f"OTP: validation reussie pour {normalized}.")
        return True


otp_service = OTPService()
