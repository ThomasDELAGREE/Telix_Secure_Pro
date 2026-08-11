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
| `captive-portal` | 🔲 À faire | — |
| `log-service` | 🔲 À faire | — |
| `siem-connector` | 🔲 À faire | — |
| `gateway` | 🔲 À faire | — |
| CI/CD complet | 🟡 Partiel | `cc8f08e` |

---

## Étape 1 — Structure de base
**Date :** 2026-08-11 | **Commit :** `ad8147f`

### Ce qui a été fait
- Création du dépôt GitHub public, licence Apache 2.0
- Arborescence complète des modules
- `README.md`, `.gitignore`, `docs/`, `infra/docker-compose.yml`, `infra/.env.example`

### Décisions techniques
- Stack 100% open source : FastAPI, React, Squid, Graylog, Logstash, PostgreSQL, Redis
- Architecture microservices pour déploiement indépendant de chaque composant
- Docker Compose pour le développement, Kubernetes envisagé pour la production

---

## Étape 2 — Module `auth-service`
**Date :** 2026-08-11 | **Commits :** `2988100`, `cc8f08e`

### Ce qui a été fait
- API FastAPI avec 4 endpoints (health, corporate, request-otp, verify-otp)
- Auth AD/LDAP via `ldap3` (bind service + bind utilisateur, vérif compte actif)
- Auth Azure AD via ROPC flow + Microsoft Graph
- OTP SMS visiteur via Kannel + Redis (TTL 5 min, usage unique)
- Traçabilité complète en base PostgreSQL (`auth_sessions`)
- Migrations Alembic
- 7 tests unitaires (OTP, JWT, health)
- Pipeline CI GitHub Actions

### Décisions techniques
- **ROPC flow Azure AD** : adapté au portail captif interne. À remplacer par Authorization Code flow pour usage public.
- **OTP usage unique** : suppression Redis immédiate après validation.
- **Traçabilité systématique** : succès ET échecs enregistrés avec IP, user-agent, timestamp.
- **JWT HS256** : suffisant pour usage interne. Migrer vers RS256 si multi-service.

---

## Étape 3 — Module `proxy-service`
**Date :** 2026-08-11 | **Commits :** `ed5ab70`, `6e71cdb`

### Ce qui a été fait
- Proxy Squid (port 3128) avec contrôle d'accès par IP authentifiée
- ACL externe (`session_helper.py`) interrogeant Redis (`telix:active_session:<ip>`)
- `auth-service` écrit désormais ce mapping IP→utilisateur à chaque login réussi
  (`session_registry.py`)
- Logs Squid au format JSON personnalisé (`telix_json`) + `gelf_shipper.py` vers Graylog
- Intégration dans `infra/docker-compose.yml`
- 3 tests unitaires, documentation dédiée `docs/proxy-service.md`

### Décisions techniques
- **Couplage faible via Redis** entre auth-service et proxy-service
- **Squid + external_acl_type** pour brancher un helper personnalisé
- **GELF/UDP** natif Graylog, faible overhead

---

## Étape 4 — Identification par MAC + identifiant générique
**Date :** 2026-08-11 | **Commits :** `101d623`, `5379e19`, `72061e1`, `8f041a1`
**ADR :** [ADR-005](./adr/ADR-005-mac-and-generic-identity.md)

### Ce qui a été fait
- Ajout du champ optionnel `mac_address` sur tous les endpoints d'authentification
  (`/auth/corporate`, `/auth/visitor/request-otp`, `/auth/visitor/verify-otp`, nouveau
  `/auth/visitor/room`), normalisé via `app/core/mac_utils.py`
- Nouveau type d'authentification visiteur : **numéro de chambre** (déploiement
  hôtelier) via `room_service.py` + table `room_codes` (migration `0002`)
- Le registre Redis (`session_registry.py`) stocke désormais une identité complète
  en JSON : `{ user_identifier, identifier_type, mac_address }` — `identifier_type`
  ∈ `{ldap, azure_ad, sms_otp, room_number}`
- `proxy-service` (`session_helper.py`, `gelf_shipper.py`) lit ce format enrichi et
  ajoute `_mac_address` / `_identifier_type` dans les logs GELF envoyés à Graylog
- Rétro-compatibilité assurée : l'ancien format Redis (chaîne brute) reste lisible
- 11 nouveaux tests unitaires (MAC utils, session registry enrichi, room service)
- Documentation mise à jour : `docs/auth-service.md`, `docs/proxy-service.md`, ADR-005

### Décisions techniques
- **MAC en métadonnée de traçabilité, pas en clé de contrôle d'accès** : le contrôle
  d'accès Squid reste basé sur l'IP (c'est elle que Squid voit réellement) ; la MAC
  enrichit les logs pour la conformité/traçabilité mais n'est pas le critère d'autorisation.
- **Champ MAC optionnel partout** : le système dégrade gracieusement si l'équipement
  Wi-Fi ne transmet pas cette information.
- **room_codes provisionné manuellement** dans un premier temps (voir hypothèse ci-dessous).

### ⚠️ Hypothèses à valider (bloquantes pour la suite)
- **Récupération de la MAC** : un navigateur ne peut pas lire la MAC de l'appareil.
  Elle doit être transmise par l'équipement Wi-Fi (contrôleur) lors de la redirection
  vers le portail captif, typiquement en paramètre d'URL (`?mac=...`). C'est le standard
  chez Unifi/Cisco/Aruba/Ruckus/MikroTik, mais **à confirmer avec l'équipement Wi-Fi cible**
  du client final.
- **Intégration PMS hôtelier** : pour un vrai déploiement hôtel, il faudrait connecter
  `room_codes` à un PMS (Odoo, Mews, Opera...) pour la génération/révocation automatique
  des codes à l'arrivée/départ. Non fait à ce stade — à planifier si ce cas d'usage
  est priorisé.

### Prochaines étapes identifiées
- [ ] `captive-portal` : récupérer les paramètres `mac`/`ip` transmis par l'équipement
  Wi-Fi lors de la redirection, et les injecter dans les appels à `auth-service`
- [ ] Endpoint admin pour provisionner/révoquer les codes de chambre (CRUD `room_codes`)
- [ ] Filtrage de contenu (SquidGuard), métriques Prometheus (reporté depuis l'étape 3)

---

## Étape 5 — Module `captive-portal` _(à venir)_

### Objectifs
- Interface React + TailwindCSS
- Récupération des paramètres MAC/IP transmis par l'équipement Wi-Fi (ADR-005)
- Page login corporate (username/password + choix LDAP ou Azure AD)
- Page login visiteur (SMS OTP **ou** numéro de chambre)
- Redirection automatique après auth réussie
- Pages d'erreur et session expirée

---

## Étape 6 — Module `log-service` _(à venir)_

### Objectifs
- Graylog + Elasticsearch + MongoDB
- Rétention 365 jours (ILM Elasticsearch)
- Dashboard Graylog : activité par utilisateur/MAC, alertes
- Réception des logs proxy-service (GELF enrichi) déjà prête côté émetteur

---

## Étape 7 — Module `siem-connector` _(à venir)_

### Objectifs
- Logstash consomme les logs Graylog
- Formatage CEF (Common Event Format), incluant MAC et type d'identifiant
- Envoi vers Sekoia via Syslog/TLS port 10514

---

## Étape 8 — Module `gateway` _(à venir)_

### Objectifs
- Nginx reverse proxy + terminaison TLS (Let's Encrypt)
- Règles de redirection portail captif
- Rate limiting global
- Headers de sécurité (HSTS, CSP, X-Frame-Options)
