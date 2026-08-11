# Documentation — auth-service

## Vue d'ensemble

Le `auth-service` est le cœur du système d'authentification de Telix_Secure_Pro.
Il expose une API REST FastAPI gérant deux grandes familles d'authentification :
- **Corporate** : Active Directory/LDAP et Azure AD
- **Visiteur** : OTP par SMS via Kannel, ou identifiant de chambre (déploiement hôtelier)

Depuis l'ADR-005, chaque authentification peut être associée à une **adresse MAC**
(si transmise par l'équipement Wi-Fi) et produit un **identifiant générique typé**
(`identifier_type`), consommé par `proxy-service` pour la traçabilité.

**Port :** `8000` | **Tech :** Python 3.12 / FastAPI / SQLAlchemy / Redis

---

## Architecture interne

```
auth-service/
├── app/
│   ├── main.py              # Point d'entrée FastAPI, CORS, routers
│   ├── core/
│   │   ├── config.py        # Variables d'environnement (Pydantic Settings)
│   │   ├── security.py      # Génération et décodage JWT
│   │   ├── database.py      # Connexion PostgreSQL (SQLAlchemy)
│   │   ├── redis_client.py  # Client Redis singleton
│   │   └── mac_utils.py     # Normalisation d'adresse MAC (ADR-005)
│   ├── models/
│   │   ├── session.py       # ORM : table auth_sessions (+ colonne mac_address)
│   │   └── room_code.py     # ORM : table room_codes (auth par chambre, ADR-005)
│   ├── schemas/
│   │   └── auth.py          # Pydantic (requêtes / réponses), valide mac_address
│   ├── services/
│   │   ├── ldap_service.py      # Auth AD/LDAP
│   │   ├── azure_ad_service.py  # Auth Azure AD
│   │   ├── otp_service.py       # OTP SMS
│   │   ├── room_service.py      # Auth par numéro de chambre (hôtel, ADR-005)
│   │   └── session_registry.py  # Registre Redis IP -> identité complète
│   └── routers/
│       ├── health.py            # GET /health
│       ├── auth_corporate.py    # POST /auth/corporate
│       └── auth_visitor.py      # POST /auth/visitor/*
├── migrations/              # Alembic (0001: auth_sessions, 0002: room_codes)
├── tests/                   # pytest
├── Dockerfile
├── requirements.txt
└── alembic.ini
```

---

## Endpoints API

### `GET /health`
```json
{ "status": "ok", "service": "auth-service", "timestamp": "2026-08-11T10:00:00Z" }
```

### `POST /auth/corporate`
**Body**
```json
{ "username": "john.doe", "password": "secret", "provider": "ldap", "mac_address": "AA:BB:CC:DD:EE:FF" }
```
> `provider` : `"ldap"` ou `"azure_ad"` | `mac_address` optionnel, normalisée automatiquement

**Réponse 200**
```json
{ "access_token": "eyJ...", "token_type": "bearer", "expires_in": 28800, "user_identifier": "john.doe", "auth_type": "ldap" }
```

### `POST /auth/visitor/request-otp`
**Body** `{ "phone": "+33612345678", "mac_address": "AA:BB:CC:DD:EE:FF" }` (téléphone au format E.164 obligatoire, MAC optionnelle)

**Réponse 200**
```json
{ "message": "Code OTP envoyé par SMS.", "phone": "+33612345678", "expires_in": 300 }
```

### `POST /auth/visitor/verify-otp`
**Body** `{ "phone": "+33612345678", "otp": "123456", "mac_address": "AA:BB:CC:DD:EE:FF" }`

**Réponse 200** : même structure que `/auth/corporate` (`auth_type: "sms_otp"`)

### `POST /auth/visitor/room` _(nouveau — ADR-005)_
Authentification visiteur par numéro de chambre (déploiement hôtelier).

**Body**
```json
{ "room_number": "101", "access_code": "secret123", "mac_address": "AA:BB:CC:DD:EE:FF" }
```

**Réponse 200** : même structure que `/auth/corporate` (`auth_type: "room_number"`)

**Erreurs**
| Code | Raison |
|---|---|
| 401 | Numéro de chambre inconnu, code incorrect, chambre inactive ou hors période de validité |

> ⚠️ **Hypothèse à valider** : la table `room_codes` est provisionnée manuellement pour
> l'instant. Une intégration avec un PMS hôtelier (Odoo, Mews, Opera...) permettrait de
> synchroniser automatiquement les codes à l'arrivée/départ des clients.

---

## Adresse MAC — comment est-elle récupérée ?

⚠️ **Hypothèse à valider avec l'équipement Wi-Fi cible.** Un navigateur ne peut pas lire
la MAC de l'appareil (limitation navigateur). Elle doit être transmise par le contrôleur
Wi-Fi lors de la redirection vers le portail captif, généralement en paramètre d'URL
(ex: `https://portal.example.com/login?mac=AA:BB:CC:DD:EE:FF&ip=...`), comme le font la
plupart des contrôleurs standards (Unifi, Cisco, Aruba, Ruckus, MikroTik...). Le
`captive-portal` (frontend, à venir) devra récupérer ce paramètre et le transmettre
tel quel à `auth-service` dans le champ `mac_address`.

Si la MAC n'est pas disponible, tous les endpoints fonctionnent quand même (champ
optionnel) — le système dégrade gracieusement vers un mapping par IP uniquement.

