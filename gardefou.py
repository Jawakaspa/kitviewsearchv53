# gardefou.py V1.0.0 - 19/12/2025 14:17:42
__pgm__ = "gardefou.py"
__version__ = "1.0.0"
__date__ = "19/12/2025 14:17:42"

"""
Module garde-fou pour vérifier l'intention "tous les patients".

PROBLÈME RÉSOLU :
Quand la détection (IA ou regex) échoue et retourne critères=[], le système
retournait TOUS les patients, ce qui n'est presque jamais l'intention de l'utilisateur.

CE MODULE VÉRIFIE :
1. L'utilisateur veut-il vraiment TOUS les patients ?
   - Mots explicites : "tous", "tout", "all", "alle", "everyone", etc.
   - Phrases : "tous les patients", "tout le monde", "la liste complète"

2. La question ressemble-t-elle à une recherche de pathologie ?
   - Mot qui ressemble à un tag connu (LIKE% dans syntags)
   - Terme médical non reconnu mais détectable
   - Si oui → ce n'était PAS l'intention "tous"

3. Logique finale :
   - Si intention_tous = True → OK, retourner tous
   - Si ressemble_pathologie = True → retourner 0 avec message
   - Sinon → situation ambiguë, retourner 0 avec suggestions

POSITION DANS LA CHAÎNE :
    trouve.py
      ├── detall.py / detia.py → critères
      ├── jsonsql.py → SQL
      ├── lancesql.py → exécution
      └── gardefou.py → VÉRIFICATION FINALE (si nb ≈ total base)

Usage :
    from gardefou import verifier_intention_tous
    
    # Après avoir obtenu les résultats
    if nb_patients >= seuil_alerte and len(criteres) == 0:
        verdict = verifier_intention_tous(question, syntags_data, verbose=True)
        if not verdict['intention_tous']:
            # Bloquer et retourner message d'erreur
            return {'nb': 0, 'erreur': verdict['message']}
"""

import re
import os
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple

# Import de standardise
try:
    from standardise import standardise
except ImportError:
    import unicodedata
    def standardise(texte):
        if texte is None or texte == "":
            return ""
        texte = texte.lower()
        texte = unicodedata.normalize('NFD', texte)
        texte = ''.join(char for char in texte if unicodedata.category(char) != 'Mn')
        for char in ".!-_?":
            texte = texte.replace(char, " ")
        texte = re.sub(r'\s+', ' ', texte)
        return texte.strip()


# =============================================================================
# MOTS INDIQUANT "TOUS LES PATIENTS"
# =============================================================================

# Ces mots/phrases indiquent explicitement l'intention "tous"
MOTS_INTENTION_TOUS = {
    # Français
    'tous', 'tout', 'toutes', 'tous les patients', 'tous les malades',
    'tout le monde', 'la liste complete', 'liste complete', 
    'l ensemble', 'ensemble des patients', 'totalite', 'integralite',
    'sans filtre', 'sans critere', 'aucun filtre',
    # Anglais
    'all', 'everyone', 'everybody', 'all patients', 'complete list',
    'no filter', 'without filter', 'entire list', 'whole database',
    # Allemand
    'alle', 'alle patienten', 'gesamte liste', 'ohne filter',
    # Espagnol
    'todos', 'todas', 'todos los pacientes', 'lista completa',
    # Italien
    'tutti', 'tutte', 'tutti i pazienti', 'lista completa',
    # Japonais (romanisé)
    'zenbu', 'subete', 'all',
}

# Phrases qui confirment l'intention "tous" (patterns regex)
PATTERNS_INTENTION_TOUS = [
    r'\btous\s+les\s+patients?\b',
    r'\btous\s+les\s+malades?\b',
    r'\btous\s+les\s+cas\b',
    r'\btout\s+le\s+monde\b',
    r'\bla\s+liste\s+complete\b',
    r'\bl\s*ensemble\s+des\s+patients?\b',
    r'\bsans\s+(aucun\s+)?filtre\b',
    r'\bsans\s+(aucun\s+)?critere\b',
    r'\ball\s+patients?\b',
    r'\beveryone\b',
    r'\bno\s+filter\b',
    r'\balle\s+patienten\b',
    r'\btodos\s+los\s+pacientes\b',
]


# =============================================================================
# DÉTECTION DE TERMES MÉDICAUX/PATHOLOGIQUES
# =============================================================================

# Suffixes/préfixes typiquement médicaux (détection heuristique)
SUFFIXES_MEDICAUX = [
    'isme', 'ite', 'ose', 'ie', 'pathie', 'plasie', 'ectomie',
    'gnathie', 'doncie', 'odontic', 'mandibu', 'maxill',
    'occlus', 'dental', 'dent', 'orthodont', 'cephalo',
]

