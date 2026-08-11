# ADR-005 — Identification par adresse MAC et identifiant generique

**Date :** 2026-08-11 | **Statut :** Accepté

## Contexte

Le modèle initial (ADR proxy-service) associait une session a une simple adresse IP.
Cela pose deux limites :
1. **Pas de MAC** : impossible de distinguer deux appareils partageant temporairement
   la meme IP (roaming DHCP, NAT), et pas de tracabilite "appareil" pour les demandes
   d'autorite (LCEN).
2. **Identifiant trop restreint** : le systeme doit supporter plusieurs types
   d'identifiants selon le contexte de deploiement :
   - Utilisateur AD/LDAP (corporate, entreprise)
   - Utilisateur Azure AD (corporate, cloud)
   - Numero de telephone (visiteur, OTP SMS)
   - Numero de chambre (visiteur, deploiement hotelier)

## Decision

1. **Adresse MAC** : ajout d'un champ optionnel `mac_address` sur tous les endpoints
   d'authentification (`/auth/corporate`, `/auth/visitor/*`). Normalisee en minuscules
   avec separateurs `:` (`app/core/mac_utils.py`). Stockee en base (`auth_sessions.mac_address`)
   et propagee dans le registre Redis (`session_registry.py`).
2. **Identifiant generique** : le registre Redis stocke desormais un objet JSON
   `{ user_identifier, identifier_type, mac_address }` au lieu d'une simple chaine.
   `identifier_type` prend l'une des valeurs : `ldap`, `azure_ad`, `sms_otp`, `room_number`.
3. **Nouveau module `room_service.py`** : authentification par numero de chambre +
   code d'acces, avec une table `room_codes` (provisionnement manuel dans un premier temps).
4. **Retro-compatibilite proxy-service** : `session_helper.py` et `gelf_shipper.py`
   savent lire l'ancien format (chaine brute) ET le nouveau format JSON, pour ne pas
   casser une session en cours pendant le deploiement de cette evolution.

## Hypotheses a valider

- **Recuperation de la MAC côté client** : la MAC n'est PAS visible depuis le navigateur
  du client final (limitation navigateur/JS). Elle doit etre recuperee soit :
  a) via l'equipement Wi-Fi (RADIUS Accounting, DHCP lease, ou parametre injecté dans
     l'URL de redirection captive, ex: `?mac=AA:BB:CC:DD:EE:FF` — standard chez la plupart
     des controleurs Wi-Fi : Unifi, Cisco, Aruba, Ruckus...)
  b) via une requete ARP/table de bail DHCP côte reseau (necessite un acces a
     l'infrastructure, hors scope de ce microservice)
  → **A valider avec l'equipement Wi-Fi cible** : c'est lui qui doit transmettre le
  parametre MAC au portail captif lors de la redirection initiale.
- **Numero de chambre / PMS hotelier** : le modele actuel (`room_codes`) est un
  provisionnement manuel. Une integration avec un PMS (Property Management System :
  Odoo, Mews, Opera...) permettrait de generer/revoquer les codes automatiquement a
  l'arrivee et au depart des clients. Non implementee a ce stade.

## Consequences

- Nouvelle table `room_codes` (migration `0002`)
- Nouveau endpoint `POST /auth/visitor/room`
- Le champ `mac_address` est optionnel partout : le systeme fonctionne meme si
  l'equipement Wi-Fi ne transmet pas la MAC (degrade gracieusement vers le mode IP seul)
- Les logs proxy (GELF) contiennent desormais `_mac_address` et `_identifier_type`
  en plus de `_user`, ce qui permet un filtrage fin dans Graylog et un mapping
  plus riche vers Sekoia (ADR-004)
