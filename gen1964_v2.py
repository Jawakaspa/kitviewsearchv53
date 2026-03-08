#*TO*#
__pgm__ = "gen1964_v2.py"
__version__ = "0.0.0"
__date__ = "01/01/1970 00:00"

import os
import re
import csv
import unicodedata
from collections import defaultdict

INPUT_FILE = "DirCcxphotothumbsbase_yu.txt"
OUTPUT_FILE = "1964.csv"
PRENOMS_FILE = "prenoms_insee.csv"  # Fichier INSEE à placer dans le même dossier


def normalize(text):
    return ''.join(
        c for c in unicodedata.normalize('NFD', text)
        if unicodedata.category(c) != 'Mn'
    ).upper()


def load_prenoms_database():
    """
    Charge une base INSEE format:
    sexe;prenom;annee;nombre
    1 = M, 2 = F
    """
    db = defaultdict(lambda: {"M": 0, "F": 0})

    if not os.path.exists(PRENOMS_FILE):
        print("⚠️ Base INSEE absente :", PRENOMS_FILE)
        return db

    with open(PRENOMS_FILE, encoding="utf-8") as f:
        reader = csv.reader(f, delimiter=";")
        for row in reader:
            if len(row) < 4:
                continue
            sexe, prenom, _, nombre = row
            prenom = normalize(prenom)

            if sexe == "1":
                db[prenom]["M"] += int(nombre)
            elif sexe == "2":
                db[prenom]["F"] += int(nombre)

    return db


def detect_sex(firstname, db):
    norm = normalize(firstname)

    if norm in db:
        m = db[norm]["M"]
        f = db[norm]["F"]
        if m > f:
            return "M"
        elif f > m:
            return "F"
        else:
            return "I"

    # heuristique secondaire
    if norm.endswith("A"):
        return "F"
    if norm.endswith(("O", "N", "R", "D", "K", "L")):
        return "M"

    return "I"


def extract_name_parts(filename):
    # FIX: support jpg/JPG/png/PNG (insensible à la casse)
    base = re.sub(r'\.(jpg|jpeg|png)$', '', filename, flags=re.IGNORECASE)
    base = re.split(r'\s\d', base)[0]
    base = re.sub(r'(\D)\d+$', r'\1', base)

    parts = base.split()
    words = [p for p in parts if re.match(r'^[A-Za-zÀ-ÖØ-öø-ÿ\-]+$', p)]

    if not words:
        return "", ""

    prenom = words[-1]
    nom = " ".join(words[:-1])

    return nom.strip(), prenom.strip()


def main():
    print(f"{__pgm__} V{__version__} - {__date__}")

    db = load_prenoms_database()
    rows = []

    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        for line in f:
            # FIX 1: [\dÿ ]+ pour gérer le séparateur de milliers ÿ (Windows FR)
            # FIX 2: extensions jpg|JPG|png|PNG|jpeg|JPEG
            match = re.search(
                r'\d{2}:\d{2}\s+[\dÿ ]+\s+(.+\.(jpg|jpeg|png))\s*$',
                line, flags=re.IGNORECASE
            )
            if match:
                filename = match.group(1)
                nom, prenom = extract_name_parts(filename)
                sexe = detect_sex(prenom, db)
                rows.append([nom, prenom, sexe, filename])

    # FIX 3: UTF-8-SIG (BOM) pour le CSV de sortie
    with open(OUTPUT_FILE, "w", newline="", encoding="utf-8-sig") as csvfile:
        writer = csv.writer(csvfile, delimiter=";")
        writer.writerow(["nom", "prenom", "sexe", "portrait"])
        writer.writerows(rows)

    print(f"{len(rows)} lignes générées dans {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
