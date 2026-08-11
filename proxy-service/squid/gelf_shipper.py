#!/usr/bin/env python3
"""
Shipper de logs Squid -> Graylog (GELF/UDP).

Suit le fichier access.log (format telix_json defini dans squid.conf), parse
chaque ligne JSON, enrichit avec l'identite complete de l'utilisateur (MAC,
type d'authentification) recuperee dans Redis via l'IP client, puis envoie le
tout en GELF vers log-service (Graylog) pour tracabilite et retention 1 an.
"""
import json
import os
import socket
import time
import zlib
import redis

LOG_FILE = "/var/log/squid/access.log"
GRAYLOG_HOST = os.environ.get("GRAYLOG_HOST", "log-service")
GRAYLOG_GELF_PORT = int(os.environ.get("GRAYLOG_GELF_PORT", "12201"))
REDIS_URL = os.environ.get("REDIS_URL", "redis://redis:6379/0")
SESSION_KEY_PREFIX = "telix:active_session:"

_redis_client = None


def get_redis_client():
    global _redis_client
    if _redis_client is None:
        _redis_client = redis.from_url(REDIS_URL, decode_responses=True)
    return _redis_client


def lookup_identity(client_ip: str) -> dict:
    """Recupere l'identite complete (MAC, type d'auth) associee a l'IP."""
    default = {"user_identifier": None, "identifier_type": "unknown", "mac_address": None}
    if not client_ip:
        return default
    try:
        raw = get_redis_client().get(f"{SESSION_KEY_PREFIX}{client_ip}")
    except redis.RedisError:
        return default
    if not raw:
        return default
    try:
        identity = json.loads(raw)
        return {
            "user_identifier": identity.get("user_identifier"),
            "identifier_type": identity.get("identifier_type", "unknown"),
            "mac_address": identity.get("mac_address"),
        }
    except (json.JSONDecodeError, AttributeError):
        # Retro-compatibilite : ancienne valeur stockee en texte brut
        return {"user_identifier": raw, "identifier_type": "unknown", "mac_address": None}


def send_gelf(payload: dict) -> None:
    identity = lookup_identity(payload.get("client_ip"))
    message = {
        "version": "1.1",
        "host": "proxy-service",
        "short_message": f"{payload.get('method')} {payload.get('url')} -> {payload.get('status')}",
        "timestamp": time.time(),
        "level": 6,
        "_client_ip": payload.get("client_ip"),
        "_user": identity["user_identifier"] or payload.get("user") or "anonymous",
        "_identifier_type": identity["identifier_type"],
        "_mac_address": identity["mac_address"],
        "_method": payload.get("method"),
        "_url": payload.get("url"),
        "_status": payload.get("status"),
        "_bytes": payload.get("bytes"),
        "_duration_ms": payload.get("duration_ms"),
        "_user_agent": payload.get("user_agent"),
    }
    data = zlib.compress(json.dumps(message).encode("utf-8"))
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        sock.sendto(data, (GRAYLOG_HOST, GRAYLOG_GELF_PORT))
    finally:
        sock.close()


def follow(path: str):
    while not os.path.exists(path):
        time.sleep(1)
    with open(path, "r") as f:
        f.seek(0, os.SEEK_END)
        while True:
            line = f.readline()
            if not line:
                time.sleep(0.5)
                continue
            yield line.strip()


def main() -> None:
    for line in follow(LOG_FILE):
        if not line:
            continue
        try:
            payload = json.loads(line)
        except json.JSONDecodeError:
            continue
        try:
            send_gelf(payload)
        except OSError:
            pass


if __name__ == "__main__":
    main()
