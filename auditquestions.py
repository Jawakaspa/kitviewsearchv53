# auditquestions.py V1.0.1 - 25/12/2025 09:06:41
__pgm__ = "auditquestions.py"
__version__ = "1.0.1"
__date__ = "25/12/2025 09:06:41"

"""
Programme d'audit des questions générées pour le système KITVIEW.

Compare les résultats attendus (generequestion.py) avec les résultats obtenus
par les différentes méthodes de détection.

MOTEURS (configurés dans refs/ia.csv) :
    rapide          : Détection regex/synonymes (detall.py) - instantané
    sonnet          : Claude 3.7 Sonnet via Eden AI
    haiku           : Claude 3.5 Haiku via Eden AI  
    opus            : Claude 3 Opus via Eden AI
    gpt4o           : GPT-4o via OpenAI direct
    gpt4omini       : GPT-4o-mini via OpenAI direct
    gemini25flash   : Gemini 2.5 Flash via Eden AI

MODES :
    detection       : Compare uniquement les critères détectés (défaut)
    recherche       : Compare les résultats de recherche complets

USAGE :
    python auditquestions.py base100.db testspats100.csv
    python auditquestions.py base100.db testspats100.csv --moteur rapide
    python auditquestions.py base100.db testspats100.csv --moteur sonnet
    python auditquestions.py base100.db testspats100.csv --moteur rapide,sonnet
    python auditquestions.py base100.db testspats100.csv --mode recherche

SORTIE :
    tests/audit_patsN.csv
"""

import sys
import os
import csv
import sqlite3
import time
import json
import argparse
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any

# Configuration
SCRIPT_DIR = Path(__file__).parent
REFS_DIR = SCRIPT_DIR / "refs"
BASES_DIR = SCRIPT_DIR / "bases"
TESTS_DIR = SCRIPT_DIR / "tests"


# =============================================================================
# CHARGEMENT DE LA CONFIGURATION DES MOTEURS
# =============================================================================

def charger_moteurs_config() -> Dict[str, Dict]:
    """
    Charge la configuration des moteurs depuis refs/ia.csv.
    
    Returns:
        Dict {nom_court: {'via': str, 'actif': bool, 'complet': str, 'cout': float}}
    """
    ia_path = REFS_DIR / "ia.csv"
    
    if not ia_path.exists():
        print(f"[WARNING] Fichier ia.csv non trouvé : {ia_path}")
        # Retourner config minimale
        return {
            'rapide': {'via': '', 'actif': True, 'complet': '', 'cout': 0, 'notes': 'Mode regex'}
        }
    
    moteurs = {}
    encodages = ["utf-8-sig", "utf-8", "windows-1252"]
    
    for encodage in encodages:
        try:
            with open(ia_path, 'r', encoding=encodage, newline='') as f:
                reader = csv.DictReader(
                    (row for row in f if not row.strip().startswith('#')),
                    delimiter=';'
                )
                for row in reader:
                    nom = row.get('moteur', '').strip()
                    if not nom:
                        continue
                    
                    moteurs[nom] = {
                        'via': row.get('via', '').strip(),
                        'actif': row.get('actif', '').strip().upper() == 'O',
                        'complet': row.get('complet', '').strip(),
                        'cout': float(row.get('cout', 0) or 0),
                        'notes': row.get('notes', '').strip()
                    }
            break
        except (UnicodeDecodeError, UnicodeError):
            continue
    
    return moteurs


# =============================================================================
# IMPORTS DES MODULES DE DÉTECTION
# =============================================================================

# detall - Détection traditionnelle (moteur "rapide")
try:
    from detall import charger_references as charger_refs_trad, detecter_tout as detecter_trad
    DETALL_DISPONIBLE = True
except ImportError as e:
    DETALL_DISPONIBLE = False
    DETALL_ERREUR = str(e)

# detia - Détection IA (tous les autres moteurs)
try:
    from detia import charger_references as charger_refs_ia, detecter_tout as detecter_ia
    DETIA_DISPONIBLE = True
except ImportError as e:
    DETIA_DISPONIBLE = False
    DETIA_ERREUR = str(e)

# cherche - Recherche complète (mode recherche)
try:
    from cherche import chercher
    CHERCHE_DISPONIBLE = True
except ImportError as e:
    CHERCHE_DISPONIBLE = False
    CHERCHE_ERREUR = str(e)


