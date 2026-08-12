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
| **Extension mobilite/teletravail** | 🔲 Cadrage fait (ADR-008), dev à venir | `<ce commit>` |

**🎉 Le périmètre initial (portail captif Wi-Fi) est entièrement développé et
déployable. Le projet entre maintenant dans une phase d'extension vers la
mobilité/télétravail (agent + passerelle de filtrage centralisée).**

---

## Étape 11 — Cadrage de l'extension mobilité/télétravail (ADR-008)
**Date :** 2026-08-12 | **Commit :** `<ce commit>`

### Contexte
L'utilisateur souhaite, en plus du portail captif Wi-Fi, pouvoir tracer et
filtrer l'usage Internet des utilisateurs en mobilité/télétravail -- un cas
d'usage différent (pas de reseau local physique commun a instrumenter),
qui se rapproche d'une solution SWG (Secure Web Gateway).

### Décisions actees (ADR-008)
- Deux familles de cas d'usage (local vs distant), un moteur commun
  (`auth-service`, `log-service` reutilisés)
- **Agent Windows et macOS** uniquement pour l'instant (pas de mobile)
- **Filtrage par categories** dans un premier temps (SNI/DNS/proxy explicite),
  **inspection SSL/TLS profonde explicitement reportée**
- **Mode dégradé pensé** en cas de coupure agent <-> passerelle centrale :
  pas de blocage total (pas de kill switch strict par defaut), maintien
  d'une liste de filtrage "de base" en cache local sur le poste, et mise en
  cache locale des evenements de tracabilite, rejoués vers `log-service` au
  retour de la connexion
- Architecture pensée sans etat sur la passerelle centrale (comme
  `proxy-service`), pour scalabilite horizontale future (200 utilisateurs
  au départ, croissance anticipée)

### ⚠️ Points explicitement ouverts, à lever avant developpement
- **Choix definitif des briques** (WireGuard, SquidGuard/e2guardian ou
  filtrage DNS, HAProxy/Traefik) -- aucune n'a ete testee a ce stade, un PoC
  est necessaire
- **Conception detaillee du mode degrade** (format du cache local chiffre,
  duree de retention locale, protocole de rejeu des logs) -- pas encore
  specifie techniquement
- **Robustesse de e2guardian** en particulier a verifier (etat de
  maintenance variable observe dans l'ecosysteme open source) avant de s'y
  engager

### Prochaines étapes
- [ ] PoC technique : agent WireGuard + passerelle Squid/SquidGuard sur un
      poste de test, mesure de la latence/charge
- [ ] Concevoir le protocole agent <-> passerelle (enregistrement, sync des
      listes de filtrage, rejeu des logs en mode degrade)
- [ ] Definir le format et la duree du cache local chiffre sur le poste
- [ ] Etendre `auth-service` pour la generation de configuration agent par
      utilisateur (cles WireGuard, association a une identite existante)
