#!/usr/bin/env python3
"""
Helper d'ACL externe Squid.

Squid envoie sur stdin, ligne par ligne, l'adresse IP source (%SRC).
Ce script interroge Redis pour savoir si cette IP correspond a une session
authentifiee active (enregistree par auth-service). Il repond :
  - "OK user=<identifiant>" si l'utilisateur est authentifie
  - "ERR message=not_authenticated" sinon
"""
import os
import sys
import redis

REDIS_URL = os.environ.get("REDIS_URL", "redis://redis:6379/0")
SESSION_KEY_PREFIX = "telix:active_session:"


def main() -> None:
    client = redis.from_url(REDIS_URL, decode_responses=True)

    for line in sys.stdin:
        line = line.strip()
        if not line:
            print('BH message="empty_query"')
            sys.stdout.flush()
            continue

        ip = line.split()[0]

        try:
            user = client.get(f"{SESSION_KEY_PREFIX}{ip}")
        except redis.RedisError:
            print('BH message="redis_unavailable"')
            sys.stdout.flush()
            continue

        if user:
            print(f"OK user={user}")
        else:
            print('ERR message="not_authenticated"')
        sys.stdout.flush()


if __name__ == "__main__":
    main()