# =============================================================================
# UTILITAIRES
# =============================================================================

def lire_csv(chemin: Path) -> List[Dict]:
    """Lit un fichier CSV et retourne une liste de dictionnaires."""
    if not chemin.exists():
        print(f"[ERREUR] Fichier non trouvé : {chemin}")
        return []
    
    encodages = ["utf-8-sig", "utf-8", "windows-1252"]
    
    for encodage in encodages:
        try:
            with open(chemin, 'r', encoding=encodage, newline='') as f:
                lignes = []
                entete = None
                
                reader = csv.reader(f, delimiter=';')
                for row in reader:
                    if not row or (row[0] or '').strip().startswith('#'):
                        continue
                    if entete is None:
                        entete = [c.strip().lower() for c in row]
                    else:
                        lignes.append(dict(zip(entete, row)))
                
                return lignes
        except (UnicodeDecodeError, UnicodeError):
            continue
    
    print(f"[ERREUR] Impossible de lire {chemin}")
    return []


def extraire_criteres_str(resultat: Dict) -> str:
    """Extrait les critères d'un résultat de détection sous forme de chaîne."""
    criteres = []
    
    for c in resultat.get('criteres', []):
        c_type = c.get('type', '')
        
        if c_type == 'tag':
            tag = c.get('canonique', c.get('label', ''))
            criteres.append(f"tag:{tag}")
            
            # Adjectifs
            for adj in c.get('adjectifs', []):
                if isinstance(adj, dict):
                    adj_val = adj.get('canonique', adj.get('valeur', ''))
                else:
                    adj_val = str(adj)
                if adj_val:
                    criteres.append(f"adj:{adj_val.strip('%')}")
                    
        elif c_type == 'age':
            criteres.append(f"age:{c.get('label', '')}")
            
        elif c_type == 'sexe':
            criteres.append(f"sexe:{c.get('label', '')}")
    
    return '; '.join(criteres)


def categoriser_ecart(nb_attendu: int, nb_obtenu: int, residu: str, erreur: str) -> str:
    """Catégorise la cause probable de l'écart."""
    if erreur:
        return f"ERREUR:{erreur[:30]}"
    
    if nb_obtenu == -1:
        return "NON_CALCULE"
    
    if nb_attendu == nb_obtenu:
        return "OK"
    
    if nb_obtenu == 0 and nb_attendu > 0:
        if residu and len(residu.strip()) > 5:
            return "DETECTION:residu"
        return "DETECTION:vide"
    
    if nb_obtenu > nb_attendu:
        return f"SUR:+{nb_obtenu - nb_attendu}"
    
    return f"SOUS:-{nb_attendu - nb_obtenu}"


# =============================================================================
# FONCTIONS DE DÉTECTION PAR MOTEUR
# =============================================================================

