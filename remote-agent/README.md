# remote-agent

Squelette de l'agent Telix Secure Pro pour les postes en mobilite/
teletravail (Windows et macOS), voir ADR-008.

## ⚠️ Etat actuel : squelette de developpement, non fonctionnel de bout en bout

Ce module pose la structure et les interfaces principales, mais **plusieurs
points bloquants restent a lever avant une utilisation reelle** -- ils sont
listes explicitement ci-dessous et dans `docs/DEVELOPMENT_LOG.md`. Rien
n'est cache : ce qui suit n'est pas encore implemente.

## Structure

```
remote-agent/
└── agent/
    ├── config.py             # Configuration locale persistee (config.json)
    ├── local_cache.py         # Cache local des evenements (mode degrade, retention 30j)
    ├── fallback_filter.py     # Filtrage de secours par domaine (liste en cache local)
    ├── sync.py                # Orchestration de la synchronisation periodique
    └── enrollment.py          # Association du poste a une identite utilisateur
```

## Fonctionnement vise (rappel ADR-008)

1. **Enrollment** : l'utilisateur s'authentifie (corporate ou visiteur, meme
   logique que le portail captif) via `auth-service`, qui retourne une
   configuration WireGuard associee a son identite
2. **Tunnel** : l'agent etablit un tunnel WireGuard vers `filtering-gateway`,
   tout le trafic web transite alors par la passerelle centrale (e2guardian)
3. **Synchronisation** : periodiquement, l'agent recupere la derniere liste
   de blocage (pour le mode degrade) et rejoue les evenements en cache
4. **Mode degrade** : si la passerelle est injoignable, l'agent continue de
   filtrer localement avec la derniere liste connue, et met les evenements
   en cache local (30 jours max, purge automatique au-dela)

## ⚠️ Points bloquants avant mise en production (a lever explicitement)

1. **Chiffrement du cache local non implemente** : `local_cache.py` utilise
   `sqlite3` standard, PAS SQLCipher comme annonce dans l'ADR-008 -- aucun
   binding SQLCipher n'est disponible dans l'environnement de developpement
   actuel. Le cache contient des donnees de navigation, sensibles -- ce
   point doit etre traite avant tout deploiement reel.
2. **Integration reseau du filtrage non implementee** : `fallback_filter.py`
   ne pose que la logique de decision (domaine bloque ou non) -- il n'y a
   pas encore de mecanisme reel qui applique ce blocage sur le systeme
   (DNS local ? pare-feu ? proxy local ?). A concevoir avec l'utilisateur.
3. **API `filtering-gateway` inexistante** : ce module n'existe pas encore
   dans le projet -- `sync.py` et `enrollment.py` posent l'orchestration
   attendue cote agent, mais les appels HTTP reels sont en `TODO` explicite
   tant que l'API de la passerelle n'est pas specifiee.
4. **Extension d'`auth-service` non faite** : la generation de cles/config
   WireGuard par utilisateur n'existe pas encore cote `auth-service`.
5. **Permissions du fichier de configuration local** (`config.py`) pas
   durcies -- il contient une cle privee WireGuard en clair pour l'instant,
   sans restriction de permissions systeme (chmod/ACL).
6. **Aucun packaging installeur** (MSI Windows, .pkg macOS) -- uniquement
   du code Python pour l'instant, pas encore un executable/service installable.

## Tests

Des tests unitaires seront ajoutes dans une prochaine etape pour
`local_cache.py` et `fallback_filter.py` (logique testable sans dependance
reseau). `sync.py` et `enrollment.py` necessitent l'API `filtering-gateway`
et l'extension d'`auth-service` avant de pouvoir etre testes de bout en
bout.
