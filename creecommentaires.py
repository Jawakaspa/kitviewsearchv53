# creecommentaires.py V1.0.1 - 26/12/2025 13:46:08
__pgm__ = "creecommentaires.py"
__version__ = "1.0.1"
__date__ = "26/12/2025 13:46:08"

"""
Programme de génération du fichier commentaires.csv
Extrait les oripathologies à partir des colonnes canontags et canonadjs d'un fichier patients.

Usage: python creecommentaires.py <fichier_patients.csv>

Le fichier de sortie est créé dans /refs/commentaires.csv
- Si le fichier existe, les lignes existantes sont conservées (même avec commentaire vide)
- Seules les nouvelles oripathologies sont ajoutées
- Les oripathologies disparues sont conservées
- Le fichier de sortie est trié alphabétiquement par oripathologie
"""

import sys
import csv
import os
from pathlib import Path


def detecter_racine() -> Path:
    """
    Détecte la racine du projet en cherchant le répertoire contenant /refs ou /data.
    Remonte depuis le répertoire courant ou celui du script.
    """
    # Essayer depuis le répertoire courant
    chemin = Path.cwd()
    for _ in range(10):  # Maximum 10 niveaux
        if (chemin / "refs").exists() or (chemin / "data").exists():
            return chemin
        if chemin.parent == chemin:
            break
        chemin = chemin.parent
    
    # Essayer depuis le répertoire du script
    chemin = Path(__file__).resolve().parent
    for _ in range(10):
        if (chemin / "refs").exists() or (chemin / "data").exists():
            return chemin
        if chemin.parent == chemin:
            break
        chemin = chemin.parent
    
    # Par défaut, utiliser le répertoire courant
    return Path.cwd()


def generer_oripathologie(tag: str, adjs: str) -> str:
    """
    Génère une oripathologie à partir d'un tag et de ses adjectifs.
    
    Args:
        tag: Le tag canonique (ex: "béance")
        adjs: Les adjectifs séparés par | (ex: "latérale|sévère")
    
    Returns:
        L'oripathologie formatée en minuscules (ex: "béance latérale sévère")
    """
    tag = tag.strip().lower()
    adjs = adjs.strip().lower()
    
    if not adjs:
        return tag
    
    # Séparer les adjectifs par | et trier alphabétiquement
    liste_adjs = [a.strip() for a in adjs.split('|') if a.strip()]
    liste_adjs.sort()
    
    # Concaténer tag + adjectifs triés
    return tag + " " + " ".join(liste_adjs)


def extraire_oripathologies_patient(canontags: str, canonadjs: str) -> list[str]:
    """
    Extrait toutes les oripathologies d'un patient.
    
    Args:
        canontags: Tags séparés par virgule (ex: "béance,Bruxisme")
        canonadjs: Adjectifs correspondants séparés par virgule (ex: "latérale,nocturne|sévère")
    
    Returns:
        Liste des oripathologies générées
    """
    canontags = canontags.strip()
    canonadjs = canonadjs.strip()
    
    if not canontags:
        return []
    
    tags = canontags.split(',')
    adjs = canonadjs.split(',') if canonadjs else []
    
    # Compléter la liste des adjectifs si nécessaire
    while len(adjs) < len(tags):
        adjs.append('')
    
    oripathologies = []
    for i, tag in enumerate(tags):
        tag = tag.strip()
        if tag:
            adj = adjs[i].strip() if i < len(adjs) else ''
            oripathologie = generer_oripathologie(tag, adj)
            oripathologies.append(oripathologie)
    
    return oripathologies


