# Documentation — proxy-service

## Vue d'ensemble

Le `proxy-service` est le point de passage obligé de tout le trafic web des utilisateurs
authentifiés. Il repose sur **Squid** et remplit deux rôles :

1. **Contrôle d'accès** : seules les IP correspondant à une session authentifiée
   (enregistrée par `auth-service`) peuvent naviguer.
2. **Traçabilité enrichie** : chaque requête HTTP/HTTPS est journalisée (utilisateur,
   **type d'identifiant**, **adresse MAC**, URL, méthode, statut, taille, durée) puis
   expédiée vers `log-service` (Graylog) pour la rétention 1 an.

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
    └── gelf_shipper.py         # Suit access.log, enrichit (MAC, type), envoie en GELF
```

---

## Fonctionnement

### 1. Contrôle d'accès (session_helper.py)

Squid utilise un **external_acl_type** qui appelle `session_helper.py` pour chaque
nouvelle connexion. Le script :
1. Reçoit l'IP source du client sur stdin (protocole Squid helper)
2. Interroge Redis : clé `telix:active_session:<ip>`, valeur JSON
   `{ user_identifier, identifier_type, mac_address }` (ADR-005)
3. Répond `OK user=<identifiant>` si la session existe, `ERR` sinon

> Rétro-compatible : si la valeur Redis est encore une simple chaîne (ancien format),
> elle est utilisée telle quelle comme identifiant.

Cette clé Redis est écrite par `auth-service` (`session_registry.py`) à chaque
authentification réussie (corporate, SMS, ou numéro de chambre), avec le même TTL
que le JWT. → **Couplage faible** : les deux services communiquent uniquement via
Redis, pas d'appel direct.

### 2. Traçabilité enrichie (gelf_shipper.py)

Squid écrit chaque requête dans `access.log` au format JSON personnalisé (`telix_json`).
Le shipper suit ce fichier, parse chaque ligne, **relit Redis pour récupérer l'identité
complète** (MAC, type d'authentification) associée à l'IP source, puis envoie un message
GELF enrichi vers `log-service` :

```json
{
  "_user": "john.doe",
  "_identifier_type": "ldap",
  "_mac_address": "aa:bb:cc:dd:ee:ff",
  "_method": "GET",
  "_url": "https://...",
  "_status": 200,
  "_duration_ms": 120
}
```

`_identifier_type` peut valoir : `ldap`, `azure_ad`, `sms_otp`, `room_number`, ou `unknown`.

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
1. L'équipement (Unifi, pfSense, OpenWRT, Cisco, Aruba...) redirige tout le trafic
   HTTP/HTTPS non authentifié vers `captive-portal`, en transmettant généralement
   l'IP **et la MAC** du client en paramètres d'URL
2. Après authentification réussie, l'utilisateur est redirigé vers le proxy
   (port 3128), configuré via WPAD/PAC ou routage transparent (iptables REDIRECT)
3. Le proxy autorise le trafic uniquement pour les IP authentifiées, et les logs
   sont enrichis avec la MAC reçue lors de l'authentification

> ⚠️ **Hypothèse à valider** : voir ADR-005 pour le détail sur la récupération de la MAC
> côté équipement Wi-Fi (le navigateur ne peut pas la lire directement).
>
> Le mapping session reste basé sur l'IP source pour le contrôle d'accès effectif
> (c'est cette IP qui génère le trafic vu par Squid). La MAC est propagée à titre de
> **métadonnée de traçabilité** dans les logs, pas comme clé de contrôle d'accès
> principale : sur un réseau NATé avec plusieurs utilisateurs derrière la même IP,
> le contrôle d'accès reste au niveau IP (limite connue).

---

## Tests manuels

```bash
# Simuler une session active dans Redis (nouveau format enrichi)
redis-cli SET telix:active_session:192.168.1.50 '{"user_identifier":"john.doe","identifier_type":"ldap","mac_address":"aa:bb:cc:dd:ee:ff"}' EX 300

# Tester le helper directement
echo "192.168.1.50" | python3 proxy-service/squid/session_helper.py
# -> OK user=john.doe

echo "10.10.10.10" | python3 proxy-service/squid/session_helper.py
# -> ERR message="not_authenticated"
```

---

## Prochaines améliorations identifiées

- [ ] Ajouter le filtrage de contenu (SquidGuard) pour bloquer les catégories à risque
- [ ] Explorer un contrôle d'accès combinant IP+MAC (nécessite validation réseau/DHCP)
- [ ] Ajouter des métriques Prometheus (nombre de requêtes, refus, latence)
- [ ] Chiffrer le flux GELF (actuellement UDP en clair — acceptable en réseau interne, à sécuriser sinon)
