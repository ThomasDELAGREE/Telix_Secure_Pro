# Telix_Secure_Pro

> Portail captif open source — Authentification corporate & visiteurs, traçabilité web, intégration SIEM Sekoia.

---

## 🎯 Objectifs

- Portail captif compatible avec **toute solution Wi-Fi existante** (via redirection HTTP/HTTPS)
- Double authentification :
  - **Corporate** : Active Directory (LDAP) et/ou Azure AD (OAuth2 / SAML)
  - **Visiteurs** : Code OTP par SMS ou intégration système de téléphonie
- **Traçabilité complète** des accès web par utilisateur
- **Conservation des logs pendant 1 an** (conformité légale)
- **Intégration SIEM Sekoia** (CEF/Syslog)
- Stack **100% open source & gratuite**

---

## 🏗️ Architecture

```
Telix_Secure_Pro/
├── captive-portal/        # Frontend du portail captif (React)
├── auth-service/          # Service d'authentification (AD, Azure AD, SMS)
├── proxy-service/         # Proxy transparent + traçabilité (Squid)
├── log-service/           # Collecte et rétention des logs (Graylog)
├── siem-connector/        # Connecteur SIEM Sekoia (CEF/Syslog forwarder)
├── gateway/               # API Gateway (Nginx)
├── infra/                 # Docker Compose
│   ├── docker-compose.yml
│   └── .env.example
├── docs/                  # Documentation technique
│   ├── architecture.md
│   ├── installation.md
│   └── api.md
├── scripts/               # Scripts d'installation et de maintenance
├── .github/
│   └── workflows/         # CI/CD GitHub Actions
├── .gitignore
├── LICENSE
└── README.md
```

---

## 🧱 Stack technique (open source)

| Composant | Technologie |
|---|---|
| Frontend portail | React + TailwindCSS |
| Backend API | FastAPI (Python) |
| Auth AD/LDAP | ldap3 |
| Auth Azure AD | MSAL Python |
| Auth SMS OTP | Kannel / FreeSWITCH |
| Proxy traçabilité | Squid + SquidGuard |
| Logs & rétention | Graylog + Elasticsearch |
| SIEM Connector | Logstash (CEF) → Sekoia |
| Base de données | PostgreSQL |
| Cache / Sessions | Redis |
| Reverse proxy | Nginx |
| Conteneurisation | Docker + Docker Compose |
| CI/CD | GitHub Actions |

---

## 🚀 Démarrage rapide

```bash
git clone https://github.com/ThomasDELAGREE/Telix_Secure_Pro.git
cd Telix_Secure_Pro
cp infra/.env.example infra/.env
# Éditer infra/.env avec vos paramètres
docker compose -f infra/docker-compose.yml up -d
```

---

## 📋 Prérequis

- Docker >= 24.x
- Docker Compose >= 2.x
- Un équipement Wi-Fi supportant la redirection de portail captif (Unifi, OpenWRT, pfSense, etc.)

---

## 📄 Licence

Apache 2.0 — voir [LICENSE](./LICENSE)