def charger_commentaires_existants(chemin_fichier: Path) -> dict[str, str]:
    """
    Charge le fichier commentaires.csv existant s'il existe.
    
    Args:
        chemin_fichier: Chemin vers le fichier commentaires.csv
    
    Returns:
        Dictionnaire {oripathologie: commentaire}
    """
    commentaires = {}
    
    if not chemin_fichier.exists():
        print(f"[INFO] Fichier {chemin_fichier} inexistant, création d'un nouveau fichier")
        return commentaires
    
    print(f"[INFO] Chargement du fichier existant : {chemin_fichier}")
    
    try:
        with open(chemin_fichier, 'r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f, delimiter=';')
            
            # Vérifier les colonnes attendues
            if reader.fieldnames is None:
                print(f"[ERREUR] Fichier vide ou sans entête : {chemin_fichier}")
                return commentaires
            
            if 'oripathologie' not in reader.fieldnames:
                print(f"[ERREUR] Colonne 'oripathologie' manquante dans {chemin_fichier}")
                sys.exit(1)
            
            for row in reader:
                oripathologie = row.get('oripathologie', '').strip().lower()
                commentaire = row.get('commentaire', '').strip()
                if oripathologie:
                    # Si l'oripathologie existe déjà, conserver le commentaire non vide
                    if oripathologie in commentaires:
                        if commentaire and not commentaires[oripathologie]:
                            commentaires[oripathologie] = commentaire
                    else:
                        commentaires[oripathologie] = commentaire
        
        print(f"[INFO] {len(commentaires)} oripathologies existantes chargées")
        
    except UnicodeDecodeError:
        print(f"[ERREUR] Le fichier {chemin_fichier} n'est pas encodé en UTF-8-BOM")
        sys.exit(1)
    
    return commentaires


def extraire_toutes_oripathologies(chemin_patients: Path) -> set[str]:
    """
    Extrait toutes les oripathologies uniques du fichier patients.
    
    Args:
        chemin_patients: Chemin vers le fichier CSV des patients
    
    Returns:
        Ensemble des oripathologies uniques
    """
    oripathologies = set()
    
    print(f"[INFO] Lecture du fichier patients : {chemin_patients}")
    
    try:
        with open(chemin_patients, 'r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f, delimiter=';')
            
            if reader.fieldnames is None:
                print(f"[ERREUR] Fichier vide ou sans entête : {chemin_patients}")
                sys.exit(1)
            
            # Vérifier les colonnes requises
            colonnes_requises = ['canontags', 'canonadjs']
            for col in colonnes_requises:
                if col not in reader.fieldnames:
                    print(f"[ERREUR] Colonne '{col}' manquante dans {chemin_patients}")
                    sys.exit(1)
            
            nb_patients = 0
            for row in reader:
                # Ignorer les lignes vides (id vide)
                if not row.get('id', '').strip():
                    continue
                
                nb_patients += 1
                canontags = row.get('canontags', '')
                canonadjs = row.get('canonadjs', '')
                
                pathologies = extraire_oripathologies_patient(canontags, canonadjs)
                oripathologies.update(pathologies)
        
        print(f"[INFO] {nb_patients} patients traités")
        print(f"[INFO] {len(oripathologies)} oripathologies uniques extraites")
        
    except UnicodeDecodeError:
        print(f"[ERREUR] Le fichier {chemin_patients} n'est pas encodé en UTF-8-BOM")
        sys.exit(1)
    except FileNotFoundError:
        print(f"[ERREUR] Fichier introuvable : {chemin_patients}")
        sys.exit(1)
    
    return oripathologies


def sauvegarder_commentaires(chemin_fichier: Path, commentaires: dict[str, str]) -> None:
    """
    Sauvegarde le fichier commentaires.csv trié alphabétiquement.
    
    Args:
        chemin_fichier: Chemin vers le fichier de sortie
        commentaires: Dictionnaire {oripathologie: commentaire}
    """
    # Créer le répertoire refs s'il n'existe pas
    chemin_fichier.parent.mkdir(parents=True, exist_ok=True)
    
    # Trier les oripathologies alphabétiquement
    oripathologies_triees = sorted(commentaires.keys(), key=str.lower)
    
    print(f"[INFO] Écriture du fichier : {chemin_fichier}")
    
    with open(chemin_fichier, 'w', encoding='utf-8-sig', newline='') as f:
        writer = csv.writer(f, delimiter=';')
        
        # Écrire l'entête
        writer.writerow(['oripathologie', 'commentaire'])
        
        # Écrire les données triées
        for oripathologie in oripathologies_triees:
            writer.writerow([oripathologie, commentaires[oripathologie]])
    
    print(f"[INFO] {len(oripathologies_triees)} oripathologies écrites")


def main():
    print(f"{__pgm__} V{__version__} - {__date__}")
    print()
    
    # Vérifier les arguments
    if len(sys.argv) != 2:
        print(f"Usage: python {__pgm__} <fichier_patients.csv>")
        print()
        print("Exemple: python creecommentaires.py pats100.csv")
        sys.exit(1)
    
    fichier_patients = sys.argv[1]
    
    # Détecter la racine du projet
    racine = detecter_racine()
    print(f"[INFO] Racine du projet : {racine}")
    
    # Construire les chemins
    # Le fichier patients peut être dans /data ou à la racine
    chemin_patients = Path(fichier_patients)
    if not chemin_patients.is_absolute():
        # Chercher dans /data d'abord, puis à la racine
        if (racine / "data" / fichier_patients).exists():
            chemin_patients = racine / "data" / fichier_patients
        elif (racine / fichier_patients).exists():
            chemin_patients = racine / fichier_patients
        else:
            # Essayer le chemin tel quel
            chemin_patients = Path(fichier_patients).resolve()
    
    chemin_commentaires = racine / "refs" / "commentaires.csv"
    
    print(f"[INFO] Fichier patients : {chemin_patients}")
    print(f"[INFO] Fichier commentaires : {chemin_commentaires}")
    print()
    
    # Charger les commentaires existants
    commentaires_existants = charger_commentaires_existants(chemin_commentaires)
    nb_existants = len(commentaires_existants)
    
    # Extraire les oripathologies du fichier patients
    nouvelles_oripathologies = extraire_toutes_oripathologies(chemin_patients)
    
    # Fusionner : conserver les existants, ajouter les nouveaux
    nb_ajoutees = 0
    for oripathologie in nouvelles_oripathologies:
        if oripathologie not in commentaires_existants:
            commentaires_existants[oripathologie] = ''
            nb_ajoutees += 1
    
    # Sauvegarder le résultat
    sauvegarder_commentaires(chemin_commentaires, commentaires_existants)
    
    # Résumé
    print()
    print("=" * 60)
    print("RÉSUMÉ")
    print("=" * 60)
    print(f"  Oripathologies existantes conservées : {nb_existants}")
    print(f"  Nouvelles oripathologies ajoutées   : {nb_ajoutees}")
    print(f"  Total dans le fichier               : {len(commentaires_existants)}")
    print(f"  Fichier généré : {chemin_commentaires}")
    print("=" * 60)


if __name__ == "__main__":
    main()