def detecter_avec_moteur(question: str, moteur: str, config: Dict,
                         references_trad: Dict, references_ia: Dict,
                         verbose: bool = False) -> Dict:
    """
    Effectue la détection avec le moteur spécifié.
    
    Args:
        question: Question à analyser
        moteur: Nom du moteur (rapide, sonnet, etc.)
        config: Configuration du moteur depuis ia.csv
        references_trad: Références chargées pour detall
        references_ia: Références chargées pour detia
        verbose: Mode verbose
    
    Returns:
        Dict avec criteres, residu, temps_ms, erreur
    """
    start = time.time()
    
    via = config.get('via', '')
    
    if not via:  # Moteur "rapide" → detall.py
        if not DETALL_DISPONIBLE:
            return {
                'criteres': [],
                'residu': question,
                'temps_ms': 0,
                'auteur': moteur,
                'erreur': f"detall non disponible: {DETALL_ERREUR}"
            }
        
        try:
            resultat = detecter_trad(question, references_trad, verbose=verbose)
            temps_ms = int((time.time() - start) * 1000)
            
            return {
                'criteres': resultat.get('criteres', []),
                'listcount': resultat.get('listcount', 'LIST'),
                'residu': resultat.get('residu', ''),
                'temps_ms': temps_ms,
                'auteur': resultat.get('auteur', 'cx'),
                'erreur': ''
            }
        except Exception as e:
            return {
                'criteres': [],
                'residu': question,
                'temps_ms': int((time.time() - start) * 1000),
                'auteur': moteur,
                'erreur': str(e)
            }
    
    else:  # Moteur IA → detia.py
        if not DETIA_DISPONIBLE:
            return {
                'criteres': [],
                'residu': question,
                'temps_ms': 0,
                'auteur': moteur,
                'erreur': f"detia non disponible: {DETIA_ERREUR}"
            }
        
        # Vérifier la clé API
        if via == 'eden' and not os.environ.get('EDENAI_API_KEY'):
            return {
                'criteres': [],
                'residu': question,
                'temps_ms': 0,
                'auteur': moteur,
                'erreur': 'EDENAI_API_KEY non définie'
            }
        
        if via == 'openai' and not os.environ.get('OPENAI_API_KEY'):
            return {
                'criteres': [],
                'residu': question,
                'temps_ms': 0,
                'auteur': moteur,
                'erreur': 'OPENAI_API_KEY non définie'
            }
        
        try:
            # Passer le modèle complet à detia
            model = config.get('complet', '')
            resultat = detecter_ia(question, references_ia, model=model, verbose=verbose)
            temps_ms = int((time.time() - start) * 1000)
            
            return {
                'criteres': resultat.get('criteres', []),
                'listcount': resultat.get('listcount', 'LIST'),
                'residu': resultat.get('residu', ''),
                'temps_ms': resultat.get('ia_latency_ms', temps_ms),
                'auteur': resultat.get('auteur', moteur),
                'erreur': resultat.get('ia_erreur', '')
            }
        except Exception as e:
            return {
                'criteres': [],
                'residu': question,
                'temps_ms': int((time.time() - start) * 1000),
                'auteur': moteur,
                'erreur': str(e)
            }


# =============================================================================
# FONCTION PRINCIPALE D'AUDIT
# =============================================================================

def auditer_questions(base_path: str, questions_path: str, 
                      moteurs: List[str], moteurs_config: Dict,
                      mode: str = 'detection',
                      verbose: bool = False) -> List[Dict]:
    """
    Audite un fichier de questions avec les moteurs spécifiés.
    
    Args:
        base_path: Chemin vers la base de données
        questions_path: Chemin vers le fichier testspatsN.csv
        moteurs: Liste des moteurs à utiliser
        moteurs_config: Configuration des moteurs depuis ia.csv
        mode: 'detection' ou 'recherche'
        verbose: Mode verbose
    
    Returns:
        Liste de dictionnaires avec les résultats d'audit
    """
    print(f"\n{'='*70}")
    print(f"AUDIT DES QUESTIONS")
    print(f"{'='*70}")
    print(f"Base      : {os.path.abspath(base_path)}")
    print(f"Questions : {os.path.abspath(questions_path)}")
    print(f"Mode      : {mode}")
    print(f"Moteurs   : {', '.join(moteurs)}")
    print()
    
    # Charger les questions
    questions = lire_csv(Path(questions_path))
    if not questions:
        print("[ERREUR] Aucune question chargée")
        return []
    
    print(f"{len(questions)} questions à auditer")
    
    # Charger les références pour chaque type de moteur
    references_trad = {}
    references_ia = {}
    
    need_trad = any(moteurs_config.get(m, {}).get('via', '') == '' for m in moteurs)
    need_ia = any(moteurs_config.get(m, {}).get('via', '') != '' for m in moteurs)
    
    if need_trad and DETALL_DISPONIBLE:
        print("Chargement références detall...")
        references_trad = charger_refs_trad(verbose=False)
    
    if need_ia and DETIA_DISPONIBLE:
        print("Chargement références detia...")
        references_ia = charger_refs_ia(verbose=False)
    
    print("-" * 70)
    
    resultats = []
    
    for i, q in enumerate(questions, 1):
        question = q.get('question', '')
        type_q = q.get('type', 'LIST')
        nb_criteres = int(q.get('nb_criteres', 0))
        nb_attendu = int(q.get('nb_resultats', 0))
        ids_attendu = q.get('ids_10', '')
        
        if verbose:
            print(f"\n[{i}/{len(questions)}] {question[:60]}...")
        else:
            print(f"  [{i:3d}/{len(questions)}] ", end='', flush=True)
        
        # Résultat de base
        audit = {
            'num': i,
            'question': question,
            'type': type_q,
            'nb_criteres_attendu': nb_criteres,
            'nb_resultats_attendu': nb_attendu,
        }
        
        # Tester chaque moteur
        for moteur in moteurs:
            config = moteurs_config.get(moteur, {})
            
            if not config.get('actif', False):
                audit[f'{moteur}_erreur'] = 'Moteur inactif'
                continue
            
            res = detecter_avec_moteur(
                question, moteur, config,
                references_trad, references_ia,
                verbose=verbose
            )
            
            # Stocker les résultats
            criteres_str = extraire_criteres_str({'criteres': res['criteres']})
            nb_criteres_obtenus = len([c for c in res['criteres'] if c.get('type') != 'count'])
            
            audit[f'{moteur}_criteres'] = criteres_str
            audit[f'{moteur}_nb_crit'] = nb_criteres_obtenus
            audit[f'{moteur}_listcount'] = res.get('listcount', '')
            audit[f'{moteur}_residu'] = res.get('residu', '')
            audit[f'{moteur}_temps_ms'] = res.get('temps_ms', 0)
            audit[f'{moteur}_auteur'] = res.get('auteur', '')
            audit[f'{moteur}_erreur'] = res.get('erreur', '')
            
            # Catégoriser l'écart sur le nombre de critères
            audit[f'{moteur}_categorie'] = categoriser_ecart(
                nb_criteres, nb_criteres_obtenus,
                res.get('residu', ''),
                res.get('erreur', '')
            )
            
            # Affichage console
            if not verbose:
                if audit[f'{moteur}_categorie'] == 'OK':
                    print("✓", end='', flush=True)
                elif 'ERREUR' in audit[f'{moteur}_categorie']:
                    print("⚠", end='', flush=True)
                else:
                    print("✗", end='', flush=True)
        
        if not verbose:
            print()
        
        resultats.append(audit)
    
    return resultats