# Mots-clés indiquant un contexte de recherche pathologique
MOTS_CONTEXTE_PATHO = [
    'avec', 'ayant', 'presentant', 'souffrant', 'atteint',
    'diagnostique', 'cas de', 'patient avec', 'patients avec',
    'who have', 'with', 'suffering', 'diagnosed',
    'mit', 'haben', 'con', 'avec une', 'avec un',
]


def _ressemble_terme_medical(mot: str) -> bool:
    """
    Vérifie si un mot ressemble à un terme médical.
    Heuristique basée sur les suffixes/préfixes courants.
    """
    mot_lower = mot.lower()
    
    for suffixe in SUFFIXES_MEDICAUX:
        if suffixe in mot_lower and len(mot_lower) >= 5:
            return True
    
    return False


def _chercher_correspondance_tags(
    question_std: str,
    syntags_data: List[Dict]
) -> List[Dict]:
    """
    Cherche si un mot de la question ressemble à un tag connu.
    Utilise une recherche LIKE% (préfixe).
    
    Args:
        question_std: Question standardisée
        syntags_data: Liste des tags [{stdtag, canontag}, ...]
        
    Returns:
        Liste des correspondances trouvées
    """
    mots_question = question_std.split()
    correspondances = []
    
    for mot in mots_question:
        if len(mot) < 3:  # Ignorer les mots trop courts
            continue
        
        for tag_info in syntags_data:
            stdtag = tag_info.get('stdtag', '')
            canontag = tag_info.get('canontag', '')
            
            # Correspondance exacte
            if mot == stdtag:
                correspondances.append({
                    'mot': mot,
                    'type': 'exact',
                    'stdtag': stdtag,
                    'canontag': canontag,
                    'score': 1.0
                })
                break
            
            # Correspondance préfixe (LIKE 'mot%')
            if stdtag.startswith(mot) and len(mot) >= 4:
                correspondances.append({
                    'mot': mot,
                    'type': 'prefixe',
                    'stdtag': stdtag,
                    'canontag': canontag,
                    'score': len(mot) / len(stdtag)
                })
            
            # Correspondance contenu (LIKE '%mot%')
            elif mot in stdtag and len(mot) >= 5:
                correspondances.append({
                    'mot': mot,
                    'type': 'contenu',
                    'stdtag': stdtag,
                    'canontag': canontag,
                    'score': len(mot) / len(stdtag) * 0.8
                })
    
    # Trier par score décroissant et dédupliquer
    correspondances.sort(key=lambda x: x['score'], reverse=True)
    
    # Garder les meilleures correspondances
    vus = set()
    uniques = []
    for c in correspondances:
        if c['mot'] not in vus:
            vus.add(c['mot'])
            uniques.append(c)
    
    return uniques[:5]  # Max 5 suggestions


def _detecter_contexte_pathologique(question_std: str) -> bool:
    """
    Détecte si la question a un contexte de recherche pathologique.
    """
    for mot_ctx in MOTS_CONTEXTE_PATHO:
        if mot_ctx in question_std:
            return True
    return False


# =============================================================================
# FONCTION PRINCIPALE
# =============================================================================

