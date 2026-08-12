"""
remote_agent.config
--------------------
Gestion de la configuration locale de l'agent Telix (fichier config.json
dans le repertoire de donnees applicatif de l'utilisateur).

HYPOTHESE (a valider) : l'agent est installe par utilisateur (pas par
machine partagee) -- le repertoire de config est donc dans le profil
utilisateur courant, pas dans un emplacement systeme partage.
"""
from __future__ import annotations

import json
import os
import platform
from dataclasses import dataclass, asdict
from pathlib import Path


def _default_data_dir() -> Path:
    system = platform.system()
    if system == "Windows":
        base = os.environ.get("APPDATA", str(Path.home() / "AppData" / "Roaming"))
        return Path(base) / "TelixSecurePro"
    if system == "Darwin":
        return Path.home() / "Library" / "Application Support" / "TelixSecurePro"
    # Fallback generique (non cible officiellement par l'ADR-008, garde-fou)
    return Path.home() / ".telix-secure-pro"


@dataclass
class AgentConfig:
    """Configuration persistee localement apres enrollment reussi."""

    tenant_id: str | None = None
    user_identifier: str | None = None
    auth_service_url: str = "https://auth.telix.example"
    filtering_gateway_url: str = "https://gateway.telix.example"
    wireguard_private_key: str | None = None
    wireguard_public_key: str | None = None
    wireguard_server_endpoint: str | None = None
    sync_interval_seconds: int = 300
    local_cache_retention_days: int = 30  # decision utilisateur, voir ADR-008

    @property
    def is_enrolled(self) -> bool:
        return bool(self.wireguard_private_key and self.tenant_id)


class ConfigStore:
    """Lecture/ecriture du fichier de configuration local de l'agent."""

    def __init__(self, data_dir: Path | None = None) -> None:
        self.data_dir = data_dir or _default_data_dir()
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.config_path = self.data_dir / "config.json"

    def load(self) -> AgentConfig:
        if not self.config_path.exists():
            return AgentConfig()
        raw = json.loads(self.config_path.read_text(encoding="utf-8"))
        return AgentConfig(**raw)

    def save(self, config: AgentConfig) -> None:
        # TODO(securite) : durcir les permissions du fichier (chmod 600 sur
        # Unix/macOS ; ACL restrictive sur Windows) -- pas encore implemente
        # dans ce squelette, a traiter avant toute mise en production reelle
        # car le fichier contient une cle privee WireGuard.
        self.config_path.write_text(
            json.dumps(asdict(config), indent=2), encoding="utf-8"
        )