def generer_rapport(resultats: List[Dict], output_path: str, moteurs: List[str]):
    """Génère le rapport d'audit en CSV."""
    if not resultats:
        print("[ERREUR] Aucun résultat à écrire")
        return
    
    # Construire les colonnes dans l'ordre
    colonnes_base = ['num', 'question', 'type', 'nb_criteres_attendu', 'nb_resultats_attendu']
    colonnes_moteurs = []
    
    for moteur in moteurs:
        colonnes_moteurs.extend([
            f'{moteur}_categorie',
            f'{moteur}_nb_crit',
            f'{moteur}_criteres',
            f'{moteur}_residu',
            f'{moteur}_temps_ms',
            f'{moteur}_erreur',
        ])
    
    colonnes = colonnes_base + colonnes_moteurs
    
    with open(output_path, 'w', encoding='utf-8-sig', newline='') as f:
        timestamp = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        f.write(f"# Audit généré par {__pgm__} V{__version__} - {timestamp}\n")
        f.write(f"# Moteurs testés : {', '.join(moteurs)}\n")
        
        writer = csv.DictWriter(f, fieldnames=colonnes, delimiter=';', extrasaction='ignore')
        writer.writeheader()
        writer.writerows(resultats)
    
    print(f"\n✓ Rapport d'audit : {os.path.abspath(output_path)}")


def afficher_statistiques(resultats: List[Dict], moteurs: List[str]):
    """Affiche les statistiques globales de l'audit."""
    print(f"\n{'='*70}")
    print("STATISTIQUES")
    print(f"{'='*70}")
    
    total = len(resultats)
    
    for moteur in moteurs:
        cat_col = f'{moteur}_categorie'
        temps_col = f'{moteur}_temps_ms'
        
        # Compter les catégories
        categories = {}
        temps_list = []
        
        for r in resultats:
            cat = r.get(cat_col, 'N/A')
            categories[cat] = categories.get(cat, 0) + 1
            
            t = r.get(temps_col, 0)
            if t and t > 0:
                temps_list.append(t)
        
        print(f"\nMoteur : {moteur.upper()}")
        print("-" * 40)
        
        for cat, count in sorted(categories.items()):
            pct = count / total * 100
            if cat == 'OK':
                print(f"  ✓ {cat:20s} : {count:3d} ({pct:5.1f}%)")
            elif 'ERREUR' in cat or 'SUR' in cat or 'SOUS' in cat or 'DETECTION' in cat:
                print(f"  ✗ {cat:20s} : {count:3d} ({pct:5.1f}%)")
            else:
                print(f"    {cat:20s} : {count:3d} ({pct:5.1f}%)")
        
        if temps_list:
            avg = sum(temps_list) // len(temps_list)
            print(f"  ⏱ Temps moyen       : {avg} ms")


