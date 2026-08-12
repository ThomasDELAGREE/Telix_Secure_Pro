"""
filtering_gateway.api.main

API interne de filtering-gateway, consommee par remote-agent :
- GET  /health
- GET  /blocklist         -> derniere liste de domaines bloques (mode degrade agent, ADR-008)
- POST /events/replay     -> reception des evenements accumules localement par l'agent, a relayer vers log-service

STATUT : squelette non teste. Points explicitement non traites (voir README.md) : authentification, relai reel vers log-service/GELF, parametrage par tenant. Ne pas deployer tel quel en production.
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone

from fastapi import FastAPI
from pydantic import BaseModel

logger = logging.getLogger("telix.filtering_gateway.api")

app = FastAPI(title="Telix Filtering Gateway API", version="0.1.0")

# TODO : remplacer par la liste reellement generee par
# scripts/sync_ut1_blocklists.py une fois celui-ci valide -- liste vide par
# defaut pour ne pas faire croire a une liste operationnelle
_CURRENT_BLOCKLIST: list[str] = []
_BLOCKLIST_UPDATED_AT: str | None = None


class TrafficEventIn(BaseModel):
    id: str
    occurred_at: float
    domain: str
    url: str | None = None
    action: str
    category: str | None = None


class ReplayRequest(BaseModel):
    tenant_id: str
    user_identifier: str
    events: list[TrafficEventIn]


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "time": datetime.now(timezone.utc).isoformat()}


@app.get("/blocklist")
def get_blocklist() -> dict:
    # TODO(securite) : authentification de l'agent appelant absente
    return {"blocked_domains": _CURRENT_BLOCKLIST, "updated_at": _BLOCKLIST_UPDATED_AT}


@app.post("/events/replay")
def replay_events(payload: ReplayRequest) -> dict:
    # TODO(integration) : relayer reellement vers log-service (GELF)
    logger.info(
        "Rejeu recu de %s evenements pour tenant=%s user=%s (relai log-service non implemente)",
        len(payload.events),
        payload.tenant_id,
        payload.user_identifier,
    )
    return {"received": len(payload.events), "forwarded_to_log_service": False}
