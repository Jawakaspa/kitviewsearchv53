# auditcsvreader.py V1.0.1 - 26/12/2025 20:07:20
__pgm__ = "auditcsvreader.py"
__version__ = "1.0.1"
__date__ = "26/12/2025 20:07:20"

"""
Audit des lectures CSV dans les fichiers Python.

Ce programme analyse tous les fichiers .py d'un répertoire pour identifier
ceux qui utilisent csv.DictReader ou csv.reader sans filtrer les lignes
de commentaires commençant par #.

Usage:
    python auditcsvreader.py [répertoire] [--silent]
    
Arguments:
    répertoire  : Répertoire à analyser (défaut: répertoire courant)
    --silent    : Mode silencieux (affiche uniquement le résumé)
"""

import os
import sys
import re
from pathlib import Path
from datetime import datetime
from dataclasses import dataclass
from typing import Optional

# =============================================================================
# FICHIERS CSV CONNUS AVEC COMMENTAIRES EN PREMIÈRE LIGNE
# =============================================================================

FICHIERS_CSV_AVEC_COMMENTAIRES = {
    "refs/commun.csv",
    "refs/glossaire.csv",
    "refs/syntags.csv",
    "refs/synadjs.csv",
    "refs/tagsadjs.csv",
}

# Pattern pour détecter refs/*.csv dans le code
PATTERN_REFS_CSV = re.compile(r'refs/\w+\.csv|refs\\\w+\.csv')


@dataclass
class Probleme:
    """Représente un problème détecté dans un fichier."""
    fichier: str
    ligne_num: int
    ligne_code: str
    fonction: str
    csv_lu: Optional[str]
    severite: str  # CRITIQUE, MOYEN, FAIBLE
    message: str


def trouver_fonction_englobante(lignes: list[str], ligne_num: int) -> str:
    """
    Trouve le nom de la fonction qui contient la ligne donnée.
    Remonte les lignes pour trouver 'def nom_fonction'.
    """
    pattern_def = re.compile(r'^\s*def\s+(\w+)\s*\(')
    
    for i in range(ligne_num - 1, -1, -1):
        match = pattern_def.match(lignes[i])
        if match:
            return match.group(1) + "()"
    
    return "<niveau module>"


def extraire_fichier_csv_lu(ligne: str, lignes: list[str], ligne_num: int) -> Optional[str]:
    """
    Tente d'extraire le nom du fichier CSV qui sera lu.
    Analyse la ligne courante et les lignes précédentes.
    """
    # Cherche un pattern refs/*.csv dans les 10 lignes précédentes
    zone = '\n'.join(lignes[max(0, ligne_num - 10):ligne_num + 1])
    
    matches = PATTERN_REFS_CSV.findall(zone)
    if matches:
        return matches[-1]  # Retourne le plus récent
    
    # Cherche d'autres patterns de fichiers CSV
    patterns_csv = [
        r'["\']([^"\']*\.csv)["\']',
        r'fichier\s*=\s*["\']([^"\']+\.csv)["\']',
        r'path\s*=\s*["\']([^"\']+\.csv)["\']',
    ]
    
    for pattern in patterns_csv:
        matches = re.findall(pattern, zone, re.IGNORECASE)
        if matches:
            return matches[-1]
    
    return None