---

## Modèle de données

### Table `auth_sessions`

| Colonne | Type | Description |
|---|---|---|
| `id` | UUID | Identifiant unique |
| `user_identifier` | VARCHAR(255) | Username AD, numéro de téléphone, ou numéro de chambre |
| `auth_type` | VARCHAR(50) | `ldap`, `azure_ad`, `sms_otp`, `sms_otp_request`, `room_number` |
| `ip_address` | VARCHAR(45) | IP client (IPv4/IPv6) |
| `mac_address` | VARCHAR(17) | Adresse MAC normalisée (`aa:bb:cc:dd:ee:ff`), si transmise |
| `user_agent` | TEXT | User-Agent navigateur |
| `success` | BOOLEAN | Succès ou échec |
| `failure_reason` | TEXT | Raison de l'échec |
| `created_at` | TIMESTAMPTZ | Horodatage |
| `expires_at` | TIMESTAMPTZ | Expiration session |

### Table `room_codes` _(nouveau — ADR-005)_

| Colonne | Type | Description |
|---|---|---|
| `room_number` | VARCHAR(50) | Numéro de chambre (clé primaire) |
| `access_code` | VARCHAR(50) | Code d'accès associé |
| `active` | BOOLEAN | Chambre active ou désactivée |
| `valid_from` / `valid_until` | TIMESTAMPTZ | Période de validité (séjour) |
| `created_at` | TIMESTAMPTZ | Horodatage de création |

---

## Registre de sessions (Redis) — format enrichi

Depuis l'ADR-005, la clé Redis `telix:active_session:<ip>` stocke un objet JSON :
```json
{ "user_identifier": "john.doe", "identifier_type": "ldap", "mac_address": "aa:bb:cc:dd:ee:ff" }
```
Ce registre est consommé par `proxy-service` pour autoriser le trafic et enrichir
les logs de traçabilité (voir `docs/proxy-service.md`).

---

## Tests

```bash
cd auth-service
pip install -r requirements.txt pytest pytest-asyncio httpx
pytest tests/ -v
```

| Fichier | Couverture |
|---|---|
| `test_health.py` | GET /health |
| `test_otp_service.py` | Normalisation, génération, vérif OTP (5 cas) |
| `test_security.py` | JWT create/decode, token invalide |
| `test_mac_utils.py` | Normalisation MAC (4 formats valides + invalides) |
| `test_session_registry.py` | Registre Redis avec identité complète (JSON) |
| `test_room_service.py` | Auth par chambre (succès, code faux, inconnue, inactive, expirée) |

---

## Lancement local

```bash
cd auth-service
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp ../infra/.env.example .env  # adapter les valeurs
alembic upgrade head
uvicorn app.main:app --reload --port 8000
# Swagger UI : http://localhost:8000/docs
```
