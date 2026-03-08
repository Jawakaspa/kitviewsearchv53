#*TO*#
__pgm__ = "renom.py"
__version__ = "0.0.0"
__date__ = "01/01/1970 00:00"

import sys
import os
import csv
import shutil
import argparse
from pathlib import Path

# ─── Configuration ───────────────────────────────────────────
SOURCE_DIR = Path(r"C:\PortraitsPhotofit\1964")
DEST_DIR = Path(r"C:\PortraitsPhotofit\1964N")
OUTPUT_CSV = DEST_DIR / "1964N.CSV"
START_NUMBER = 10000
EXTENSION = ".JPG"


def show_help():
    """Affiche l'aide du programme."""
    print(f"{__pgm__} V{__version__} - {__date__}")
    print()
    print("Renomme les portraits du répertoire 1964 vers 1964N avec numérotation séquentielle.")
    print()
    print("Usage :")
    print(f"  python {__pgm__} <fichier.csv>          Traite le fichier CSV")
    print(f"  python {__pgm__} <fichier.csv> -v        Mode verbose")
    print(f"  python {__pgm__} <fichier.csv> -d        Mode debug")
    print()
    print("Arguments :")
    print("  fichier.csv   Fichier CSV source (encodage UTF-8-SIG, séparateur ;)")
    print()
    print("Options :")
    print("  -v             Mode verbose (détails des opérations)")
    print("  -d             Mode debug (informations techniques)")
    print("  -h, --help     Affiche cette aide")
    print()
    print(f"Source     : {SOURCE_DIR}")
    print(f"Destination: {DEST_DIR}")
    print(f"CSV sortie : {OUTPUT_CSV}")
    print(f"Numérotation à partir de {START_NUMBER}")


def main():
    # --- Pas d'arguments → aide ---
    if len(sys.argv) < 2 or sys.argv[1] in ("-h", "--help"):
        show_help()
        sys.exit(0)

    # --- Parsing des arguments ---
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("csv_file", type=str)
    parser.add_argument("-v", "--verbose", action="store_true")
    parser.add_argument("-d", "--debug", action="store_true")
    args = parser.parse_args()

    verbose = args.verbose or args.debug
    debug = args.debug

    print(f"{__pgm__} V{__version__} - {__date__}")

    csv_path = Path(args.csv_file).resolve()
    print(f"Fichier CSV : {csv_path}")

    # --- Vérifications ---
    if not csv_path.is_file():
        print(f"ERREUR : Fichier introuvable : {csv_path}")
        sys.exit(1)

    if not SOURCE_DIR.is_dir():
        print(f"ERREUR : Répertoire source introuvable : {SOURCE_DIR}")
        sys.exit(1)

    # Créer le répertoire destination si nécessaire
    DEST_DIR.mkdir(parents=True, exist_ok=True)
    print(f"Répertoire source      : {SOURCE_DIR}")
    print(f"Répertoire destination : {DEST_DIR}")

    # --- Lecture du CSV ---
    rows = []
    with open(csv_path, mode="r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f, delimiter=";")
        fieldnames = reader.fieldnames
        if debug:
            print(f"[DEBUG] Colonnes détectées : {fieldnames}")
        for row in reader:
            rows.append(row)

    total = len(rows)
    print(f"Lignes lues : {total}")

    # Vérifier colonnes requises
    for col in ("portrait", "nportrait"):
        if col not in fieldnames:
            print(f"ERREUR : Colonne '{col}' absente du CSV. Colonnes trouvées : {fieldnames}")
            sys.exit(1)

    # --- Index des fichiers présents dans le répertoire source ---
    print(f"Indexation des fichiers dans {SOURCE_DIR}...")
    fichiers_source = {}
    for f in SOURCE_DIR.iterdir():
        if f.is_file():
            fichiers_source[f.name] = f
    print(f"Fichiers trouvés dans source : {len(fichiers_source)}")

    # --- Traitement ---
    try:
        from tqdm import tqdm
        iterator = tqdm(enumerate(rows), total=total, desc="Renommage", unit="fichier",
                        bar_format="{l_bar}{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}]")
    except ImportError:
        print("(tqdm non disponible, progression simple)")
        iterator = enumerate(rows)

    compteur = START_NUMBER
    copies = 0
    absents = 0
    vides = 0

    for i, row in iterator:
        portrait = row.get("portrait", "").strip()

        if not portrait:
            vides += 1
            if debug:
                print(f"[DEBUG] Ligne {i + 2} : colonne portrait vide, ignorée")
            continue

        if portrait in fichiers_source:
            nouveau_nom = f"{compteur}{EXTENSION}"
            src = fichiers_source[portrait]
            dst = DEST_DIR / nouveau_nom

            shutil.copy2(src, dst)
            row["nportrait"] = nouveau_nom
            copies += 1

            if verbose:
                print(f"  {portrait} → {nouveau_nom}")
            if debug:
                print(f"[DEBUG] Copie : {src} → {dst}")

            compteur += 1
        else:
            absents += 1
            if verbose:
                print(f"  ABSENT : {portrait}")
            if debug:
                print(f"[DEBUG] Ligne {i + 2} : fichier introuvable : {portrait}")

    # --- Écriture du CSV de sortie ---
    print(f"Écriture du CSV : {OUTPUT_CSV}")
    with open(OUTPUT_CSV, mode="w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, delimiter=";")
        writer.writeheader()
        writer.writerows(rows)

    # --- Résumé ---
    print()
    print("═" * 50)
    print(f"  Lignes traitées   : {total}")
    print(f"  Portraits vides   : {vides}")
    print(f"  Fichiers copiés   : {copies}")
    print(f"  Fichiers absents  : {absents}")
    print(f"  Numéros attribués : {START_NUMBER} → {compteur - 1}")
    print(f"  CSV sauvegardé    : {OUTPUT_CSV}")
    print("═" * 50)


if __name__ == "__main__":
    main()
