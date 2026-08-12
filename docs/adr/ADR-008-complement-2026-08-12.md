# ADR-008 -- Complement du 2026-08-12 : separation portail captif / agent d'itinerance, et generation de cle cote agent

## Contexte

Deux points souleves par l'utilisateur apres la premiere version de
l'enrollment agent (module `auth-service/app/routers/auth_agent.py`) :

1. La generation de la cle privee WireGuard cote serveur posait une
   question de securite legitime.
2. Le processus d'enrollment agent ne doit pas se melanger avec les
   authentifications temporaires du portail captif (visiteur SMS OTP,
   numero de chambre) -- ce sont deux sujets distincts, avec des cycles
   de vie d'identite totalement differents.

## Decisions

### 1. Generation de la cle WireGuard : desormais cote agent, pas cote serveur

La cle privee est generee **localement sur le poste**, lors du premier
enrollment, et **ne quitte jamais l'appareil**. Seule la cle publique est
transmise a `auth-service` via `/auth/agent/enroll`. C'est le choix
recommande du point de vue securite (un secret aussi sensible ne devrait
jamais transiter par le reseau, meme une seule fois) -- accepte par
l'utilisateur malgre l'orchestration legerement plus complexe qu'il
implique cote agent.

Ce processus reste **entierement automatique** : aucune action manuelle
de l'utilisateur ni d'un administrateur au-dela du login initial (LDAP/
Azure AD) qui declenche deja la sequence -- confirme explicitement avec
l'utilisateur.

### 2. Enrollment agent reserve aux identites durables (LDAP/Azure AD)

Le portail captif Wi-Fi (visiteurs, chambres d'hotel) et l'agent
d'itinerance repondent a des besoins differents :

| | Portail captif (visiteur/chambre) | Agent d'itinerance |
|---|---|---|
| Duree de vie de l'identite | Ephemere (heures/jours) | Durable (poste rattache a une personne) |
| Nature de l'identite | Souvent partagee/anonyme (code de chambre) | Individuelle et nommee |
| Besoin d'un tunnel permanent | Non -- trafic local via proxy-service | Oui -- c'est le principe de l'agent |

Un visiteur avec un code SMS ou un client d'hotel avec un numero de
chambre n'a donc **aucune raison** de se voir proposer un enrollment
agent : l'identite disparait ou change de titulaire trop rapidement pour
qu'un tunnel permanent ait un sens.

`/auth/agent/enroll` retourne desormais explicitement une erreur 403 si
le type d'identifiant du token (`auth_type` dans les claims JWT) n'est
pas `ldap` ou `azure_ad`. Les types `sms_otp` et `room_number` restent
strictement cantonnes au portail captif Wi-Fi existant, sans changement
de comportement de ce cote.

## Consequences

- `AgentEnrollRequest`/`AgentEnrollResponse` ont change de forme : la
  requete porte desormais `wireguard_public_key` (fourni par l'agent), la
  reponse ne contient plus de cle privee/publique WireGuard mais ajoute
  `wireguard_server_public_key` (necessaire a l'agent pour configurer son
  tunnel local vers filtering-gateway)
- `wireguard_service.generate_keypair()` a ete retire cote auth-service
  -- ce module ne genere, ne voit et ne stocke plus aucune cle privee
  WireGuard
- Le point encore ouvert (TODO explicite dans le code) reste
  l'enregistrement effectif du peer (cle publique + IP) auprès d'un vrai
  serveur WireGuard cote `filtering-gateway` -- sans cette etape, la cle
  generee par l'agent n'ouvre pas encore de tunnel fonctionnel
