#!/bin/sh
set -e

DOMAIN="${GATEWAY_SERVER_NAME:-portal.telix.local}"
CERT_DIR="/etc/nginx/certs"
LE_LIVE_DIR="/etc/letsencrypt/live/${DOMAIN}"
mkdir -p "$CERT_DIR"

# 1. Genere un certificat auto-signe de SECOURS s'il n'en existe pas encore
#    (permet de demarrer sans dependance externe et sans jamais bloquer le
#    lancement de la stack, meme en tout premier demarrage).
if [ ! -f "$CERT_DIR/telix.crt" ] || [ ! -f "$CERT_DIR/telix.key" ]; then
  echo "Aucun certificat de secours trouve, generation d'un certificat auto-signe (fallback)..."
  openssl req -x509 -nodes -days 365 \
    -newkey rsa:2048 \
    -keyout "$CERT_DIR/telix.key" \
    -out "$CERT_DIR/telix.crt" \
    -subj "/CN=${DOMAIN}"
fi

# 2. Fonction de bascule : si un certificat Let's Encrypt valide existe pour ce
#    domaine (emis par le conteneur certbot, volume 'letsencrypt_certs' partage
#    en lecture), on l'utilise a la place du certificat auto-signe.
sync_letsencrypt_cert() {
  if [ -f "$LE_LIVE_DIR/fullchain.pem" ] && [ -f "$LE_LIVE_DIR/privkey.pem" ]; then
    if [ "$LE_LIVE_DIR/fullchain.pem" -nt "$CERT_DIR/telix.crt" ] || [ ! -L "$CERT_DIR/telix.crt" ]; then
      echo "Certificat Let's Encrypt detecte pour ${DOMAIN}, bascule en cours..."
      cp "$LE_LIVE_DIR/fullchain.pem" "$CERT_DIR/telix.crt"
      cp "$LE_LIVE_DIR/privkey.pem" "$CERT_DIR/telix.key"
      nginx -s reload 2>/dev/null || true
    fi
  fi
}

sync_letsencrypt_cert

# 3. Boucle de fond : re-verifie toutes les 6h si un nouveau certificat
#    Let's Encrypt a ete emis/renouvele par Certbot, et recharge Nginx si oui.
(
  while true; do
    sleep 6h
    sync_letsencrypt_cert
  done
) &

exec nginx -g "daemon off;"