def verifier_intention_tous(
    question: str,
    syntags_data: List[Dict] = None,
    verbose: bool = False,
    debug: bool = False
) -> Dict[str, Any]:
    """
    Vérifie si l'intention de l'utilisateur est vraiment "tous les patients".
    
    LOGIQUE :
    1. Si mots explicites "tous" → intention_tous = True
    2. Si ressemble à une pathologie → intention_tous = False
    3. Sinon → situation ambiguë, retourner False par sécurité
    
    Args:
        question: Question originale
        syntags_data: Liste des tags pour recherche LIKE
        verbose: Mode verbose
        debug: Mode debug
        
    Returns:
        {
            'intention_tous': bool,
            'raison': str,
            'message': str (message utilisateur si blocage),
            'suggestions': [str] (tags suggérés si applicable),
            'analyse': {
                'mots_tous_trouves': [str],
                'correspondances_tags': [dict],
                'contexte_patho': bool,
                'termes_medicaux': [str]
            }
        }
    """
    question_std = standardise(question)
    question_lower = question.lower()
    
    analyse = {
        'mots_tous_trouves': [],
        'correspondances_tags': [],
        'contexte_patho': False,
        'termes_medicaux': []
    }
    
    if debug:
        print(f"[DEBUG] gardefou: Question: '{question}'")
        print(f"[DEBUG] gardefou: Standardisée: '{question_std}'")
    
    # ═══════════════════════════════════════════════════════════════
    # ÉTAPE 1 : Chercher les mots d'intention "tous"
    # ═══════════════════════════════════════════════════════════════
    
    # Vérifier les patterns regex
    for pattern in PATTERNS_INTENTION_TOUS:
        if re.search(pattern, question_std, re.IGNORECASE):
            analyse['mots_tous_trouves'].append(f"pattern:{pattern}")
    
    # Vérifier les mots/phrases explicites
    for mot_tous in MOTS_INTENTION_TOUS:
        mot_std = standardise(mot_tous)
        if mot_std in question_std or mot_tous.lower() in question_lower:
            analyse['mots_tous_trouves'].append(mot_tous)
    
    if debug and analyse['mots_tous_trouves']:
        print(f"[DEBUG] gardefou: Mots 'tous' trouvés: {analyse['mots_tous_trouves']}")
    
    # ═══════════════════════════════════════════════════════════════
    # ÉTAPE 2 : Chercher des correspondances avec les tags
    # ═══════════════════════════════════════════════════════════════
    
    if syntags_data:
        analyse['correspondances_tags'] = _chercher_correspondance_tags(
            question_std, syntags_data
        )
        
        if debug and analyse['correspondances_tags']:
            print(f"[DEBUG] gardefou: Correspondances tags: {analyse['correspondances_tags']}")
    
    # ═══════════════════════════════════════════════════════════════
    # ÉTAPE 3 : Détecter contexte pathologique
    # ═══════════════════════════════════════════════════════════════
    
    analyse['contexte_patho'] = _detecter_contexte_pathologique(question_std)
    
    # Chercher termes médicaux par heuristique
    mots = question_std.split()
    for mot in mots:
        if _ressemble_terme_medical(mot) and len(mot) >= 5:
            analyse['termes_medicaux'].append(mot)
    
    if debug:
        if analyse['contexte_patho']:
            print(f"[DEBUG] gardefou: Contexte pathologique détecté")
        if analyse['termes_medicaux']:
            print(f"[DEBUG] gardefou: Termes médicaux: {analyse['termes_medicaux']}")
    
    # ═══════════════════════════════════════════════════════════════
    # ÉTAPE 4 : DÉCISION FINALE
    # ═══════════════════════════════════════════════════════════════
    
    # CAS 1 : Mots explicites "tous" trouvés
    if analyse['mots_tous_trouves']:
        # Mais si aussi des correspondances tags → ambigu
        if analyse['correspondances_tags']:
            # Priorité à la recherche pathologique
            suggestions = [c['canontag'] for c in analyse['correspondances_tags'][:3]]
            return {
                'intention_tous': False,
                'raison': 'ambigu_tous_et_patho',
                'message': (
                    f"Question ambiguë : 'tous' détecté mais aussi des termes "
                    f"ressemblant à des pathologies. "
                    f"Vouliez-vous chercher : {', '.join(suggestions)} ?"
                ),
                'suggestions': suggestions,
                'analyse': analyse
            }
        
        # Intention "tous" confirmée
        return {
            'intention_tous': True,
            'raison': 'mots_explicites_tous',
            'message': '',
            'suggestions': [],
            'analyse': analyse
        }
    
    # CAS 2 : Correspondances avec des tags trouvées
    if analyse['correspondances_tags']:
        # L'utilisateur cherchait probablement une pathologie
        correspondance = analyse['correspondances_tags'][0]
        suggestions = [c['canontag'] for c in analyse['correspondances_tags'][:3]]
        
        if correspondance['type'] == 'exact':
            # Correspondance exacte mais pas détectée → bug de détection
            return {
                'intention_tous': False,
                'raison': 'tag_exact_non_detecte',
                'message': (
                    f"Le terme '{correspondance['mot']}' correspond au tag "
                    f"'{correspondance['canontag']}' mais n'a pas été détecté. "
                    f"Vérifiez l'orthographe ou reformulez."
                ),
                'suggestions': suggestions,
                'analyse': analyse
            }
        else:
            # Correspondance partielle → suggestion
            return {
                'intention_tous': False,
                'raison': 'tag_partiel_suggere',
                'message': (
                    f"Aucun critère exact détecté. "
                    f"Vouliez-vous dire : {', '.join(suggestions)} ?"
                ),
                'suggestions': suggestions,
                'analyse': analyse
            }
    
    # CAS 3 : Contexte pathologique ou termes médicaux
    if analyse['contexte_patho'] or analyse['termes_medicaux']:
        return {
            'intention_tous': False,
            'raison': 'contexte_patho_sans_tag',
            'message': (
                f"La question semble concerner une pathologie mais aucun terme "
                f"reconnu n'a été trouvé. Vérifiez l'orthographe ou utilisez "
                f"un terme plus courant."
            ),
            'suggestions': [],
            'analyse': analyse
        }
    
    # CAS 4 : Question trop courte ou vide
    if len(question_std.split()) <= 1:
        return {
            'intention_tous': False,
            'raison': 'question_trop_courte',
            'message': (
                f"Question trop courte ou ambiguë. "
                f"Précisez votre recherche (ex: 'patients avec béance')."
            ),
            'suggestions': [],
            'analyse': analyse
        }
    
    # CAS 5 : Rien de spécifique détecté → par sécurité, bloquer
    return {
        'intention_tous': False,
        'raison': 'aucun_critere_clair',
        'message': (
            f"Aucun critère de recherche détecté. "
            f"Pour afficher tous les patients, utilisez 'tous les patients'."
        ),
        'suggestions': [],
        'analyse': analyse
    }


