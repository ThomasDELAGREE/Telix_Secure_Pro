# ADR-001 — Choix du framework d'authentification

**Date :** 2026-08-11 | **Statut :** Accepté

## Contexte

Le portail captif doit gérer deux types d'authentification très différents :
- Corporate : annuaire d'entreprise (AD/LDAP, Azure AD)
- Visiteur : OTP par SMS

Nous avons besoin d'un backend léger, performant, avec une bonne gestion des I/O asynchrones (appels LDAP, appels HTTP vers Azure/Kannel).

## Options envisagées

| Option | Pour | Contre |
|---|---|---|
| **FastAPI** | Async natif, validation Pydantic, doc OpenAPI auto, performant | — |
| Django REST Framework | Mature, batteries included | Trop lourd, sync par défaut |
| Flask | Léger | Pas d'async natif, validation manuelle |

## Décision

**FastAPI** retenu pour son async natif, sa validation Pydantic et sa doc OpenAPI automatique.

## Conséquences

- Python 3.12 minimum
- `httpx` pour les appels HTTP async (Azure AD, Kannel)
- Tests avec `pytest-asyncio`
