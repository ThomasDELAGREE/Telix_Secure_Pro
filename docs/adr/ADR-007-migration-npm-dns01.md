# ADR-007 — Migration du reverse proxy/TLS vers Nginx Proxy Manager (DNS-01 OVH)

## Statut
Accepte (2026-08-11)

## Contexte
Les modules `gateway` (Nginx custom, config versionnee) et `certbot` (defi
HTTP-01) avaient ete developpes pour Telix_Secure_Pro de maniere autonome
(voir `docs/gateway.md` et `docs/tls-renewal-certbot.md`).

Le porteur du projet a indique que l'infrastructure existante du groupe
(`groupe-odisecure.fr`, deploiement SBC) utilise deja **Nginx Proxy Manager
(NPM)** avec un defi **DNS-01** via le plugin OVH, provisionne par des scripts
Python appelant l'API OVH (creation de l'enregistrement DNS) puis l'API REST
de NPM (creation du proxy host + certificat).

Par souci de coherence et de mutualisation avec l'infrastructure existante,
la decision est prise d'aligner Telix_Secure_Pro sur cette approche plutot
que de maintenir une solution Nginx/Certbot parallele et independante.

## Decision
- **Suppression** des modules `gateway/` et `certbot/` (config Nginx custom +
  Certbot HTTP-01)
- **Ajout** du module `npm-provisioning/` : deux scripts Python idempotents,
  bases sur les scripts fournis par l'utilisateur (`ovh_dns_sbc.py` et la
  creation de proxy host NPM), adaptes a Telix_Secure_Pro :
  - `ovh_dns_setup.py` : creation/mise a jour de l'enregistrement DNS A
  - `npm_proxy_host_setup.py` : creation/mise a jour du proxy host NPM avec
    certificat Let's Encrypt via defi **DNS-01** (et non plus HTTP-01)
- Le defi **DNS-01** est conserve (plutot que HTTP-01) car c'est celui deja en
  place et configure sur l'infrastructure NPM existante (plugin OVH), et il
  presente l'avantage de ne pas necessiter l'exposition publique du port 80

## Consequences
- **Positif** : coherence avec l'infra existante, reutilisation d'un outil
  (NPM) deja maitrise par l'equipe, pas de duplication d'un mecanisme de
  gestion de certificats
- **Positif** : le defi DNS-01 permettra si besoin l'emission de certificats
  wildcard a l'avenir
- **Negatif** : la configuration du reverse proxy n'est plus versionnee dans
  Git de maniere native (NPM stocke sa configuration en base de donnees, pas
  en fichiers texte) — la tracabilite des changements de routage repose
  desormais sur l'interface/API NPM, pas sur l'historique Git de ce depot
- **Negatif** : Nginx Proxy Manager lui-meme n'est pas un composant versionne
  dans ce depot ; ce depot ne contient que les scripts de provisioning qui
  s'y connectent, pas NPM en tant que tel

## Hypotheses a valider avec l'utilisateur
- Nom et port exacts du conteneur cible pour le forward NPM une fois
  `captive-portal` developpe (actuellement suppose : `captive-portal:80`)
- Frequence d'execution souhaitee des scripts de provisioning (ponctuelle vs
  cron/automatisee en cas de changement d'IP publique)
- Version de NPM utilisee et configuration exacte du plugin DNS OVH deja en
  place (non verifiable depuis ce depot)

## Alternatives ecartees
- **Conserver `gateway`/`certbot` (HTTP-01)** : ecarte pour ne pas dupliquer un
  mecanisme de gestion TLS deja standardise sur l'infra du groupe
