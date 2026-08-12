# filtering-gateway

Passerelle centrale de filtrage/tracabilite pour les postes en mobilite/teletravail (agent remote-agent), voir ADR-008.

## Etat actuel : squelette de developpement, non fonctionnel de bout en bout

Comme pour remote-agent, ce module pose la structure et les choix de configuration, mais plusieurs points necessitent encore un PoC reel avant mise en production -- listes explicitement ci-dessous.

## Principe (rappel ADR-008)

```
   remote-agent (Windows/macOS)
          |
     WireGuard (UDP, tunnel chiffre)
          |
          v
   HAProxy (repartition sans etat) --> e2guardian (filtrage par categories, UT1) --> Internet
          |                                   |
          v                                   v
   API interne (FastAPI)                Logs de trafic (JSON)
   - distribution blocklist                   |
   - reception evenements rejoues             v
     par l'agent                        log-service (Graylog, retention 1 an)
```

## Structure

```
filtering-gateway/
  README.md
  docker-compose.filtering.yml
  e2guardian/
    e2guardian.conf.template
    lists/README.md
  haproxy/haproxy.cfg
  scripts/sync_ut1_blocklists.py
  api/
    main.py
    requirements.txt
```

## Points bloquants avant mise en production (a lever explicitement)

1. Aucun test reel avec e2guardian : la configuration fournie est ecrite a partir de la documentation publique du projet, pas encore validee par un deploiement/test concret.
2. Telechargement des listes UT1 non teste : sync_ut1_blocklists.py pose la logique attendue, mais l'URL exacte et le format des archives UT1 doivent etre verifies avant utilisation reelle (source academique, sans garantie de disponibilite contractuelle).
3. Authentification de l'API interne absente : /blocklist et /events/replay n'ont pour l'instant aucune authentification -- a ajouter avant tout deploiement (ex: mTLS via le tunnel WireGuard, ou jeton partage).
4. Pas d'integration reelle avec log-service : les evenements recus sur /events/replay sont pour l'instant seulement journalises localement (stdout) -- le relai effectif vers Graylog/GELF reste a cabler.
5. HAProxy non teste en UDP+WireGuard : la config fournie est une base standard, mais le comportement precis avec des tunnels WireGuard multiples necessite un PoC.
6. Generation des cles WireGuard serveur non couverte ici -- depend de l'extension d'auth-service prevue dans une prochaine etape.

## Variables d'environnement (voir .env.example a la racine d'infra/)

| Variable | Usage |
|---|---|
| FILTERING_GATEWAY_API_PORT | Port d'ecoute de l'API interne (defaut 8090) |
| UT1_BLOCKLIST_CATEGORIES | Categories UT1 a activer (ex: publicite,reseaux_sociaux,streaming) |
| E2GUARDIAN_LISTS_DIR | Repertoire local des listes normalisees pour e2guardian |

## Prochaines etapes

- [ ] PoC e2guardian + verification concrete du filtrage par categorie
- [ ] Ajouter l'authentification sur l'API interne
- [ ] Cabler le relai des evenements vers log-service (GELF)
- [ ] Tester HAProxy avec plusieurs tunnels WireGuard simultanes
