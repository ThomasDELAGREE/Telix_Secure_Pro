# Documentation — auth-service

## Vue d'ensemble

Le `auth-service` est le cœur du système d'authentification de Telix_Secure_Pro.
Il expose une API REST FastAPI gérant deux types d'authentification :
- **Corporate** : Active Directory/LDAP et Azure AD
- **Visiteur** : OTP par SMS via Kannel

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
│   │   └── redis_client.py  # Client Redis singleton
│   ├── models/
│   │   └── session.py       # ORM : table auth_sessions
│   ├── schemas/
│   │   └── auth.py          # Pydantic (requêtes / réponses)
│   ├── services/
│   │   ├── ldap_service.py      # Auth AD/LDAP
│   │   ├── azure_ad_service.py  # Auth Azure AD
│   │   └── otp_service.py       # OTP SMS
│   └── routers/
│       ├── health.py            # GET /health
│       ├── auth_corporate.py    # POST /auth/corporate
│       └── auth_visitor.py      # POST /auth/visitor/*
├── migrations/              # Alembic
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
{ "username": "john.doe", "password": "secret", "provider": "ldap" }
```
> `provider` : `"ldap"` ou `"azure_ad"`

**Réponse 200**
```json
{ "access_token": "eyJ...", "token_type": "bearer", "expires_in": 28800, "user_identifier": "john.doe", "auth_type": "ldap" }
```

| Code | Raison |
|---|---|
| 401 | Identifiants invalides ou compte désactivé |
| 400 | Provider non supporté |

### `POST /auth/visitor/request-otp`
**Body** `{ "phone": "+33612345678" }` (format E.164 obligatoire)

**Réponse 200**
```json
{ "message": "Code OTP envoyé par SMS.", "phone": "+33612345678", "expires_in": 300 }
```

### `POST /auth/visitor/verify-otp`
**Body** `{ "phone": "+33612345678", "otp": "123456" }`

**Réponse 200** : même structure que `/auth/corporate`

---

## Variables d'environnement

| Variable | Requis | Défaut | Description |
|---|---|---|---|
| `JWT_SECRET` | ✅ | — | Clé secrète JWT |
| `JWT_EXPIRY_MINUTES` | — | `480` | Durée validité JWT |
| `POSTGRES_DB` | ✅ | — | Nom de la base |
| `POSTGRES_USER` | ✅ | — | Utilisateur PostgreSQL |
| `POSTGRES_PASSWORD` | ✅ | — | Mot de passe PostgreSQL |
| `POSTGRES_HOST` | — | `postgres` | Hôte PostgreSQL |
| `REDIS_URL` | — | `redis://redis:6379/0` | URL Redis |
| `LDAP_SERVER` | LDAP | — | URL serveur AD |
| `LDAP_BASE_DN` | LDAP | — | Base DN |
| `LDAP_BIND_DN` | LDAP | — | DN compte de service |
| `LDAP_BIND_PASSWORD` | LDAP | — | Mot de passe service |
| `LDAP_USE_SSL` | — | `false` | Activer LDAPS |
| `AZURE_TENANT_ID` | Azure | — | ID tenant Azure |
| `AZURE_CLIENT_ID` | Azure | — | ID app Azure |
| `AZURE_CLIENT_SECRET` | Azure | — | Secret app Azure |
| `KANNEL_URL` | SMS | — | URL passerelle Kannel |
| `KANNEL_USER` | SMS | — | User Kannel |
| `KANNEL_PASSWORD` | SMS | — | Password Kannel |
| `SMS_SENDER` | — | `TelixSecure` | Expéditeur SMS |
| `OTP_EXPIRY_SECONDS` | — | `300` | TTL OTP (secondes) |
| `OTP_LENGTH` | — | `6` | Longueur code OTP |

---

## Modèle de données — `auth_sessions`

| Colonne | Type | Description |
|---|---|---|
| `id` | UUID | Identifiant unique |
| `user_identifier` | VARCHAR(255) | Username AD ou numéro de téléphone |
| `auth_type` | VARCHAR(50) | `ldap`, `azure_ad`, `sms_otp`, `sms_otp_request` |
| `ip_address` | VARCHAR(45) | IP client (IPv4/IPv6) |
| `mac_address` | VARCHAR(17) | Adresse MAC (optionnel) |
| `user_agent` | TEXT | User-Agent navigateur |
| `success` | BOOLEAN | Succès ou échec |
| `failure_reason` | TEXT | Raison de l'échec |
| `created_at` | TIMESTAMPTZ | Horodatage |
| `expires_at` | TIMESTAMPTZ | Expiration session |

---

## Flux détaillés

### Corporate LDAP
```
1. POST /auth/corporate {username, password, provider: "ldap"}
2. Bind compte de service sur AD
3. Recherche DN via sAMAccountName
4. Vérif userAccountControl (bit 2 = compte désactivé)
5. Bind utilisateur pour valider le mot de passe
6. Enregistrement auth_sessions
7. Génération JWT (sub, auth_type, email, display_name)
8. Retour token
```

### Visiteur SMS OTP
```
1. POST /auth/visitor/request-otp {phone}
2. Normalisation numéro E.164
3. Génération OTP 6 chiffres
4. Stockage Redis : telix:otp:<phone> TTL=300s
5. Envoi SMS via Kannel
6. POST /auth/visitor/verify-otp {phone, otp}
7. Lecture Redis, comparaison
8. Suppression Redis (usage unique)
9. Enregistrement auth_sessions + JWT
```

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
