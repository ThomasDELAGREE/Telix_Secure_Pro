# Documentation — npm-provisioning (Nginx Proxy Manager + DNS-01 OVH)

## Vue d'ensemble

Ce module **remplace** les anciens modules `gateway` (Nginx custom) et `certbot`
(HTTP-01), decrits precedemment dans `docs/gateway.md` et
`docs/tls-renewal-certbot.md` (desormais obsoletes, conserves pour tracabilite
historique — voir [ADR-007](./adr/ADR-007-migration-npm-dns01.md)).

Le reverse proxy, la terminaison TLS et le renouvellement des certificats sont
desormais entierement geres par **Nginx Proxy Manager (NPM)**, aligne sur
l'infrastructure existante du groupe (`groupe-odisecure.fr`).

Le defi utilise pour l'emission des certificats est **DNS-01** (plugin OVH
cote NPM), et non plus HTTP-01 : cela permet notamment d'emettre des
certificats **wildcard** et de ne pas dependre de l'exposition publique du
port 80 pour la validation.

---

## Architecture

```
npm-provisioning/
├── ovh_dns_setup.py          # Cree/met a jour l'enregistrement DNS A du sous-domaine (API OVH)
├── npm_proxy_host_setup.py   # Cree/met a jour le proxy host + certificat DNS-01 dans NPM (API REST)
└── requirements.txt
```

Ces deux scripts sont **complementaires et sequentiels** :
1. `ovh_dns_setup.py` : s'assure que `telix.groupe-odisecure.fr` pointe bien
   vers l'IP publique du serveur (enregistrement A)
2. `npm_proxy_host_setup.py` : declare ce domaine dans NPM comme proxy host
   vers le conteneur `telix_gateway_backend` (ex: `captive-portal` ou un futur
   point d'entree unique), et demande l'emission d'un certificat Let's Encrypt
   via DNS-01

---

## Prerequis (a realiser une seule fois, manuellement)

1. **Nginx Proxy Manager doit deja etre deploye** sur l'infra cible (hors de ce
   depot — fait partie de l'infra `groupe-odisecure.fr`/SBC existante, pas
   d'un composant de `Telix_Secure_Pro`)
2. **Le plugin DNS OVH doit etre configure dans NPM** : interface NPM ><br>
   `Settings > Certificates`, credentials API OVH renseignes (les memes que
   `OVH_APPLICATION_KEY`/`OVH_APPLICATION_SECRET`/`OVH_CONSUMER_KEY`)
3. **Un compte API OVH** avec les droits sur la zone DNS du domaine
   (`groupe-odisecure.fr`), obtenu via https://api.ovh.com/createToken/

> ⚠️ **Hypothèse à valider avec toi** : Nginx Proxy Manager n'etant pas un
> composant versionne dans ce depot mais une brique d'infra partagee existante,
> je n'ai pas de visibilite sur sa configuration actuelle (version, plugins deja
> installes, autres proxy hosts en place). Ces deux scripts sont ecrits pour
> s'integrer a une instance NPM deja fonctionnelle, sans supposer d'autres
> details que ceux que tu as fournis.

---

## Variables d'environnement

| Variable | Description |
|---|---|
| `OVH_ENDPOINT` | Endpoint API OVH (ex: `ovh-eu`) |
| `OVH_APPLICATION_KEY` / `OVH_APPLICATION_SECRET` / `OVH_CONSUMER_KEY` | Credentials API OVH |
| `DOMAIN` | Domaine racine (ex: `groupe-odisecure.fr`) |
| `SUBDOMAIN` | Sous-domaine du portail (ex: `telix`) |
| `VPS_PUBLIC_IP` | IP publique du serveur hebergeant NPM |
| `NPM_URL` | URL de l'API NPM (ex: `http://127.0.0.1:81/api`) |
| `NPM_ADMIN_EMAIL` / `NPM_ADMIN_PASSWORD` | Identifiants admin NPM |
| `TELIX_DOMAIN` | FQDN complet du portail (ex: `telix.groupe-odisecure.fr`) |
| `TELIX_FORWARD_HOST` / `TELIX_FORWARD_PORT` | Conteneur Docker et port cibles du proxy |
| `CERTBOT_EMAIL` | Email de contact Let's Encrypt |

---

## Execution

```bash
pip install -r npm-provisioning/requirements.txt

python3 npm-provisioning/ovh_dns_setup.py
python3 npm-provisioning/npm_proxy_host_setup.py
```

---

## Points a valider avec toi

- **Nom du conteneur cible** (`TELIX_FORWARD_HOST`) et son port : dans le
  script d'exemple que tu as fourni, `forward_host` etait `telix_backend` sur
  le port `3100`. Dans notre docker-compose actuel, le point d'entree logique
  serait plutot `captive-portal` (port 80). A confirmer selon comment tu
  veux router une fois `captive-portal` developpe.
- **Frequence d'execution** de ces scripts : ponctuelle (une fois au
  provisioning initial) ou doivent-ils tourner en continu/cron pour detecter
  un changement d'IP publique ? Pas encore automatise a ce stade.
