# saisis2fr.py V1.0.1 - 07/12/2025 19:56:53
__pgm__ = "saisis2fr.py"
__version__ = "1.0.1"
__date__ = "07/12/2025 19:56:53"

# ╔════════════════════════════════════════════════════════════════
# ║ saisis2fr.py
# ║ Transforme tagssaisis.csv (format utilisateur français)
# ║ en tagsfr.csv (format informatique, préparé pour multilingue)
# ╚════════════════════════════════════════════════════════════════

import csv
import sys
import os
import io
import unicodedata
import re


def standardise(texte):
    """
    Normalise un texte selon les règles définies dans standardise.txt.
    
    Args:
        texte: Le texte à normaliser (str ou None)
        
    Returns:
        Le texte normalisé (str)
    """
    # Gérer les cas None ou vides
    if texte is None or texte == "":
        return ""
    
    # 1. Tout en minuscules
    texte = texte.lower()
    
    # 2. Supprimer les accents et diacritiques
    # Décomposer les caractères accentués puis filtrer les marques diacritiques
    texte = unicodedata.normalize('NFD', texte)
    texte = ''.join(char for char in texte if unicodedata.category(char) != 'Mn')
    
    # 3. Remplacer ".", "!", "-", "?" et "_" par des espaces
    texte = texte.replace(".", " ")
    texte = texte.replace("!", " ")
    texte = texte.replace("-", " ")
    texte = texte.replace("_", " ")
    texte = texte.replace("?", " ")
    
    # 4. Dédoublonner les espaces multiples
    texte = re.sub(r'\s+', ' ', texte)
    
    # Supprimer les espaces en début et fin
    texte = texte.strip()
    
    return texte


def standardise_liste(liste_csv: str) -> str:
    """
    Standardise chaque élément d'une liste CSV (séparateur virgule).
    Conserve la structure avec | pour les synonymes d'adjectifs.
    
    Args:
        liste_csv: chaîne avec éléments séparés par des virgules
        
    Returns:
        chaîne standardisée avec mêmes séparateurs
    """
    if not liste_csv or liste_csv.strip() == "":
        return ""
    
    elements = liste_csv.split(",")
    elements_std = []
    
    for elem in elements:
        # Traiter les synonymes d'adjectifs (séparés par |)
        if "|" in elem:
            sous_elements = elem.split("|")
            sous_elements_std = [standardise(se) for se in sous_elements]
            elements_std.append("|".join(sous_elements_std))
        else:
            elements_std.append(standardise(elem))
    
    return ",".join(elements_std)


def transformer_ligne(row: dict) -> dict:
    """
    Transforme une ligne de tagssaisis.csv en ligne pour tagsfr.csv.
    
    Args:
        row: dictionnaire avec les colonnes type, canonfr, synonymesfr, adjectifsfr
        
    Returns:
        dictionnaire avec les colonnes type, frtags, stdfrtags, fradjs, stdfradjs
    """
    type_tag = row.get("type", "").strip()
    canonfr = row.get("canonfr", "").strip()
    synonymesfr = row.get("synonymesfr", "").strip()
    adjectifsfr = row.get("adjectifsfr", "").strip()
    
    # frtags = canonfr + synonymes (si présents)
    if synonymesfr:
        frtags = f"{canonfr},{synonymesfr}"
    else:
        frtags = canonfr
    
    # stdfrtags = frtags standardisé
    stdfrtags = standardise_liste(frtags)
    
    # fradjs = copie de adjectifsfr
    fradjs = adjectifsfr
    
    # stdfradjs = fradjs standardisé
    stdfradjs = standardise_liste(fradjs)
    
    return {
        "type": type_tag,
        "frtags": frtags,
        "stdfrtags": stdfrtags,
        "fradjs": fradjs,
        "stdfradjs": stdfradjs
    }


def verifier_encodage_bom(filepath: str) -> bool:
    """
    Vérifie si un fichier CSV est encodé en UTF-8 avec BOM.
    
    Args:
        filepath: chemin du fichier à vérifier
        
    Returns:
        True si UTF-8-BOM, False sinon
    """
    try:
        with open(filepath, 'rb') as f:
            debut = f.read(3)
            return debut == b'\xef\xbb\xbf'
    except Exception as e:
        print(f"ERREUR : Impossible de lire {filepath} : {e}", file=sys.stderr)
        return False


