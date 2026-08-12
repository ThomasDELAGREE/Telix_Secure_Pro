"""
remote_agent.enrollment
-----------------------
Processus d'enrollment initial de l'agent : associe le poste a une
identite utilisateur existante (via auth-service) et genere/recupere une
configuration WireGuard.

HYPOTHESE IMPORTANTE (a valider) : auth-service n'expose pas encore
d'endpoint dedie a la generation de cles WireGuard par utilisateur --
c'est un developpement a faire cote auth-service (liste dans le journal
de developpement). Ce module pose l'interface attendue cote agent, a
adapter une fois cet endpoint reellement specifie et developpe.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass

from .config import AgentConfig, ConfigStore

logger = logging.getLogger("telix.remote_agent.enrollment")


class EnrollmentError(Exception):
    pass


@dataclass
class EnrollmentResult:
    tenant_id: str
    user_identifier: str
    wireguard_private_key: str
    wireguard_public_key: str
    wireguard_server_endpoint: str


class EnrollmentClient:
    """
    Realise l'enrollment auprès d'auth-service. Squelette : la logique
    d'appel HTTP reelle et le format exact de la reponse restent a
    implementer/valider une fois l'endpoint cote auth-service defini
    (voir docstring du module).
    """

    def __init__(self, auth_service_url: str, http_client=None) -> None:
        self.auth_service_url = auth_service_url
        self.http_client = http_client

    def enroll(self, corporate_credentials: dict | None = None, visitor_otp: dict | None = None) -> EnrollmentResult:
        """
        Reutilise la meme logique d'authentification que le portail captif
        (corporate LDAP/Azure AD, ou visiteur OTP) -- endpoint cote
        auth-service a etendre pour repondre en plus avec une config
        WireGuard, pas seulement un JWT comme aujourd'hui.
        """
        if self.http_client is None:
            raise EnrollmentError(
                "Client HTTP non configure -- squelette de developpement, "
                "endpoint auth-service dedie a l'agent pas encore implemente"
            )
        raise EnrollmentError("Enrollment reel pas encore implemente (voir TODO du module)")


def save_enrollment_result(store: ConfigStore, base_config: AgentConfig, result: EnrollmentResult) -> AgentConfig:
    base_config.tenant_id = result.tenant_id
    base_config.user_identifier = result.user_identifier
    base_config.wireguard_private_key = result.wireguard_private_key
    base_config.wireguard_public_key = result.wireguard_public_key
    base_config.wireguard_server_endpoint = result.wireguard_server_endpoint
    store.save(base_config)
    return base_config
