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
| `captive-portal` | 🔲 À faire | — |
| `siem-connector` | 🔲 À faire | — |
| `gateway` | 🔲 À faire | — |
| CI/CD complet | 🟡 Partiel | `cc8f08e` |

---

## Étape 1 — Structure de base
**Date :** 2026-08-11 | **Commit :** `ad8147f`

Création du dépôt, arborescence complète, README, docker-compose de base.
Stack choisie : FastAPI, React, Squid, Graylog, Logstash, PostgreSQL, Redis (100% open source).

---

## Étape 2 — Module `auth-service`
**Date :** 2026-08-11 | **Commits :** `2988100`, `cc8f08e`

API FastAPI (corporate LDAP/Azure AD + visiteur OTP SMS), traçabilité en base,
migrations Alembic, tests, CI GitHub Actions.

---

## Étape 3 — Module `proxy-service`
**Date :** 2026-08-11 | **Commits :** `ed5ab70`, `6e71cdb`

Proxy Squid + ACL externe (Redis) + logs JSON + shipper GELF vers Graylog.
Couplage faible auth-service <-> proxy-service via Redis partagé.

---

## Étape 4 — Identification par MAC + identifiant générique
**Date :** 2026-08-11 | **Commits :** `101d623`, `5379e19`, `72061e1`, `8f041a1`
**ADR :** [ADR-005](./adr/ADR-005-mac-and-generic-identity.md)

Champ `mac_address` sur tous les endpoints, nouveau type d'auth `room_number`
(hôtel), registre Redis enrichi (JSON), logs proxy enrichis. MAC = métadonnée de
traçabilité, pas clé de contrôle d'accès (limitation NAT documentee).

**Hypotheses a valider :** récupération de la MAC côté équipement Wi-Fi (paramètre
URL lors de la redirection) ; intégration PMS hôtelier pour `room_codes`.

---

## Étape 5 — Module `log-service`
**Date :** 2026-08-11 | **Commits :** `488fc11`, `5c126f1`

### Ce qui a été fait
- Stack Graylog 6 + Elasticsearch 8 + MongoDB 6 ajoutée au `docker-compose.yml`
- Conteneur de **provisioning automatique** (`log-service/provisioning/provision.py`) :
  crée via l'API REST Graylog, de facon idempotente :
  - Un **index set `telix_web_traffic`** avec rotation quotidienne et retention
    de **365 jours** (suppression automatique au-dela)
  - Un **input GELF UDP** (port 12201) recevant les logs de `proxy-service`
  - Un **stream `Telix - Traffic Web`** routant les messages `source=proxy-service`
    vers l'index set dedie
- Variables d'environnement ajoutées (`GRAYLOG_PASSWORD_SECRET`,
  `GRAYLOG_ROOT_PASSWORD_SHA2/PLAIN`, `LOG_RETENTION_DAYS`)
- Documentation dédiée : `docs/log-service.md`

### Décisions techniques
- **Provisioning as code** : toute la configuration fonctionnelle de Graylog
  (input, index set, stream) est créée via script versionné plutôt que
  manuellement dans l'UI — reproductible, reviewé en revue de code, idempotent.
- **Retention par suppression** (`DeletionRetentionStrategy`) après 365 jours,
  pas d'archivage à froid à ce stade (voir hypothèse ci-dessous).
- **Isolation par stream** : les logs de trafic web sont séparés des logs
  système Graylog par défaut, dans leur propre index set.

### ⚠️ Hypothèse à valider
- **Suppression vs archivage a froid** : au bout d'1 an, les logs sont
  **supprimés definitivement**. Si une obligation reglementaire ou
  contractuelle impose plutot un archivage (ex: export vers un stockage froid
  type MinIO/S3 avant suppression), il faudra completer le provisioning.
  A confirmer avec le client/l'obligation legale visee (ex: LCEN en France
  impose 1 an de conservation minimum, mais ne precise pas nativement de mode
  d'archivage particulier au-dela).

### Prochaines étapes identifiées
- [ ] Dashboard Graylog pre-construit (activite par utilisateur/MAC)
- [ ] Regles d'alerte (volume anormal, categories sensibles)
- [ ] `siem-connector` : Logstash consomme Graylog -> format CEF -> Sekoia

---

## Étape 6 — Module `siem-connector` _(à venir)_

### Objectifs
- Logstash consomme les logs Graylog (via GELF output Graylog ou lecture Elasticsearch)
- Formatage CEF (Common Event Format), incluant MAC et type d'identifiant
- Envoi vers Sekoia via Syslog/TLS port 10514

---

## Étape 7 — Module `captive-portal` _(à venir)_

### Objectifs
- Interface React + TailwindCSS
- Récupération des paramètres MAC/IP transmis par l'équipement Wi-Fi (ADR-005)
- Page login corporate (LDAP/Azure AD) et visiteur (SMS OTP / numéro de chambre)

---

## Étape 8 — Module `gateway` _(à venir)_

### Objectifs
- Nginx reverse proxy + TLS (Let's Encrypt), redirection portail captif, rate limiting, headers de securite
