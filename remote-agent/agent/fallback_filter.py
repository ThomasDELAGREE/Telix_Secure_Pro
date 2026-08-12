"""
remote_agent.fallback_filter
----------------------------
Filtrage "de base" applique localement quand l'agent ne peut pas joindre
la passerelle centrale (filtering-gateway / e2guardian) -- voir ADR-008,
section 4 (mode degrade).

Principe : une liste de domaines bloques (derniere version synchronisee
depuis la passerelle centrale) est conservee localement. Ce module ne
remplace PAS e2guardian -- c'est un filet de secours minimal, uniquement
base sur le nom de domaine (pas d'inspection de contenu), actif seulement
quand la passerelle centrale est injoignable.

HYPOTHESE (a valider) : l'application effective du blocage sur le poste
(redirection du trafic vers ce filtre local) suppose une integration avec
la pile reseau du systeme (ex: modification du resolveur DNS local, ou
règles de pare-feu) qui n'est PAS implementee dans ce squelette -- seule
la logique de decision (bloque/autorise un domaine donne) est posee ici.
L'integration reseau reelle reste a concevoir avec l'utilisateur avant
toute mise en production, notamment le choix entre approche DNS et
approche pare-feu/proxy local.
"""
from __future__ import annotations

import json
import time
from pathlib import Path


class FallbackFilter:
    def __init__(self, blocklist_path: Path) -> None:
        self.blocklist_path = blocklist_path
        self._blocked_domains: set[str] = set()
        self._last_updated: float | None = None
        self._load()

    def _load(self) -> None:
        if not self.blocklist_path.exists():
            return
        data = json.loads(self.blocklist_path.read_text(encoding="utf-8"))
        self._blocked_domains = set(data.get("blocked_domains", []))
        self._last_updated = data.get("updated_at")

    def update_from_gateway(self, blocked_domains: list[str]) -> None:
        """
        Appelee par le module de synchronisation quand la passerelle
        centrale est joignable, pour rafraichir la derniere liste connue.
        """
        self._blocked_domains = set(blocked_domains)
        self._last_updated = time.time()
        self.blocklist_path.parent.mkdir(parents=True, exist_ok=True)
        self.blocklist_path.write_text(
            json.dumps(
                {"blocked_domains": sorted(self._blocked_domains), "updated_at": self._last_updated},
                indent=2,
            ),
            encoding="utf-8",
        )

    def is_blocked(self, domain: str) -> bool:
        domain = domain.lower().strip().rstrip(".")
        if domain in self._blocked_domains:
            return True
        # Blocage par sous-domaine : si "exemple.com" est bloque, on bloque
        # aussi "www.exemple.com", "sub.exemple.com", etc.
        return any(domain.endswith("." + d) for d in self._blocked_domains)

    @property
    def staleness_seconds(self) -> float | None:
        """Depuis combien de temps cette liste n'a pas ete rafraichie."""
        if self._last_updated is None:
            return None
        return time.time() - self._last_updated
