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
| CI/CD complet | 🟡 Partiel | `cc8f08e` |

**🎉 Tous les modules fonctionnels prevus initialement sont desormais
développés.** Reste des points d'affinage/validation lignes ci-dessous.

---

## Étape 9 — Module `siem-connector`
**Date :** 2026-08-11 | **Commits :** `bcef70f`, `002c519`

### Ce qui a été fait
- **Logstash OSS** (Apache 2.0, sans X-Pack) : pipeline unique
  `graylog-to-sekoia.conf`
- **Input GELF** (port 12202, distinct de celui de `log-service` pour ne pas
  interferer avec l'ingestion primaire Graylog)
- **Filtres** : renommage des champs vers le vocabulaire CEF, calcul d'une
  severite automatique selon le code HTTP
- **Output** : syslog/TLS vers Sekoia, codec `cef` (plugin communautaire
  `logstash-codec-cef`, open source)
- Ajout du service `siem-connector` dans `docker-compose.yml`
- Documentation : `docs/siem-connector.md`, avec mapping complet des champs

### Décisions techniques
- **Logstash OSS plutot que Fluentd/Vector** : coherent avec l'ecosysteme
  Elastic deja utilise pour `log-service` (Graylog s'appuie sur
  Elasticsearch), et le plugin CEF est mature et bien documente
- **Port GELF distinct (12202)** : evite toute interference avec le flux
  primaire `proxy-service -> log-service` (port 12201)

### ⚠️ Points a valider avec l'utilisateur (bloquants pour la mise en prod)
- **Mécanisme d'authentification exact attendu par l'intake Sekoia** (cle
  d'intake, mTLS, whitelisting IP...) -- non implemente par manque de
  documentation Sekoia officielle disponible au moment du developpement
- **Configuration de l'output GELF cote Graylog** vers `siem-connector` :
  manuelle actuellement (pas encore scriptee dans le provisioning
  `log-service`)
- **Mapping CEF** : a completer si Sekoia attend des champs specifiques
  additionnels

---

## Prochaines étapes possibles (aucune n'est bloquante pour un premier POC)

- [ ] Lever les points d'authentification Sekoia ci-dessus avec un contact Sekoia
- [ ] Automatiser l'output GELF Graylog -> siem-connector dans le provisioning
- [ ] Tests end-to-end du parcours complet (redirection Wi-Fi -> auth -> tracabilite -> SIEM)
- [ ] CI/CD complet sur tous les modules (actuellement partiel, auth-service uniquement)
- [ ] Personnalisation visuelle du portail (logo, couleurs de marque)
- [ ] Integration PMS hotelier pour le provisionnement automatique des codes de chambre
