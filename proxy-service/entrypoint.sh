#!/bin/bash
set -e

mkdir -p /var/log/squid /var/spool/squid
chown -R proxy:proxy /var/log/squid /var/spool/squid

# Initialisation du cache Squid si necessaire
if [ ! -d /var/spool/squid/00 ]; then
  squid -N -z || true
fi

# Demarrage du shipper de logs en arriere-plan
/usr/local/bin/gelf_shipper.py &

# Demarrage de Squid au premier plan (PID 1)
exec squid -N -d 1
