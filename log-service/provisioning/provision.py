#!/usr/bin/env python3
"""
Provisioning automatique de Graylog pour Telix_Secure_Pro.

Ce script s'execute une fois au demarrage de la stack (conteneur ephemere) et
configure Graylog via son API REST, de facon idempotente (relancable sans
doublon) :

1. Attend que l'API Graylog soit disponible
2. Cree un index set dedie "telix_web_traffic" avec rotation quotidienne et
   une strategie de retention correspondant a RETENTION_DAYS (365 par defaut) :
   conservation legale/contractuelle des logs de navigation pendant 1 an.
3. Cree une entree GELF UDP (port 12201) recevant les logs de proxy-service.
4. Cree un stream "Telix - Traffic Web" qui route tous les messages GELF vers
   l'index set dedie, avec une regle simple sur le champ host=proxy-service.

HYPOTHESE A VALIDER : la strategie de retention choisie ici est "delete"
(suppression definitive apres 365 jours). Si une obligation reglementaire
impose un archivage a froid plutot qu'une suppression, il faudra completer ce
script avec un export vers un stockage froid (S3-compatible, MinIO...) avant
suppression.
"""
import os
import sys
import time
import requests
from requests.auth import HTTPBasicAuth

GRAYLOG_URL = os.environ.get("GRAYLOG_URL", "http://log-service:9000")
GRAYLOG_API_USER = os.environ.get("GRAYLOG_API_USER", "admin")
GRAYLOG_API_PASSWORD = os.environ.get("GRAYLOG_API_PASSWORD", "changeme")
RETENTION_DAYS = int(os.environ.get("LOG_RETENTION_DAYS", "365"))

HEADERS = {"X-Requested-By": "telix-provisioning", "Content-Type": "application/json"}
AUTH = HTTPBasicAuth(GRAYLOG_API_USER, GRAYLOG_API_PASSWORD)

INDEX_SET_TITLE = "telix_web_traffic"
STREAM_TITLE = "Telix - Traffic Web"
GELF_INPUT_TITLE = "Telix - GELF UDP (proxy-service)"


def wait_for_graylog(max_retries: int = 60, delay: int = 5) -> None:
    for attempt in range(max_retries):
        try:
            resp = requests.get(f"{GRAYLOG_URL}/api/system/lbstatus", timeout=5)
            if resp.status_code == 200:
                print("Graylog est disponible.")
                return
        except requests.exceptions.RequestException:
            pass
        print(f"En attente de Graylog... ({attempt + 1}/{max_retries})")
        time.sleep(delay)
    print("ERREUR : Graylog n'a pas repondu a temps.", file=sys.stderr)
    sys.exit(1)


def get_or_create_index_set() -> str:
    """Cree (si absent) l'index set dedie avec retention RETENTION_DAYS. Retourne son ID."""
    resp = requests.get(f"{GRAYLOG_URL}/api/system/indices/index_sets", auth=AUTH, headers=HEADERS)
    resp.raise_for_status()
    for index_set in resp.json().get("index_sets", []):
        if index_set["title"] == INDEX_SET_TITLE:
            print(f"Index set '{INDEX_SET_TITLE}' deja present (id={index_set['id']}).")
            return index_set["id"]

    payload = {
        "title": INDEX_SET_TITLE,
        "description": "Logs de trafic web (proxy-service) - retention 1 an - Telix_Secure_Pro",
        "index_prefix": "telix_web",
        "rotation_strategy_class": "org.graylog2.indexer.rotation.strategies.TimeBasedRotationStrategy",
        "rotation_strategy": {"type": "time-size-optimizing", "rotation_period": "P1D"},
        "retention_strategy_class": "org.graylog2.indexer.retention.strategies.DeletionRetentionStrategy",
        "retention_strategy": {"type": "deletion", "max_number_of_indices": RETENTION_DAYS},
        "shards": 1,
        "replicas": 0,
        "index_analyzer": "standard",
        "index_optimization_max_num_segments": 1,
        "index_optimization_disabled": False,
        "field_type_refresh_interval": 5000,
        "writable": True,
    }
    resp = requests.post(f"{GRAYLOG_URL}/api/system/indices/index_sets", auth=AUTH, headers=HEADERS, json=payload)
    resp.raise_for_status()
    index_set_id = resp.json()["id"]
    print(f"Index set '{INDEX_SET_TITLE}' cree (id={index_set_id}), retention={RETENTION_DAYS} indices quotidiens.")
    return index_set_id


def get_or_create_gelf_input() -> None:
    """Cree (si absent) l'input GELF UDP sur le port 12201."""
    resp = requests.get(f"{GRAYLOG_URL}/api/system/inputs", auth=AUTH, headers=HEADERS)
    resp.raise_for_status()
    for inp in resp.json().get("inputs", []):
        if inp["message"]["title"] == GELF_INPUT_TITLE:
            print(f"Input '{GELF_INPUT_TITLE}' deja present.")
            return

    payload = {
        "title": GELF_INPUT_TITLE,
        "type": "org.graylog2.inputs.gelf.udp.GELFUDPInput",
        "global": True,
        "configuration": {
            "bind_address": "0.0.0.0",
            "port": 12201,
            "recv_buffer_size": 262144,
            "decompress_size_limit": 8388608,
        },
    }
    resp = requests.post(f"{GRAYLOG_URL}/api/system/inputs", auth=AUTH, headers=HEADERS, json=payload)
    resp.raise_for_status()
    print(f"Input '{GELF_INPUT_TITLE}' cree sur le port UDP 12201.")


def get_or_create_stream(index_set_id: str) -> None:
    """Cree (si absent) le stream qui route les messages de proxy-service vers l'index set dedie."""
    resp = requests.get(f"{GRAYLOG_URL}/api/streams", auth=AUTH, headers=HEADERS)
    resp.raise_for_status()
    for stream in resp.json().get("streams", []):
        if stream["title"] == STREAM_TITLE:
            print(f"Stream '{STREAM_TITLE}' deja present (id={stream['id']}).")
            return

    payload = {
        "title": STREAM_TITLE,
        "description": "Trafic web des utilisateurs authentifies (proxy-service) - Telix_Secure_Pro",
        "index_set_id": index_set_id,
        "matching_type": "AND",
        "remove_matches_from_default_stream": False,
    }
    resp = requests.post(f"{GRAYLOG_URL}/api/streams", auth=AUTH, headers=HEADERS, json=payload)
    resp.raise_for_status()
    stream_id = resp.json()["stream_id"]

    rule_payload = {
        "field": "source",
        "type": 1,  # EXACT match
        "value": "proxy-service",
        "inverted": False,
    }
    requests.post(
        f"{GRAYLOG_URL}/api/streams/{stream_id}/rules", auth=AUTH, headers=HEADERS, json=rule_payload
    ).raise_for_status()

    requests.post(f"{GRAYLOG_URL}/api/streams/{stream_id}/resume", auth=AUTH, headers=HEADERS).raise_for_status()
    print(f"Stream '{STREAM_TITLE}' cree et active (id={stream_id}).")


def main() -> None:
    wait_for_graylog()
    index_set_id = get_or_create_index_set()
    get_or_create_gelf_input()
    get_or_create_stream(index_set_id)
    print("Provisioning Graylog termine avec succes.")


if __name__ == "__main__":
    main()
