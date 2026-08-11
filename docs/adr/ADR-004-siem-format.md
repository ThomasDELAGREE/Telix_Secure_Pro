# ADR-004 — Format d'export SIEM (Sekoia)

**Date :** 2026-08-11 | **Statut :** Accepté

## Contexte

Sekoia.io supporte plusieurs formats d'ingestion. Nous devons choisir le format le plus adapté pour les événements de sécurité.

## Options envisagées

| Format | Pour | Contre |
|---|---|---|
| **CEF over Syslog/TLS** | Standard SIEM, supporté nativement par Sekoia | Verbeux |
| JSON | Flexible | Mapping manuel côté Sekoia |
| Syslog brut | Simple | Parsing complexe |

## Décision

**CEF over Syslog/TLS** vers `intake.sekoia.io:10514`.
Logstash comme pipeline de transformation (Graylog → CEF → Sekoia).

## Conséquences

- Logstash doit accéder à `intake.sekoia.io:10514`
- Clé d'intake : `SEKOIA_INTAKE_KEY`
- Mapping : `user_identifier` → `duser`, `ip_address` → `src`, `auth_type` → `cs1`