# =============================================================================
# POINT D'ENTRÉE
# =============================================================================

def main():
    """Point d'entrée CLI."""
    print(f"{__pgm__} V{__version__} - {__date__}")
    print()
    
    # Charger la configuration des moteurs
    moteurs_config = charger_moteurs_config()
    moteurs_actifs = [m for m, c in moteurs_config.items() if c.get('actif', False)]
    
    parser = argparse.ArgumentParser(
        description="Audit des questions générées pour KITVIEW",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=f"""
Moteurs disponibles :
  {', '.join(moteurs_actifs)}

Exemples :
  python {__pgm__} base100.db testspats100.csv
  python {__pgm__} base100.db testspats100.csv --moteur rapide
  python {__pgm__} base100.db testspats100.csv --moteur rapide,sonnet
  python {__pgm__} base100.db testspats100.csv --moteur sonnet --verbose
"""
    )
    parser.add_argument('base', help='Nom de la base SQLite (cherchée dans bases/)')
    parser.add_argument('questions', help='Nom du fichier testspatsN.csv (cherché dans tests/)')
    parser.add_argument('--moteur', '-m', default='rapide',
                        help=f'Moteur(s) séparés par virgule (défaut: rapide)')
    parser.add_argument('--mode', choices=['detection', 'recherche'],
                        default='detection', help='Mode d\'audit (défaut: detection)')
    parser.add_argument('--verbose', '-v', action='store_true', help='Mode verbose')
    parser.add_argument('--output', '-o', help='Fichier de sortie (défaut: tests/audit_patsN.csv)')
    
    args = parser.parse_args()
    
    # Parser les moteurs demandés
    moteurs_demandes = [m.strip() for m in args.moteur.split(',')]
    
    # Vérifier que les moteurs existent
    for m in moteurs_demandes:
        if m not in moteurs_config:
            print(f"[ERREUR] Moteur inconnu : {m}")
            print(f"  Moteurs disponibles : {', '.join(moteurs_actifs)}")
            return 1
    
    # Résoudre les chemins
    base_path = Path(args.base)
    if not base_path.exists():
        base_path = BASES_DIR / args.base
    if not base_path.exists() and not args.base.endswith('.db'):
        base_path = BASES_DIR / (args.base + ".db")
    
    if not base_path.exists():
        print(f"[ERREUR] Base non trouvée : {args.base}")
        print(f"  Cherché dans : {BASES_DIR.resolve()}")
        return 1
    
    questions_path = Path(args.questions)
    if not questions_path.exists():
        questions_path = TESTS_DIR / args.questions
    
    if not questions_path.exists():
        print(f"[ERREUR] Fichier questions non trouvé : {args.questions}")
        print(f"  Cherché dans : {TESTS_DIR.resolve()}")
        return 1
    
    # Créer tests/ si nécessaire
    TESTS_DIR.mkdir(exist_ok=True)
    
    # Déterminer le fichier de sortie
    if args.output:
        output_path = Path(args.output)
    else:
        questions_name = Path(args.questions).stem
        if 'pats' in questions_name:
            n = questions_name.split('pats')[-1].split('_')[0]
            output_path = TESTS_DIR / f"audit_pats{n}.csv"
        else:
            output_path = TESTS_DIR / f"audit_{questions_name}.csv"
    
    # Afficher les modules disponibles
    print("Modules disponibles :")
    print(f"  detall  : {'✓' if DETALL_DISPONIBLE else '✗'}")
    print(f"  detia   : {'✓' if DETIA_DISPONIBLE else '✗'}")
    print(f"  cherche : {'✓' if CHERCHE_DISPONIBLE else '✗'}")
    print()
    
    # Auditer
    resultats = auditer_questions(
        base_path=str(base_path),
        questions_path=str(questions_path),
        moteurs=moteurs_demandes,
        moteurs_config=moteurs_config,
        mode=args.mode,
        verbose=args.verbose
    )
    
    if not resultats:
        return 1
    
    # Générer le rapport
    generer_rapport(resultats, str(output_path), moteurs_demandes)
    
    # Afficher les statistiques
    afficher_statistiques(resultats, moteurs_demandes)
    
    print(f"\n{'='*70}")
    print("[OK] Audit terminé")
    print(f"{'='*70}")
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