def lire_csv_avec_commentaires(filepath: str):
    """
    Lit un fichier CSV en ignorant les lignes de commentaires (commençant par #).
    
    Args:
        filepath: chemin du fichier CSV
        
    Returns:
        tuple (fieldnames, rows, nb_commentaires) où rows est une liste de dictionnaires
    """
    lignes_donnees = []
    nb_commentaires_entete = 0
    
    with open(filepath, 'r', encoding='utf-8-sig', newline='') as f:
        # Lire toutes les lignes et filtrer les commentaires
        for ligne in f:
            ligne_stripped = ligne.strip()
            if ligne_stripped.startswith('#'):
                nb_commentaires_entete += 1
                continue
            lignes_donnees.append(ligne)
    
    if nb_commentaires_entete > 0:
        print(f"Lignes de commentaires en entête ignorées : {nb_commentaires_entete}")
    
    # Recréer un fichier virtuel avec les lignes filtrées
    contenu_filtre = ''.join(lignes_donnees)
    fichier_virtuel = io.StringIO(contenu_filtre)
    
    reader = csv.DictReader(fichier_virtuel, delimiter=';')
    fieldnames = reader.fieldnames
    rows = list(reader)
    
    return fieldnames, rows, nb_commentaires_entete


def main():
    print(f"{__pgm__} V{__version__} - {__date__}")
    
    # Déterminer le répertoire du script puis le sous-répertoire refs
    script_dir = os.path.dirname(os.path.abspath(__file__))
    refs_dir = os.path.join(script_dir, "refs")
    
    # Chemins des fichiers
    fichier_entree = os.path.join(refs_dir, "tagssaisis.csv")
    fichier_sortie = os.path.join(refs_dir, "tagsfr.csv")
    
    print(f"Fichier d'entrée  : {fichier_entree}")
    print(f"Fichier de sortie : {fichier_sortie}")
    
    # Vérifier l'existence du répertoire refs
    if not os.path.exists(refs_dir):
        print(f"ERREUR : Le répertoire {refs_dir} n'existe pas.", file=sys.stderr)
        sys.exit(1)
    
    # Vérifier l'existence du fichier d'entrée
    if not os.path.exists(fichier_entree):
        print(f"ERREUR : Le fichier {fichier_entree} n'existe pas.", file=sys.stderr)
        sys.exit(1)
    
    # Vérifier l'encodage UTF-8-BOM
    if not verifier_encodage_bom(fichier_entree):
        print(f"ERREUR : Le fichier {fichier_entree} n'est pas encodé en UTF-8-BOM.", file=sys.stderr)
        sys.exit(1)
    
    print("Encodage UTF-8-BOM vérifié ✓")
    
    # Lire le fichier en ignorant les commentaires
    try:
        fieldnames, rows, nb_commentaires_entete = lire_csv_avec_commentaires(fichier_entree)
        
        # Vérifier les colonnes attendues
        colonnes_attendues = {"type", "canonfr", "synonymesfr", "adjectifsfr"}
        colonnes_presentes = set(fieldnames) if fieldnames else set()
        
        if not colonnes_attendues.issubset(colonnes_presentes):
            colonnes_manquantes = colonnes_attendues - colonnes_presentes
            print(f"ERREUR : Colonnes manquantes dans {fichier_entree} : {colonnes_manquantes}", file=sys.stderr)
            sys.exit(1)
        
        print(f"Colonnes détectées : {fieldnames}")
        
    except Exception as e:
        print(f"ERREUR lors de la lecture de {fichier_entree} : {e}", file=sys.stderr)
        sys.exit(1)
    
    # Transformer les lignes
    lignes_sortie = []
    nb_lignes_traitees = 0
    nb_lignes_commentaires_corps = 0
    
    for row in rows:
        # Ignorer les lignes de commentaires dans le corps (commençant par #)
        if row.get("type", "").startswith("#"):
            nb_lignes_commentaires_corps += 1
            continue
        
        # Ignorer les lignes vides
        if not row.get("type", "").strip() and not row.get("canonfr", "").strip():
            continue
        
        ligne_transformee = transformer_ligne(row)
        lignes_sortie.append(ligne_transformee)
        nb_lignes_traitees += 1
        print(f"  [{nb_lignes_traitees}] {ligne_transformee['frtags'][:50]}...")
    
    # Écrire le fichier de sortie en UTF-8-BOM
    try:
        with open(fichier_sortie, 'w', encoding='utf-8-sig', newline='') as f_out:
            colonnes_sortie = ["type", "frtags", "stdfrtags", "fradjs", "stdfradjs"]
            writer = csv.DictWriter(f_out, fieldnames=colonnes_sortie, delimiter=';')
            
            writer.writeheader()
            for ligne in lignes_sortie:
                writer.writerow(ligne)
        
        print(f"\n{'='*60}")
        print(f"Transformation terminée avec succès !")
        print(f"  - Lignes traitées            : {nb_lignes_traitees}")
        print(f"  - Commentaires entête        : {nb_commentaires_entete}")
        print(f"  - Commentaires corps         : {nb_lignes_commentaires_corps}")
        print(f"  - Fichier créé               : {fichier_sortie}")
        print(f"{'='*60}")
    
    except Exception as e:
        print(f"ERREUR lors de l'écriture de {fichier_sortie} : {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
