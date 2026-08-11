# Documentation — log-service

## Vue d'ensemble

Le `log-service` est le point central de **traçabilité** de Telix_Secure_Pro. Il repose
sur **Graylog** (+ Elasticsearch pour le stockage/recherche, MongoDB pour la config
Graylog). Il reçoit :
- Les logs de navigation web enrichis envoyés par `proxy-service` (GELF/UDP,
  utilisateur, MAC, type d'identifiant, URL, statut, durée...)
- Potentiellement d'autres sources (Syslog UDP 1514, extensible)

Il garantit la **retention legale/contractuelle d'1 an** et sert de source pour
l'export vers le SIEM Sekoia (`siem-connector`, étape suivante).

**Port :** `9000` (UI/API), `12201/udp` (GELF), `1514/udp` (Syslog) | **Tech :** Graylog 6 + Elasticsearch 8 + MongoDB 6

---

## Architecture interne

```
log-service/
└── provisioning/
    ├── Dockerfile
    ├── requirements.txt
    └── provision.py     # Provisioning automatique via l'API REST Graylog
```

Graylog lui-meme n'est pas "codeé" (image officielle `graylog/graylog:6.0`), mais sa
configuration fonctionnelle (input GELF, index set avec retention, stream de routage)
est **provisionnée automatiquement** au demarrage par un petit conteneur Python
ephemere (`log-service-provisioning`), pour que tout soit reproductible et versionne
dans le depot (pas de configuration manuelle via l'UI).

---

## Ce que fait `provision.py`

Au demarrage de la stack, ce script :

1. **Attend** que l'API Graylog soit disponible (`/api/system/lbstatus`)
2. **Cree l'index set `telix_web_traffic`** : rotation quotidienne, strategie de
   retention par suppression apres `LOG_RETENTION_DAYS` jours (365 par defaut)
3. **Cree l'input GELF UDP** sur le port 12201 (reception des logs de `proxy-service`)
4. **Cree le stream `Telix - Traffic Web`** qui route les messages ayant
   `source=proxy-service` vers l'index set dedie (isolation du reste des logs systeme Graylog)

Le script est **idempotent** : relancable plusieurs fois sans creer de doublons
(chaque etape verifie l'existence avant creation).

---

## Strategie de retention (1 an)

| Parametre | Valeur par defaut | Description |
|---|---|---|
| `LOG_RETENTION_DAYS` | `365` | Nombre de jours (indices quotidiens) conserves |
| Rotation | Quotidienne (`P1D`) | Un nouvel indice Elasticsearch chaque jour |
| Strategie au-dela | Suppression (`DeletionRetentionStrategy`) | L'indice le plus ancien est supprime automatiquement |

> ⚠️ **Hypothese a valider** : la strategie actuelle est la **suppression definitive**
> au-dela d'1 an. Si une contrainte reglementaire ou contractuelle impose un archivage
> a froid (plutot qu'une suppression pure), il faudra ajouter une etape d'export
> (ex : vers un stockage S3-compatible / MinIO) avant la suppression de l'indice.
> A ce stade, ce n'est pas implemente.

---

## Variables d'environnement

| Variable | Description |
|---|---|
| `GRAYLOG_PASSWORD_SECRET` | Secret de chiffrement interne Graylog (>= 16 car., generer avec `pwgen -N 1 -s 96`) |
| `GRAYLOG_ROOT_PASSWORD_SHA2` | SHA-256 du mot de passe admin (`echo -n "motdepasse" \| sha256sum`) |
| `GRAYLOG_ROOT_PASSWORD_PLAIN` | Meme mot de passe en clair, utilise uniquement par le conteneur de provisioning pour appeler l'API REST |
| `LOG_RETENTION_DAYS` | Duree de conservation en jours (365 = 1 an) |

---

## Flux de donnees

```
proxy-service (Squid + gelf_shipper.py)
        │  GELF/UDP :12201
        ▼
log-service (Graylog)
        │  index set "telix_web_traffic", retention 365j
        ▼
Elasticsearch (stockage/recherche) + MongoDB (config Graylog)
        │
        ▼  (etape suivante)
siem-connector (Logstash) ──────▶ Sekoia (Syslog/TLS, format CEF)
```

---

## Verification manuelle

```bash
# 1. Demarrer la stack
docker compose -f infra/docker-compose.yml up -d

# 2. Se connecter a l'UI Graylog
# http://localhost:9000  (utilisateur: admin, mot de passe: GRAYLOG_ROOT_PASSWORD_PLAIN)

# 3. Verifier que l'index set et le stream existent (menu System > Indices / Streams)

# 4. Generer un peu de trafic via proxy-service, puis rechercher dans Graylog :
#    Search > stream "Telix - Traffic Web" > filtrer par _user, _mac_address, _identifier_type
```

---

## Prochaines ameliorations identifiees

- [ ] Dashboard Graylog pre-construit (activite par utilisateur, top domaines visites, alertes)
- [ ] Regles d'alerte Graylog (ex: volume anormal, acces a des categories sensibles)
- [ ] Etudier l'archivage a froid avant suppression (voir hypothese ci-dessus)
- [ ] Durcir l'acces reseau a l'input GELF (actuellement ouvert sur le reseau Docker interne uniquement, a verifier en production)
