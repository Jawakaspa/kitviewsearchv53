# csv_utils.py V1.0.0 - 26/12/2025 20:07:20
__pgm__ = "csv_utils.py"
__version__ = "1.0.0"
__date__ = "26/12/2025 20:07:20"

"""
Module utilitaire pour la lecture sécurisée des fichiers CSV.

Ce module fournit des fonctions pour lire les fichiers CSV en filtrant
automatiquement les lignes de commentaires (commençant par #).

Utilisation:
    from csv_utils import lire_csv, lire_csv_reader
    
    # Avec DictReader (accès par nom de colonne)
    for row in lire_csv("fichier.csv"):
        valeur = row['ma_colonne']
    
    # Avec reader simple (accès par index)
    for row in lire_csv_reader("fichier.csv"):
        valeur = row[0]
    
    # Avec context manager pour contrôle fin
    with ouvrir_csv("fichier.csv") as (reader, f):
        for row in reader:
            ...
"""

import csv
import io
import os
from pathlib import Path
from typing import Iterator, TextIO, Any
from contextlib import contextmanager


# =============================================================================
# CONSTANTES
# =============================================================================

ENCODAGE_CSV = 'utf-8-sig'  # UTF-8 avec BOM pour Excel/CSV
SEPARATEUR_COLONNES = ';'
CARACTERE_COMMENTAIRE = '#'


# =============================================================================
# FONCTIONS PRINCIPALES
# =============================================================================

def filtrer_commentaires(fichier: TextIO) -> io.StringIO:
    """
    Filtre les lignes de commentaires d'un fichier ouvert.
    
    Args:
        fichier: Objet fichier ouvert en lecture
        
    Returns:
        StringIO contenant uniquement les lignes non-commentaires
        
    Note:
        Les lignes vides sont conservées (sauf si elles sont des commentaires).
        Les lignes de commentaires sont celles qui commencent par '#' 
        (après strip des espaces).
    """
    lignes_filtrees = []
    for ligne in fichier:
        ligne_strip = ligne.strip()
        # Garder les lignes non vides qui ne commencent pas par #
        if ligne_strip and not ligne_strip.startswith(CARACTERE_COMMENTAIRE):
            lignes_filtrees.append(ligne)
    
    return io.StringIO(''.join(lignes_filtrees))


def lire_csv(chemin: str | Path, 
             delimiter: str = SEPARATEUR_COLONNES,
             encodage: str = ENCODAGE_CSV) -> Iterator[dict[str, str]]:
    """
    Lit un fichier CSV et retourne un itérateur de dictionnaires.
    
    Les lignes de commentaires (commençant par #) sont automatiquement
    filtrées AVANT la lecture, garantissant que l'en-tête est correctement
    identifiée.
    
    Args:
        chemin: Chemin vers le fichier CSV
        delimiter: Séparateur de colonnes (défaut: ';')
        encodage: Encodage du fichier (défaut: 'utf-8-sig')
        
    Yields:
        Dictionnaires {nom_colonne: valeur} pour chaque ligne de données
        
    Raises:
        FileNotFoundError: Si le fichier n'existe pas
        UnicodeDecodeError: Si l'encodage est incorrect
        
    Example:
        >>> for row in lire_csv("refs/syntags.csv"):
        ...     print(row['original'], row['standard'])
    """
    chemin = Path(chemin)
    
    if not chemin.exists():
        raise FileNotFoundError(f"Fichier CSV introuvable: {chemin.absolute()}")
    
    with open(chemin, 'r', encoding=encodage) as f:
        contenu_filtre = filtrer_commentaires(f)
        reader = csv.DictReader(contenu_filtre, delimiter=delimiter)
        
        for row in reader:
            yield row


