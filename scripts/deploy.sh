#!/usr/bin/env bash
#
# deploy.sh -- Script de deploiement unique pour Telix_Secure_Pro.
#
# Enchaine les etapes decrites dans docs/deployment.md :
#   1. Verifications prealables (.env, Docker)
#   2. Demarrage de la stack applicative (docker compose up)
#   3. Attente de la disponibilite de Graylog
#   4. Provisioning Graylog (retention 1 an, input GELF, stream)
#   5. Provisioning DNS (OVH) + proxy host NPM (DNS-01)
#
# Ce script est idempotent : il peut etre relance sans effet de bord (chaque
# etape sous-jacente -- docker compose, provisioning Graylog, scripts NPM --
# est elle-meme idempotente).
#
# La configuration de l'output Graylog -> siem-connector (etape manuelle,
# voir docs/siem-connector.md) et le mecanisme d'authentification Sekoia
# (point ouvert) NE SONT PAS geres par ce script -- a faire separement.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
INFRA_DIR="${REPO_ROOT}/infra"
NPM_DIR="${REPO_ROOT}/npm-provisioning"

SKIP_NPM="${SKIP_NPM:-false}"       # export SKIP_NPM=true pour sauter l'etape DNS/NPM
GRAYLOG_WAIT_TIMEOUT="${GRAYLOG_WAIT_TIMEOUT:-180}"  # secondes

log() { echo -e "\n\033[1;34m[deploy]\033[0m $1"; }
err() { echo -e "\n\033[1;31m[deploy][erreur]\033[0m $1" >&2; }

# --- Etape 1 : verifications prealables -------------------------------------
log "Verification des prerequis..."

if ! command -v docker &> /dev/null; then
  err "Docker n'est pas installe ou pas dans le PATH. Installation requise avant de continuer."
  exit 1
fi

if ! docker compose version &> /dev/null; then
  err "Docker Compose (plugin 'docker compose') n'est pas disponible. Installation requise."
  exit 1
fi

if [[ ! -f "${INFRA_DIR}/.env" ]]; then
  err "Fichier ${INFRA_DIR}/.env introuvable. Copiez .env.example vers .env et renseignez les valeurs avant de relancer ce script."
  exit 1
fi

log "Prerequis OK."

# --- Etape 2 : demarrage de la stack applicative -----------------------------
log "Demarrage de la stack Docker (infra/docker-compose.yml)..."
cd "${INFRA_DIR}"
docker compose up -d --build

# --- Etape 3 : attente de la disponibilite de Graylog ------------------------
log "Attente de la disponibilite de Graylog (timeout ${GRAYLOG_WAIT_TIMEOUT}s)..."

# Graylog expose son API HTTP sur le port 9000. On sonde ce port depuis
# l'interieur du reseau Docker via un conteneur ephemere, pour ne pas
# dependre d'outils (curl) installes ou non sur la machine hote.
elapsed=0
until docker compose exec -T log-service curl -sf http://localhost:9000/api/system/lbstatus &> /dev/null; do
  if (( elapsed >= GRAYLOG_WAIT_TIMEOUT )); then
    err "Graylog n'est pas devenu disponible apres ${GRAYLOG_WAIT_TIMEOUT}s. Verifiez les logs : docker compose logs log-service"
    exit 1
  fi
  sleep 5
  elapsed=$((elapsed + 5))
  log "... toujours en attente de Graylog (${elapsed}s ecoulees)"
done

log "Graylog est disponible."

# --- Etape 4 : provisioning Graylog ------------------------------------------
log "Provisioning de Graylog (index set retention 1 an, input GELF, stream)..."
docker compose run --rm log-service-provisioning

# --- Etape 5 : provisioning DNS (OVH) + proxy host NPM ----------------------
if [[ "${SKIP_NPM}" == "true" ]]; then
  log "Etape DNS/NPM ignoree (SKIP_NPM=true)."
else
  log "Provisioning DNS OVH + proxy host Nginx Proxy Manager (defi DNS-01)..."

  if [[ ! -f "${NPM_DIR}/.env" ]]; then
    err "Fichier ${NPM_DIR}/.env introuvable. Cette etape necessite les identifiants OVH et NPM (voir docs/npm-provisioning.md). Relancez avec SKIP_NPM=true pour l'ignorer."
    exit 1
  fi

  cd "${NPM_DIR}"
  set -a
  # shellcheck disable=SC1091
  source "${NPM_DIR}/.env"
  set +a

  python3 ovh_dns_setup.py
  python3 npm_proxy_host_setup.py
fi

log "Deploiement termine."
log "Etapes manuelles restantes (voir docs/deployment.md) :"
log "  - Configurer l'output GELF Graylog -> siem-connector (docs/siem-connector.md)"
log "  - Confirmer le mecanisme d'authentification de l'intake Sekoia"
log "  - Configurer la redirection captive portal sur le controleur Wi-Fi"
