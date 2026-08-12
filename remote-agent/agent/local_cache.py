"""
remote_agent.local_cache
------------------------
Cache local chiffre (SQLCipher) pour la tracabilite en mode degrade
(voir ADR-008, section 4) : quand l'agent ne peut pas joindre le
log-service central, les evenements de navigation sont stockes ici puis
rejoues a la reconnexion. Retention locale : 30 jours (decision
utilisateur, ADR-008).

HYPOTHESE IMPORTANTE (a valider) : ce squelette utilise le module
standard `sqlite3` avec un chiffrement applicatif place en TODO --
SQLCipher necessite un binding Python dedie (ex: `pysqlcipher3` ou
une build sqlite3 liee a libsqlcipher) qui n'est pas disponible dans cet
environnement de developpement. Ne pas considerer ce cache comme
reellement chiffre tant que ce point n'est pas traite explicitement --
c'est un point de securite bloquant avant toute mise en production,
documente ci-dessous et dans le journal de developpement.
"""
from __future__ import annotations

import sqlite3
import time
import uuid
from dataclasses import dataclass
from pathlib import Path

RETENTION_SECONDS_DEFAULT = 30 * 24 * 3600  # 30 jours, decision utilisateur

_SCHEMA = """
CREATE TABLE IF NOT EXISTS traffic_events (
    id TEXT PRIMARY KEY,
    occurred_at REAL NOT NULL,
    domain TEXT NOT NULL,
    url TEXT,
    action TEXT NOT NULL,          -- 'allowed' | 'blocked'
    category TEXT,                 -- categorie de filtrage appliquee, si connue
    synced INTEGER NOT NULL DEFAULT 0
);
CREATE INDEX IF NOT EXISTS idx_traffic_events_synced ON traffic_events(synced);
CREATE INDEX IF NOT EXISTS idx_traffic_events_occurred_at ON traffic_events(occurred_at);
"""


@dataclass
class TrafficEvent:
    domain: str
    action: str
    url: str | None = None
    category: str | None = None
    occurred_at: float | None = None
    id: str | None = None


class LocalCache:
    """
    Stockage local des evenements de tracabilite en mode degrade.

    SECURITE -- NON RESOLU DANS CE SQUELETTE : le chiffrement SQLCipher
    annonce dans l'ADR-008 n'est pas implemente ici (voir docstring du
    module). A traiter avant toute utilisation en dehors d'un
    environnement de developpement.
    """

    def __init__(self, db_path: Path, retention_seconds: int = RETENTION_SECONDS_DEFAULT) -> None:
        self.db_path = db_path
        self.retention_seconds = retention_seconds
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(str(self.db_path))
        self._conn.executescript(_SCHEMA)
        self._conn.commit()

    def record_event(self, event: TrafficEvent) -> None:
        self._conn.execute(
            "INSERT INTO traffic_events (id, occurred_at, domain, url, action, category, synced) "
            "VALUES (?, ?, ?, ?, ?, ?, 0)",
            (
                event.id or str(uuid.uuid4()),
                event.occurred_at or time.time(),
                event.domain,
                event.url,
                event.action,
                event.category,
            ),
        )
        self._conn.commit()

    def pending_events(self, limit: int = 500) -> list[sqlite3.Row]:
        """Evenements pas encore rejoues vers log-service."""
        self._conn.row_factory = sqlite3.Row
        cur = self._conn.execute(
            "SELECT * FROM traffic_events WHERE synced = 0 ORDER BY occurred_at ASC LIMIT ?",
            (limit,),
        )
        return cur.fetchall()

    def mark_synced(self, event_ids: list[str]) -> None:
        if not event_ids:
            return
        placeholders = ",".join("?" for _ in event_ids)
        self._conn.execute(
            f"UPDATE traffic_events SET synced = 1 WHERE id IN ({placeholders})",
            event_ids,
        )
        self._conn.commit()

    def purge_expired(self) -> int:
        """
        Supprime les evenements plus vieux que la retention locale
        (30 jours par defaut, ADR-008). Ne supprime PAS les evenements
        non synchronises plus jeunes que ce seuil, meme si la
        synchronisation echoue depuis longtemps -- un scenario de coupure
        tres prolongee (> 30 jours) entraine une perte de tracabilite
        locale, comportement accepte explicitement dans l'ADR-008 mais a
        surveiller operationnellement (alerte a prevoir cote passerelle
        si un agent ne se synchronise plus).
        """
        cutoff = time.time() - self.retention_seconds
        cur = self._conn.execute(
            "DELETE FROM traffic_events WHERE occurred_at < ?", (cutoff,)
        )
        self._conn.commit()
        return cur.rowcount

    def close(self) -> None:
        self._conn.close()
