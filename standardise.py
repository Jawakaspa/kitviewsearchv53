# standardise.py V1.0.2 - 17/12/2025 19:22:56
__pgm__ = "standardise.py"
__version__ = "1.0.2"
__date__ = "17/12/2025 19:22:56"

"""
Module de standardisation de texte.

Transforme un texte en forme standardisée :
- Minuscules
- Suppression des accents
- Suppression de la ponctuation
- Normalisation des espaces
"""

import re
import unicodedata


def standardise(texte):
    """
    Standardise un texte pour la recherche.
    
    Args:
        texte: Texte à standardiser
        
    Returns:
        Texte standardisé (minuscules, sans accents, sans ponctuation)
    """
    if texte is None or texte == "":
        return ""
    
    # Minuscules
    texte = texte.lower()
    
    # Supprimer les accents
    texte = unicodedata.normalize('NFD', texte)
    texte = ''.join(char for char in texte if unicodedata.category(char) != 'Mn')
    
    # Supprimer la ponctuation (SAUF {} qui sont des placeholders techniques)
    for char in ".!-_?',;:\"()[]":
        texte = texte.replace(char, " ")
    
    # Normaliser les espaces
    texte = re.sub(r'\s+', ' ', texte)
    
    return texte.strip()


if __name__ == "__main__":
    # Tests
    tests = [
        ("Béance antérieure", "beance anterieure"),
        ("Classe II d'Angle", "classe ii d angle"),
        ("  Multiple   espaces  ", "multiple espaces"),
        ("MAJUSCULES", "majuscules"),
        ("àéïôù", "aeiou"),
    ]
    
    print(f"{__pgm__} V{__version__}")
    print()
    
    for entree, attendu in tests:
        resultat = standardise(entree)
        ok = "✓" if resultat == attendu else "✗"
        print(f"{ok} '{entree}' → '{resultat}' (attendu: '{attendu}')")
