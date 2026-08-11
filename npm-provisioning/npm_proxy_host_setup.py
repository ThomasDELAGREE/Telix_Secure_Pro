"""
Creation/mise a jour du proxy host dans Nginx Proxy Manager (NPM) pour le
portail captif Telix_Secure_Pro, avec certificat Let's Encrypt emis via le
defi DNS-01 (plugin OVH cote NPM, configure manuellement une seule fois dans
l'interface NPM : Settings > Certificates > DNS Challenge).

Ce script est idempotent : si le proxy host existe deja pour ce domaine, il
est mis a jour plutot que duplique.

Variables d'environnement requises :
  NPM_URL                  (ex: http://127.0.0.1:81/api)
  NPM_ADMIN_EMAIL
  NPM_ADMIN_PASSWORD
  TELIX_DOMAIN              (ex: telix.groupe-odisecure.fr)
  TELIX_FORWARD_HOST        (nom du conteneur Docker cible, ex: telix_gateway_backend)
  TELIX_FORWARD_PORT        (port interne du service cible)
  CERTBOT_EMAIL             (email utilise pour l'emission Let's Encrypt)
"""
import os
import sys

import requests


def get_token(npm_url: str, email: str, password: str) -> str:
    resp = requests.post(f"{npm_url}/tokens", json={"identity": email, "secret": password}, timeout=30)
    resp.raise_for_status()
    return resp.json()["token"]


def find_existing_host(npm_url: str, headers: dict, domain: str):
    resp = requests.get(f"{npm_url}/nginx/proxy-hosts", headers=headers, timeout=30)
    resp.raise_for_status()
    for host in resp.json():
        if domain in host.get("domain_names", []):
            return host["id"]
    return None


def main() -> int:
    required = ["NPM_URL", "NPM_ADMIN_EMAIL", "NPM_ADMIN_PASSWORD", "TELIX_DOMAIN",
                "TELIX_FORWARD_HOST", "TELIX_FORWARD_PORT", "CERTBOT_EMAIL"]
    missing = [v for v in required if not os.environ.get(v)]
    if missing:
        print(f"Variables manquantes : {', '.join(missing)}")
        return 1

    npm_url = os.environ["NPM_URL"]
    domain = os.environ["TELIX_DOMAIN"]

    token = get_token(npm_url, os.environ["NPM_ADMIN_EMAIL"], os.environ["NPM_ADMIN_PASSWORD"])
    headers = {"Authorization": f"Bearer {token}"}

    payload = {
        "domain_names": [domain],
        "forward_scheme": "http",
        "forward_host": os.environ["TELIX_FORWARD_HOST"],
        "forward_port": int(os.environ["TELIX_FORWARD_PORT"]),
        "block_exploits": True,
        "allow_websocket_upgrade": True,
        "ssl_forced": True,
        "http2_support": True,
        "certificate_id": "new",
        "meta": {
            "letsencrypt_agree": True,
            "dns_challenge": True,
            "dns_provider": "ovh",
            "letsencrypt_email": os.environ["CERTBOT_EMAIL"],
        },
    }

    existing_id = find_existing_host(npm_url, headers, domain)
    if existing_id:
        print(f"Proxy host existant pour {domain} (id={existing_id}), mise a jour...")
        resp = requests.put(f"{npm_url}/nginx/proxy-hosts/{existing_id}", headers=headers, json=payload, timeout=30)
    else:
        print(f"Creation du proxy host pour {domain}...")
        resp = requests.post(f"{npm_url}/nginx/proxy-hosts", headers=headers, json=payload, timeout=30)

    print(resp.status_code, resp.json())
    resp.raise_for_status()
    return 0


if __name__ == "__main__":
    sys.exit(main())
