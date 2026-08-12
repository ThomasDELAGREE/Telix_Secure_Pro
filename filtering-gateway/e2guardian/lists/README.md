# Provenance des listes de blocage

Ce repertoire recoit les listes generees par ../scripts/sync_ut1_blocklists.py a partir des UT1 Blacklists (Universite Toulouse 1 Capitole), un projet academique gratuit et regulierement mis a jour.

## A verifier avant utilisation reelle

- L'URL de telechargement exacte et le format d'archive peuvent evoluer cote UT1 -- sync_ut1_blocklists.py centralise cette URL dans une constante en tete de fichier, a verifier/ajuster au moment de la mise en place reelle (pas de garantie de disponibilite/format figee dans le temps, s'agissant d'un projet academique sans contrat de service).
- Les noms de categories utilises dans e2guardian.conf.template (publicite, reseaux_sociaux, streaming) sont des exemples illustratifs -- les noms de categories reels du jeu UT1 doivent etre confirmes et mappes explicitement.
