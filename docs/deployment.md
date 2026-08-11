# Guide de déploiement — Telix_Secure_Pro

## Vue d'ensemble

Ce guide decrit le deploiement complet de la stack, via le script unique
`scripts/deploy.sh`, qui enchaine automatiquement les etapes decrites
precedemment a la main dans les echanges de developpement.

---

## Pre-requis

- Un serveur (VPS ou on-premise) avec **Docker** et le plugin **Docker
  Compose** installes
- Acces reseau vers : ton annuaire AD/Azure AD, ton infrastructure NPM
  existante (`groupe-odisecure.fr`), et Internet (pour Sekoia et Let's
  Encrypt/OVH)
- Au moins ~4 Go de RAM disponibles (Elasticsearch + Graylog sont les plus
  gourmands de la stack)
- `bash`, `python3` installes sur la machine qui lance le script (pas
  necessairement dans les conteneurs)

---

## Configuration prealable (secrets)

Deux fichiers `.env` sont necessaires, **jamais committes** :

1. **`infra/.env`** (copier depuis `infra/.env.example`) : credentials
   PostgreSQL/Redis, secrets Graylog, parametres LDAP/Azure AD, host/port
   Sekoia...
2. **`npm-provisioning/.env`** (voir `docs/npm-provisioning.md`) :
   `OVH_APPLICATION_KEY`, `OVH_APPLICATION_SECRET`, `OVH_CONSUMER_KEY`,
   `DOMAIN`, `VPS_PUBLIC_IP`, `SUBDOMAINS`, identifiants NPM...

> ⚠️ Sans ces deux fichiers correctement remplis, le script s'arrete avec un
> message d'erreur explicite plutot que d'echouer silencieusement.

---

## Lancer le deploiement

```bash
cd Telix_Secure_Pro
chmod +x scripts/deploy.sh
./scripts/deploy.sh
```

### Ce que fait le script, dans l'ordre

| Etape | Action | Idempotent ? |
|---|---|---|
| 1 | Vérifie Docker, Docker Compose, et la présence de `infra/.env` | — |
| 2 | `docker compose up -d --build` (toute la stack applicative) | ✅ |
| 3 | Attend que Graylog reponde sur son API HTTP (timeout 180s par defaut) | — |
| 4 | Lance le provisioning Graylog (index set 365j, input GELF, stream) | ✅ |
| 5 | Lance le provisioning DNS OVH + proxy host NPM (defi DNS-01) | ✅ |

### Variables d'environnement du script lui-meme

| Variable | Defaut | Usage |
|---|---|---|
| `SKIP_NPM` | `false` | Si `true`, sautE l'etape 5 (utile en environnement de dev sans acces OVH/NPM) |
| `GRAYLOG_WAIT_TIMEOUT` | `180` | Duree max (secondes) d'attente de la disponibilite de Graylog |

Exemple pour un environnement de developpement local (sans toucher au DNS
de production) :

```bash
SKIP_NPM=true ./scripts/deploy.sh
```

---

## Ce que le script NE fait PAS (etapes manuelles restantes)

Ces points sont volontairement laisses manuels, faute d'automatisation
developpee a ce jour ou de decision externe a valider :

1. **Configuration de l'output GELF Graylog -> siem-connector** (voir
   `docs/siem-connector.md`, section "Configuration cote Graylog")
2. **Mecanisme d'authentification de l'intake Sekoia** (cle, mTLS...) --
   point ouvert, a clarifier avant mise en production reelle
3. **Configuration de la redirection sur le controleur Wi-Fi** vers l'URL du
   portail (depend entierement du materiel Wi-Fi retenu, voir
   `docs/captive-portal.md`)

---

## Verifier que tout fonctionne

```bash
cd infra
docker compose ps                    # tous les services doivent etre "running"
docker compose logs -f auth-service   # verifier l'absence d'erreurs au demarrage
```

Acces direct (avant configuration DNS/NPM, pour test local) :
- Portail captif : `http://localhost` (via le port expose par `captive-portal`, a mapper si besoin en local)
- Interface Graylog : `http://localhost:9000`

---

## Mettre a jour un deploiement existant

Le script etant idempotent, il peut etre relance sans risque apres un
`git pull` pour appliquer des changements de code :

```bash
git pull
./scripts/deploy.sh
```

Docker Compose ne reconstruira que les images dont le contexte de build a
change.

---

## Points a valider avec l'utilisateur

- **Dimensionnement serveur reel** : les besoins en RAM/CPU n'ont pas ete
  valides en conditions de charge reelle (nombre d'utilisateurs Wi-Fi
  simultanes attendu ?)
- **Strategie de sauvegarde** (PostgreSQL, volumes Graylog/Elasticsearch) :
  non couverte par ce script, a definir separement
- **Environnement de staging** avant la mise en production : aucun
  environnement de ce type n'a ete mis en place a ce stade
