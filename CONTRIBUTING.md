# Guide de contribution — Telix_Secure_Pro

## Branches

| Branche | Usage |
|---|---|
| `main` | Code stable, déployable |
| `develop` | Intégration des features |
| `feat/<nom>` | Nouvelle fonctionnalité |
| `fix/<nom>` | Correction de bug |
| `docs/<nom>` | Documentation uniquement |

## Convention de commits (Conventional Commits)

```
<type>(<scope>): <description courte>
```

**Types :** `feat`, `fix`, `docs`, `chore`, `test`, `refactor`, `ci`

**Exemples :**
```
feat(auth-service): ajouter rate limiting sur /auth/visitor/request-otp
fix(ldap): corriger la détection des comptes désactivés
docs(auth-service): documenter les variables Azure AD
```

## Workflow

```bash
git checkout -b feat/mon-module
# ... développer + tester ...
pytest tests/ -v
git add . && git commit -m "feat(mon-module): description"
git push origin feat/mon-module
# Ouvrir une Pull Request vers main
```

## Standards de code

- **Python** : PEP 8, type hints obligatoires, docstrings sur les classes/méthodes publiques
- **Tests** : toute nouvelle fonctionnalité doit être accompagnée de tests unitaires
- **Env vars** : toute nouvelle variable → `infra/.env.example` + doc du module concerné
- **ADR** : toute décision d'architecture → nouveau fichier dans `docs/adr/`

## Mettre à jour le journal de développement

A chaque étape complétée, mettre à jour `docs/DEVELOPMENT_LOG.md` :
1. Passer le statut du module de 🔲 à ✅
2. Ajouter le(s) commit(s) de référence
3. Documenter les décisions prises et les prochaines étapes
