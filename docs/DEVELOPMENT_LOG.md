# Journal de développement — Telix_Secure_Pro

> Ce fichier est mis à jour à chaque étape du développement.
> Il sert de fil conducteur pour reprendre le projet à tout moment.

---

## État global du projet

| Module | Statut | Commit(s) |
|---|---|---|
| Structure de base | ✅ Terminé | `ad8147f` |
| `auth-service` (portail captif) | ✅ Terminé | `2988100`, `cc8f08e`, `6e71cdb`, `101d623` |
| `proxy-service` | ✅ Terminé | `ed5ab70`, `6e71cdb`, `5379e19` |
| `log-service` | ✅ Terminé | `488fc11`, `5c126f1` |
| Conformité LCEN (retention) | ✅ Confirmée | `0a5b899` (ADR-006) |
| ~~`gateway` (Nginx custom)~~ | ❌ Remplace | → voir ADR-007 |
| ~~`certbot` (HTTP-01)~~ | ❌ Remplace | → voir ADR-007 |
| `npm-provisioning` (NPM + DNS-01 OVH) | ✅ Terminé | `7cd5403`, `66321a4` |
| `captive-portal` | ✅ Terminé | `e73e5bf`, `51b69c4`, `76de9df`, `3d8677c`, `bcebdd3` |
| `siem-connector` | ✅ Terminé (voir limitation auth Sekoia) | `bcef70f`, `002c519` |
| `scripts/deploy.sh` | ✅ Terminé | `4343971`, `0348a14` |
| CI/CD complet | 🟡 Partiel | `cc8f08e` |
| **Extension mobilité/télétravail (ADR-008)** | | |
| `remote-agent` (squelette) | 🟡 Squelette, non fonctionnel de bout en bout | `38b6f12` |
| `filtering-gateway` (squelette) | 🟡 Squelette, non fonctionnel de bout en bout | `d9957e1` |
| `auth-service` — enrollment agent WireGuard | 🟡 Partiel (voir limitations) | `f717ed0`, `7329dba` |

**🎉 Le périmètre initial (portail captif Wi-Fi) est entièrement développé et
déployable. L'extension mobilité/télétravail est en cours de construction
(squelettes poses, briques choisies, mais integration de bout en bout pas
encore realisee ni testee).**

---

## Étape 13 — Squelette `remote-agent`
**Date :** 2026-08-12 | **Commit :** `38b6f12`

### Ce qui a été fait
- `config.py` : configuration locale persistée (chemins Windows/macOS)
- `local_cache.py` : cache SQLite des événements de navigation en mode
  dégradé, purge automatique à 30 jours (décision utilisateur, ADR-008)
- `fallback_filter.py` : logique de décision "domaine bloqué ou non" en
  local, alimentée par la dernière liste connue
- `sync.py` : orchestration de la synchronisation périodique agent ↔
  passerelle centrale
- `enrollment.py` : association poste ↔ identité utilisateur (voir
  étape 15 pour la révision sécurité)

### ⚠️ Limitations explicites (non résolues)
- Chiffrement SQLCipher **non implémenté** (sqlite3 standard utilisé en
  attendant un binding disponible) -- point de sécurité bloquant avant
  production, le cache contient des données de navigation
- Aucun mécanisme réel d'application du blocage sur le système (DNS ?
  pare-feu ? proxy local ?) -- à concevoir avec l'utilisateur
- Aucun installeur (MSI/.pkg) -- code Python seul pour l'instant

---

## Étape 14 — Squelette `filtering-gateway`
**Date :** 2026-08-12 | **Commit :** `d9957e1`

### Ce qui a été fait
- `e2guardian/e2guardian.conf.template` : gabarit de filtrage par
  catégories (non testé en conditions réelles)
