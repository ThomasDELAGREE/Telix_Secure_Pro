"""
remote_agent.sync
-----------------
Orchestration de la synchronisation periodique entre l'agent et
l'infrastructure centrale (auth-service pour l'enrollment,
filtering-gateway pour la liste de blocage, log-service via la
passerelle pour le rejeu des evenements en cache).

HYPOTHESE IMPORTANTE (a valider) : les URLs/endpoints exacts de
filtering-gateway ne sont pas encore definis (module pas encore
developpe) -- ce fichier pose l'orchestration generale avec des appels
HTTP a integrer une fois l'API de filtering-gateway specifiee.
"""
from __future__ import annotations

import logging
import time

from .config import AgentConfig
from .fallback_filter import FallbackFilter
from .local_cache import LocalCache

logger = logging.getLogger("telix.remote_agent.sync")


class SyncError(Exception):
    """Levee quand la passerelle centrale est injoignable."""


class SyncService:
    def __init__(
        self,
        config: AgentConfig,
        cache: LocalCache,
        fallback_filter: FallbackFilter,
        http_client=None,  # injecte pour les tests -- eviter une dependance dure a une lib HTTP precise ici
    ) -> None:
        self.config = config
        self.cache = cache
        self.fallback_filter = fallback_filter
        self.http_client = http_client

    def run_once(self) -> bool:
        """
        Tente un cycle complet de synchronisation. Retourne True si la
        passerelle centrale a ete joignable, False si l'agent bascule (ou
        reste) en mode degrade.
        """
        try:
            self._push_pending_events()
            self._pull_blocklist()
            self.cache.purge_expired()
            return True
        except SyncError as exc:
            logger.warning("Synchronisation impossible, mode degrade actif : %s", exc)
            return False

    def _push_pending_events(self) -> None:
        events = self.cache.pending_events()
        if not events:
            return
        if self.http_client is None:
            raise SyncError("Aucun client HTTP configure (squelette de developpement)")
        # TODO : POST vers l'endpoint de rejeu de filtering-gateway une fois
        # son API definie ; a la reussite, appeler self.cache.mark_synced(...)
        raise SyncError("Endpoint de rejeu des evenements pas encore implemente")

    def _pull_blocklist(self) -> None:
        if self.http_client is None:
            raise SyncError("Aucun client HTTP configure (squelette de developpement)")
        # TODO : GET vers l'endpoint de distribution de blocklist de
        # filtering-gateway une fois son API definie ; appeler ensuite
        # self.fallback_filter.update_from_gateway(domaines)
        raise SyncError("Endpoint de distribution de blocklist pas encore implemente")


def run_forever(sync_service: SyncService) -> None:  # pragma: no cover - boucle demon, pas testee unitairement
    """Boucle principale de l'agent (a lancer en tache de fond/service)."""
    while True:
        sync_service.run_once()
        time.sleep(sync_service.config.sync_interval_seconds)
