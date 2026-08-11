# Documentation — proxy-service

## Vue d'ensemble

Le `proxy-service` est le point de passage obligé de tout le trafic web des utilisateurs
authentifiés. Il repose sur **Squid** et remplit deux rôles :

1. **Contrôle d'accès** : seules les IP correspondant à une session authentifiée
   (enregistrée par `auth-service`) peuvent naviguer.
2. **Traçabilité** : chaque requête HTTP/HTTPS est journalisée (utilisateur, URL, méthode,
   statut, taille, durée) puis expédiée vers `log-service` (Graylog) pour la rétention 1 an.

**Port :** `3128` | **Tech :** Squid + Python 3 (scripts helper)

---

## Architecture interne

```
proxy-service/
├── Dockerfile
├── entrypoint.sh              # Init cache Squid + lance le shipper + Squid
├── requirements.txt
└── squid/
    ├── squid.conf              # Config Squid (ACL, logformat, http_port)
    ├── session_helper.py       # ACL externe : vérifie IP authentifiée via Redis
    └── gelf_shipper.py         # Suit access.log et envoie en GELF/UDP vers Graylog
```

---

## Fonctionnement

### 1. Contrôle d'accès (session_helper.py)

Squid utilise un **external_acl_type** qui appelle `session_helper.py` pour chaque
nouvelle connexion. Le script :
1. Reçoit l'IP source du client sur stdin (protocole Squid helper)
2. Interroge Redis : clé `telix:active_session:<ip>`
3. Répond `OK user=<identifiant>` si la session existe, `ERR` sinon

Cette clé Redis est écrite par `auth-service` (`session_registry.py`) à chaque
authentification réussie (corporate ou visiteur), avec le même TTL que le JWT.
→ **Couplage faible** : les deux services communiquent uniquement via Redis, pas d'appel direct.

### 2. Traçabilité (gelf_shipper.py)

Squid écrit chaque requête dans `access.log` au format JSON personnalisé (`telix_json`) :
```json
{"timestamp":"...","client_ip":"10.0.0.5","user":"john.doe","method":"GET","url":"https://...","status":200,"bytes":1024,"duration_ms":120,"user_agent":"..."}
```
Le shipper suit ce fichier en continu (`tail -f` maison), parse chaque ligne et
l'envoie en GELF (compressé zlib) vers `log-service` sur le port UDP `12201`.

---

## Variables d'environnement

| Variable | Défaut | Description |
|---|---|---|
| `REDIS_URL` | `redis://redis:6379/0` | Redis partagé avec auth-service |
| `GRAYLOG_HOST` | `log-service` | Hôte Graylog (GELF) |
| `GRAYLOG_GELF_PORT` | `12201` | Port UDP GELF de Graylog |

---

## Intégration avec l'infrastructure Wi-Fi existante

Le `proxy-service` est conçu pour s'intégrer à **n'importe quel équipement Wi-Fi** :
1. L'équipement (Unifi, pfSense, OpenWRT...) redirige tout le trafic HTTP/HTTPS
   non authentifié vers `captive-portal` (port 8080)
2. Après authentification réussie, l'utilisateur est redirigé vers le proxy
   (port 3128), configuré via WPAD/PAC ou routage transparent (iptables REDIRECT)
3. Le proxy autorise le trafic uniquement pour les IP authentifiées

> ⚠️ **Hypothèse à valider** : le mapping se fait par IP. Sur un réseau NATé ou avec
> plusieurs utilisateurs derrière la même IP (rare en Wi-Fi mais possible), il faudra
> envisager un mapping par IP+MAC ou par plage de ports (NAT explicite).

---

## Tests manuels

```bash
# Simuler une session active dans Redis
redis-cli SET telix:active_session:192.168.1.50 "john.doe" EX 300

# Tester le helper directement
echo "192.168.1.50" | python3 proxy-service/squid/session_helper.py
# -> OK user=john.doe

echo "10.10.10.10" | python3 proxy-service/squid/session_helper.py
# -> ERR message="not_authenticated"
```

---

## Prochaines améliorations identifiées

- [ ] Ajouter le filtrage de contenu (SquidGuard) pour bloquer les catégories à risque
- [ ] Gérer le cas multi-utilisateurs derrière une même IP (NAT)
- [ ] Ajouter des métriques Prometheus (nombre de requêtes, refus, latence)
- [ ] Chiffrer le flux GELF (actuellement UDP en clair — acceptable en réseau interne, à sécuriser sinon)