def detecter_filtrage_commentaires(lignes: list[str], ligne_num: int) -> bool:
    """
    Vérifie si les lignes précédentes contiennent un filtrage des commentaires.
    Cherche des patterns comme:
    - startswith('#')
    - .startswith('#')
    - ligne.strip().startswith('#')
    - not ligne.startswith('#')
    - if ligne[0] == '#'
    - StringIO après filtrage
    """
    # Zone à analyser : 20 lignes avant et 5 après
    debut = max(0, ligne_num - 20)
    fin = min(len(lignes), ligne_num + 5)
    zone = '\n'.join(lignes[debut:fin])
    
    patterns_filtrage = [
        r"startswith\s*\(\s*['\"]#",
        r"\.strip\s*\(\s*\)\s*\.\s*startswith\s*\(\s*['\"]#",
        r"not\s+.*startswith\s*\(\s*['\"]#",
        r"if\s+.*\[\s*0\s*\]\s*[!=]=\s*['\"]#",
        r"skip.*comment",
        r"ignore.*comment",
        r"filtr.*comment",
        r"StringIO",
        r"io\.StringIO",
        r"comment_char\s*=",
    ]
    
    for pattern in patterns_filtrage:
        if re.search(pattern, zone, re.IGNORECASE):
            return True
    
    return False


def determiner_severite(csv_lu: Optional[str]) -> str:
    """
    Détermine la sévérité du problème.
    
    Tous les fichiers CSV peuvent contenir des commentaires (#).
    Un code qui ne filtre pas les commentaires est donc TOUJOURS critique,
    car il peut casser le jour où quelqu'un ajoute un commentaire.
    """
    # Tous les usages de csv.reader/DictReader sans filtrage sont critiques
    return "CRITIQUE"


def analyser_fichier(chemin_fichier: Path, silent: bool = False) -> list[Probleme]:
    """
    Analyse un fichier Python pour détecter les utilisations de csv.reader/DictReader
    sans filtrage des commentaires.
    """
    problemes = []
    
    try:
        with open(chemin_fichier, 'r', encoding='utf-8') as f:
            contenu = f.read()
            lignes = contenu.split('\n')
    except UnicodeDecodeError:
        try:
            with open(chemin_fichier, 'r', encoding='utf-8-sig') as f:
                contenu = f.read()
                lignes = contenu.split('\n')
        except Exception as e:
            if not silent:
                print(f"  [WARN] Impossible de lire {chemin_fichier}: {e}")
            return problemes
    except Exception as e:
        if not silent:
            print(f"  [WARN] Erreur lecture {chemin_fichier}: {e}")
        return problemes
    
    # Pattern pour détecter csv.DictReader ou csv.reader
    pattern_csv_reader = re.compile(r'csv\.(DictReader|reader)\s*\(')
    
    for i, ligne in enumerate(lignes):
        ligne_strip = ligne.strip()
        
        # Ignorer les commentaires Python
        if ligne_strip.startswith('#'):
            continue
        
        match = pattern_csv_reader.search(ligne)
        if match:
            type_reader = match.group(1)
            
            # Vérifier si un filtrage des commentaires existe
            if detecter_filtrage_commentaires(lignes, i):
                continue  # OK, filtrage détecté
            
            # Problème potentiel détecté
            fonction = trouver_fonction_englobante(lignes, i)
            csv_lu = extraire_fichier_csv_lu(ligne, lignes, i)
            severite = determiner_severite(csv_lu)
            
            probleme = Probleme(
                fichier=str(chemin_fichier.absolute()),
                ligne_num=i + 1,
                ligne_code=ligne_strip[:100] + ('...' if len(ligne_strip) > 100 else ''),
                fonction=fonction,
                csv_lu=csv_lu,
                severite=severite,
                message=f"csv.{type_reader} utilisé sans filtrage des commentaires"
            )
            problemes.append(probleme)
    
    return problemes


