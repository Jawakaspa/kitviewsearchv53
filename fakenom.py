#*TO*#
__pgm__ = "fakenom.py"
__version__ = "0.0.0"
__date__ = "01/01/1970 00:00"

import sys
import os
import csv
import argparse
from faker import Faker

# ============================================================
# fakenom.py - Anonymisation des noms et prénoms dans un CSV
# ============================================================
# Usage :
#   python fakenom.py pats01964.csv toto.csv        # génère data/toto.csv
#   python fakenom.py pats01964.csv toto.csv -d      # mode debug
#   python fakenom.py pats01964.csv toto.csv -v      # mode verbose
#
# - Le fichier source est cherché dans /data
# - Le fichier résultat est créé dans /data
# - Les colonnes "nom" et "prenom" sont remplacées par des faux noms
#   générés avec Faker (locale fr_FR)
# - Le prénom généré respecte le sexe (colonne "sexe" : M/F)
# - Un même couple (prenom, nom) original → même couple fake (cohérence)
# ============================================================


def detect_root():
    """Détecte la racine du projet (là où se trouve le script)."""
    return os.path.dirname(os.path.abspath(__file__))


def show_help():
    """Affiche l'aide du programme."""
    print()
    print("Anonymisation des noms et prénoms d'un fichier CSV patients.")
    print()
    print("Usage :")
    print(f"  python {__pgm__} <source.csv> <resultat.csv> [-d] [-v]")
    print()
    print("Arguments :")
    print("  source.csv     Fichier CSV source (dans /data)")
    print("  resultat.csv   Fichier CSV résultat (créé dans /data)")
    print()
    print("Options :")
    print("  -d, --debug    Mode debug (affichage détaillé)")
    print("  -v, --verbose  Mode verbose (identique à -d)")


def main():
    print(f"{__pgm__} V{__version__} - {__date__}")

    # --- Sans arguments → aide ---
    if len(sys.argv) < 2:
        show_help()
        return

    # --- Parsing des arguments ---
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("source", nargs="?", help="Fichier CSV source")
    parser.add_argument("resultat", nargs="?", help="Fichier CSV résultat")
    parser.add_argument("-d", "--debug", action="store_true")
    parser.add_argument("-v", "--verbose", action="store_true")
    args = parser.parse_args()

    debug = args.debug or args.verbose

    if not args.source or not args.resultat:
        show_help()
        return

    # --- Chemins ---
    root = detect_root()
    data_dir = os.path.join(root, "data")
    src_path = os.path.join(data_dir, args.source)
    dst_path = os.path.join(data_dir, args.resultat)

    if not os.path.isfile(src_path):
        print(f"ERREUR : fichier source introuvable : {src_path}")
        sys.exit(1)

    print(f"Source  : {src_path}")
    print(f"Résultat: {dst_path}")

    # --- Lecture du fichier source ---
    with open(src_path, "r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f, delimiter=";")
        fieldnames = reader.fieldnames

        if not fieldnames:
            print("ERREUR : impossible de lire l'entête du CSV.")
            sys.exit(1)

        for col in ("prenom", "nom", "sexe"):
            if col not in fieldnames:
                print(f"ERREUR : colonne '{col}' absente de l'entête.")
                sys.exit(1)

        rows = list(reader)

    nb_total = len(rows)
    print(f"Lignes lues : {nb_total}")

    # --- Génération des faux noms avec Faker ---
    fake = Faker("fr_FR")
    Faker.seed(42)  # reproductibilité

    # Mapping (prenom_original, nom_original, sexe) → (fake_prenom, fake_nom)
    # On inclut le sexe dans la clé pour gérer le cas improbable
    # d'homonymes de sexe différent.
    mapping = {}

    # Compteur de noms de famille uniques pour éviter les doublons fake
    used_lastnames = set()

    def get_fake_identity(prenom_orig, nom_orig, sexe):
        """Retourne un couple (fake_prenom, fake_nom) cohérent et stable."""
        key = (prenom_orig.strip(), nom_orig.strip(), sexe.strip())
        if key in mapping:
            return mapping[key]

        # Prénom selon le sexe
        if sexe.strip().upper() == "M":
            fake_prenom = fake.first_name_male()
        else:
            fake_prenom = fake.first_name_female()

        # Nom de famille unique
        for _ in range(100):
            fake_nom = fake.last_name()
            if fake_nom not in used_lastnames:
                break
        used_lastnames.add(fake_nom)

        mapping[key] = (fake_prenom, fake_nom)
        return fake_prenom, fake_nom

    # --- Transformation ---
    for row in rows:
        prenom_orig = row["prenom"]
        nom_orig = row["nom"]
        sexe = row["sexe"]

        fake_prenom, fake_nom = get_fake_identity(prenom_orig, nom_orig, sexe)
        row["prenom"] = fake_prenom
        row["nom"] = fake_nom

    # --- Écriture du fichier résultat ---
    with open(dst_path, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, delimiter=";")
        writer.writeheader()
        writer.writerows(rows)

    nb_identites = len(mapping)
    print(f"Identités uniques anonymisées : {nb_identites}")
    print(f"Fichier créé : {dst_path}")

    # --- Debug : échantillon ---
    if debug:
        print()
        print("[DEBUG] Échantillon des 10 premiers mappings :")
        for i, (key, val) in enumerate(mapping.items()):
            if i >= 10:
                break
            print(f"  ({key[0]}, {key[1]}, {key[2]}) → ({val[0]}, {val[1]})")


if __name__ == "__main__":
    main()
