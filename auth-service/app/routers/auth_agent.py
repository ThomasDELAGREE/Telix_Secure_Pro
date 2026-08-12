"""
routers.auth_agent
------------------
Endpoint d'enrollment pour remote-agent : reutilise les mecanismes
d'authentification existants, puis enregistre un peer WireGuard pour
l'identite de l'utilisateur.

DECISIONS ACTEES (voir ADR-008, complement du 2026-08-12) :

1. RESTRICTION AUX IDENTITES DURABLES -- l'enrollment agent (tunnel
   permanent de navigation en itinerance) n'a de sens que pour des
   identites stables, rattachees a une personne reelle dans un annuaire.
   Les identifiants ephemeres/partages du portail captif (sms_otp pour
   les visiteurs, room_number pour les chambres d'hotel) sont donc
   explicitement REFUSES ici -- ces deux sujets (portail captif Wi-Fi vs
   agent d'itinerance) ne doivent pas etre melanges, cf discussion avec
   l'utilisateur.

2. GENERATION DE CLE COTE AGENT -- contrairement a une premiere version
   de ce squelette, la cle privee WireGuard n'est plus generee cote
   serveur. L'agent genere sa propre paire de cles localement (voir
   remote-agent/agent/enrollment.py) et n'envoie ici QUE sa cle publique.
   La cle privee ne transite donc jamais par le reseau ni par
   auth-service -- c'est le choix recommande du point de vue securite,
   valide avec l'utilisateur, meme s'il demande un peu plus
   d'orchestration cote agent.
"""
from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.core.security import decode_access_token
from app.models.agent_enrollment import AgentEnrollment
from app.schemas.auth import AgentEnrollRequest, AgentEnrollResponse
from app.services.wireguard_service import allocate_ip

router = APIRouter(prefix="/auth/agent", tags=["agent-enrollment"])

# HYPOTHESE (a valider) : pool CIDR reserve au tunnel des agents distants,
# distinct de tout reseau existant chez les clients pour eviter des
# conflits d'adressage. A confirmer avant deploiement reel.
WIREGUARD_POOL_CIDR = "10.200.0.0/16"

# Types d'identifiants durables, seuls autorises pour l'enrollment agent
# (voir docstring du module, point 1). sms_otp et room_number sont
# explicitement exclus : ce sont des identites ephemeres/partagees du
# portail captif Wi-Fi, sans lien avec un agent de navigation permanent.
DURABLE_IDENTIFIER_TYPES = {"ldap", "azure_ad"}


@router.post("/enroll", response_model=AgentEnrollResponse, status_code=status.HTTP_201_CREATED)
def enroll_agent(
    payload: AgentEnrollRequest,
    db: Session = Depends(get_db),
) -> AgentEnrollResponse:
    try:
        claims = decode_access_token(payload.access_token)
    except Exception as exc:  # noqa: BLE001 -- remonte en 401 explicite, pas d'inference sur la cause exacte
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token invalide ou expire") from exc

    user_identifier = claims.get("sub")
    identifier_type = claims.get("auth_type")
    if not user_identifier or not identifier_type:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token incomplet")

    if identifier_type not in DURABLE_IDENTIFIER_TYPES:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=(
                "L'enrollment de l'agent d'itinerance est reserve aux identites "
                "corporate durables (LDAP/Azure AD). Les identites visiteur/chambre "
                "(SMS OTP, numero de chambre) relevent uniquement du portail captif Wi-Fi."
            ),
        )

    if not payload.wireguard_public_key:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "wireguard_public_key manquant -- l'agent doit generer sa paire de "
                "cles localement et transmettre uniquement sa cle publique (la cle "
                "privee ne doit jamais transiter par le reseau)"
            ),
        )

    already_allocated = {row.assigned_ip for row in db.query(AgentEnrollment.assigned_ip).all()}
    assigned_ip = allocate_ip(WIREGUARD_POOL_CIDR, already_allocated)

    enrollment = AgentEnrollment(
        id=str(uuid.uuid4()),
        tenant_id=None,  # multi-tenant non implemente a ce stade, cf ADR-008
        user_identifier=user_identifier,
        identifier_type=identifier_type,
        device_label=payload.device_label,
        wireguard_public_key=payload.wireguard_public_key,
        assigned_ip=assigned_ip,
    )
    db.add(enrollment)
    db.commit()

    # TODO(integration) : enregistrer ce peer (public_key + assigned_ip)
    # cote filtering-gateway / WireGuard server reel -- non implemente ici,
    # ce squelette persiste seulement l'enrollment cote auth-service. Sans
    # cette etape, le peer n'est pas encore utilisable pour un tunnel reel.

    return AgentEnrollResponse(
        assigned_ip=assigned_ip,
        wireguard_server_endpoint=settings.WIREGUARD_SERVER_ENDPOINT,
        wireguard_server_public_key=settings.WIREGUARD_SERVER_PUBLIC_KEY,
    )
