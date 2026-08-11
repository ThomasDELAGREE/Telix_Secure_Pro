# Documentation — captive-portal (frontend React)

## Vue d'ensemble

Interface web presentee a l'utilisateur lorsqu'il se connecte au Wi-Fi. Elle
gere le choix du type de connexion, les 4 flux d'authentification
(LDAP, Azure AD, OTP SMS, code de chambre) et consomme l'API `auth-service`
via `/api/auth/*`.

Stack : React 18 + TypeScript + Vite + TailwindCSS + react-router-dom. Servi
en production par un conteneur Nginx leger (build statique), cible finale du
proxy host Nginx Proxy Manager (voir `docs/npm-provisioning.md`).

---

## Architecture

```
captive-portal/
├── Dockerfile                          # Build multi-etapes (Node -> Nginx statique)
├── nginx.conf                          # Sert le build React (SPA fallback)
├── vite.config.ts                      # Proxy /api -> auth-service en dev
└── src/
    ├── App.tsx                         # Routes
    ├── context/WifiParamsContext.tsx   # Extraction MAC/IP/SSID depuis l'URL de redirection Wi-Fi
    ├── api/authClient.ts               # Client Axios vers auth-service
    ├── components/                      # PortalLayout, ErrorBanner
    └── pages/
        ├── LoginChoicePage.tsx         # Choix du type de connexion
        ├── CorporateLoginPage.tsx      # LDAP / Azure AD
        ├── VisitorSmsPage.tsx          # OTP SMS (2 etapes : demande + verification)
        ├── VisitorRoomPage.tsx         # Numero de chambre + code d'acces
        └── SuccessPage.tsx             # Confirmation finale
```

---

## Recuperation des parametres Wi-Fi (MAC/IP)

Comme etabli dans **ADR-005**, un navigateur ne peut pas lire l'adresse MAC
d'un appareil. Elle doit etre transmise par l'equipement Wi-Fi (controleur)
au moment de la redirection vers le portail, generalement en parametre d'URL.

`WifiParamsContext.tsx` lit l'URL au chargement et tente plusieurs alias de
parametres connus, pour rester compatible avec differents constructeurs :

| Donnee | Alias recherches |
|---|---|
| MAC client | `mac`, `client_mac`, `clientMac`, `user_mac` |
| IP client | `ip`, `client_ip`, `clientIp` |
| MAC point d'acces | `ap_mac`, `apMac`, `gw_id` |
| SSID | `ssid` |

La MAC est normalisee vers le format `aa:bb:cc:dd:ee:ff`, coherent avec la
normalisation deja appliquee cote `auth-service`.

> ⚠️ **Hypothese a valider avec l'utilisateur** : le nom exact des parametres
> depend du constructeur Wi-Fi retenu (Unifi, Cisco, Aruba, Ruckus,
> MikroTik...). Les alias ci-dessus couvrent les conventions les plus
> courantes, mais il faudra confirmer/ajuster une fois l'equipement cible
> connu, et tester une redirection reelle.

---

## Flux d'authentification

1. **Corporate (LDAP/Azure AD)** : formulaire identifiant/mot de passe, choix
   explicite du fournisseur, POST `/api/auth/corporate`
2. **Visiteur SMS** : POST `/api/auth/visitor/request-otp` (numero de
   telephone) puis POST `/api/auth/visitor/verify-otp` (code recu)
3. **Visiteur chambre** : POST `/api/auth/visitor/room` (numero de chambre +
   code d'acces)

Dans les 3 cas, la MAC (si disponible) est transmise avec la requete pour
enrichir la tracabilite cote `auth-service`/`proxy-service`.

---

## Variables et configuration

Aucune variable d'environnement necessaire au runtime (le frontend est un
build statique). En developpement, `vite.config.ts` proxifie `/api` vers
`http://localhost:8000` (auth-service expose en local).

---

## Tests

```bash
cd captive-portal
npm install
npm run test   # Vitest -- tests de la logique de normalisation MAC
npm run dev    # Serveur de developpement (localhost:5173)
npm run build  # Build de production (dist/)
```

---

## Points a valider avec l'utilisateur

- **Format exact des parametres de redirection** transmis par l'equipement
  Wi-Fi cible (a confirmer selon le materiel retenu)
- **Integration PMS hotelier** pour le provisionnement automatique des codes
  de chambre (actuellement manuel, cf ADR-005)
- **Personnalisation visuelle** (logo, couleurs de marque) : le theme actuel
  (`tailwind.config.js`, couleur `telix`) est un choix par defaut, a ajuster
  selon l'identite visuelle souhaitee
