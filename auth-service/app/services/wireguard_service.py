"""
services.wireguard_service
--------------------------
Allocation d'adresses IP dans le pool du tunnel, pour l'enrollment des
agents distants (remote-agent), voir ADR-008.

CHANGEMENT (2026-08-12) : la fonction generate_keypair() a ete retiree de
ce module -- la generation de cles WireGuard se fait desormais
EXCLUSIVEMENT cote agent (voir remote-agent/agent/enrollment.py), pas cote
serveur. auth-service ne genere plus, ne voit plus et ne stocke plus de
cle privee WireGuard d'aucun utilisateur.
"""
from __future__ import annotations

import ipaddress


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
