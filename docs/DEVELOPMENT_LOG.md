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
| Renouvellement TLS (Certbot) | ✅ Terminé | `da833ee`, `c43ce4e`, `1d9f764`, `03b2620` |
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

---

## Étape 6 — Module `gateway`
**Date :** 2026-08-11 | **Commits :** `b78a383`, `d24c1ab`

Reverse proxy Nginx : redirection HTTP->HTTPS, routage vers captive-portal et
auth-service, rate limiting (global + renforce sur l'auth), headers de securite
OWASP. Voir `docs/gateway.md`.

**Hypotheses ouvertes à l'epoque :** renouvellement TLS automatique (resolu
ci-dessous), CSP a adapter selon le frontend.

---

## Étape 6bis — Renouvellement TLS automatique (Certbot)
**Date :** 2026-08-11 | **Commits :** `da833ee`, `c43ce4e`, `1d9f764`, `03b2620`

### Ce qui a été fait
- Nouveau service **`certbot`** (client officiel Let's Encrypt, image officielle) :
  émission initiale + boucle de renouvellement automatique (verif. toutes les 12h)
- **Défi ACME HTTP-01** : le `gateway` sert desormais `/.well-known/acme-challenge/`
  en clair (meme apres la redirection HTTPS generale) via un volume webroot partage
- **Bascule automatique** dans `gateway/entrypoint.sh` : detecte un certificat
  Let's Encrypt valide et l'utilise a la place du certificat auto-signe, avec
  `nginx -s reload` sans coupure de service
- **Fallback robuste** : si le domaine n'est pas public (dev local), l'echec
  d'emission est logge sans jamais bloquer le demarrage — le certificat
  auto-signe de secours prend le relais automatiquement
- Documentation dédiée : `docs/tls-renewal-certbot.md`

### Décisions techniques
- **Certbot plutot que reverse-proxy integre type Traefik/Caddy** : coherent avec
  le choix Nginx deja fait pour `gateway` (ADR implicite de l'etape 6), pas de
  remise en cause de l'architecture existante
- **HTTP-01 plutot que DNS-01** : plus simple a mettre en oeuvre sans dependance
  a un fournisseur DNS specifique ; suffisant tant que le port 80 est exposable
  publiquement
- **Reload sans coupure** (`nginx -s reload`) plutot qu'un restart du conteneur :
  evite toute interruption du portail lors du renouvellement

### ⚠️ Limitations connues (documentées dans `docs/tls-renewal-certbot.md`)
- Un seul domaine gere pour l'instant (`GATEWAY_SERVER_NAME`) — pas de
  multi-domaine
- Uniquement le defi HTTP-01 — pas de support DNS-01 si le port 80 ne peut pas
  etre expose publiquement dans certains contextes de deploiement

### Prochaines étapes identifiées
- [ ] `captive-portal` : frontend React
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
- Consomme l'API via `/api/auth/*` derriere le `gateway`
