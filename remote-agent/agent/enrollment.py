"""
remote_agent.enrollment
-----------------------
Processus d'enrollment initial de l'agent : associe le poste a une
identite utilisateur existante (via auth-service) et genere/recupere une
configuration WireGuard.

DECISIONS ACTEES (voir ADR-008, complement du 2026-08-12) :

1. RESTRICTION AUX IDENTITES DURABLES -- seuls les utilisateurs corporate
   (LDAP/Azure AD) peuvent enroler un agent d'itinerance. Les identites
   visiteur/chambre (SMS OTP, numero de chambre) relevent uniquement du
   portail captif Wi-Fi et n'ont pas de sens ici (identite ephemere/
   partagee, pas de lien durable avec un poste). auth-service rejette
   desormais explicitement ces types via /auth/agent/enroll (403).

2. GENERATION DE CLE COTE AGENT -- la paire de cles WireGuard est
   generee ICI, localement sur le poste, au premier enrollment. Seule la
   cle publique est envoyee a auth-service. La cle privee ne quitte
   jamais le poste -- c'est le choix retenu du point de vue securite
   (evite qu'un secret aussi sensible transite par le reseau, meme
   transitoirement).

HYPOTHESE IMPORTANTE (a valider) : auth-service n'expose pas encore
l'ensemble complet de l'API attendue ici (le format exact de la reponse
reelle une fois deployee reste a valider par un test d'integration). Ce
module pose l'interface attendue cote agent.
"""
from __future__ import annotations

import base64
import logging
from dataclasses import dataclass

from cryptography.hazmat.primitives.asymmetric.x25519 import X25519PrivateKey
from cryptography.hazmat.primitives import serialization

from .config import AgentConfig, ConfigStore

logger = logging.getLogger("telix.remote_agent.enrollment")


class EnrollmentError(Exception):
    pass


def generate_local_keypair() -> tuple[str, str]:
    """
    Genere la paire de cles WireGuard localement sur le poste. La cle
    privee reste en memoire/sur disque local uniquement (voir config.py
    pour le stockage) -- elle n'est JAMAIS envoyee a auth-service.
    """
    private_key = X25519PrivateKey.generate()
    public_key = private_key.public_key()
    private_bytes = private_key.private_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PrivateFormat.Raw,
        encryption_algorithm=serialization.NoEncryption(),
    )
    public_bytes = public_key.public_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PublicFormat.Raw,
    )
    return (
        base64.b64encode(private_bytes).decode("ascii"),
        base64.b64encode(public_bytes).decode("ascii"),
    )


@dataclass
class EnrollmentResult:
    tenant_id: str
    user_identifier: str
    assigned_ip: str
    wireguard_server_endpoint: str
    wireguard_server_public_key: str


class EnrollmentClient:
    """
    Realise l'enrollment auprès d'auth-service en transmettant la cle
    publique generee localement. Squelette : la logique d'appel HTTP
    reelle reste a implementer/valider une fois l'API auth-service testee
    en integration.
    """

    def __init__(self, auth_service_url: str, http_client=None) -> None:
        self.auth_service_url = auth_service_url
        self.http_client = http_client

    def enroll(self, access_token: str, wireguard_public_key: str, device_label: str | None = None) -> EnrollmentResult:
        """
        access_token : JWT deja obtenu via un login corporate existant
        (LDAP/Azure AD uniquement -- un token visiteur/chambre sera
        rejete en 403 par auth-service, voir docstring du module).
        """
        if self.http_client is None:
            raise EnrollmentError(
                "Client HTTP non configure -- squelette de developpement, "
                "appel reel a /auth/agent/enroll pas encore implemente"
            )
        raise EnrollmentError("Enrollment reel pas encore implemente (voir TODO du module)")


def save_enrollment_result(
    store: ConfigStore,
    base_config: AgentConfig,
    result: EnrollmentResult,
    wireguard_private_key: str,
    wireguard_public_key: str,
) -> AgentConfig:
    """wireguard_private_key provient de generate_local_keypair(), pas de
    la reponse serveur -- voir point 2 de la docstring du module."""
    base_config.tenant_id = result.tenant_id
    base_config.user_identifier = result.user_identifier
    base_config.wireguard_private_key = wireguard_private_key
    base_config.wireguard_public_key = wireguard_public_key
    base_config.wireguard_server_endpoint = result.wireguard_server_endpoint
    store.save(base_config)
    return base_config
