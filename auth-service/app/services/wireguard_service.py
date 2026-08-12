"""
services.wireguard_service
--------------------------
Generation de paires de cles WireGuard (X25519) et allocation d'adresses
IP dans le pool du tunnel, pour l'enrollment des agents distants
(remote-agent), voir ADR-008.

HYPOTHESE (a valider) : la generation de cles se fait ici cote serveur
(auth-service genere la cle privee ET la transmet une seule fois a
l'agent). C'est plus simple a operer que de demander a l'agent de
generer sa propre paire et de n'envoyer que la cle publique, mais cela
signifie qu'auth-service voit transitoirement la cle privee de
l'utilisateur. Alternative a envisager si ce point pose probleme cote
securite/conformite : agent genere sa propre paire localement et
n'envoie que sa cle publique a /auth/agent/enroll.
"""
from __future__ import annotations

import base64
import ipaddress

from cryptography.hazmat.primitives.asymmetric.x25519 import (
    X25519PrivateKey,
)
from cryptography.hazmat.primitives import serialization


def generate_keypair() -> tuple[str, str]:
    """
    Genere une paire de cles X25519 compatible WireGuard, encodee en
    base64 (format attendu par `wg` / les fichiers de config WireGuard).
    Retourne (private_key_b64, public_key_b64).
    """
    private_key = X25519PrivateKey.generate()
    public_key = private_key.public_key()

    private_bytes = private_key.private_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PrivateFormat.Raw,
        encryption_algorithm=serialization.NoEncryption(),
    )
    public_bytes = public_key.public_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PublicFormat.Raw,
    )
    return (
        base64.b64encode(private_bytes).decode("ascii"),
        base64.b64encode(public_bytes).decode("ascii"),
    )


class IpPoolExhausted(Exception):
    pass


def allocate_ip(pool_cidr: str, already_allocated: set[str]) -> str:
    """
    Alloue la premiere adresse libre du pool CIDR donne (en excluant
    l'adresse reseau et de broadcast). `already_allocated` doit contenir
    les IP deja attribuees (chargees depuis la base par l'appelant).

    HYPOTHESE (a valider) : allocation sequentielle simple, suffisante a
    l'echelle visee (200 utilisateurs). Si le volume augmente fortement,
    une allocation plus efficace (bitmap, table dediee avec verrou) serait
    preferable pour eviter un parcours lineaire du pool a chaque
    enrollment.
    """
    network = ipaddress.ip_network(pool_cidr, strict=False)
    for ip in network.hosts():
        ip_str = str(ip)
        if ip_str not in already_allocated:
            return ip_str
    raise IpPoolExhausted(f"Aucune adresse libre dans le pool {pool_cidr}")
