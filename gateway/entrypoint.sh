#!/bin/sh
set -e

# Genere un certificat auto-signe de SECOURS pour le developpement local ou en
# attendant l'emission Certbot (permet de demarrer sans dependance externe et
# sans jamais bloquer le lancement de la stack).
DOMAIN="${GATEWAY_SERVER_NAME:-portal.telix.local}"
CERT_DIR="/etc/nginx/certs"
mkdir -p "$CERT_DIR"

if [ ! -f "$CERT_DIR/telix.crt" ] || [ ! -f "$CERT_DIR/telix.key" ]; then
  echo "Aucun certificat de secours trouve, generation d'un certificat auto-signe (fallback)..."
  openssl req -x509 -nodes -days 365 \
    -newkey rsa:2048 \
    -keyout "$CERT_DIR/telix.key" \
    -out "$CERT_DIR/telix.crt" \
    -subj "/CN=${DOMAIN}"
fi

# Boucle de fond : recharge Nginx toutes les 6h pour prendre en compte un
# eventuel nouveau certificat Let's Encrypt emis/renouvele par Certbot
# (le volume letsencrypt_certs est partage en lecture avec le conteneur certbot).
# 'nginx -s reload' echoue silencieusement si nginx n'est pas encore demarre,
# ce qui est sans consequence ici.
(
  while true; do
    sleep 6h
    nginx -s reload 2>/dev/null || true
  done
) &

exec nginx -g "daemon off;"
