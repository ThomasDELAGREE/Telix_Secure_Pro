# Documentation — Renouvellement TLS automatique (Certbot / Let's Encrypt)

## Vue d'ensemble

Ce module comble l'hypothèse laissée ouverte lors du développement du `gateway` :
l'émission et le **renouvellement automatique** des certificats TLS via
**Certbot** (client officiel Let's Encrypt, gratuit et open source).

Il repose sur le **defi ACME HTTP-01** : Let's Encrypt vérifie que vous possédez
bien le domaine en demandant à votre serveur de répondre à une requête HTTP sur
`http://<domaine>/.well-known/acme-challenge/...`.

---

## Architecture

```
certbot/
├── Dockerfile
└── entrypoint.sh     # Emission initiale + boucle de renouvellement (verif. toutes les 12h)

gateway/
└── entrypoint.sh     # Bascule automatique vers le certificat Let's Encrypt si present,
                     # sinon utilise un certificat auto-signe de secours
```

### Volumes partages entre `gateway` et `certbot`

| Volume | Usage |
|---|---|
| `certbot_webroot` | Fichiers de preuve du defi ACME HTTP-01, deposes par Certbot, servis par Nginx sur `/.well-known/acme-challenge/` |
| `letsencrypt_certs` | Certificats emis par Certbot (`/etc/letsencrypt/live/<domaine>/`), lus en lecture seule par le gateway |
| `gateway_certs` | Certificat effectivement utilise par Nginx (`telix.crt`/`telix.key`) — soit une copie du certificat Let's Encrypt, soit le certificat auto-signe de secours |

---

## Fonctionnement

1. **Au demarrage**, `certbot/entrypoint.sh` tente une emission initiale si
   aucun certificat n'existe encore pour `GATEWAY_SERVER_NAME`
2. **En parallele**, `gateway/entrypoint.sh` vérifie si un certificat Let's
   Encrypt valide est present et, si oui, le copie dans `gateway_certs` puis
   recharge Nginx (`nginx -s reload`, sans coupure de service)
3. **En continu**, `certbot` relance `certbot renew` toutes les 12h (Certbot ne
   renouvelle reellement que si le certificat expire dans moins de 30 jours —
   cette frequence est donc sans risque de sur-solliciter Let's Encrypt) et le
   `gateway` revérifie toutes les 6h s'il doit basculer vers un certificat plus
   recent

### Comportement en developpement (domaine non public)

Si `GATEWAY_SERVER_NAME` n'est pas un vrai domaine public (ex: valeur par
defaut `portal.telix.local`), l'emission Certbot **echoue silencieusement**
(message logge, pas de crash) et le `gateway` continue de fonctionner avec son
**certificat auto-signe de secours**. Aucune action manuelle n'est necessaire
pour demarrer la stack en local.

---

## Prérequis pour la production

| Prérequis | Détail |
|---|---|
| Nom de domaine public | `GATEWAY_SERVER_NAME` doit resoudre en DNS vers l'IP publique du serveur |
| Port 80 accessible depuis Internet | Le defi HTTP-01 en a besoin (le port 443 seul ne suffit pas pour l'emission initiale) |
| Adresse email valide | `CERTBOT_EMAIL`, utilisee par Let's Encrypt pour notifier les expirations en cas d'echec de renouvellement |

---

## Variables d'environnement

| Variable | Description |
|---|---|
| `GATEWAY_SERVER_NAME` | Domaine public du portail captif (deja existante, reutilisee ici) |
| `CERTBOT_EMAIL` | Email de contact Let's Encrypt (nouveau) |

---

## Tests manuels

```bash
docker compose -f infra/docker-compose.yml up -d gateway certbot

# Suivre les logs d'emission/renouvellement
docker compose -f infra/docker-compose.yml logs -f certbot

# Verifier quel certificat est effectivement charge par Nginx
docker compose -f infra/docker-compose.yml exec gateway \
  openssl x509 -in /etc/nginx/certs/telix.crt -noout -issuer -dates
```

---

## Limitations connues

- Le mecanisme actuel gere **un seul domaine** (`GATEWAY_SERVER_NAME`). Pour du
  multi-domaine (ex: plusieurs sites clients), il faudra etendre `entrypoint.sh`
  (boucle sur une liste de domaines) — non implemente a ce stade, a faire selon
  le besoin reel de deploiement.
- Le defi utilise est **HTTP-01** uniquement (le plus simple). Si le port 80
  ne peut pas etre expose publiquement dans votre contexte, il faudrait passer
  au defi **DNS-01** (plus complexe, necessite un acces programmable a votre
  fournisseur DNS) — non implemente, a evaluer si HTTP-01 s'avere impossible.
