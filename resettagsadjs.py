# resettagsadjs.py V1.0.2 - 27/12/2025 12:50:46
__pgm__ = "resettagsadjs.py"
__version__ = "1.0.2"
__date__ = "27/12/2025 12:50:46"

"""
Script d'orchestration pour régénérer tous les fichiers de synonymes multilingues.

Ce script exécute dans l'ordre :
1. Copie tagsadjs.csv → frtagsadjs.csv (français, pas de traduction)
2. Traduit tagsadjs.csv vers toutes les autres langues → xxtagsadjs.csv
3. Génère xxsyntags.csv et xxsynadjs.csv pour chaque langue

IMPORTANT : 
- Le fichier source tagsadjs.csv doit contenir TAGS (type='p') ET ADJECTIFS (type='a')
- Ce script n'utilise PAS l'option -t de traduis.py (traduction complète)

Usage :
    python resettagsadjs.py                # Exécution complète
    python resettagsadjs.py --verbose      # Avec détails
    python resettagsadjs.py --only fr      # Une seule langue (skip traduction)
    python resettagsadjs.py --skip-trad    # Skip l'étape de traduction
"""

import sys
import os
import shutil
import time
from pathlib import Path
from datetime import datetime

# ══════════════════════════════════════════════════════════════════════════════
# CONFIGURATION
# ══════════════════════════════════════════════════════════════════════════════

CHEMIN_COMMUN = "refs/commun.csv"
FICHIER_SOURCE = "refs/tagsadjs.csv"

# Encodages à essayer pour lire les fichiers CSV
ENCODAGES = ['utf-8-sig', 'utf-8', 'windows-1252', 'latin-1']

# ══════════════════════════════════════════════════════════════════════════════
# UTILITAIRES
# ══════════════════════════════════════════════════════════════════════════════

def lire_fichier_multi_encodage(chemin: Path) -> tuple:
    """
    Lit un fichier en essayant plusieurs encodages.
    
    Returns:
        tuple: (contenu, encodage_utilise) ou (None, None) si échec
    """
    for encodage in ENCODAGES:
        try:
            with open(chemin, 'r', encoding=encodage) as f:
                contenu = f.read()
            return contenu, encodage
        except (UnicodeDecodeError, UnicodeError):
            continue
    return None, None


def charger_langues(chemin_commun: Path) -> list:
    """Charge les langues depuis commun.csv."""
    import csv
    import io
    
    if not chemin_commun.exists():
        print(f"[ERREUR] Fichier non trouvé : {chemin_commun}")
        return []
    
    try:
        contenu, encodage = lire_fichier_multi_encodage(chemin_commun)
        if contenu is None:
            print(f"[ERREUR] Impossible de lire {chemin_commun}")
            return []
        
        # Filtrer les commentaires
        lignes_data = [l for l in contenu.splitlines() if l.strip() and not l.strip().startswith('#')]
        
        reader = csv.DictReader(io.StringIO('\n'.join(lignes_data)), delimiter=';')
        
        langues = []
        for row in reader:
            lang = row.get('langues', '').strip()
            if lang and lang not in langues:
                langues.append(lang)
        
        return langues
        
    except Exception as e:
        print(f"[ERREUR] Lecture de {chemin_commun}: {e}")
        return []


def compter_types(contenu: str) -> tuple:
    """
    Compte le nombre de tags et d'adjectifs dans le contenu.
    
    Returns:
        tuple: (nb_tags, nb_adjectifs)
    """
    nb_type_p = contenu.count(';p;')
    nb_type_a = contenu.count(';a;')
    return nb_type_p, nb_type_a


# ══════════════════════════════════════════════════════════════════════════════
# ÉTAPES
# ══════════════════════════════════════════════════════════════════════════════

