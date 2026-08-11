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
| `siem-connector` | 🔲 À faire | — |
| CI/CD complet | 🟡 Partiel | `cc8f08e` |

---

## Étape 8 — Module `captive-portal`
**Date :** 2026-08-11 | **Commits :** `e73e5bf`, `51b69c4`, `76de9df`, `3d8677c`, `bcebdd3`

### Ce qui a été fait
- **Scaffold React 18 + TypeScript + Vite + TailwindCSS**, buildable en image
  Docker legere (multi-etapes Node -> Nginx statique)
- **`WifiParamsContext.tsx`** : extraction et normalisation des parametres
  MAC/IP/SSID transmis par l'equipement Wi-Fi via l'URL de redirection
  (plusieurs alias geres pour couvrir differents constructeurs)
- **`authClient.ts`** : client Axios centralise vers `auth-service`
  (`/api/auth/*`), gestion uniforme des messages d'erreur
- **4 pages de connexion** : choix du type, corporate (LDAP/Azure AD),
  visiteur SMS (2 etapes), visiteur chambre d'hotel, page de succes
- Reintegration du service `captive-portal` dans `docker-compose.yml`, comme
  cible finale du proxy host NPM (`TELIX_FORWARD_HOST=captive-portal`)
- Tests unitaires (Vitest) sur la logique de normalisation MAC
- Documentation : `docs/captive-portal.md`

### Décisions techniques
- **Vite plutot que Create React App** : build plus rapide, plus leger,
  standard actuel de l'ecosysteme React
- **TailwindCSS** : coherent avec une personnalisation visuelle rapide selon
  l'identite de marque du client final (couleur `telix` isolee dans
  `tailwind.config.js`, facilement remplacable)
- **Alias multiples de parametres URL** pour la MAC/IP : evite de coder en
  dur un format specifique a un seul constructeur Wi-Fi, plus robuste face a
  l'inconnu du materiel final

### ⚠️ Points a valider avec l'utilisateur
- **Format exact des parametres transmis par l'equipement Wi-Fi cible** : les
  alias couverts sont ceux des conventions les plus courantes (Unifi, Cisco,
  Aruba, Ruckus, MikroTik), mais non testes contre un equipement reel
- **Integration PMS hotelier** pour automatiser le provisionnement des codes
  de chambre (actuellement manuel)
- **Identite visuelle finale** (logo, couleurs) : placeholder actuel a
  remplacer

### Prochaines étapes identifiées
- [ ] `siem-connector` : dernier module fonctionnel restant (Logstash -> CEF -> Sekoia)
- [ ] Tests end-to-end du parcours complet (redirection Wi-Fi -> auth -> acces reseau)

---

## Étape 9 — Module `siem-connector` _(à venir)_

### Objectifs
- Logstash consomme les logs Graylog (GELF output ou lecture Elasticsearch)
- Formatage CEF (Common Event Format), incluant MAC et type d'identifiant
- Envoi vers Sekoia via Syslog/TLS port 10514
