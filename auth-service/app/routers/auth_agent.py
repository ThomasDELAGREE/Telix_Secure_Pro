"""
routers.auth_agent
------------------
Endpoint d'enrollment pour remote-agent : reutilise les mecanismes
d'authentification existants (corporate LDAP/Azure AD, ou visiteur
OTP/chambre deja verifie), puis genere/retourne une configuration
WireGuard associee a l'identite de l'utilisateur.

HYPOTHESE IMPORTANTE (a valider) : ce squelette suppose que l'appelant a
DEJA ete authentifie via les endpoints existants (/auth/corporate,
/auth/visitor/verify-otp, /auth/visitor/room) et transmet ici le JWT
obtenu -- /auth/agent/enroll ne refait pas une authentification complete,
il verifie seulement ce JWT et procede a l'enrollment WireGuard. Ce choix
evite de dupliquer la logique LDAP/Azure AD/OTP, mais implique que
remote-agent.enrollment devra d'abord appeler un endpoint existant pour
obtenir ce JWT avant d'appeler celui-ci -- point a confirmer/adapter dans
remote-agent une fois ce flux valide.
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
from app.services.wireguard_service import allocate_ip, generate_keypair

router = APIRouter(prefix="/auth/agent", tags=["agent-enrollment"])

# HYPOTHESE (a valider) : pool CIDR reserve au tunnel des agents distants,
# distinct de tout reseau existant chez les clients pour eviter des
# conflits d'adressage. A confirmer avant deploiement reel.
WIREGUARD_POOL_CIDR = "10.200.0.0/16"


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

    private_key, public_key = generate_keypair()

    already_allocated = {row.assigned_ip for row in db.query(AgentEnrollment.assigned_ip).all()}
    assigned_ip = allocate_ip(WIREGUARD_POOL_CIDR, already_allocated)

    enrollment = AgentEnrollment(
        id=str(uuid.uuid4()),
        tenant_id=None,  # multi-tenant non implemente a ce stade, cf ADR-008
        user_identifier=user_identifier,
        identifier_type=identifier_type,
        device_label=payload.device_label,
        wireguard_public_key=public_key,
        assigned_ip=assigned_ip,
    )
    db.add(enrollment)
    db.commit()

    # TODO(integration) : enregistrer ce peer (public_key + assigned_ip)
    # cote filtering-gateway / WireGuard server reel -- non implemente ici,
    # ce squelette persiste seulement l'enrollment cote auth-service.
    # Sans cette etape, la cle generee n'est pas encore utilisable pour un
    # tunnel reel.

    return AgentEnrollResponse(
        wireguard_private_key=private_key,
        wireguard_public_key=public_key,
        assigned_ip=assigned_ip,
        wireguard_server_endpoint=settings.WIREGUARD_SERVER_ENDPOINT,
    )
