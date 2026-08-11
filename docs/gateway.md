# Documentation — gateway

## Vue d'ensemble

Le `gateway` est le **point d'entree unique** du portail captif Telix_Secure_Pro.
Base sur **Nginx**, il assure :

1. **Terminaison TLS** : tout le trafic est chiffre en HTTPS, redirection automatique
   depuis HTTP
2. **Reverse proxy** : route les requetes vers `captive-portal` (frontend) et
   `auth-service` (API), en cachant leur port/adresse interne
3. **Rate limiting** : protection anti brute-force sur les endpoints d'authentification,
   protection anti-DoS basique sur l'ensemble du site
4. **Headers de securite** : jeu de headers HTTP recommandes (OWASP) appliques a
   toutes les reponses

**Ports :** `80` (redirige vers 443), `443` (HTTPS) | **Tech :** Nginx 1.27 (Alpine)

---

## Architecture interne

```
gateway/
├── Dockerfile
├── entrypoint.sh              # Genere un certificat auto-signe si absent (dev), puis lance Nginx
├── nginx.conf                 # Config globale : logs, gzip, zones de rate limiting
├── conf.d/
│   ├── 00-http-redirect.conf  # Redirection HTTP -> HTTPS
│   └── 10-portal.conf         # Vhost HTTPS principal (TLS, routes, rate limiting)
└── snippets/
    └── security-headers.conf  # Headers de securite communs (inclus dans les vhosts)
```

---

## Routage

| Chemin | Destination | Particularite |
|---|---|---|
| `/` | `captive-portal:80` | Interface web (React) |
| `/api/auth/*` | `auth-service:8000/*` | Rate limiting renforce (5 req/min/IP, anti brute-force) |
| `/api/health` | `auth-service:8000/health` | Verification de sante (supervision) |

---

## TLS / Certificats

- **En developpement** : si aucun certificat n'est present dans le volume
  `gateway_certs`, `entrypoint.sh` genere automatiquement un **certificat
  auto-signe** (valide 365 jours) pour `GATEWAY_SERVER_NAME` — permet de demarrer
  la stack sans configuration TLS externe.
- **En production** : il faut monter de vrais certificats dans ce volume, nommes
  `telix.crt` et `telix.key`. Recommandation : **Certbot** (Let's Encrypt, gratuit
  et open source) avec renouvellement automatique, execute hors de ce conteneur
  (ex: conteneur `certbot` dedie ou tache cron sur l'hote), qui depose les
  certificats dans le volume partage.

> ⚠️ **Hypothèse à valider** : le renouvellement automatique via Certbot n'est pas
> encore implementé dans ce depot (necessite un nom de domaine public resolvable et
> accessible depuis Internet pour la validation ACME HTTP-01/DNS-01). A mettre en
> place lors du deploiement reel selon le domaine choisi.

---

## Rate limiting

| Zone | Limite | Cible |
|---|---|---|
| `telix_global` | 10 requetes/s par IP (burst 20) | Toutes les routes |
| `telix_auth` | 5 requetes/min par IP (burst 3) | `/api/auth/*` uniquement — protection contre le brute-force sur les identifiants et les OTP |

---

## Headers de securite appliques

| Header | Valeur | Objectif |
|---|---|---|
| `Strict-Transport-Security` | `max-age=63072000; includeSubDomains` | Force HTTPS pendant 2 ans |
| `X-Frame-Options` | `SAMEORIGIN` | Anti clickjacking |
| `X-Content-Type-Options` | `nosniff` | Anti MIME-sniffing |
| `Content-Security-Policy` | `default-src 'self'; ...` | Limite les sources de scripts/styles |
| `Referrer-Policy` | `strict-origin-when-cross-origin` | Limite la fuite d'URL vers des tiers |
| `Permissions-Policy` | `geolocation=(), microphone=(), camera=()` | Désactive les capteurs non utilisés |

> ⚠️ **Hypothèse à valider** : la `Content-Security-Policy` actuelle est restrictive
> (`'self'` uniquement). Si le frontend `captive-portal` charge des ressources
> externes (polices, CDN...), il faudra l'adapter au fur et à mesure du
> developpement du frontend.

---

## Integration avec l'equipement Wi-Fi existant

Le `gateway` expose une seule adresse/port public (443). C'est **cette URL** que
l'equipement Wi-Fi doit configurer comme cible de redirection captive (avec les
parametres `mac`/`ip` en query string, cf ADR-005). Le `gateway` route ensuite vers
`captive-portal`, qui affiche la page de login et appelle `auth-service` via
`/api/auth/*`.

---

## Tests manuels

```bash
docker compose -f infra/docker-compose.yml up -d gateway captive-portal auth-service

# Verifier la redirection HTTP -> HTTPS
curl -I http://localhost

# Verifier le certificat auto-signe (dev) et les headers de securite
curl -Ik https://localhost --insecure

# Verifier le rate limiting sur l'auth (au-dela de 5 req/min, doit renvoyer 503/429)
for i in $(seq 1 10); do curl -sk -o /dev/null -w "%{http_code}\n" https://localhost/api/auth/corporate --insecure; done
```

---

## Prochaines ameliorations identifiees

- [ ] Automatiser le renouvellement TLS avec Certbot pour un vrai nom de domaine (production)
- [ ] Adapter la Content-Security-Policy une fois `captive-portal` developpe
- [ ] Ajouter un endpoint `/metrics` (Nginx stub_status ou nginx-prometheus-exporter) pour supervision
