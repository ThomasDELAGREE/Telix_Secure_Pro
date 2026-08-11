# Journal de développement — Telix_Secure_Pro

> Ce fichier est mis à jour à chaque étape du développement.
> Il sert de fil conducteur pour reprendre le projet à tout moment.

---

## État global du projet

| Module | Statut | Commit(s) |
|---|---|---|
| Structure de base | ✅ Terminé | `ad8147f` |
| `auth-service` | ✅ Terminé | `2988100`, `cc8f08e` |
| `captive-portal` | 🔲 À faire | — |
| `proxy-service` | 🔲 À faire | — |
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

## Étape 3 — Module `captive-portal` _(à venir)_

### Objectifs
- Interface React + TailwindCSS
- Page login corporate (username/password + choix LDAP ou Azure AD)
- Page login visiteur (saisie numéro → OTP)
- Redirection automatique après auth réussie
- Pages d'erreur et session expirée

---

## Étape 4 — Module `proxy-service` _(à venir)_

### Objectifs
- Proxy transparent Squid
- Injection identité utilisateur dans les headers (X-Authenticated-User)
- Log de toutes les URLs visitées par utilisateur
- Export logs vers Graylog (GELF UDP)

---

## Étape 5 — Module `log-service` _(à venir)_

### Objectifs
- Graylog + Elasticsearch + MongoDB
- Rétention 365 jours (ILM Elasticsearch)
- Dashboard Graylog : activité par utilisateur, alertes

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
