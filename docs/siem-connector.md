# Documentation — siem-connector (Logstash -> CEF -> Sekoia)

## Vue d'ensemble

Dernier maillon de la chaine de tracabilite : ce module recupere les logs de
trafic web enrichis (utilisateur, MAC, IP, URL, statut...) et les transmet a
la plateforme SIEM **Sekoia**, au format **CEF (Common Event Format)**, via
un flux **syslog/TLS**.

Outil retenu : **Logstash OSS** (licence Apache 2.0, sans les modules
payants Elastic/X-Pack) -- 100% open source et gratuit, conforme a la
contrainte du projet.

---

## Architecture du flux complet

```
proxy-service (Squid)
      | GELF/UDP (port 12201)
      v
log-service (Graylog)  --- stockage + retention 1 an (LCEN, ADR-006)
      | GELF/UDP (port 12202, output a configurer manuellement dans Graylog)
      v
siem-connector (Logstash)
      | reformatage CEF
      | syslog/TLS (port 10514)
      v
Sekoia (intake SIEM)
```

**Important** : `siem-connector` ne remplace pas `log-service` -- Graylog
reste la source de verite pour la retention 1 an. Ce module ne fait que
**dupliquer/relayer** en temps reel une partie du flux vers Sekoia, a des
fins de detection/correlation de securite.

---

## Configuration cote Graylog (a realiser manuellement)

Le pipeline Logstash attend une **deuxieme** sortie GELF de la part de
Graylog (en plus de celle deja recue depuis `proxy-service`) :

1. Dans Graylog : `System > Outputs`
2. Creer un output de type **GELF UDP**, cible `siem-connector:12202`
3. Rattacher cet output au stream **"Telix - Traffic Web"** (cree par le
   provisioning de `log-service`)

> ⚠️ **Point non automatise** : contrairement au reste du provisioning
> Graylog (qui est scripte, voir `log-service/provisioning/`), cette
> configuration d'output n'a pas encore ete ajoutee au script de
> provisioning automatique. C'est une limitation actuelle a corriger si un
> deploiement reproductible complet est necessaire -- a valider si tu
> veux que je l'automatise egalement.

---

## Mapping des champs GELF -> CEF

| Champ GELF (Graylog) | Champ CEF | Signification |
|---|---|---|
| `user_identifier` | `suser` | Identifiant utilisateur (login AD, tel, n° chambre) |
| `identifier_type` | `cs1` (label `identifierType`) | Type d'identifiant (`ldap`, `azure_ad`, `sms_otp`, `room_number`) |
| `mac_address` | `cs2` | Adresse MAC de l'appareil |
| `client_ip` | `src` | IP source |
| `http_method` | `requestMethod` | Methode HTTP |
| `http_url` | `request` | URL visitee |
| `http_status` | `outcome` | Code de statut HTTP |
| `bytes_sent` | `out` | Volume de donnees |
| `duration_ms` | `cn1` (label `durationMs`) | Duree de la requete |

Une severite CEF (0-10) est calculee automatiquement a partir du code HTTP
(5xx -> 7, 4xx -> 5, sinon 2), pour faire ressortir plus facilement les
anomalies dans les regles de correlation Sekoia.

---

## Variables d'environnement

| Variable | Description |
|---|---|
| `SEKOIA_SYSLOG_HOST` | Hote de l'intake Sekoia (ex: `intake.sekoia.io`) |
| `SEKOIA_SYSLOG_PORT` | Port syslog/TLS Sekoia (ex: `10514`) |
| `SEKOIA_INTAKE_KEY` | Cle d'intake Sekoia -- **non utilisee dans le pipeline actuel** (voir limitation ci-dessous) |

---

## ⚠️ Limitation connue — authentification a l'intake Sekoia

Le pipeline actuel etablit une connexion **syslog/TLS** standard vers Sekoia,
mais **n'inclut pas encore la cle d'intake (`SEKOIA_INTAKE_KEY`)** dans le
flux envoye. Selon la methode d'authentification exacte attendue par ton
intake Sekoia (cle en en-tete syslog structure, certificat client mTLS, ou
autre), une adaptation du pipeline sera necessaire.

**Je n'ai pas invente ce detail** faute de documentation Sekoia officielle
sous la main au moment du developpement -- **a valider avec toi ou ton
contact Sekoia** avant une mise en production : quel est le mecanisme exact
d'authentification de ton intake (cle dans le message, mTLS, whitelisting
IP...) ?

---

## Tests manuels

```bash
# Simuler un message GELF entrant (sans dependre de Graylog)
echo '{"version":"1.1","host":"test","short_message":"test","user_identifier":"john.doe","identifier_type":"ldap","mac_address":"aa:bb:cc:dd:ee:ff","client_ip":"10.0.0.5","http_method":"GET","http_url":"https://example.com","http_status":200,"bytes_sent":1024,"duration_ms":42}' | nc -u -w1 localhost 12202

# Verifier la sortie CEF dans les logs du conteneur (stdout debug active)
docker logs -f telix_siem-connector_1
```

---

## Points a valider avec l'utilisateur

- **Authentification exacte attendue par l'intake Sekoia** (cle, mTLS...) --
  point bloquant pour la mise en production reelle, voir limitation ci-dessus
- **Automatisation de la configuration de l'output GELF Graylog** (actuellement manuelle)
- **Mapping CEF** : les champs choisis couvrent le besoin de tracabilite web
  de base ; a completer si Sekoia attend des champs CEF specifiques
  supplementaires (a verifier avec la documentation d'integration Sekoia)
