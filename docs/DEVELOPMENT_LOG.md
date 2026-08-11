# Journal de développement — Telix_Secure_Pro

> Ce fichier est mis à jour à chaque étape du développement.
> Il sert de fil conducteur pour reprendre le projet à tout moment.

---

## État global du projet

| Module | Statut | Commit(s) |
|---|---|---|
| Structure de base | ✅ Terminé | `ad8147f` |
| `auth-service` | ✅ Terminé | `2988100`, `cc8f08e`, `6e71cdb`, `101d623` |
| `proxy-service` | ✅ Terminé | `ed5ab70`, `6e71cdb`, `5379e19` |
| `log-service` | ✅ Terminé | `488fc11`, `5c126f1` |
| Conformité LCEN (retention) | ✅ Confirmée | `0a5b899` (ADR-006) |
| ~~`gateway` (Nginx custom)~~ | ❌ Remplace | `b78a383`, `d24c1ab` → voir ADR-007 |
| ~~`certbot` (HTTP-01)~~ | ❌ Remplace | `da833ee`...`03b2620` → voir ADR-007 |
| `npm-provisioning` (NPM + DNS-01 OVH) | ✅ Terminé | `7cd5403`, `66321a4` |
| `captive-portal` | 🔲 À faire | — |
| `siem-connector` | 🔲 À faire | — |
| CI/CD complet | 🟡 Partiel | `cc8f08e` |

---

## Étape 1 — Structure de base
**Date :** 2026-08-11 | **Commit :** `ad8147f`

Création du dépôt, arborescence complète, README, docker-compose de base.

---

## Étape 2 — Module `auth-service`
**Date :** 2026-08-11 | **Commits :** `2988100`, `cc8f08e`

API FastAPI (corporate LDAP/Azure AD + visiteur OTP SMS), traçabilité en base,
migrations Alembic, tests, CI GitHub Actions.

---

## Étape 3 — Module `proxy-service`
**Date :** 2026-08-11 | **Commits :** `ed5ab70`, `6e71cdb`

Proxy Squid + ACL externe (Redis) + logs JSON + shipper GELF vers Graylog.

---

## Étape 4 — Identification par MAC + identifiant générique
**Date :** 2026-08-11 | **Commits :** `101d623`, `5379e19`, `72061e1`, `8f041a1`
**ADR :** [ADR-005](./adr/ADR-005-mac-and-generic-identity.md)

Champ `mac_address` sur tous les endpoints, nouveau type d'auth `room_number`
(hôtel), registre Redis enrichi (JSON), logs proxy enrichis.

---

## Étape 5 — Module `log-service`
**Date :** 2026-08-11 | **Commits :** `488fc11`, `5c126f1`

Stack Graylog 6 + Elasticsearch 8 + MongoDB 6, provisioning automatique
(index set retention 365j, input GELF, stream de routage).

---

## Étape 5bis — Conformité LCEN (retention 1 an)
**Date :** 2026-08-11 | **Commit :** `0a5b899` | **ADR :** [ADR-006](./adr/ADR-006-lcen-retention-compliance.md)

Analyse du décret n°2021-1362 : la retention par suppression apres 365 jours
est conforme a l'obligation legale de conservation d'1 an.

---

## Étape 6 — Module `gateway` (Nginx custom) — ~~remplacé~~
**Date :** 2026-08-11 | **Commits :** `b78a383`, `d24c1ab`

Reverse proxy Nginx custom : TLS, routage, rate limiting, headers de securite.
**Remplace a l'etape 6ter par Nginx Proxy Manager — voir ADR-007.**

---

## Étape 6bis — Renouvellement TLS automatique (Certbot HTTP-01) — ~~remplacé~~
**Date :** 2026-08-11 | **Commits :** `da833ee`, `c43ce4e`, `1d9f764`, `03b2620`

Service `certbot` + defi HTTP-01 + bascule automatique de certificat dans le
`gateway`. **Remplace a l'etape 6ter — voir ADR-007.**

---

## Étape 6ter — Migration vers Nginx Proxy Manager + DNS-01 OVH
**Date :** 2026-08-11 | **Commits :** `7cd5403`, `66321a4`
**ADR :** [ADR-007](./adr/ADR-007-migration-npm-dns01.md)

### Contexte
L'utilisateur a indique que l'infrastructure existante du groupe
(`groupe-odisecure.fr`) utilise deja Nginx Proxy Manager avec un defi DNS-01
(plugin OVH), provisionne par des scripts Python existants. Decision
d'aligner Telix_Secure_Pro sur cette approche plutot que de maintenir une
solution Nginx/Certbot HTTP-01 parallele.

### Ce qui a été fait
- **Suppression** des modules `gateway/` et `certbot/` (Nginx custom + Certbot HTTP-01)
- **Nouveau module `npm-provisioning/`** avec deux scripts idempotents,
  adaptes des scripts fournis par l'utilisateur :
  - `ovh_dns_setup.py` : cree/met a jour l'enregistrement DNS A du sous-domaine
    via l'API OVH officielle (client `ovh`)
  - `npm_proxy_host_setup.py` : cree/met a jour le proxy host dans NPM avec
    certificat Let's Encrypt via **defi DNS-01** (`dns_challenge: True`,
    `dns_provider: ovh`), au lieu du HTTP-01 utilise precedemment
- `docker-compose.yml` allege : les services applicatifs restent inchanges,
  mais ne sont plus exposes/geres par un reverse proxy local (NPM etant
  externe a ce depot)
- Documentation : `docs/npm-provisioning.md`, `ADR-007`

### Decisions techniques
- **DNS-01 conserve** (pas de retour a HTTP-01) : c'est le mecanisme deja
  configure sur l'infra NPM existante (plugin OVH), et il a l'avantage de ne
  pas necessiter l'exposition publique du port 80
- **Secrets jamais committes** : les scripts lisent des variables
  d'environnement ; seuls des placeholders figurent dans `.env.example`
- **Client officiel `ovh`** plutot que des appels API bruts : plus robuste et
  maintenu par la communaute

### ⚠️ Points a valider avec l'utilisateur
- Nom/port exacts du conteneur cible pour le forward NPM une fois
  `captive-portal` developpe (suppose actuellement : `captive-portal:80`)
- Frequence d'execution des scripts de provisioning (ponctuelle vs automatisee)
- Version de NPM et configuration exacte du plugin DNS OVH deja en place
  (non verifiable depuis ce depot)

### Prochaines étapes identifiées
- [ ] `captive-portal` : frontend React, cible finale du proxy host NPM
- [ ] `siem-connector` : dernier module fonctionnel restant

---

## Étape 7 — Module `siem-connector` _(à venir)_

### Objectifs
- Logstash consomme les logs Graylog (GELF output ou lecture Elasticsearch)
- Formatage CEF (Common Event Format), incluant MAC et type d'identifiant
- Envoi vers Sekoia via Syslog/TLS port 10514

---

## Étape 8 — Module `captive-portal` _(à venir)_

### Objectifs
- Interface React + TailwindCSS
- Récupération des paramètres MAC/IP transmis par l'équipement Wi-Fi (ADR-005)
- Page login corporate (LDAP/Azure AD) et visiteur (SMS OTP / numéro de chambre)
- Point de forward final du proxy host NPM (`TELIX_FORWARD_HOST`/`TELIX_FORWARD_PORT`)
