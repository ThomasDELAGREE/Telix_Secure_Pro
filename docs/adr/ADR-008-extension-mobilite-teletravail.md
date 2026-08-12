# ADR-008 : Extension mobilite/teletravail (agent + passerelle de filtrage)

## Statut
Accepte -- oriente les developpements futurs. Ne remet pas en cause les
modules deja livres (portail captif Wi-Fi), qui restent le premier cas
d'usage pleinement fonctionnel du projet.

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
  continue d'appliquer cette derniere liste connue localement (via un
  filtrage DNS/hosts local, voir section Implementation).
- Les evenements de navigation sont **mis en cache local** (fichier local
  chiffre, taille et duree de retention locale limitees) pendant la
  coupure, puis **rejoues vers `log-service`** dès que la connexion a la
  passerelle centrale est retablie -- pas de perte de tracabilite, juste un
  delai de remontee.
- Ce comportement est un choix par defaut **a valider dans la duree** avec
  l'utilisateur : un mode plus strict (blocage total hors ligne) reste une
  option de configuration possible si le contexte client l'exige plus tard
  (ex: exigence contractuelle stricte d'un client).

### 5. Scalabilite horizontale de la passerelle centrale
A 200 utilisateurs, une seule instance suffit largement. Neanmoins,
l'architecture est pensee sans etat local sur les instances de passerelle
(sessions dans Redis, comme pour `proxy-service` existant), pour permettre
d'ajouter des instances derriere un equilibreur de charge open source
(a confirmer : HAProxy ou Traefik) sans reecriture, si la croissance
l'exige.

## Pistes de briques envisagees (a confirmer/tester avant developpement)

| Fonction | Piste | Statut |
|---|---|---|
| Agent client (tunnel) | WireGuard (client officiel open source) | A valider en PoC |
| Filtrage par categorie | SquidGuard / e2guardian, ou filtrage DNS (Pi-hole-like) | A comparer, verifier l'etat de maintenance actuel |
| Cache/filtrage local hors ligne (agent) | Liste de blocage locale + resolveur DNS local sur le poste | A concevoir |
| Equilibrage de charge passerelle | HAProxy ou Traefik (open source) | A confirmer selon la charge reelle observee |

> ⚠️ Aucune de ces briques n'a encore ete testee dans le cadre de ce
> projet -- ce tableau liste des pistes serieuses et connues de
> l'ecosysteme open source, pas des choix definitifs.

## Consequences

- Le portail captif Wi-Fi existant n'est pas modifie par cette decision : il
  reste un cas d'usage a part entiere, deploye tel que documente dans
  `docs/deployment.md`
- Un nouveau module `remote-agent` (ou nom a definir) et une passerelle de
  filtrage centralisee seront necessaires -- a developper apres validation
  d'un PoC technique sur les briques candidates
- Le mode degrade introduit une complexite additionnelle (cache local
  chiffre, synchronisation, rejeu des logs) qui devra etre testee
  specifiquement (coupures reseau simulees) avant mise en production