def etape1_copie_francais(dossier_refs: Path, verbose=False):
    """
    Étape 1 : Copie tagsadjs.csv → frtagsadjs.csv
    
    Le français n'a pas besoin de traduction, on copie simplement le fichier.
    """
    print()
    print("═" * 70)
    print("ÉTAPE 1 : Copie du fichier français")
    print("═" * 70)
    
    source = dossier_refs / "tagsadjs.csv"
    destination = dossier_refs / "frtagsadjs.csv"
    
    if not source.exists():
        print(f"[ERREUR] Fichier source introuvable : {source}")
        return False
    
    try:
        shutil.copy2(source, destination)
        print(f"  ✓ Copié : {source.name} → {destination.name}")
        
        # Vérifier le contenu en mode verbose
        if verbose:
            contenu, encodage = lire_fichier_multi_encodage(destination)
            if contenu:
                nb_tags, nb_adjs = compter_types(contenu)
                print(f"    → Encodage détecté : {encodage}")
                print(f"    → {nb_tags} tags (type='p'), {nb_adjs} adjectifs (type='a')")
                if nb_adjs == 0:
                    print(f"    ⚠ ATTENTION : Aucun adjectif trouvé ! frsynadjs.csv sera vide.")
            else:
                print(f"    ⚠ Impossible de lire le fichier pour vérification")
        
        return True
    except Exception as e:
        print(f"[ERREUR] Copie échouée : {e}")
        return False


def etape2_traduction(dossier_refs: Path, langues: list, verbose=False):
    """
    Étape 2 : Traduit tagsadjs.csv vers toutes les langues (sauf fr).
    
    Utilise traduis.py pour créer xxtagsadjs.csv pour chaque langue.
    """
    print()
    print("═" * 70)
    print("ÉTAPE 2 : Traduction vers les autres langues")
    print("═" * 70)
    
    # Importer traduis
    try:
        from traduis import traduire_fichier_structure, charger_glossaire, sauvegarder_glossaire
    except ImportError:
        print("[ERREUR] Module traduis.py introuvable")
        return False
    
    source = dossier_refs / "tagsadjs.csv"
    
    if not source.exists():
        print(f"[ERREUR] Fichier source introuvable : {source}")
        return False
    
    print(f"  Source : {source.name}")
    
    # Charger le glossaire
    glossaire = charger_glossaire()
    print(f"  Glossaire : {len(glossaire)} entrées")
    
    # Traduire vers chaque langue (sauf français)
    langues_a_traduire = [l for l in langues if l != 'fr']
    print(f"  Langues à traduire : {', '.join(langues_a_traduire)}")
    
    fichiers_crees = []
    
    for langue in langues_a_traduire:
        print(f"\n  → Traduction vers {langue}...")
        
        try:
            fichiers = traduire_fichier_structure(
                str(source), glossaire, [langue],
                langue_unique=langue,
                mode_test=False  # IMPORTANT : pas de mode test
            )
            fichiers_crees.extend(fichiers)
        except Exception as e:
            print(f"    [ERREUR] {e}")
    
    # Sauvegarder le glossaire mis à jour
    sauvegarder_glossaire(glossaire, langues=langues)
    
    print(f"\n  ✓ {len(fichiers_crees)} fichiers créés")
    return True


def etape3_generation_synonymes(dossier_refs: Path, langues: list, verbose=False):
    """
    Étape 3 : Génère xxsyntags.csv et xxsynadjs.csv pour chaque langue.
    
    Utilise tags2syn.py pour traiter tous les fichiers xxtagsadjs.csv.
    """
    print()
    print("═" * 70)
    print("ÉTAPE 3 : Génération des fichiers de synonymes")
    print("═" * 70)
    
    # Importer tags2syn
    try:
        from tags2syn import generer_toutes_langues
    except ImportError:
        print("[ERREUR] Module tags2syn.py introuvable")
        return False
    
    try:
        resultats = generer_toutes_langues(dossier_refs, verbose=verbose)
        
        print()
        print("-" * 70)
        print("Résumé de la génération :")
        for langue, data in resultats.items():
            if data.get('erreur'):
                print(f"  ✗ {langue}: ERREUR")
            else:
                print(f"  ✓ {langue}: {data['tags']} tags, {data['adjs']} adjs")
        
        return True
        
    except Exception as e:
        print(f"[ERREUR] Génération échouée : {e}")
        import traceback
        traceback.print_exc()
        return False


# ══════════════════════════════════════════════════════════════════════════════
# POINT D'ENTRÉE
# ══════════════════════════════════════════════════════════════════════════════