def afficher_rapport(problemes: list[Probleme], repertoire: str, silent: bool = False) -> None:
    """
    Affiche le rapport d'audit formaté.
    """
    date_audit = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    
    print("\n" + "=" * 70)
    print(f"=== AUDIT CSV READER - {date_audit} ===")
    print("=" * 70)
    print(f"\nRépertoire analysé: {Path(repertoire).absolute()}")
    
    if not problemes:
        print("\n✅ Aucun problème détecté !")
        print("   Tous les fichiers filtrent correctement les commentaires CSV.")
        print("=" * 70)
        return
    
    # Grouper par fichier
    problemes_par_fichier: dict[str, list[Probleme]] = {}
    for p in problemes:
        if p.fichier not in problemes_par_fichier:
            problemes_par_fichier[p.fichier] = []
        problemes_par_fichier[p.fichier].append(p)
    
    # Compter par sévérité
    nb_critique = sum(1 for p in problemes if p.severite == "CRITIQUE")
    nb_moyen = sum(1 for p in problemes if p.severite == "MOYEN")
    nb_faible = sum(1 for p in problemes if p.severite == "FAIBLE")
    
    print(f"\n📊 RÉSUMÉ: {len(problemes)} problème(s) dans {len(problemes_par_fichier)} fichier(s)")
    print(f"   🔴 CRITIQUE: {nb_critique}")
    print(f"   🟠 MOYEN: {nb_moyen}")
    print(f"   🟢 FAIBLE: {nb_faible}")
    
    if not silent:
        print("\n" + "-" * 70)
        print("DÉTAILS PAR FICHIER")
        print("-" * 70)
        
        for fichier, probs in sorted(problemes_par_fichier.items()):
            print(f"\n📁 FICHIER: {fichier}")
            
            for p in probs:
                icone = {"CRITIQUE": "🔴", "MOYEN": "🟠", "FAIBLE": "🟢"}.get(p.severite, "⚪")
                
                print(f"\n  Ligne {p.ligne_num}: {p.message}")
                print(f"  Code: {p.ligne_code}")
                print(f"  Fonction: {p.fonction}")
                print(f"  CSV lu: {p.csv_lu or 'non identifié'}")
                print(f"  Risque: {icone} {p.severite}")
                
                if p.severite == "CRITIQUE":
                    print(f"  ⚠️  Action: Utiliser csv_utils.lire_csv() ou csv_utils.lire_csv_reader()")
                elif p.severite == "MOYEN":
                    print(f"  📝 Action: Utiliser csv_utils pour sécuriser la lecture")
                else:
                    print(f"  ℹ️  Action: Recommandé d'utiliser csv_utils")
    
    print("\n" + "=" * 70)
    print("=== FIN AUDIT ===")
    print("=" * 70)
    
    # Code de sortie non-zéro si problèmes critiques
    if nb_critique > 0:
        print(f"\n⚠️  {nb_critique} problème(s) CRITIQUE(s) nécessitent une correction immédiate!")


def main():
    """Point d'entrée principal."""
    print(f"{__pgm__} V{__version__} - {__date__}")
    
    # Parser les arguments
    args = sys.argv[1:]
    silent = "--silent" in args
    args = [a for a in args if a != "--silent"]
    
    repertoire = args[0] if args else "."
    
    if not os.path.isdir(repertoire):
        print(f"❌ Erreur: Le répertoire '{repertoire}' n'existe pas.")
        sys.exit(1)
    
    chemin_repertoire = Path(repertoire)
    
    print(f"\n🔍 Analyse des fichiers .py dans: {chemin_repertoire.absolute()}")
    
    # Trouver tous les fichiers .py
    fichiers_py = list(chemin_repertoire.glob("*.py"))
    
    if not fichiers_py:
        print("⚠️  Aucun fichier .py trouvé dans ce répertoire.")
        sys.exit(0)
    
    print(f"   {len(fichiers_py)} fichier(s) .py trouvé(s)")
    
    # Analyser chaque fichier
    tous_problemes: list[Probleme] = []
    
    for fichier in fichiers_py:
        if not silent:
            print(f"   Analyse de {fichier.name}...")
        
        problemes = analyser_fichier(fichier, silent)
        tous_problemes.extend(problemes)
    
    # Afficher le rapport
    afficher_rapport(tous_problemes, repertoire, silent)
    
    # Code de sortie
    nb_critique = sum(1 for p in tous_problemes if p.severite == "CRITIQUE")
    sys.exit(1 if nb_critique > 0 else 0)


if __name__ == "__main__":
    main()
