#!/bin/sh
set -e

# Ce conteneur gere le cycle de vie complet des certificats TLS Let's Encrypt :
# 1. Emission initiale (si aucun certificat n'existe encore pour ce domaine)
# 2. Boucle de renouvellement automatique (Certbot ne renouvelle que si le
#    certificat expire dans moins de 30 jours, donc cette boucle peut tourner
#    en continu sans risque de sur-solliciter Let's Encrypt)
#
# PREREQUIS (obligatoires en production, inutiles en dev) :
#   - GATEWAY_SERVER_NAME doit etre un nom de domaine PUBLIC, resolvable en DNS,
#     et pointant vers l'IP publique exposant le port 80 de ce serveur
#     (le defi HTTP-01 de Let's Encrypt a besoin d'y acceder depuis Internet)
#   - CERTBOT_EMAIL doit etre une adresse valide (notifications d'expiration)
#
# En developpement local (domaine non public, ex: portal.telix.local), l'emission
# echouera silencieusement (message logge) et le gateway continuera d'utiliser
# son certificat auto-signe de secours : aucun blocage du demarrage de la stack.

DOMAIN="${GATEWAY_SERVER_NAME:-portal.telix.local}"
EMAIL="${CERTBOT_EMAIL:-admin@example.com}"
WEBROOT="/var/www/certbot"

echo "Certbot demarre pour le domaine : $DOMAIN"

if [ ! -d "/etc/letsencrypt/live/$DOMAIN" ]; then
  echo "Aucun certificat existant, tentative d'emission initiale..."
  certbot certonly \
    --webroot -w "$WEBROOT" \
    -d "$DOMAIN" \
    --email "$EMAIL" \
    --agree-tos \
    --non-interactive \
    || echo "Emission initiale echouee. Verifiez que '$DOMAIN' est un domaine public resolvable pointant vers ce serveur (port 80 accessible). Le gateway utilisera son certificat auto-signe de secours en attendant."
fi

echo "Demarrage de la boucle de renouvellement (verification toutes les 12h)..."
while true; do
  certbot renew --webroot -w "$WEBROOT" --quiet || echo "Tentative de renouvellement echouee, nouvelle tentative dans 12h."
  sleep 12h
done
