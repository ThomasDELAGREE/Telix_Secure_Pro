# ADR-003 — Stratégie de rétention des logs

**Date :** 2026-08-11 | **Statut :** Accepté

## Contexte

La réglementation (LCEN, RGPD) impose la conservation des logs de connexion pendant **1 an** pour les opérateurs Wi-Fi publics.

## Décision

**Graylog + Elasticsearch** avec ILM (Index Lifecycle Management) :
- Index rolling mensuel
- Suppression automatique des index > 365 jours
- Graylog comme interface de consultation et d'alerte

## Conséquences

- Elasticsearch : 4 Go RAM minimum dédiés
- Logs d'auth PostgreSQL : purge planifiée après 1 an
- Logs proxy Squid : envoi GELF UDP vers Graylog
