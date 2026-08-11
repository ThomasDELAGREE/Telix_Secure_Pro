# ADR-006 — Conformité de la retention 1 an (LCEN)

**Date :** 2026-08-11 | **Statut :** Accepté

## Contexte

ADR-003 et la documentation `log-service.md` laissaient en suspens une hypothèse :
la stratégie de retention (suppression definitive apres 365 jours, sans archivage a
froid) etait-elle suffisante au regard des obligations legales francaises (LCEN) ?

## Analyse

Le **décret n°2021-1362 du 20 octobre 2021** (pris en application du II de l'article 6
de la loi n°2004-575 du 21 juin 2004 pour la confiance dans l'économie numérique - LCEN),
qui définit les obligations de conservation des données de connexion pour les opérateurs
et fournisseurs d'accès, précise notamment :

- Les **données techniques permettant d'identifier la source de la connexion** ou
  relatives aux **équipements terminaux utilisés** (IP, adresse MAC...) doivent être
  conservées **jusqu'à l'expiration d'un délai d'un an** à compter de la connexion ou
  de l'utilisation des équipements terminaux.
- Les **catégories de données de trafic et de localisation** doivent être conservées
  **pour une durée d'un an** (mobilisables en cas d'injonction du Premier ministre).

Le texte fixe une **durée de conservation obligatoire** (1 an), mais n'impose **aucune
modalité d'archivage à froid** particulière au-delà de cette durée : il s'agit d'une
obligation de conservation pendant la période donnée, pas d'une obligation d'archivage
perpétuel.

## Décision

La stratégie actuelle de `log-service` (index set `telix_web_traffic`, rotation
quotidienne, **suppression automatique après `LOG_RETENTION_DAYS=365` jours**) est
**conforme** à l'obligation légale :
- Conservation garantie pendant la durée minimale requise (1 an)
- Suppression au-delà, ce qui évite également une conservation excessive de données
  à caractère personnel (principe de minimisation RGPD, art. 5.1.e)

Aucun archivage à froid supplémentaire n'est nécessaire pour respecter cette obligation
spécifique. L'hypothèse ouverte dans ADR-003 / `log-service.md` est donc **levée**.

## Points de vigilance restants (hors périmètre technique, à statuer côté juridique/DPO)

- Vérifier si Telix_Secure_Pro, selon son contexte de déploiement précis (entreprise
  privée vs prestataire d'accès au sens de la LCEN), entre bien dans le champ
  d'application de ce décret, ou si d'autres textes s'appliquent (ex: obligations
  spécifiques secteur hôtelier, contrat client).
- S'assurer que l'information des utilisateurs (mentions légales / politique de
  confidentialité du portail captif) mentionne cette durée de conservation.
- La procédure de communication des données sur injonction (réquisition judiciaire,
  Premier ministre) n'est pas encore outillée coté export/administration — à prévoir
  si un usage réel l'exige.

## Consequences

- `docs/log-service.md` et `docs/DEVELOPMENT_LOG.md` mis à jour pour refléter cette
  conformité confirmée.
- Aucun changement de code nécessaire : l'implémentation existante (étape 5,
  `log-service`) satisfait déjà l'exigence.