def lire_csv_reader(chemin: str | Path,
                    delimiter: str = SEPARATEUR_COLONNES,
                    encodage: str = ENCODAGE_CSV,
                    skip_header: bool = False) -> Iterator[list[str]]:
    """
    Lit un fichier CSV et retourne un itérateur de listes.
    
    Similaire à lire_csv() mais utilise csv.reader au lieu de DictReader.
    Utile quand on veut accéder aux colonnes par index ou quand
    l'en-tête n'est pas nécessaire.
    
    Args:
        chemin: Chemin vers le fichier CSV
        delimiter: Séparateur de colonnes (défaut: ';')
        encodage: Encodage du fichier (défaut: 'utf-8-sig')
        skip_header: Si True, ignore la première ligne (défaut: False)
        
    Yields:
        Listes de valeurs pour chaque ligne
        
    Raises:
        FileNotFoundError: Si le fichier n'existe pas
        UnicodeDecodeError: Si l'encodage est incorrect
        
    Example:
        >>> for row in lire_csv_reader("data.csv", skip_header=True):
        ...     print(row[0], row[1])
    """
    chemin = Path(chemin)
    
    if not chemin.exists():
        raise FileNotFoundError(f"Fichier CSV introuvable: {chemin.absolute()}")
    
    with open(chemin, 'r', encoding=encodage) as f:
        contenu_filtre = filtrer_commentaires(f)
        reader = csv.reader(contenu_filtre, delimiter=delimiter)
        
        if skip_header:
            next(reader, None)  # Ignorer l'en-tête
        
        for row in reader:
            yield row


def lire_csv_complet(chemin: str | Path,
                     delimiter: str = SEPARATEUR_COLONNES,
                     encodage: str = ENCODAGE_CSV) -> list[dict[str, str]]:
    """
    Lit un fichier CSV et retourne une liste complète de dictionnaires.
    
    Contrairement à lire_csv() qui est un générateur, cette fonction
    charge tout le fichier en mémoire. À utiliser pour les petits fichiers
    ou quand on a besoin d'accéder plusieurs fois aux données.
    
    Args:
        chemin: Chemin vers le fichier CSV
        delimiter: Séparateur de colonnes (défaut: ';')
        encodage: Encodage du fichier (défaut: 'utf-8-sig')
        
    Returns:
        Liste de dictionnaires {nom_colonne: valeur}
        
    Example:
        >>> donnees = lire_csv_complet("refs/ages.csv")
        >>> print(f"{len(donnees)} lignes chargées")
    """
    return list(lire_csv(chemin, delimiter, encodage))


def lire_csv_en_dict(chemin: str | Path,
                     colonne_cle: str,
                     delimiter: str = SEPARATEUR_COLONNES,
                     encodage: str = ENCODAGE_CSV) -> dict[str, dict[str, str]]:
    """
    Lit un fichier CSV et retourne un dictionnaire indexé par une colonne.
    
    Pratique pour créer des tables de lookup rapides.
    
    Args:
        chemin: Chemin vers le fichier CSV
        colonne_cle: Nom de la colonne à utiliser comme clé
        delimiter: Séparateur de colonnes (défaut: ';')
        encodage: Encodage du fichier (défaut: 'utf-8-sig')
        
    Returns:
        Dictionnaire {valeur_cle: {nom_colonne: valeur}}
        
    Raises:
        KeyError: Si la colonne_cle n'existe pas dans le fichier
        
    Example:
        >>> tags = lire_csv_en_dict("refs/syntags.csv", "original")
        >>> print(tags["bruxisme"]["standard"])
    """
    resultat = {}
    
    for row in lire_csv(chemin, delimiter, encodage):
        if colonne_cle not in row:
            raise KeyError(f"Colonne '{colonne_cle}' introuvable dans {chemin}")
        
        cle = row[colonne_cle]
        resultat[cle] = row
    
    return resultat


@contextmanager
def ouvrir_csv(chemin: str | Path,
               mode_dict: bool = True,
               delimiter: str = SEPARATEUR_COLONNES,
               encodage: str = ENCODAGE_CSV):
    """
    Context manager pour ouvrir un CSV avec filtrage des commentaires.
    
    Permet un contrôle plus fin sur la lecture, notamment pour accéder
    aux fieldnames du DictReader.
    
    Args:
        chemin: Chemin vers le fichier CSV
        mode_dict: Si True, utilise DictReader; sinon reader (défaut: True)
        delimiter: Séparateur de colonnes (défaut: ';')
        encodage: Encodage du fichier (défaut: 'utf-8-sig')
        
    Yields:
        Tuple (reader, fichier_original) pour accès au reader et cleanup
        
    Example:
        >>> with ouvrir_csv("data.csv") as (reader, f):
        ...     print("Colonnes:", reader.fieldnames)
        ...     for row in reader:
        ...         print(row)
    """
    chemin = Path(chemin)
    
    if not chemin.exists():
        raise FileNotFoundError(f"Fichier CSV introuvable: {chemin.absolute()}")
    
    f = open(chemin, 'r', encoding=encodage)
    try:
        contenu_filtre = filtrer_commentaires(f)
        
        if mode_dict:
            reader = csv.DictReader(contenu_filtre, delimiter=delimiter)
        else:
            reader = csv.reader(contenu_filtre, delimiter=delimiter)
        
        yield reader, f
    finally:
        f.close()


