# ADR-008 : Extension mobilite/teletravail (agent + passerelle de filtrage)

## Statut
Accepte -- briques de reference validees. Oriente les developpements
futurs. Ne remet pas en cause les modules deja livres (portail captif
Wi-Fi), qui restent le premier cas d'usage pleinement fonctionnel du
projet.

## Contexte

Le projet `Telix_Secure_Pro` couvrait initialement le controle d'acces et la
tracabilite pour des utilisateurs connectes a un reseau Wi-Fi/filaire
physique (site client, hotel, bureau). L'utilisateur a exprime le besoin
d'etendre ce controle aux utilisateurs **en mobilite ou en teletravail**, qui
ne transitent par aucun reseau local commun -- leur propre box Internet, 4G,
ou un Wi-Fi public quelconque.

Ce cas d'usage sort du perimetre "portail captif" au sens strict et
s'apparente au principe d'une solution **SWG (Secure Web Gateway)** : un
agent installe sur le poste redirige le trafic vers un point de controle
central, qui applique tracabilite et filtrage.

## Decisions

### 1. Deux familles de cas d'usage, un moteur commun
- **Acces local (Wi-Fi/filaire on-site)** : portail captif existant, proxy
  local, pas de centralisation du trafic (deja livre)
- **Acces distant (teletravail/mobilite)** : agent + passerelle de
  filtrage centralisee, scalable horizontalement
- Les deux s'appuient sur le meme `auth-service` pour l'authentification et
  la meme logique de tracabilite/retention (`log-service`), evitant une
  duplication de la logique metier.

### 2. Plateformes cibles de l'agent : Windows et macOS uniquement (pour l'instant)
Decision de l'utilisateur : pas de support mobile (iOS/Android) au demarrage
de ce chantier -- ecarte pour l'instant la complexite additionnelle d'un
agent mobile (contraintes des stores, permissions systeme plus restrictives).
A reevaluer si le besoin mobile se confirme.

### 3. Filtrage par categories dans un premier temps, sans inspection SSL/TLS
Decision de l'utilisateur : le filtrage repose sur les **noms de domaine/URL
visibles sans dechiffrement** (SNI TLS, requetes DNS, ou proxy explicite
pour le trafic HTTP clair). L'inspection SSL/TLS profonde (necessitant
l'installation d'un certificat racine sur chaque poste) est explicitement
**reportee** -- plus intrusive, a peser plus tard avec l'utilisateur avant
de l'implementer.

### 4. Mode degrade en cas de coupure agent <-> passerelle centrale
Point souleve par l'utilisateur : que se passe-t-il si le poste ne peut pas
joindre la passerelle centrale (panne reseau, passerelle indisponible) ?
Decision : **ne pas bloquer la navigation** (pas de kill switch strict au
lancement du projet), mais maintenir un service degrade local :
- L'agent embarque une **liste de filtrage "de base" en cache local**
  (categories bloquees), synchronisee periodiquement depuis la passerelle
  centrale quand la connexion est disponible. En cas de coupure, l'agent
  continue d'appliquer cette derniere liste connue localement.
- Les evenements de navigation sont **mis en cache local** (base SQLite
  chiffree, voir section Briques) pendant la coupure, puis **rejoues vers
  `log-service`** dès que la connexion a la passerelle centrale est
  retablie -- pas de perte de tracabilite, juste un delai de remontee.
- **Duree de retention locale du cache : 30 jours** (decision utilisateur).
  Au-dela de 30 jours sans synchronisation reussie, les evenements les plus
  anciens sont purges localement -- a considerer comme un scenario
  d'exception (coupure tres prolongee), a surveiller operationnellement
  (alerte si un agent ne se synchronise plus depuis plusieurs jours).
- Ce comportement est un choix par defaut **a valider dans la duree** avec
  l'utilisateur : un mode plus strict (blocage total hors ligne) reste une
  option de configuration possible si le contexte client l'exige plus tard
  (ex: exigence contractuelle stricte d'un client).

### 5. Scalabilite horizontale de la passerelle centrale
A 200 utilisateurs, une seule instance suffit largement. Neanmoins,
l'architecture est pensee sans etat local sur les instances de passerelle
(sessions dans Redis, comme pour `proxy-service` existant), pour permettre
d'ajouter des instances derriere un equilibreur de charge open source sans
reecriture, si la croissance l'exige.

### 6. Choix definitif des briques

| Fonction | Brique retenue | Justification |
|---|---|---|
| Tunnel agent <-> passerelle | **WireGuard** | Open source, tres leger, multiplateforme (Windows/macOS), performant, standard de facto du marche |
| Filtrage par categories | **e2guardian** | Alternative retenue a SquidGuard (voir analyse ci-dessous) |
| Listes de categories (blocklists) | **UT1 Blacklists** (Universite Toulouse 1) | Projet academique gratuit, blocklists categorisees (reseaux sociaux, streaming, etc.), mises a jour regulierement, format compatible e2guardian |
| Cache/tracabilite local hors ligne (agent) | **SQLite chiffre (SQLCipher)** | Stockage local leger et chiffre, adapte a la retention locale de 30 jours decidee ci-dessus |
| Equilibrage de charge passerelle | **HAProxy** | Plus simple a operer que Traefik pour du trafic TCP/UDP brut (WireGuard fonctionne en UDP), tres eprouve en production |

#### Analyse SquidGuard vs e2guardian (verifiee via recherche web le 2026-08-12)
- **SquidGuard** : projet en pratique a l'arret -- derniere version stable
  (1.3.0) datant de plus de 15 ans, sans evolution de fond depuis. Netgate/
  pfSense a retire le support officiel de ce paquet de sa distribution,
  notamment pour des raisons de securite non corrigees. **Ecarte malgre sa
  notoriete historique**, qui ne reflete plus l'etat reel du projet.
- **e2guardian** : commits recents constates sur le depot officiel
  (corrections de bugs, compatibilite avec les protections anti-bot
  recentes de Cloudflare). Fonctionne en mode "maintenance active" plutot
  qu'en developpement de nouvelles fonctionnalites -- pas de risque
  immediat identifie, mais **a surveiller dans la duree** (point de
  vigilance a reevaluer periodiquement, pas une garantie definitive).

> ⚠️ Ces briques n'ont pas encore ete testees en PoC dans le cadre de ce
> projet -- ce choix s'appuie sur une analyse documentaire, pas encore sur
> une validation technique pratique (charge, compatibilite fine avec les
> besoins du projet). Un PoC reste necessaire avant developpement complet.

## Consequences

- Le portail captif Wi-Fi existant n'est pas modifie par cette decision : il
  reste un cas d'usage a part entiere, deploye tel que documente dans
  `docs/deployment.md`
- Un nouveau module `remote-agent` et une passerelle de filtrage
  centralisee (`filtering-gateway`) seront necessaires -- a developper
  apres validation d'un PoC technique sur les briques retenues
- Le mode degrade introduit une complexite additionnelle (cache SQLite
  chiffre, synchronisation, rejeu des logs, purge a 30 jours) qui devra
  etre testee specifiquement (coupures reseau simulees) avant mise en
  production
- La vitalite d'e2guardian devra etre revue periodiquement (ex: a chaque
  montee de version majeure du projet) pour anticiper un eventuel besoin de
  migration future
