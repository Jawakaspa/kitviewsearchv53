#*TO*#
__pgm__ = "renomme.py"
__version__ = "0.0.0"
__date__ = "01/01/1970 00:00"

"""
renomme.py - Renomme des images (png/jpg) selon un fichier CSV de correspondance.

Le CSV doit avoir deux colonnes : ancien;nouveau
- ancien : nom complet du fichier avec extension (ex: IMG_2245.png)
- nouveau : nouveau nom SANS extension (ex: fake thierry 123456)
L'extension d'origine est conservée telle quelle.

En cas de doublons (même nouveau nom + même extension), un suffixe _2, _3... est ajouté.

Usage :
    python renomme.py <répertoire> <fichier_csv> [-d] [-v] [--dry-run]

Exemples :
    python renomme.py                                  # → Affiche l'aide
    python renomme.py C:/photos renomme.csv            # → Renomme les fichiers
    python renomme.py C:/photos renomme.csv --dry-run  # → Simule sans renommer
    python renomme.py C:/photos renomme.csv -d         # → Mode debug
"""

import argparse
import csv
import os
import sys
from pathlib import Path


def lire_csv(chemin_csv, debug=False):
    """Lit le CSV de correspondance ancien;nouveau. Retourne une liste de tuples (ancien, nouveau)."""
    chemin = Path(chemin_csv).resolve()
    if not chemin.exists():
        print(f"ERREUR : Fichier CSV introuvable : {chemin}")
        sys.exit(1)

    # Vérification encodage UTF-8-SIG (BOM)
    with open(chemin, "rb") as f:
        bom = f.read(3)
    if bom != b'\xef\xbb\xbf':
        print(f"ERREUR : Le fichier {chemin} n'est pas en UTF-8-SIG (BOM manquant)")
        sys.exit(1)

    correspondances = []
    with open(chemin, encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f, delimiter=";")

        # Vérification colonnes
        if "ancien" not in reader.fieldnames or "nouveau" not in reader.fieldnames:
            print(f"ERREUR : Le CSV doit contenir les colonnes 'ancien' et 'nouveau'")
            print(f"  Colonnes trouvées : {reader.fieldnames}")
            sys.exit(1)

        for i, row in enumerate(reader, start=2):
            ancien = row["ancien"].strip()
            nouveau = row["nouveau"].strip()
            if not ancien or not nouveau:
                if debug:
                    print(f"[DEBUG] Ligne {i} ignorée (valeur vide) : ancien='{ancien}', nouveau='{nouveau}'")
                continue
            # Ignorer les lignes de commentaire
            if ancien.startswith("#"):
                continue
            correspondances.append((ancien, nouveau))

    if debug:
        print(f"[DEBUG] {len(correspondances)} correspondances lues depuis {chemin}")
    return correspondances


def construire_plan_renommage(repertoire, correspondances, debug=False):
    """
    Construit le plan de renommage en gérant les doublons.
    Retourne une liste de tuples (chemin_ancien, chemin_nouveau, statut).
    statut : 'ok', 'absent', 'doublon_géré'
    """
    rep = Path(repertoire).resolve()

    # Lister les fichiers réels du répertoire (pour matching insensible à la casse)
    fichiers_reels = {}
    for f in rep.iterdir():
        if f.is_file():
            fichiers_reels[f.name.lower()] = f

    plan = []
    compteur_noms = {}  # clé = (nouveau_lower, ext_lower) → compteur

    for ancien, nouveau in correspondances:
        # Chercher le fichier source (insensible à la casse)
        fichier_source = fichiers_reels.get(ancien.lower())
        if fichier_source is None:
            if debug:
                print(f"[DEBUG] Fichier absent, ignoré : {ancien}")
            plan.append((rep / ancien, None, "absent"))
            continue

        # Conserver l'extension d'origine (y compris sa casse)
        ext = fichier_source.suffix  # ex: .PNG, .jpg

        # Gestion des doublons
        cle = (nouveau.lower(), ext.lower())
        if cle not in compteur_noms:
            compteur_noms[cle] = 1
            nom_final = f"{nouveau}{ext}"
            statut = "ok"
        else:
            compteur_noms[cle] += 1
            num = compteur_noms[cle]
            nom_final = f"{nouveau}_{num}{ext}"
            statut = "doublon_géré"

        chemin_nouveau = rep / nom_final

        if debug:
            print(f"[DEBUG] {fichier_source.name} → {nom_final} ({statut})")

        plan.append((fichier_source, chemin_nouveau, statut))

    return plan


