# motsvides.py V1.0.2 - 17/12/2025 17:14:35
__pgm__ = "motsvides.py"
__version__ = "1.0.2"
__date__ = "17/12/2025 17:14:35"

"""
Module de filtrage des mots vides (stopwords).

Supprime les mots vides d'un texte pour ne garder que les mots significatifs.
"""

# Mots vides français courants
MOTS_VIDES = {
    # Articles
    'le', 'la', 'les', 'un', 'une', 'des', 'du', 'de', 'l',
    # Prépositions
    'a', 'au', 'aux', 'avec', 'dans', 'en', 'pour', 'par', 'sur', 'sous',
    'entre', 'vers', 'chez', 'sans', 'contre',
    # Conjonctions
    'et', 'ou', 'mais', 'donc', 'car', 'ni', 'que', 'qui', 'quoi',
    # Pronoms
    'je', 'tu', 'il', 'elle', 'on', 'nous', 'vous', 'ils', 'elles',
    'me', 'te', 'se', 'lui', 'leur', 'y', 'en',
    'ce', 'cet', 'cette', 'ces', 'cela', 'ca',
    # Verbes auxiliaires
    'est', 'sont', 'a', 'ont', 'ai', 'as', 'avons', 'avez',
    'etre', 'avoir', 'faire', 'fait',
    # Adverbes
    'ne', 'pas', 'plus', 'moins', 'tres', 'bien', 'mal',
    # Mots interrogatifs
    'quels', 'quelles', 'quel', 'quelle', 'combien', 'comment', 'pourquoi',
    # Autres
    'tous', 'tout', 'toute', 'toutes',
    'autre', 'autres', 'meme', 'memes',
    'patient', 'patients', 'patiente', 'patientes',
    'ans', 'an', 'annee', 'annees',
}


def filtrer_mots_vides(texte, mots_vides_suppl=None):
    """
    Supprime les mots vides d'un texte.
    
    Args:
        texte: Texte à filtrer
        mots_vides_suppl: Set de mots vides supplémentaires (optionnel)
        
    Returns:
        Texte filtré (mots significatifs uniquement)
    """
    if not texte:
        return ""
    
    mots_vides = MOTS_VIDES.copy()
    if mots_vides_suppl:
        mots_vides.update(mots_vides_suppl)
    
    mots = texte.lower().split()
    mots_filtres = [m for m in mots if m not in mots_vides]
    
    return ' '.join(mots_filtres)


def identifier_motsvides(residu, filtres, verbose=False, debug=False):
    """
    Wrapper de compatibilité pour detall.py.
    
    Filtre les mots vides du résidu.
    
    Args:
        residu: Texte résiduel
        filtres: Dict de filtres (non modifié)
        verbose: Mode verbose
        debug: Mode debug
        
    Returns:
        Tuple (filtres, residu_filtre)
    """
    residu_filtre = filtrer_mots_vides(residu)
    
    if debug:
        print(f"[DEBUG] motsvides: '{residu}' → '{residu_filtre}'")
    
    return filtres, residu_filtre


if __name__ == "__main__":
    # Tests
    tests = [
        "les patients avec une beance",
        "quels sont les patients de moins de 30 ans",
        "combien de femmes avec bruxisme",
    ]
    
    print(f"{__pgm__} V{__version__}")
    print()
    
    for texte in tests:
        resultat = filtrer_mots_vides(texte)
        print(f"'{texte}'")
        print(f"  → '{resultat}'")
        print()
