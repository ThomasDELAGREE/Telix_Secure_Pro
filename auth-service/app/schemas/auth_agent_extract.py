"""
schemas.auth (extrait agent) -- AgentEnrollRequest / AgentEnrollResponse

Ce fichier ne remplace pas les schemas existants d'auth-service : il
documente ici uniquement les deux schemas ajoutes pour l'enrollment
agent, a fusionner dans le fichier schemas/auth.py existant du projet.

CHANGEMENT (voir auth_agent.py) : AgentEnrollRequest porte desormais
wireguard_public_key (fourni par l'agent) au lieu de rien -- et
AgentEnrollResponse ne contient plus wireguard_private_key ni
wireguard_public_key (generes cote agent), mais ajoute
wireguard_server_public_key (necessaire a l'agent pour configurer son
tunnel local).
"""
from __future__ import annotations

from pydantic import BaseModel


class AgentEnrollRequest(BaseModel):
    access_token: str
    wireguard_public_key: str
    device_label: str | None = None


class AgentEnrollResponse(BaseModel):
    assigned_ip: str
    wireguard_server_endpoint: str
    wireguard_server_public_key: str
