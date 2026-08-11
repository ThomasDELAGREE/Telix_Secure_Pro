# Guide d'installation

## Prérequis

- Docker >= 24.x
- Docker Compose >= 2.x
- Minimum 4 vCPU / 8 Go RAM / 100 Go stockage

## Installation

```bash
git clone https://github.com/ThomasDELAGREE/Telix_Secure_Pro.git
cd Telix_Secure_Pro
cp infra/.env.example infra/.env
```

Éditer `infra/.env` avec vos paramètres (AD, Azure AD, SMS gateway, etc.)

```bash
docker compose -f infra/docker-compose.yml up -d
```

## Configuration du portail captif Wi-Fi

Rediriger le trafic HTTP/HTTPS non authentifié vers `http://<IP_SERVEUR>:8080`
sur votre équipement réseau (Unifi, pfSense, OpenWRT, etc.).