def executer_renommage(plan, dry_run=False, debug=False, verbose=False):
    """Exécute le plan de renommage."""
    total = len(plan)
    renommes = 0
    absents = 0
    erreurs = 0
    doublons = 0

    for chemin_ancien, chemin_nouveau, statut in plan:
        if statut == "absent":
            absents += 1
            if verbose:
                print(f"  ABSENT  : {chemin_ancien.name}")
            continue

        if statut == "doublon_géré":
            doublons += 1

        try:
            if dry_run:
                print(f"  [DRY-RUN] {chemin_ancien.name} → {chemin_nouveau.name}")
            else:
                # Vérifier que la destination n'existe pas déjà
                if chemin_nouveau.exists():
                    print(f"  ERREUR  : Destination existe déjà : {chemin_nouveau}")
                    erreurs += 1
                    continue

                chemin_ancien.rename(chemin_nouveau)
                if verbose:
                    print(f"  OK      : {chemin_ancien.name} → {chemin_nouveau.name}")
            renommes += 1
        except OSError as e:
            print(f"  ERREUR  : {chemin_ancien.name} → {e}")
            erreurs += 1

    return renommes, absents, erreurs, doublons


def main():
    print(f"{__pgm__} V{__version__} - {__date__}")

    parser = argparse.ArgumentParser(
        description="Renomme des images (png/jpg) selon un fichier CSV de correspondance.",
        epilog="""
Exemples :
  python renomme.py C:/photos renomme.csv            # Renomme les fichiers
  python renomme.py C:/photos renomme.csv --dry-run  # Simule sans renommer
  python renomme.py C:/photos renomme.csv -d         # Mode debug
        """,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("repertoire", help="Répertoire contenant les images à renommer")
    parser.add_argument("csv_file", help="Fichier CSV de correspondance (ancien;nouveau)")
    parser.add_argument("-d", "--debug", action="store_true", help="Mode debug")
    parser.add_argument("-v", "--verbose", action="store_true", help="Mode verbose")
    parser.add_argument("--dry-run", action="store_true", help="Simule le renommage sans rien modifier")

    # Si aucun argument → afficher l'aide
    if len(sys.argv) == 1:
        parser.print_help()
        sys.exit(0)

    args = parser.parse_args()

    # Debug implique verbose
    if args.debug:
        args.verbose = True

    repertoire = Path(args.repertoire).resolve()
    csv_file = Path(args.csv_file).resolve()

    print(f"  Répertoire : {repertoire}")
    print(f"  Fichier CSV : {csv_file}")
    if args.dry_run:
        print(f"  Mode : DRY-RUN (simulation)")
    print()

    # Vérifications
    if not repertoire.is_dir():
        print(f"ERREUR : Répertoire introuvable : {repertoire}")
        sys.exit(1)

    # Lecture du CSV
    correspondances = lire_csv(csv_file, debug=args.debug)
    print(f"  {len(correspondances)} correspondances lues dans le CSV")

    # Extensions autorisées
    extensions_ok = {".jpg", ".jpeg", ".png"}

    # Filtrer : ne garder que les lignes dont l'ancien a une extension image
    correspondances_filtrees = []
    for ancien, nouveau in correspondances:
        ext = Path(ancien).suffix.lower()
        if ext in extensions_ok:
            correspondances_filtrees.append((ancien, nouveau))
        elif args.debug:
            print(f"[DEBUG] Extension non image ignorée : {ancien} ({ext})")

    if len(correspondances_filtrees) != len(correspondances):
        print(f"  {len(correspondances_filtrees)} correspondances retenues (extensions png/jpg uniquement)")

    # Construction du plan
    plan = construire_plan_renommage(repertoire, correspondances_filtrees, debug=args.debug)

    # Exécution
    print()
    renommes, absents, erreurs, doublons = executer_renommage(
        plan, dry_run=args.dry_run, debug=args.debug, verbose=args.verbose
    )

    # Bilan
    print()
    print(f"  Bilan :")
    print(f"    Renommés   : {renommes}")
    if doublons:
        print(f"    (dont doublons gérés avec suffixe : {doublons})")
    if absents:
        print(f"    Absents    : {absents}")
    if erreurs:
        print(f"    Erreurs    : {erreurs}")
    print()
    print(f"{__pgm__} terminé.")


if __name__ == "__main__":
    main()