def obtenir_colonnes(chemin: str | Path,
                     delimiter: str = SEPARATEUR_COLONNES,
                     encodage: str = ENCODAGE_CSV) -> list[str]:
    """
    Retourne la liste des noms de colonnes d'un fichier CSV.
    
    Args:
        chemin: Chemin vers le fichier CSV
        delimiter: Séparateur de colonnes (défaut: ';')
        encodage: Encodage du fichier (défaut: 'utf-8-sig')
        
    Returns:
        Liste des noms de colonnes
        
    Example:
        >>> cols = obtenir_colonnes("refs/syntags.csv")
        >>> print(cols)  # ['original', 'standard', 'synonymes', ...]
    """
    chemin = Path(chemin)
    
    if not chemin.exists():
        raise FileNotFoundError(f"Fichier CSV introuvable: {chemin.absolute()}")
    
    with open(chemin, 'r', encoding=encodage) as f:
        contenu_filtre = filtrer_commentaires(f)
        reader = csv.DictReader(contenu_filtre, delimiter=delimiter)
        return reader.fieldnames or []


def compter_lignes(chemin: str | Path,
                   encodage: str = ENCODAGE_CSV) -> tuple[int, int]:
    """
    Compte les lignes d'un fichier CSV (avec et sans commentaires).
    
    Args:
        chemin: Chemin vers le fichier CSV
        encodage: Encodage du fichier (défaut: 'utf-8-sig')
        
    Returns:
        Tuple (lignes_totales, lignes_donnees) où lignes_donnees
        exclut les commentaires et l'en-tête
        
    Example:
        >>> total, donnees = compter_lignes("data.csv")
        >>> print(f"{donnees} lignes de données sur {total} lignes totales")
    """
    chemin = Path(chemin)
    
    if not chemin.exists():
        raise FileNotFoundError(f"Fichier CSV introuvable: {chemin.absolute()}")
    
    lignes_totales = 0
    lignes_commentaires = 0
    
    with open(chemin, 'r', encoding=encodage) as f:
        for ligne in f:
            lignes_totales += 1
            if ligne.strip().startswith(CARACTERE_COMMENTAIRE):
                lignes_commentaires += 1
    
    # lignes_donnees = total - commentaires - 1 (en-tête)
    lignes_donnees = max(0, lignes_totales - lignes_commentaires - 1)
    
    return lignes_totales, lignes_donnees


# =============================================================================
# FONCTION DE TEST
# =============================================================================

def main():
    """Fonction de test du module."""
    print(f"{__pgm__} V{__version__} - {__date__}")
    print("\nCe module fournit des fonctions utilitaires pour lire les CSV.")
    print("\nFonctions disponibles:")
    print("  - lire_csv(chemin)           : Itérateur de dict (DictReader)")
    print("  - lire_csv_reader(chemin)    : Itérateur de list (reader)")
    print("  - lire_csv_complet(chemin)   : Liste complète en mémoire")
    print("  - lire_csv_en_dict(chemin, cle) : Dict indexé par une colonne")
    print("  - ouvrir_csv(chemin)         : Context manager")
    print("  - obtenir_colonnes(chemin)   : Liste des noms de colonnes")
    print("  - compter_lignes(chemin)     : Compte lignes totales/données")
    print("\nExemple d'utilisation:")
    print("  from csv_utils import lire_csv")
    print("  for row in lire_csv('refs/syntags.csv'):")
    print("      print(row['original'])")


if __name__ == "__main__":
    main()
