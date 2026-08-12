"""
models.agent_enrollment
-----------------------
Table de suivi des enrollments d'agents distants (remote-agent) : associe
un utilisateur (identifie de la meme facon que dans auth_sessions --
ldap/azure_ad/sms_otp/room_number) a une cle publique WireGuard et une
adresse IP allouee dans le pool du tunnel.

HYPOTHESE (a valider) : un utilisateur peut avoir plusieurs enrollments
(un par poste Windows/macOS enrole), donc pas de contrainte d'unicite sur
user_identifier seul -- seulement sur (user_identifier, device_label) si
un libelle de poste est fourni. A ce stade, device_label est optionnel et
non deduplique automatiquement -- risque de doublons si l'agent est
re-enrole plusieurs fois sans libelle distinct, a surveiller.
"""
from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, String

from app.core.database import Base


class AgentEnrollment(Base):
    __tablename__ = "agent_enrollments"

    id = Column(String, primary_key=True)
    tenant_id = Column(String, nullable=True, index=True)  # prepare le multi-tenant, cf ADR-008/discussion SaaS -- non exploite ailleurs pour l'instant
    user_identifier = Column(String, nullable=False, index=True)
    identifier_type = Column(String, nullable=False)  # ldap | azure_ad | sms_otp | room_number
    device_label = Column(String, nullable=True)
    wireguard_public_key = Column(String, nullable=False, unique=True)
    assigned_ip = Column(String, nullable=False, unique=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    revoked_at = Column(DateTime, nullable=True)
