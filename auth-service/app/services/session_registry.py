"""
Registre des sessions actives (IP -> identifiant utilisateur) dans Redis.

Utilise par proxy-service (session_helper.py) pour savoir si une IP client
correspond a un utilisateur authentifie, sans dependance directe entre
les deux services (couplage faible via Redis partage).
"""
import logging
from app.core.redis_client import get_redis
from app.core.config import settings

logger = logging.getLogger(__name__)
SESSION_KEY_PREFIX = "telix:active_session:"


def register_session(ip: str, user_identifier: str) -> None:
    """Enregistre le mapping IP -> utilisateur avec le meme TTL que le JWT."""
    if not ip or ip == "unknown":
        logger.warning("Session non enregistree : IP client inconnue.")
        return

    r = get_redis()
    key = f"{SESSION_KEY_PREFIX}{ip}"
    ttl_seconds = settings.JWT_EXPIRY_MINUTES * 60
    r.setex(key, ttl_seconds, user_identifier)
    logger.info(f"Session enregistree : {ip} -> {user_identifier} (TTL {ttl_seconds}s)")


def revoke_session(ip: str) -> None:
    """Revoque une session active (ex: deconnexion manuelle)."""
    if not ip or ip == "unknown":
        return
    r = get_redis()
    r.delete(f"{SESSION_KEY_PREFIX}{ip}")
    logger.info(f"Session revoquee pour {ip}.")
