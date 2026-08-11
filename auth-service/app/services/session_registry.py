"""
Registre des sessions actives dans Redis : IP -> identite complete
(identifiant utilisateur, type d'authentification, MAC declaree par le portail).

Utilise par proxy-service (session_helper.py) pour autoriser le trafic et
enrichir la tracabilite (utilisateur + MAC + moyen d'authentification) sans
dependance directe entre les deux services (couplage faible via Redis partage).

Types d'identifiant (identifier_type) :
  - "ldap"        : utilisateur AD/LDAP corporate
  - "azure_ad"     : utilisateur Azure AD corporate
  - "sms_otp"      : visiteur identifie par numero de telephone
  - "room_number"  : visiteur identifie par numero de chambre (deploiement hotelier)
"""
import json
import logging
from typing import Optional
from app.core.redis_client import get_redis
from app.core.config import settings

logger = logging.getLogger(__name__)
SESSION_KEY_PREFIX = "telix:active_session:"


def register_session(
    ip: str,
    user_identifier: str,
    identifier_type: str,
    mac_address: Optional[str] = None,
) -> None:
    """Enregistre l'identite complete associee a une IP, avec le TTL du JWT."""
    if not ip or ip == "unknown":
        logger.warning("Session non enregistree : IP client inconnue.")
        return

    identity = {
        "user_identifier": user_identifier,
        "identifier_type": identifier_type,
        "mac_address": mac_address,
    }

    r = get_redis()
    key = f"{SESSION_KEY_PREFIX}{ip}"
    ttl_seconds = settings.JWT_EXPIRY_MINUTES * 60
    r.setex(key, ttl_seconds, json.dumps(identity))
    logger.info(
        f"Session enregistree : {ip} -> {user_identifier} "
        f"(type={identifier_type}, mac={mac_address}, TTL {ttl_seconds}s)"
    )


def revoke_session(ip: str) -> None:
    """Revoque une session active (ex: deconnexion manuelle)."""
    if not ip or ip == "unknown":
        return
    r = get_redis()
    r.delete(f"{SESSION_KEY_PREFIX}{ip}")
    logger.info(f"Session revoquee pour {ip}.")
