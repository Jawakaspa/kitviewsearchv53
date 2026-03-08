#*TO*#
__pgm__ = "alea_portraits.py"
__version__ = "0.0.0"
__date__ = "01/01/1970 00:00"

import argparse
import csv
import io
import os
import random
import sys

DESCRIPTION = """
Modifie aléatoirement (seed 42) 1600 idportraits dans un fichier patients CSV.
- Les 1600 positions sont choisies aléatoirement parmi les 3200 lignes
- Les valeurs assignées vont de 1000 à 2599 (1600 valeurs uniques)
- Les valeurs sont distribuées aléatoirement sur les positions sélectionnées
- Pour les idportrait 1000-1009 : prénom → "Thierry", sexe → "M"
- Pour les idportrait 1180-1189 : prénom → "Gérard", sexe → "M"
"""


def parse_args():
    parser = argparse.ArgumentParser(
        description=DESCRIPTION,
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("input", nargs="?", help="Fichier CSV d'entrée (ex: pats3200.csv)")
    parser.add_argument("-o", "--output", help="Fichier CSV de sortie (défaut: <input>_alea.csv)")
    parser.add_argument("-d", "--debug", action="store_true", help="Mode debug")
    parser.add_argument("-v", "--verbose", action="store_true", help="Mode verbose")

    args = parser.parse_args()

    if not args.input:
        parser.print_help()
        print("\nArguments:")
        print("  input              Fichier CSV d'entrée (obligatoire)")
        print("\nOptions:")
        print("  -o, --output       Fichier CSV de sortie")
        print("  -d, --debug        Mode debug (détails internes)")
        print("  -v, --verbose      Mode verbose (équivalent à -d)")
        sys.exit(0)

    args.debug = args.debug or args.verbose
    return args


def load_csv(filepath, debug=False):
    """Charge un CSV en ignorant les lignes de commentaire (#)."""
    abs_path = os.path.abspath(filepath)
    print(f"  Lecture de {abs_path}")

    if not os.path.exists(filepath):
        print(f"ERREUR : Fichier introuvable : {abs_path}")
        sys.exit(1)

    with open(filepath, encoding="utf-8-sig") as f:
        raw_lines = f.readlines()

    comments = [l for l in raw_lines if l.startswith("#")]
    data_lines = [l for l in raw_lines if not l.startswith("#")]

    reader = csv.DictReader(io.StringIO("".join(data_lines)), delimiter=";")
    rows = list(reader)
    fieldnames = reader.fieldnames

    if debug:
        print(f"  [DEBUG] {len(comments)} ligne(s) de commentaire, {len(rows)} lignes de données")
        print(f"  [DEBUG] Colonnes : {fieldnames}")

    return comments, fieldnames, rows


def process(rows, debug=False):
    """Applique les modifications aléatoires."""
    rng = random.Random(42)
    n_total = len(rows)
    n_modify = 1600
    portrait_values = list(range(1000, 2600))  # 1000..2599 = 1600 valeurs

    # Sélection aléatoire de 1600 positions parmi 3200
    all_indices = list(range(n_total))
    selected_indices = sorted(rng.sample(all_indices, n_modify))

    # Mélange des valeurs de portrait
    rng.shuffle(portrait_values)

    if debug:
        print(f"  [DEBUG] {n_modify} positions sélectionnées sur {n_total}")
        print(f"  [DEBUG] Premiers indices sélectionnés : {selected_indices[:10]}...")
        print(f"  [DEBUG] Premières valeurs portrait : {portrait_values[:10]}...")

    # Assignation des idportrait
    modified_count = 0
    for i, idx in enumerate(selected_indices):
        rows[idx]["idportrait"] = str(portrait_values[i])
        modified_count += 1

    print(f"  {modified_count} idportraits modifiés (valeurs 1000-2599)")

    # Modification des prénoms et sexe par idportrait
    thierry_count = 0
    gerard_count = 0
    for row in rows:
        portrait = int(row["idportrait"])
        if 1000 <= portrait <= 1009:
            row["prenom"] = "Thierry"
            row["sexe"] = "M"
            thierry_count += 1
        elif 1180 <= portrait <= 1189:
            row["prenom"] = "Gérard"
            row["sexe"] = "M"
            gerard_count += 1

    print(f"  {thierry_count} prénoms → Thierry, sexe → M (idportrait 1000-1009)")
    print(f"  {gerard_count} prénoms → Gérard, sexe → M (idportrait 1180-1189)")

    return rows


def save_csv(filepath, comments, fieldnames, rows, debug=False):
    """Sauvegarde le CSV en UTF-8-SIG avec les commentaires d'origine."""
    abs_path = os.path.abspath(filepath)

    with open(filepath, "w", encoding="utf-8-sig", newline="") as f:
        # Réécrire les commentaires
        for c in comments:
            f.write(c)

        writer = csv.DictWriter(f, fieldnames=fieldnames, delimiter=";", lineterminator="\r\n")
        writer.writeheader()
        writer.writerows(rows)

    print(f"  Fichier écrit : {abs_path}")
    print(f"  {len(rows)} lignes écrites")


def main():
    print(f"{__pgm__} V{__version__} - {__date__}")
    args = parse_args()
    debug = args.debug

    input_path = args.input
    if args.output:
        output_path = args.output
    else:
        base, ext = os.path.splitext(input_path)
        output_path = f"{base}_alea{ext}"

    print(f"\n--- Chargement ---")
    comments, fieldnames, rows = load_csv(input_path, debug)

    print(f"\n--- Traitement (seed=42) ---")
    rows = process(rows, debug)

    print(f"\n--- Sauvegarde ---")
    save_csv(output_path, comments, fieldnames, rows, debug)

    print(f"\nTerminé.")


if __name__ == "__main__":
    main()
