#*TO*#
__pgm__ = "update_portraits_csv.py"
__version__ = "0.0.0"
__date__ = "01/01/1970 00:00"

"""
Ajout des URLs GitHub des portraits dans portraits.csv.

Ce script ajoute 1600 lignes (IDs 1000 à 2599) avec les URLs raw GitHub
au fichier portraits.csv existant, sans toucher aux lignes existantes.

IMPORTANT : portraits.csv est un fichier utilisateur protégé.
Ce script AJOUTE des lignes, il ne remplace RIEN.

PRÉREQUIS :
    - Le repo GitHub Jawakaspa/orqual-portraits doit exister
    - Les vignettes doivent avoir été uploadées dans thumbs/

FORMAT portraits.csv :
    idportrait;sexe;portrait
    1000;U;https://raw.githubusercontent.com/Jawakaspa/orqual-portraits/main/thumbs/1000.jpg

NOTE : Le sexe est 'U' (Unknown) pour les portraits Photofit car le sexe
réel est dans la base patients, pas dans le fichier portraits.

Usage CLI :
    python update_portraits_csv.py                                  # → Affiche l'aide
    python update_portraits_csv.py refs/portraits.csv               # → Ajoute les 1600 URLs
    python update_portraits_csv.py refs/portraits.csv --dry-run     # → Simule sans écrire
    python update_portraits_csv.py refs/portraits.csv -v            # → Mode verbose
    python update_portraits_csv.py refs/portraits.csv -d            # → Mode debug
    python update_portraits_csv.py refs/portraits.csv --repo USER/REPO  # → Repo personnalisé
"""

import sys
import os
import csv
import argparse
from pathlib import Path
from typing import Set


# Configuration par défaut
GITHUB_REPO = "Jawakaspa/orqual-portraits"
GITHUB_BRANCH = "main"
GITHUB_FOLDER = "thumbs"
ID_MIN = 1000
ID_MAX = 2599


def construire_url_github(id_portrait: int, repo: str, branch: str, folder: str) -> str:
    """Construit l'URL raw GitHub pour un portrait."""
    return f"https://raw.githubusercontent.com/{repo}/{branch}/{folder}/{id_portrait}.jpg"


def lire_ids_existants(fichier_csv: Path, verbose: bool = False, debug: bool = False) -> Set[str]:
    """
    Lit les IDs déjà présents dans portraits.csv.

    Returns:
        Set des idportrait existants (en str)
    """
    ids = set()

    if not fichier_csv.exists():
        if verbose:
            print(f"  Fichier inexistant, sera créé : {fichier_csv.resolve()}")
        return ids

    encodages = ["utf-8-sig", "utf-8", "windows-1252"]

    for encodage in encodages:
        try:
            with open(fichier_csv, 'r', encoding=encodage, newline='') as f:
                reader = csv.DictReader(
                    (line for line in f if not line.strip().startswith('#')),
                    delimiter=';'
                )

                if 'idportrait' not in (reader.fieldnames or []):
                    if debug:
                        print(f"[DEBUG] Colonne 'idportrait' absente, colonnes trouvées : {reader.fieldnames}")
                    continue

                for row in reader:
                    id_val = (row.get('idportrait') or '').strip()
                    if id_val:
                        ids.add(id_val)

            if verbose:
                print(f"  {len(ids)} portrait(s) existant(s) dans {fichier_csv.resolve()}")
            return ids

        except (UnicodeDecodeError, UnicodeError):
            continue

    print(f"[ERREUR] Impossible de lire {fichier_csv.resolve()}")
    return ids