def charger_syntags_pour_gardefou(syntags_path: str, verbose: bool = False) -> List[Dict]:
    """
    Charge syntags.csv pour utilisation par le garde-fou.
    Format simplifié : liste de {stdtag, canontag}
    """
    if not os.path.exists(syntags_path):
        if verbose:
            print(f"[AVERTISSEMENT] gardefou: syntags.csv non trouvé: {syntags_path}")
        return []
    
    tags = []
    encodages = ["utf-8-sig", "utf-8", "windows-1252"]
    
    for encodage in encodages:
        try:
            with open(syntags_path, 'r', encoding=encodage, newline='') as f:
                import csv
                import io
                
                lignes = [l for l in f if not l.strip().startswith('#')]
                reader = csv.DictReader(io.StringIO(''.join(lignes)), delimiter=';')
                
                for row in reader:
                    stdtag = (row.get('stdtag') or '').strip()
                    canontag = (row.get('canontag') or '').strip()
                    
                    if stdtag and canontag:
                        tags.append({
                            'stdtag': stdtag,
                            'canontag': canontag
                        })
            
            if verbose:
                print(f"  ✓ gardefou: {len(tags)} tags chargés depuis {syntags_path}")
            break
            
        except (UnicodeDecodeError, UnicodeError):
            continue
    
    return tags


# =============================================================================
# POINT D'ENTRÉE CLI (pour tests)
# =============================================================================

def main():
    """Point d'entrée CLI pour tester le garde-fou."""
    import argparse
    
    print(f"╔════════════════════════════════════════════════════════════════")
    print(f"║ {__pgm__} V{__version__} - {__date__}")
    print(f"║ Vérification intention 'tous les patients'")
    print(f"╚════════════════════════════════════════════════════════════════")
    print()
    
    parser = argparse.ArgumentParser(
        description="Teste si une question a l'intention 'tous les patients'"
    )
    parser.add_argument('question', help='Question à analyser')
    parser.add_argument('--verbose', '-v', action='store_true')
    parser.add_argument('--debug', '-d', action='store_true')
    
    args = parser.parse_args()
    
    # Charger les tags
    script_dir = Path(__file__).parent
    syntags_path = script_dir / "refs" / "syntags.csv"
    
    if not syntags_path.exists():
        syntags_path = Path("c:/g/refs/syntags.csv")
    
    syntags_data = charger_syntags_pour_gardefou(str(syntags_path), verbose=args.verbose)
    
    print(f"Question: \"{args.question}\"")
    print()
    
    # Analyser
    resultat = verifier_intention_tous(
        args.question,
        syntags_data,
        verbose=args.verbose,
        debug=args.debug
    )
    
    # Afficher résultat
    print("═" * 70)
    print("VERDICT")
    print("═" * 70)
    
    if resultat['intention_tous']:
        print("✅ Intention 'TOUS LES PATIENTS' confirmée")
    else:
        print("❌ Intention 'tous' NON confirmée")
    
    print(f"   Raison : {resultat['raison']}")
    
    if resultat['message']:
        print(f"   Message: {resultat['message']}")
    
    if resultat['suggestions']:
        print(f"   Suggestions: {', '.join(resultat['suggestions'])}")
    
    print()
    print("═" * 70)
    print("ANALYSE DÉTAILLÉE")
    print("═" * 70)
    
    import json
    print(json.dumps(resultat['analyse'], indent=2, ensure_ascii=False))
    
    return 0


if __name__ == '__main__':
    import sys
    sys.exit(main())
