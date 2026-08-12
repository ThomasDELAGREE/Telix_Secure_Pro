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
| `scripts/deploy.sh` | ✅ Terminé | `4343971`, `0348a14` |
| CI/CD complet | 🟡 Partiel | `cc8f08e` |
| **Extension mobilite/teletravail** | 🔲 Briques choisies (ADR-008), PoC à venir | `7dc2068`, `<ce commit>` |

**🎉 Le périmètre initial (portail captif Wi-Fi) est entièrement développé et
déployable. Le choix des briques pour l'extension mobilité/télétravail est
désormais acté, un PoC technique est la prochaine étape.**

---

## Étape 12 — Choix des briques pour l'extension mobilité/télétravail (ADR-008)
**Date :** 2026-08-12 | **Commit :** `<ce commit>`

### Contexte
Suite au cadrage de l'étape 11, il fallait trancher les briques concrètes.
L'utilisateur proposait initialement SquidGuard pour le filtrage -- une
vérification a montré que ce projet est en pratique à l'arrêt (dernière
version stable vieille de plus de 15 ans, support retiré par pfSense/
Netgate). **e2guardian** a été retenu à la place, après vérification de
son activité réelle (commits récents constatés sur son dépôt officiel).

### Décisions actees
- **Tunnel** : WireGuard
- **Filtrage par catégories** : e2guardian (et non SquidGuard)
- **Blocklists** : UT1 Blacklists (Université Toulouse 1)
- **Cache local chiffré (agent)** : SQLite + SQLCipher
- **Rétention locale du cache en mode dégradé : 30 jours** (decision
  utilisateur)
- **Equilibrage de charge de la passerelle** : HAProxy

### ⚠️ Points explicitement ouverts, à lever avant developpement complet
- **PoC technique requis** : aucune de ces briques n'a encore été testée
  dans le cadre concret de ce projet (charge, compatibilité fine)
- **Vitalité d'e2guardian à surveiller dans la durée** (mode maintenance,
  pas de developpement actif de nouvelles fonctionnalites observe)
- **Conception detaillee du protocole de synchronisation/rejeu** des logs
  en mode degrade, et de la purge a 30 jours -- pas encore specifiee
  techniquement

### Prochaines étapes
- [ ] PoC technique : agent WireGuard + passerelle e2guardian sur un poste
      de test, mesure de la latence/charge
- [ ] Concevoir le protocole agent <-> passerelle (enregistrement, sync des
      listes de filtrage UT1, rejeu des logs en mode degrade, purge 30j)
- [ ] Etendre `auth-service` pour la generation de configuration agent par
      utilisateur (cles WireGuard, association a une identite existante)
- [ ] Mettre en place HAProxy devant la passerelle de filtrage
