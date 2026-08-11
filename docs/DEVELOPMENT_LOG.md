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
| ~~`gateway` (Nginx custom)~~ | ❌ Remplace | → voir ADR-007 |
| ~~`certbot` (HTTP-01)~~ | ❌ Remplace | → voir ADR-007 |
| `npm-provisioning` (NPM + DNS-01 OVH) | ✅ Terminé | `7cd5403`, `66321a4` |
| `captive-portal` | ✅ Terminé | `e73e5bf`, `51b69c4`, `76de9df`, `3d8677c`, `bcebdd3` |
| `siem-connector` | ✅ Terminé (voir limitation auth Sekoia) | `bcef70f`, `002c519` |
| **`scripts/deploy.sh`** | ✅ Terminé | `4343971`, `<ce commit>` |
| CI/CD complet | 🟡 Partiel | `cc8f08e` |

**🎉 Tous les modules fonctionnels prevus initialement sont développés, et le
déploiement est desormais scripte de bout en bout (hors etapes manuelles
documentees).**

---

## Étape 10 — Script de déploiement unique `scripts/deploy.sh`
**Date :** 2026-08-11 | **Commits :** `4343971`, `<ce commit>`

### Ce qui a été fait
- **`scripts/deploy.sh`** : script bash idempotent qui enchaine
  automatiquement :
  1. Vérifications préalables (Docker, Docker Compose, presence de `infra/.env`)
  2. `docker compose up -d --build`
  3. Attente active de la disponibilite de l'API Graylog
  4. Provisioning Graylog (retention 1 an, input GELF, stream)
  5. Provisioning DNS OVH + proxy host NPM (defi DNS-01), avec option de
     saut (`SKIP_NPM=true`) pour les environnements de developpement
- Documentation complète : `docs/deployment.md` (pre-requis, variables,
  etapes manuelles restantes, verification post-deploiement)

### Décisions techniques
- **Bash plutot qu'un outil d'orchestration dedie** (Ansible, Terraform) :
  coherent avec la taille actuelle du projet (une seule machine cible),
  evite d'introduire une dependance supplementaire non demandee
- **Attente active de Graylog** (polling) plutot qu'un simple `sleep` fixe :
  plus fiable, car le temps de demarrage de Graylog/Elasticsearch peut varier
  significativement selon les ressources de la machine
- **Option `SKIP_NPM`** : permet de tester la stack applicative en local sans
  toucher a la configuration DNS/NPM de production

### ⚠️ Points a valider avec l'utilisateur
- **Dimensionnement serveur reel** non valide en conditions de charge
- **Strategie de sauvegarde** (PostgreSQL, volumes Graylog/Elasticsearch) non
  couverte par ce script -- a definir separement
- Toujours en attente : **mecanisme d'authentification Sekoia** (report
  explicitement accepte par l'utilisateur pour une prochaine etape)

---

## Prochaines étapes possibles

- [ ] Clarifier et implementer l'authentification de l'intake Sekoia
- [ ] Automatiser l'output GELF Graylog -> siem-connector dans le provisioning
- [ ] Tests end-to-end du parcours complet (redirection Wi-Fi -> auth -> tracabilite -> SIEM)
- [ ] CI/CD complet sur tous les modules (actuellement partiel, auth-service uniquement)
- [ ] Definir une strategie de sauvegarde (PostgreSQL, Graylog, Elasticsearch)
- [ ] Personnalisation visuelle du portail (logo, couleurs de marque)
- [ ] Integration PMS hotelier pour le provisionnement automatique des codes de chambre
