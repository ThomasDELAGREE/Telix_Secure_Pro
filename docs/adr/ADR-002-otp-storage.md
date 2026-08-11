# ADR-002 — Stockage des OTP

**Date :** 2026-08-11 | **Statut :** Accepté

## Contexte

Les codes OTP doivent être stockés temporairement (TTL court), supprimés après usage unique, et accessibles rapidement.

## Options envisagées

| Option | Pour | Contre |
|---|---|---|
| **Redis** | TTL natif, ultra-rapide, DEL pour usage unique | Service supplémentaire |
| PostgreSQL | Déjà présent | Nettoyage TTL manuel, plus lent |
| Mémoire applicative | Zéro dépendance | Non partageable, perte au redémarrage |

## Décision

**Redis** retenu. TTL natif (`SETEX`) + suppression immédiate (`DEL`) après validation.

## Conséquences

- Clé Redis : `telix:otp:<phone_e164>`
- TTL configurable via `OTP_EXPIRY_SECONDS` (défaut : 300s)
- OTP perdus en cas de redémarrage Redis (comportement acceptable)
