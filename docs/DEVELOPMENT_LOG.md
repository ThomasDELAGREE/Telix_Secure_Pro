# Journal de développement — Telix_Secure_Pro

> Ce fichier est mis à jour à chaque étape du développement.
> Il sert de fil conducteur pour reprendre le projet à tout moment.

---

## État global du projet

| Module | Statut | Commit(s) |
|---|---|---|
| Structure de base | ✅ Terminé | `ad8147f` |
| `auth-service` | ✅ Terminé | `2988100`, `cc8f08e`, `6e71cdb` |
| `proxy-service` | ✅ Terminé | `ed5ab70`, `6e71cdb` |
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

### Prochaines étapes identifiées
- [ ] Endpoint `GET /auth/sessions` pour l'admin
- [ ] Rate limiting sur `/auth/visitor/request-otp` (anti-spam SMS)
- [ ] Test LDAPS (SSL) avec un vrai AD

---

## Étape 3 — Module `proxy-service`
**Date :** 2026-08-11 | **Commits :** `ed5ab70`, `6e71cdb`

### Ce qui a été fait
- Proxy Squid (port 3128) avec contrôle d'accès par IP authentifiée
- ACL externe (`session_helper.py`) interrogeant Redis (`telix:active_session:<ip>`)
- `auth-service` écrit désormais ce mapping IP→utilisateur à chaque login réussi
  (`session_registry.py`, appelé depuis `auth_corporate.py` et `auth_visitor.py`)
- Logs Squid au format JSON personnalisé (`telix_json`) : user, url, méthode, statut, durée
- `gelf_shipper.py` : suit `access.log` et expédie chaque requête en GELF/UDP vers
  `log-service` (Graylog) pour la traçabilité et la rétention 1 an
- Dockerfile basé sur Ubuntu 24.04 + Squid + Python 3
- Intégration dans `infra/docker-compose.yml` (dépend de `redis` et `log-service`)
- 3 tests unitaires sur le registre de sessions (`test_session_registry.py`)
- Documentation dédiée : `docs/proxy-service.md`

### Décisions techniques
- **Couplage faible via Redis** : `auth-service` et `proxy-service` ne s'appellent jamais
  directement, ils partagent uniquement une clé Redis (mapping IP→utilisateur, même TTL que le JWT).
- **Squid + external_acl_type** : solution open source standard, permet de brancher un
  helper personnalisé sans forker Squid.
- **GELF/UDP** : format natif Graylog, faible overhead, adapté au volume de logs proxy.

### Limitation connue / à valider
- Le mapping est basé sur l'IP source. Si plusieurs utilisateurs partagent la même IP
  (NAT en cascade), le modèle actuel ne les distingue pas. À valider avec l'équipement
  Wi-Fi cible ; une évolution possible est un mapping par port source ou par MAC (DHCP).

### Prochaines étapes identifiées
- [ ] Filtrage de contenu (SquidGuard) pour catégories à risque
- [ ] Métriques Prometheus (requêtes, refus, latence)
- [ ] Évaluer le chiffrement du flux GELF (actuellement UDP en clair, réseau interne uniquement)

---

## Étape 4 — Module `captive-portal` _(à venir)_

### Objectifs
- Interface React + TailwindCSS
- Page login corporate (username/password + choix LDAP ou Azure AD)
- Page login visiteur (saisie numéro → OTP)
- Redirection automatique après auth réussie
- Pages d'erreur et session expirée

---

## Étape 5 — Module `log-service` _(à venir)_

### Objectifs
- Graylog + Elasticsearch + MongoDB
- Rétention 365 jours (ILM Elasticsearch)
- Dashboard Graylog : activité par utilisateur, alertes
- Réception des logs proxy-service (GELF) déjà prête côté émetteur

---

## Étape 6 — Module `siem-connector` _(à venir)_

### Objectifs
- Logstash consomme les logs Graylog
- Formatage CEF (Common Event Format)
- Envoi vers Sekoia via Syslog/TLS port 10514

---

## Étape 7 — Module `gateway` _(à venir)_

### Objectifs
- Nginx reverse proxy + terminaison TLS (Let's Encrypt)
- Règles de redirection portail captif
- Rate limiting global
- Headers de sécurité (HSTS, CSP, X-Frame-Options)
