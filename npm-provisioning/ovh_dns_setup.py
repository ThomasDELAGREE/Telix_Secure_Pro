"""
Creation/mise a jour de l'enregistrement DNS pour le sous-domaine du portail
captif, via l'API OVH (defi DNS-01 gere en amont par Nginx Proxy Manager,
cette etape ne fait que preparer le sous-domaine lui-meme).

Dependance : ovh (client officiel OVH, open source - pip install ovh)

Variables d'environnement requises :
  OVH_ENDPOINT             (ex: ovh-eu)
  OVH_APPLICATION_KEY
  OVH_APPLICATION_SECRET
  OVH_CONSUMER_KEY
  DOMAIN                   (ex: groupe-odisecure.fr)
  SUBDOMAIN                (ex: telix)
  VPS_PUBLIC_IP             IP publique du serveur hebergeant Nginx Proxy Manager

Ce script est idempotent : si l'enregistrement A existe deja avec la bonne
valeur, aucune action n'est effectuee. S'il existe avec une valeur differente,
il est mis a jour.
"""
import os
import sys

import ovh


def main() -> int:
    required = ["OVH_ENDPOINT", "OVH_APPLICATION_KEY", "OVH_APPLICATION_SECRET",
                "OVH_CONSUMER_KEY", "DOMAIN", "SUBDOMAIN", "VPS_PUBLIC_IP"]
    missing = [v for v in required if not os.environ.get(v)]
    if missing:
        print(f"Variables manquantes : {', '.join(missing)}")
        return 1

    domain = os.environ["DOMAIN"]
    subdomain = os.environ["SUBDOMAIN"]
    target_ip = os.environ["VPS_PUBLIC_IP"]

    client = ovh.Client(
        endpoint=os.environ["OVH_ENDPOINT"],
        application_key=os.environ["OVH_APPLICATION_KEY"],
        application_secret=os.environ["OVH_APPLICATION_SECRET"],
        consumer_key=os.environ["OVH_CONSUMER_KEY"],
    )

    existing_ids = client.get(
        f"/domain/zone/{domain}/record",
        fieldType="A",
        subDomain=subdomain,
    )

    if existing_ids:
        for record_id in existing_ids:
            record = client.get(f"/domain/zone/{domain}/record/{record_id}")
            if record["target"] != target_ip:
                print(f"Mise a jour de l'enregistrement {subdomain}.{domain} -> {target_ip}")
                client.put(f"/domain/zone/{domain}/record/{record_id}", target=target_ip)
            else:
                print(f"Enregistrement {subdomain}.{domain} deja a jour ({target_ip}), rien a faire.")
    else:
        print(f"Creation de l'enregistrement {subdomain}.{domain} -> {target_ip}")
        client.post(
            f"/domain/zone/{domain}/record",
            fieldType="A",
            subDomain=subdomain,
            target=target_ip,
            ttl=300,
        )

    client.post(f"/domain/zone/{domain}/refresh")
    print(f"Zone DNS {domain} rafraichie.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
