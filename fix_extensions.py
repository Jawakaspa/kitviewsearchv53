#*TO*#
__pgm__ = "fix_extensions.py"
__version__ = "0.0.0"
__date__ = "01/01/1970 00:00"

"""
Renomme les extensions d'images en minuscules dans un répertoire.
Corrige .JPG → .jpg, .PNG → .png, etc.

Usage CLI :
    python fix_extensions.py                          # → Affiche l'aide
    python fix_extensions.py C:\\cx\\data\\thumbs        # → Renomme les extensions
    python fix_extensions.py C:\\cx\\data\\thumbs -v     # → Mode verbose
    python fix_extensions.py C:\\cx\\data\\thumbs -d     # → Mode debug
    python fix_extensions.py C:\\cx\\data\\thumbs --dry-run  # → Simule sans renommer
"""

import sys
import os
import argparse
from pathlib import Path

EXTENSIONS_IMAGES = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}


def show_help():
    """Affiche l'aide du programme."""
    print(f"{__pgm__} V{__version__} - {__date__}")
    print()
    print("Renomme les extensions d'images en minuscules (.JPG → .jpg, etc.)")
    print()
    print("Usage :")
    print(f"  python {__pgm__} <répertoire>              Renomme les extensions")
    print(f"  python {__pgm__} <répertoire> --dry-run    Simule sans renommer")
    print(f"  python {__pgm__} <répertoire> -v           Mode verbose")
    print(f"  python {__pgm__} <répertoire> -d           Mode debug")
    print()
    print("Exemples :")
    print(f"  python {__pgm__} C:\\cx\\data\\thumbs")
    print(f"  python {__pgm__} C:\\cx\\data\\thumbs --dry-run")


def main():
    if len(sys.argv) < 2 or sys.argv[1] in ("-h", "--help"):
        show_help()
        sys.exit(0)

    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("repertoire", type=str)
    parser.add_argument("-v", "--verbose", action="store_true")
    parser.add_argument("-d", "--debug", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    verbose = args.verbose or args.debug
    debug = args.debug
    dry_run = args.dry_run

    print(f"{__pgm__} V{__version__} - {__date__}")

    rep = Path(args.repertoire).resolve()
    if not rep.is_dir():
        print(f"ERREUR : Répertoire introuvable : {rep}")
        sys.exit(1)

    print(f"Répertoire : {rep}")
    if dry_run:
        print("MODE DRY-RUN : aucun fichier ne sera renommé")
    print()

    nb_renommes = 0
    nb_deja_ok = 0
    nb_total = 0

    for f in sorted(rep.iterdir()):
        if not f.is_file():
            continue
        if f.suffix.lower() not in EXTENSIONS_IMAGES:
            continue

        nb_total += 1
        ext_lower = f.suffix.lower()

        if f.suffix == ext_lower:
            nb_deja_ok += 1
            if debug:
                print(f"[DEBUG] OK : {f.name}")
            continue

        # Extension en majuscule → renommer
        nouveau_nom = f.stem + ext_lower
        nouveau_chemin = f.parent / nouveau_nom

        if verbose:
            print(f"  {f.name} → {nouveau_nom}")

        if not dry_run:
            # Sur Windows/NTFS, rename case-only nécessite un passage intermédiaire
            tmp = f.parent / (f.stem + ".tmp_rename")
            f.rename(tmp)
            tmp.rename(nouveau_chemin)

        nb_renommes += 1

    print()
    print("═" * 50)
    print(f"  Fichiers images   : {nb_total}")
    print(f"  Déjà en minuscule : {nb_deja_ok}")
    print(f"  Renommés          : {nb_renommes}")
    if dry_run:
        print(f"  (dry-run, aucun fichier modifié)")
    print("═" * 50)


if __name__ == "__main__":
    main()
