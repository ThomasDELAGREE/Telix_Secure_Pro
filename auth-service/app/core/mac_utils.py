"""
Utilitaires de normalisation d'adresse MAC.

Accepte les formats courants (AA:BB:CC:DD:EE:FF, AA-BB-CC-DD-EE-FF,
AABBCCDDEEFF) et les normalise en minuscules avec separateur ':'.
"""
import re

MAC_RE = re.compile(r"^[0-9a-fA-F]{12}$")


def normalize_mac(mac: str) -> str | None:
    if not mac:
        return None
    cleaned = mac.strip().replace(":", "").replace("-", "").replace(".", "")
    if not MAC_RE.match(cleaned):
        return None
    cleaned = cleaned.lower()
    return ":".join(cleaned[i:i + 2] for i in range(0, 12, 2))
