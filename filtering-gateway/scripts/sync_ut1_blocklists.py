"""
sync_ut1_blocklists.py

Telecharge et normalise les listes de blocage UT1 (Universite Toulouse 1)
pour les rendre utilisables par e2guardian.

STATUT : squelette non teste. L'URL ci-dessous correspond a la
distribution publique connue du projet UT1 au moment de la redaction,
MAIS n'a pas ete verifiee par un telechargement reel dans cet
environnement de developpement (absence d'acces reseau dans le
bac a sable utilise). A CONFIRMER avant toute utilisation en production.
"""
from __future__ import annotations

import argparse
import logging
import tarfile
from pathlib import Path

logger = logging.getLogger("telix.filtering_gateway.sync_ut1")

# A VERIFIER avant utilisation reelle (voir docstring du module et
# filtering-gateway/e2guardian/lists/README.md)
UT1_ARCHIVE_URL = "https://dsi.ut-capitole.fr/blacklists/download/blacklists.tar.gz"

# Mapping illustratif -- a confirmer avec les noms de categories reels du
# jeu UT1 avant utilisation
CATEGORY_DIR_MAP = {
    "publicite": "publicite",
    "reseaux_sociaux": "reseaux_sociaux",
    "streaming": "streaming",
}


def download_archive(dest_path: Path, http_client=None) -> None:
    """
    Telecharge l'archive UT1. http_client est injecte pour permettre les
    tests sans acces reseau reel -- aucune dependance HTTP n'est importee
    en dur ici tant que le besoin (requests ? urllib ? httpx ?) n'est pas
    tranche avec l'utilisateur.
    """
    if http_client is None:
        raise NotImplementedError(
            "Telechargement reel non implemente dans ce squelette -- "
            "aucun acces reseau disponible pour valider l'URL UT1_ARCHIVE_URL "
            "dans cet environnement de developpement."
        )
    http_client.download(UT1_ARCHIVE_URL, dest_path)


def extract_categories(archive_path: Path, output_dir: Path, categories: list[str]) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    with tarfile.open(archive_path, "r:gz") as tar:
        for category in categories:
            dir_name = CATEGORY_DIR_MAP.get(category)
            if dir_name is None:
                logger.warning("Categorie inconnue, ignoree : %s", category)
                continue
            members = [m for m in tar.getmembers() if m.name.startswith(f"{dir_name}/")]
            if not members:
                logger.warning(
                    "Aucun fichier trouve pour la categorie %s dans l'archive -- "
                    "verifier le mapping CATEGORY_DIR_MAP",
                    category,
                )
                continue
            tar.extractall(path=output_dir, members=members)


def normalize_for_e2guardian(category_dir: Path) -> Path:
    """
    Convertit le format brut UT1 (fichier domains par categorie) vers le
    format attendu par e2guardian -- a ce stade, le format est suppose
    deja compatible (une entree de domaine par ligne), hypothese A
    VERIFIER lors du premier test reel.
    """
    domains_file = category_dir / "domains"
    if not domains_file.exists():
        raise FileNotFoundError(
            f"Fichier 'domains' introuvable dans {category_dir} -- "
            "le format de l'archive UT1 ne correspond peut-etre pas a "
            "l'hypothese posee dans ce script, a verifier."
        )
    return domains_file


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--categories", default="publicite,reseaux_sociaux,streaming")
    parser.add_argument("--output-dir", default="/etc/e2guardian/lists")
    parser.parse_args()

    logging.basicConfig(level=logging.INFO)
    logger.error(
        "Ce script est un squelette non teste (pas d'acces reseau dans "
        "l'environnement de developpement) -- voir docstring du module "
        "avant toute execution en production."
    )
    raise SystemExit(1)


if __name__ == "__main__":
    main()
