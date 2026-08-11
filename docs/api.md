# Documentation API

## auth-service (FastAPI)

Base URL : `http://<host>:8000`

### POST /auth/corporate
Authentification via AD/LDAP ou Azure AD.

**Body**
```json
{ "username": "john.doe", "password": "secret", "provider": "ldap" }
```

**Réponse**
```json
{ "access_token": "<jwt>", "token_type": "bearer", "expires_in": 28800 }
```

### POST /auth/visitor/request-otp
Demande d'envoi d'un code OTP par SMS.

**Body**
```json
{ "phone": "+33612345678" }
```

### POST /auth/visitor/verify-otp
Validation du code OTP.

**Body**
```json
{ "phone": "+33612345678", "otp": "123456" }
```

### GET /health
Vérification de l'état du service.