- `scripts/sync_ut1_blocklists.py` : squelette de téléchargement/
  normalisation des listes UT1 -- s'arrête volontairement
  (`SystemExit`) car l'URL/format UT1 n'ont pas pu être vérifiés (aucun
  accès réseau dans l'environnement de développement)
- `haproxy/haproxy.cfg` : base de répartition sans état (UDP/WireGuard),
  non testée avec des tunnels réels
- `api/main.py` (FastAPI) : `/health`, `/blocklist`, `/events/replay` --
  **sans authentification** pour l'instant (TODO explicite)

### ⚠️ Limitations explicites (non résolues)
- e2guardian jamais testé concrètement
- URL/format des listes UT1 non confirmés
- Aucune authentification sur l'API interne (`/blocklist`,
  `/events/replay`) -- bloquant avant tout déploiement, ces endpoints
  seront exposés aux agents distants
- Pas de relai réel vers `log-service` (GELF) -- journalisation locale
  uniquement pour l'instant
- HAProxy non testé avec plusieurs tunnels WireGuard simultanés

---

## Étape 15 — Extension `auth-service` : enrollment agent WireGuard
**Date :** 2026-08-12 | **Commits :** `f717ed0` (première version), `7329dba` (révision sécurité + séparation des sujets)

### Première version (`f717ed0`)
- `wireguard_service.py` : génération de paires de clés X25519 +
  allocation d'IP dans le pool `10.200.0.0/16`
- `models/agent_enrollment.py` : table de suivi des enrollments
- `routers/auth_agent.py` : `POST /auth/agent/enroll`

### Révision sécurité et périmètre (`7329dba`) -- suite à discussion avec l'utilisateur
Deux points souleveés et traités, documentés dans
`docs/adr/ADR-008-complement-2026-08-12.md` :

1. **Génération de clé côté agent, plus côté serveur** : la clé privée
   WireGuard est désormais générée localement par l'agent
   (`generate_local_keypair()` dans `remote-agent/agent/enrollment.py`)
   et ne quitte jamais le poste. `auth-service` ne génère, ne voit et ne
   stocke plus aucune clé privée (`generate_keypair()` retiré de
   `wireguard_service.py`). Confirmé avec l'utilisateur : ce processus
   reste **entièrement automatique**, sans action manuelle au-delà du
   login initial.
2. **Séparation stricte portail captif / agent d'itinérance** :
   `/auth/agent/enroll` rejette désormais explicitement en 403 les
   identités éphémères/partagées du portail captif (`sms_otp`,
   `room_number`) -- seules les identités durables (`ldap`, `azure_ad`)
   peuvent enrôler un agent d'itinérance. Rationale détaillé dans l'ADR.

### ⚠️ Limitations explicites (non résolues)
- **Le peer (clé publique + IP) n'est pas encore enregistré auprès d'un
  vrai serveur WireGuard côté `filtering-gateway`** -- sans cette étape,
  la clé générée par l'agent n'ouvre pas encore de tunnel fonctionnel.
  C'est le point bloquant principal pour rendre ce chantier utilisable
  de bout en bout.
- Le flux d'appel HTTP réel entre `remote-agent` et `auth-service`
  (`EnrollmentClient.enroll()`) reste à implémenter et tester en
  intégration -- actuellement il lève une erreur explicite si appelé.
- Allocation IP séquentielle simple -- suffisante à 200 utilisateurs,
  à revoir si le volume augmente fortement (cf commentaire dans le code).

### Prochaines étapes proposées
- [ ] Câbler l'enregistrement réel du peer WireGuard côté
      `filtering-gateway` (c'est le point bloquant n°1 actuellement)
- [ ] Implémenter l'appel HTTP réel `remote-agent` → `auth-service`
      (`EnrollmentClient.enroll()`)
- [ ] Ajouter l'authentification sur l'API interne de `filtering-gateway`
- [ ] Résoudre le chiffrement SQLCipher du cache local de l'agent
- [ ] PoC réel e2guardian + vérification des listes UT1 (nécessite un
      accès réseau, absent de l'environnement de développement actuel)