def main():
    """Point d'entrée principal."""
    print(f"╔════════════════════════════════════════════════════════════════")
    print(f"║ {__pgm__} V{__version__} - {__date__}")
    print(f"║ Régénération complète des fichiers de synonymes multilingues")
    print(f"╚════════════════════════════════════════════════════════════════")
    print()
    print(f"Démarrage : {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
    
    t0 = time.time()
    
    # Analyse des arguments
    args = sys.argv[1:]
    
    verbose = '--verbose' in args
    args = [a for a in args if a != '--verbose']
    
    skip_trad = '--skip-trad' in args
    args = [a for a in args if a != '--skip-trad']
    
    langue_unique = None
    if '--only' in args:
        idx = args.index('--only')
        if idx + 1 < len(args):
            langue_unique = args[idx + 1]
    
    # Trouver le dossier refs
    chemins_possibles = [
        Path("refs"),
        Path(__file__).parent / "refs",
        Path("c:/g/refs"),
    ]
    
    dossier_refs = None
    for chemin in chemins_possibles:
        if chemin.exists():
            dossier_refs = chemin
            break
    
    if dossier_refs is None:
        print("[ERREUR] Dossier refs introuvable")
        return 1
    
    print(f"Dossier refs : {dossier_refs.resolve()}")
    
    # Charger les langues
    langues = charger_langues(dossier_refs / "commun.csv")
    if not langues:
        print("[ERREUR] Aucune langue configurée")
        return 1
    
    print(f"Langues configurées : {', '.join(langues)}")
    
    # Mode langue unique
    if langue_unique:
        print(f"\n[MODE] Langue unique : {langue_unique}")
        langues = [langue_unique]
        skip_trad = (langue_unique == 'fr')  # Pas de traduction pour le français
    
    # Vérifier que tagsadjs.csv existe et contient des adjectifs
    source = dossier_refs / "tagsadjs.csv"
    if not source.exists():
        print(f"[ERREUR] Fichier source introuvable : {source}")
        return 1
    
    # Vérifier le contenu du fichier source
    contenu, encodage = lire_fichier_multi_encodage(source)
    if contenu:
        nb_tags, nb_adjs = compter_types(contenu)
        print(f"Fichier source : {source.name} (encodage: {encodage})")
        print(f"  → {nb_tags} tags (type='p'), {nb_adjs} adjectifs (type='a')")
        if nb_adjs == 0:
            print(f"  ⚠ ATTENTION : tagsadjs.csv ne contient aucun adjectif (type='a') !")
            print(f"    Les fichiers xxsynadjs.csv seront vides.")
    else:
        print(f"[ERREUR] Impossible de lire {source}")
        return 1
    
    # ══════════════════════════════════════════════════════════════════════
    # EXÉCUTION DES ÉTAPES
    # ══════════════════════════════════════════════════════════════════════
    
    succes = True
    
    # Étape 1 : Copie du français
    if 'fr' in langues:
        if not etape1_copie_francais(dossier_refs, verbose):
            succes = False
    
    # Étape 2 : Traduction
    if not skip_trad and succes:
        langues_autres = [l for l in langues if l != 'fr']
        if langues_autres:
            if not etape2_traduction(dossier_refs, langues, verbose):
                succes = False
    elif skip_trad:
        print()
        print("═" * 70)
        print("ÉTAPE 2 : Traduction IGNORÉE (--skip-trad)")
        print("═" * 70)
    
    # Étape 3 : Génération des synonymes
    if succes:
        if not etape3_generation_synonymes(dossier_refs, langues, verbose):
            succes = False
    
    # ══════════════════════════════════════════════════════════════════════
    # RÉSUMÉ FINAL
    # ══════════════════════════════════════════════════════════════════════
    
    elapsed = time.time() - t0
    
    print()
    print("═" * 70)
    print("RÉSUMÉ FINAL")
    print("═" * 70)
    
    if succes:
        print("  ✓ Toutes les étapes ont réussi")
    else:
        print("  ✗ Des erreurs se sont produites")
    
    print()
    print(f"Fin : {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
    print(f"Durée totale : {elapsed:.1f} secondes")
    print("═" * 70)
    
    return 0 if succes else 1


if __name__ == '__main__':
    sys.exit(main())