def ajouter_portraits(
    fichier_csv: Path,
    repo: str = GITHUB_REPO,
    branch: str = GITHUB_BRANCH,
    folder: str = GITHUB_FOLDER,
    id_min: int = ID_MIN,
    id_max: int = ID_MAX,
    dry_run: bool = False,
    verbose: bool = False,
    debug: bool = False
) -> dict:
    """
    Ajoute les URLs GitHub des portraits au fichier CSV.

    Args:
        fichier_csv: Chemin vers portraits.csv
        repo: Repo GitHub (user/repo)
        branch: Branche GitHub
        folder: Dossier dans le repo
        id_min: ID portrait minimum
        id_max: ID portrait maximum
        dry_run: Simuler sans écrire
        verbose: Mode verbose
        debug: Mode debug

    Returns:
        dict: {"nb_ajoutes": int, "nb_ignores": int, "nb_total": int}
    """
    ids_existants = lire_ids_existants(fichier_csv, verbose=verbose, debug=debug)

    nouvelles_lignes = []
    nb_ignores = 0

    for id_portrait in range(id_min, id_max + 1):
        id_str = str(id_portrait)

        if id_str in ids_existants:
            nb_ignores += 1
            if debug:
                print(f"[DEBUG] ID {id_portrait} déjà présent, ignoré")
            continue

        url = construire_url_github(id_portrait, repo, branch, folder)
        nouvelles_lignes.append({
            'idportrait': id_str,
            'sexe': 'U',
            'portrait': url
        })

    nb_total = id_max - id_min + 1
    nb_ajoutes = len(nouvelles_lignes)

    print(f"IDs à traiter    : {nb_total} ({id_min} → {id_max})")
    print(f"Déjà présents    : {nb_ignores}")
    print(f"À ajouter        : {nb_ajoutes}")
    print(f"Repo GitHub      : {repo}")
    print()

    if nb_ajoutes == 0:
        print("Rien à ajouter.")
        return {"nb_ajoutes": 0, "nb_ignores": nb_ignores, "nb_total": nb_total}

    if dry_run:
        print("[DRY-RUN] Aperçu des 5 premières lignes :")
        for ligne in nouvelles_lignes[:5]:
            print(f"  {ligne['idportrait']};{ligne['sexe']};{ligne['portrait']}")
        if nb_ajoutes > 5:
            print(f"  ... et {nb_ajoutes - 5} autres")
        return {"nb_ajoutes": nb_ajoutes, "nb_ignores": nb_ignores, "nb_total": nb_total}

    fichier_existe = fichier_csv.exists()

    with open(fichier_csv, 'a', encoding='utf-8-sig', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['idportrait', 'sexe', 'portrait'], delimiter=';')

        if not fichier_existe:
            f.write(f"# portraits.csv - Généré par {__pgm__}\n")
            writer.writeheader()

        for ligne in nouvelles_lignes:
            writer.writerow(ligne)

    print(f"✓ {nb_ajoutes} ligne(s) ajoutée(s) → {fichier_csv.resolve()}")

    return {"nb_ajoutes": nb_ajoutes, "nb_ignores": nb_ignores, "nb_total": nb_total}


def main():
    """Point d'entrée CLI."""
    print(f"╔════════════════════════════════════════════════════════════════")
    print(f"║ {__pgm__} V{__version__} - {__date__}")
    print(f"║ Ajout des URLs GitHub des portraits dans portraits.csv")
    print(f"╚════════════════════════════════════════════════════════════════")
    print()

    if len(sys.argv) < 2:
        print("Usage :")
        print(f"  python {__pgm__} <portraits.csv> [options]")
        print()
        print("Arguments :")
        print("  portraits.csv        Chemin vers le fichier portraits.csv")
        print()
        print("Options :")
        print("  --repo USER/REPO     Repo GitHub (défaut: Jawakaspa/orqual-portraits)")
        print("  --branch BRANCH      Branche GitHub (défaut: main)")
        print("  --folder FOLDER      Dossier dans le repo (défaut: thumbs)")
        print("  --id-min N           ID portrait minimum (défaut: 1000)")
        print("  --id-max N           ID portrait maximum (défaut: 2599)")
        print("  --dry-run            Simuler sans écrire")
        print("  -v, --verbose        Affichage modéré")
        print("  -d, --debug          Affichage complet")
        print()
        print("Exemples :")
        print(f"  python {__pgm__} refs/portraits.csv")
        print(f"  python {__pgm__} refs/portraits.csv --dry-run")
        print(f"  python {__pgm__} C:\\cx\\refs\\portraits.csv -v")
        return 0

    parser = argparse.ArgumentParser(description="Ajout URLs GitHub dans portraits.csv")
    parser.add_argument('csv', help='Chemin vers portraits.csv')
    parser.add_argument('--repo', default=GITHUB_REPO, help='Repo GitHub')
    parser.add_argument('--branch', default=GITHUB_BRANCH, help='Branche GitHub')
    parser.add_argument('--folder', default=GITHUB_FOLDER, help='Dossier dans le repo')
    parser.add_argument('--id-min', type=int, default=ID_MIN, help='ID portrait minimum')
    parser.add_argument('--id-max', type=int, default=ID_MAX, help='ID portrait maximum')
    parser.add_argument('--dry-run', action='store_true', help='Simuler sans écrire')
    parser.add_argument('-v', '--verbose', action='store_true', help='Affichage modéré')
    parser.add_argument('-d', '--debug', action='store_true', help='Affichage complet')

    args = parser.parse_args()

    fichier_csv = Path(args.csv)

    stats = ajouter_portraits(
        fichier_csv=fichier_csv,
        repo=args.repo,
        branch=args.branch,
        folder=args.folder,
        id_min=args.id_min,
        id_max=args.id_max,
        dry_run=args.dry_run,
        verbose=args.verbose,
        debug=args.debug
    )

    print()
    print("═" * 70)
    print("RÉSUMÉ")
    print("═" * 70)
    print(f"Total IDs        : {stats['nb_total']}")
    print(f"Ajoutés          : {stats['nb_ajoutes']}")
    print(f"Ignorés (déjà)   : {stats['nb_ignores']}")

    if args.dry_run:
        print()
        print("⚠ Mode dry-run : rien n'a été écrit.")

    return 0


if __name__ == '__main__':
    sys.exit(main())
