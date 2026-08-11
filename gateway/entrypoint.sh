#!/bin/sh
set -e

# Genere un certificat auto-signe pour le developpement local si aucun
# certificat n'est present (permet de demarrer sans dependance externe).
# En production, ce repertoire doit etre monte avec de vrais certificats
# (ex: Let's Encrypt via certbot, gere hors de ce conteneur).
CERT_DIR="/etc/nginx/certs"
mkdir -p "$CERT_DIR"

if [ ! -f "$CERT_DIR/telix.crt" ] || [ ! -f "$CERT_DIR/telix.key" ]; then
  echo "Aucun certificat trouve, generation d'un certificat auto-signe (DEV UNIQUEMENT)..."
  openssl req -x509 -nodes -days 365 \
    -newkey rsa:2048 \
    -keyout "$CERT_DIR/telix.key" \
    -out "$CERT_DIR/telix.crt" \
    -subj "/CN=${GATEWAY_SERVER_NAME:-portal.telix.local}"
fi

exec nginx -g "daemon off;"
