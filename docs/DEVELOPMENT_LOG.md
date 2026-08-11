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
| `gateway` | ✅ Terminé | `b78a383`, `d24c1ab` |
| `captive-portal` | 🔲 À faire | — |
| `siem-connector` | 🔲 À faire | — |
| CI/CD complet | 🟡 Partiel | `cc8f08e` |

---

## Étape 1 — Structure de base
**Date :** 2026-08-11 | **Commit :** `ad8147f`

Création du dépôt, arborescence complète, README, docker-compose de base.
Stack : FastAPI, React, Squid, Graylog, Logstash, PostgreSQL, Redis, Nginx (100% open source).

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
(hôtel), registre Redis enrichi (JSON), logs proxy enrichis.

**Hypotheses ouvertes :** récupération de la MAC côté équipement Wi-Fi ; intégration
PMS hôtelier pour `room_codes`.

---

## Étape 5 — Module `log-service`
**Date :** 2026-08-11 | **Commits :** `488fc11`, `5c126f1`

Stack Graylog 6 + Elasticsearch 8 + MongoDB 6, provisioning automatique (index set
retention 365j, input GELF, stream de routage). Voir `docs/log-service.md`.

---

## Étape 5bis — Conformité LCEN (retention 1 an)
**Date :** 2026-08-11 | **Commit :** `0a5b899` | **ADR :** [ADR-006](./adr/ADR-006-lcen-retention-compliance.md)

Analyse du décret n°2021-1362 (LCEN, art. 6) : la stratégie de retention par
suppression après 365 jours **est conforme** à l'obligation legale de conservation
d'1 an des données de connexion. Aucun changement de code necessaire.

**Points de vigilance juridiques restants (hors code) :** champ d'application exact
du decret selon le contexte de deploiement, mention dans les mentions legales du
portail, procedure de communication sur reqisition.

---

## Étape 6 — Module `gateway`
**Date :** 2026-08-11 | **Commits :** `b78a383`, `d24c1ab`

### Ce qui a été fait
- Reverse proxy **Nginx** (image Alpine, legere) comme point d'entree unique du portail
- **Redirection HTTP -> HTTPS** systematique (les identifiants ne transitent jamais en clair)
- **TLS** : certificat auto-signe genere automatiquement en dev si absent
  (`entrypoint.sh`), volume `gateway_certs` prevu pour de vrais certificats en prod
- **Routage** : `/` -> `captive-portal`, `/api/auth/*` -> `auth-service`
- **Rate limiting** à deux niveaux : global (10 req/s/IP) et renforce sur l'auth
  (5 req/min/IP) pour limiter le brute-force sur les identifiants/OTP
- **Headers de securite OWASP** : HSTS, CSP, X-Frame-Options, X-Content-Type-Options,
  Referrer-Policy, Permissions-Policy
- Documentation dédiée : `docs/gateway.md`

### Décisions techniques
- **Nginx plutot que Traefik/Caddy** : simplicite, tres large adoption, configuration
  explicite et versionnee (pas de decouverte automatique de services a gerer ici,
  la topologie est fixe et connue)
- **Rate limiting renforce specifiquement sur l'auth** : le portail captif expose
  des endpoints sensibles (mot de passe AD, OTP SMS) qui doivent etre proteges du
  brute-force independamment du reste du trafic
- **Certificat auto-signe en dev, volume dedie en prod** : permet de demarrer la
  stack immediatement sans dependance a un nom de domaine reel, tout en preparant
  le terrain pour Let's Encrypt/Certbot en production

### ⚠️ Hypotheses à valider
- **Renouvellement TLS automatique (Certbot)** non implementé à ce stade —
  necessite un nom de domaine public resolvable, à mettre en place au deploiement reel
- **Content-Security-Policy restrictive** (`'self'` uniquement) : à adapter une fois
  `captive-portal` developpe si des ressources externes (CDN, polices) sont utilisees

### Prochaines étapes identifiées
- [ ] `captive-portal` : frontend React consommé via ce gateway
- [ ] `siem-connector` : dernier module fonctionnel restant
- [ ] Automatisation Certbot pour la production

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
- Consomme l'API via `/api/auth/*` derriere le `gateway`
