# Architecture Telix_Secure_Pro

## Vue d'ensemble

Telix_Secure_Pro est composé de plusieurs microservices indépendants communiquant via une API Gateway Nginx.

## Flux d'authentification

### Corporate (AD / Azure AD)
```
Client Wi-Fi → Redirection portail captif → captive-portal (React)
  → auth-service (FastAPI) → LDAP/AD ou Azure AD (OAuth2/SAML)
  → Token JWT → Accès réseau autorisé via gateway
```

### Visiteur (SMS OTP)
```
Client Wi-Fi → Portail captif → Saisie numéro de téléphone
  → auth-service → Envoi SMS OTP (Kannel/FreeSWITCH)
  → Validation OTP → Token JWT → Accès réseau autorisé
```

## Traçabilité

Tout le trafic web des utilisateurs authentifiés transite par le proxy Squid.
Les logs sont collectés par Graylog, stockés dans Elasticsearch avec une rétention de 365 jours.

## Intégration SIEM Sekoia

Logstash collecte les logs Graylog et les formate en CEF (Common Event Format)
avant de les transmettre à Sekoia via Syslog/TLS sur le port 10514.
