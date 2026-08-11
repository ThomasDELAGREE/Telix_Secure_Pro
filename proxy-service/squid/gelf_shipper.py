#!/usr/bin/env python3
"""
Shipper de logs Squid -> Graylog (GELF/UDP).

Suit le fichier access.log (format telix_json defini dans squid.conf),
parse chaque ligne JSON et l'envoie sous forme de message GELF compresse
vers log-service (Graylog), pour tracabilite et retention 1 an.
"""
import json
import os
import socket
import time
import zlib

LOG_FILE = "/var/log/squid/access.log"
GRAYLOG_HOST = os.environ.get("GRAYLOG_HOST", "log-service")
GRAYLOG_GELF_PORT = int(os.environ.get("GRAYLOG_GELF_PORT", "12201"))


def send_gelf(payload: dict) -> None:
    message = {
        "version": "1.1",
        "host": "proxy-service",
        "short_message": f"{payload.get('method')} {payload.get('url')} -> {payload.get('status')}",
        "timestamp": time.time(),
        "level": 6,
        "_client_ip": payload.get("client_ip"),
        "_user": payload.get("user") or "anonymous",
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
