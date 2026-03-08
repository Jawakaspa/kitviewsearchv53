# detiavsdetall.py V1.0.1 - 04/01/2026 18:35:54
__pgm__ = "detiavsdetall.py"
__version__ = "1.0.1"
__date__ = "04/01/2026 18:35:54"

"""
Générateur de questions de test comparatif IA vs Algorithme.

Ce programme génère des questions de test pour comparer les performances de :
- detiabrut (détection par IA, avec/sans référentiels)
- detall (détection algorithmique)

OBJECTIF : Identifier les forces et faiblesses de chaque approche.

TYPES DE MUTATIONS (favorisant l'IA) :
- Orthographe phonétique : "bruksisme" → bruxisme
- Accents manquants : "beance laterale" → béance latérale  
- Pluriels/accords erronés : "encombrement sévères"
- Synonymes non référencés : "dents qui se chevauchent" → crowding
- Reformulations naturelles : "mâchoire en avant" → prognathisme
- Abréviations courantes : "Cl II" → classe II

TYPES DE QUESTIONS (favorisant detall) :
- Termes exacts du référentiel
- Patterns d'âge/sexe stricts
- Angles avec valeurs numériques
- Combinaisons tag + adjectif standard

USAGE CLI :
    python detiavsdetall.py                    # Affiche l'aide
    python detiavsdetall.py brut               # 200 questions, IA mode brut
    python detiavsdetall.py tags               # Sans référentiel tags
    python detiavsdetall.py tags adjs          # Sans tags ni adjs
    python detiavsdetall.py brut sonnet        # Mode brut avec Sonnet
    python detiavsdetall.py brut --seed 42     # Seed fixe pour reproductibilité
    python detiavsdetall.py brut -n 50         # 50 questions seulement

FORMAT DE SORTIE CSV :
    question;canonquestion;optionsia;commun;nomia;tempsia;all;tempsall
"""

import os
import sys
import csv
import random
import argparse
import time
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Set, Tuple, Optional

# =============================================================================
# IMPORTS DES MODULES DE DÉTECTION
# =============================================================================

# Import de detiabrut
try:
    from detiabrut import (
        detecter_tout_brut,
        charger_references as charger_references_ia,
        get_options_from_args,
        OPTIONS_DISPONIBLES,
        RACCOURCI_BRUT,
        RACCOURCI_DETIA
    )
    from detia import get_modeles_ia, charger_langues_actives, DEFAULT_MODEL
    DETIABRUT_DISPONIBLE = True
except ImportError as e:
    print(f"[ERREUR] Impossible d'importer detiabrut: {e}")
    DETIABRUT_DISPONIBLE = False

# Import de detall
try:
    from detall import (
        detecter_tout as detecter_tout_all,
        charger_references as charger_references_all
    )
    DETALL_DISPONIBLE = True
except ImportError as e:
    print(f"[ERREUR] Impossible d'importer detall: {e}")
    DETALL_DISPONIBLE = False

# Import de standardise
try:
    from standardise import standardise
except ImportError:
    import unicodedata
    import re
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
# CONSTANTES
# =============================================================================

NB_QUESTIONS_DEFAUT = 200
NB_QUESTIONS_IA = 100  # Questions favorisant l'IA
NB_QUESTIONS_ALL = 100  # Questions favorisant detall

# Mutations phonétiques courantes (français)
MUTATIONS_PHONETIQUES = {
    'bruxisme': ['bruksisme', 'bruckisme', 'bruxissme', 'brucsisme'],
    'béance': ['beance', 'béense', 'beense', 'bayance'],
    'supraclusion': ['suracclusion', 'supraoclusion', 'sur-occlusion', 'supraclusion'],
    'prognathisme': ['prognatisme', 'prognathisme', 'prognatismes'],
    'rétrognathie': ['retrognatie', 'rétrognatie', 'retrognacie'],
    'agénésie': ['agenésie', 'agénésis', 'agenézie'],
    'diastème': ['diastéme', 'diasteme', 'diasthème'],
    'céramique': ['ceramique', 'céramike', 'seramique'],
    'occlusion': ['oclusion', 'occlusio', 'occluzion'],
    'orthodontique': ['ortodontique', 'orthodontik', 'ortondontique'],
    'céphalométrie': ['cephalometrie', 'céfalométrie', 'céphalometri'],
    'gingivite': ['gingivit', 'gingvite', 'jinjivite'],
    'parodontite': ['parodontit', 'parodentite', 'paradontite'],
    'malocclusion': ['maloclusion', 'maloccluzion', 'mal occlusion'],
}

# Reformulations naturelles (langage patient vs technique)
REFORMULATIONS = {
    'crowding': ['dents trop serrées', 'dents entassées', 'manque de place pour les dents'],
    'prognathisme mandibulaire': ['mâchoire du bas en avant', 'menton qui avance', 'menton proéminent'],
    'prognathisme maxillaire': ['mâchoire du haut en avant', 'dents du haut qui sortent'],
    'béance': ['dents qui ne se touchent pas', 'trou entre les dents quand je mords'],
    'bruxisme': ['grince des dents la nuit', 'serre les dents', 'mâchoire crispée'],
    'classe ii d\'angle': ['mâchoire en arrière', 'menton fuyant', 'dents du haut en avant'],
    'classe iii d\'angle': ['mâchoire en avant', 'prognate', 'dents du bas devant'],
    'supraclusion': ['dents du haut qui recouvrent trop', 'morsure trop profonde'],
    'respiration buccale': ['respire par la bouche', 'dort la bouche ouverte', 'bouche toujours ouverte'],
    'succion': ['suce son pouce', 'tète encore son pouce', 'pouce dans la bouche'],
    'gouttière': ['appareil invisible', 'aligneur transparent', 'invisalign'],
    'bagues': ['appareil dentaire', 'bagues métalliques', 'train de fer'],
    'diastème': ['dents du bonheur', 'écart entre les dents de devant', 'dents de la chance'],
    'agénésie': ['dent qui manque', 'il lui manque une dent', 'dent absente'],
    'onychophagie': ['se ronge les ongles', 'ronge ses ongles'],
    'atm': ['mâchoire qui craque', 'articulation qui claque', 'douleur à la mâchoire'],
}

# Abréviations courantes
ABBREVIATIONS = {
    'classe i d\'angle': ['cl1', 'cl i', 'cl.i', 'classe 1', 'cli'],
    'classe ii d\'angle': ['cl2', 'cl ii', 'cl.ii', 'classe 2', 'clii'],
    'classe iii d\'angle': ['cl3', 'cl iii', 'cl.iii', 'classe 3', 'cliii'],
    'division 1': ['div1', 'div 1', 'd1'],
    'division 2': ['div2', 'div 2', 'd2'],
    'panoramique': ['pano', 'opg', 'radio pano'],
    'céphalométrie': ['céphalo', 'télécrâne', 'radio profil'],
}

# Patterns d'âge alternatifs
AGES_ALTERNATIFS = {
    'enfant': ['gamin', 'môme', 'petit', 'gosse', 'pitchoun'],
    'adolescent': ['ado', 'jeune', 'teenager'],
    'adulte': ['grand', 'majeur'],
    'senior': ['personne âgée', 'vieux', 'papy', 'mamie'],
}

# Erreurs grammaticales courantes
ERREURS_ACCORD = [
    ('sévère', 'sévères'),  # singulier mal accordé
    ('antérieur', 'antérieurs'),
    ('postérieur', 'postérieurs'),
    ('bilatéral', 'bilatéraux'),
    ('modéré', 'modérés'),
]


# =============================================================================
# CHARGEMENT DES RÉFÉRENTIELS
# =============================================================================

def charger_tags_csv(chemin: Path) -> List[Dict]:
    """Charge tags.csv et retourne la liste des tags avec leurs infos."""
    tags = []
    if not chemin.exists():
        return tags
    
    for encodage in ["utf-8-sig", "utf-8", "windows-1252"]:
        try:
            with open(chemin, 'r', encoding=encodage, newline='') as f:
                lignes = [line for line in f if line.strip() and not line.strip().startswith('#')]
            
            import io
            reader = csv.DictReader(io.StringIO(''.join(lignes)), delimiter=';')
            for row in reader:
                tag = (row.get('t') or '').strip()
                if tag:
                    adjs_str = (row.get('as') or '').strip()
                    adjs = [a.strip() for a in adjs_str.split(',') if a.strip()] if adjs_str else []
                    tags.append({
                        'tag': tag,
                        'genre': row.get('gn', ''),
                        'adjectifs': adjs,
                        'patterns': (row.get('pts') or '').strip()
                    })
            return tags
        except (UnicodeDecodeError, UnicodeError):
            continue
    return tags


def charger_adjectifs_csv(chemin: Path) -> List[str]:
    """Charge adjectifs.csv et retourne la liste des adjectifs canoniques."""
    adjectifs = []
    if not chemin.exists():
        return adjectifs
    
    for encodage in ["utf-8-sig", "utf-8", "windows-1252"]:
        try:
            with open(chemin, 'r', encoding=encodage, newline='') as f:
                lignes = [line for line in f if line.strip() and not line.strip().startswith('#')]
            
            import io
            reader = csv.DictReader(io.StringIO(''.join(lignes)), delimiter=';')
            for row in reader:
                adj = (row.get('a') or '').strip()
                if adj:
                    adjectifs.append(adj)
            return adjectifs
        except (UnicodeDecodeError, UnicodeError):
            continue
    return adjectifs


# =============================================================================
# GÉNÉRATEURS DE QUESTIONS
# =============================================================================

def generer_question_ia(tags: List[Dict], adjectifs: List[str], rng: random.Random) -> Tuple[str, str]:
    """
    Génère une question favorisant l'IA (mutations, reformulations, etc.).
    
    Returns:
        Tuple (question_mutée, question_canonique)
    """
    # Choisir le type de mutation
    mutation_type = rng.choice(['phonetique', 'reformulation', 'abbreviation', 'accent', 'accord', 'mixte'])
    
    # Choisir un tag au hasard
    tag_info = rng.choice(tags)
    tag = tag_info['tag']
    tag_adjs = tag_info['adjectifs']
    
    question_canon = tag
    question_mutee = tag
    
    if mutation_type == 'phonetique':
        # Mutation phonétique
        if tag in MUTATIONS_PHONETIQUES:
            question_mutee = rng.choice(MUTATIONS_PHONETIQUES[tag])
        else:
            # Supprimer les accents
            question_mutee = standardise(tag)
    
    elif mutation_type == 'reformulation':
        # Reformulation naturelle
        if tag in REFORMULATIONS:
            question_mutee = rng.choice(REFORMULATIONS[tag])
        else:
            # Fallback: mutation phonétique
            question_mutee = standardise(tag)
    
    elif mutation_type == 'abbreviation':
        # Utiliser une abréviation
        if tag in ABBREVIATIONS:
            question_mutee = rng.choice(ABBREVIATIONS[tag])
        else:
            question_mutee = standardise(tag)
    
    elif mutation_type == 'accent':
        # Supprimer les accents
        question_mutee = standardise(tag)
    
    elif mutation_type == 'accord':
        # Erreur d'accord sur adjectif
        if tag_adjs:
            adj = rng.choice(tag_adjs)
            question_canon = f"{tag} {adj}"
            # Chercher une erreur d'accord
            for sing, plur in ERREURS_ACCORD:
                if adj == sing:
                    question_mutee = f"{standardise(tag)} {plur}"  # mauvais accord
                    break
            else:
                question_mutee = f"{standardise(tag)} {adj}"
        else:
            question_mutee = standardise(tag)
    
    elif mutation_type == 'mixte':
        # Combinaison de plusieurs mutations
        question_mutee = standardise(tag)
        if tag_adjs and rng.random() > 0.5:
            adj = rng.choice(tag_adjs)
            question_canon = f"{tag} {adj}"
            question_mutee = f"{question_mutee} {standardise(adj)}"
    
    # Ajouter parfois un critère d'âge avec reformulation
    if rng.random() > 0.7:
        age_expr_canon, age_expr_mutee = generer_age_mute(rng)
        question_canon = f"{question_canon} {age_expr_canon}"
        question_mutee = f"{question_mutee} {age_expr_mutee}"
    
    # Ajouter parfois "combien" avec variante
    if rng.random() > 0.8:
        count_mutee = rng.choice(['cb de', 'cb', 'combien de', 'quel nombre de', 'y a t il des'])
        question_canon = f"combien de {question_canon}"
        question_mutee = f"{count_mutee} {question_mutee}"
    
    return question_mutee, question_canon


def generer_age_mute(rng: random.Random) -> Tuple[str, str]:
    """Génère un critère d'âge avec mutation."""
    ages_canon = [
        ('moins de 30 ans', ['- de 30 ans', 'moins de 30ans', 'inf 30 ans', '<30 ans']),
        ('plus de 18 ans', ['+ de 18 ans', 'plus de 18ans', 'sup 18 ans', '>18 ans']),
        ('entre 12 et 18 ans', ['12-18 ans', '12/18 ans', 'de 12 a 18 ans']),
        ('enfant', ['gamin', 'môme', 'gosse', 'petit']),
        ('adolescent', ['ado', 'teenager', 'jeune']),
        ('femme', ['fille', 'dame', 'sexe feminin']),
        ('homme', ['garçon', 'monsieur', 'sexe masculin']),
    ]
    
    canon, mutations = rng.choice(ages_canon)
    mutee = rng.choice(mutations)
    return canon, mutee


def generer_question_all(tags: List[Dict], adjectifs: List[str], rng: random.Random) -> Tuple[str, str]:
    """
    Génère une question favorisant detall (termes exacts du référentiel).
    
    Returns:
        Tuple (question, question_canonique) - identiques pour detall
    """
    question_type = rng.choice(['tag_simple', 'tag_adj', 'tag_age', 'angle', 'combinaison'])
    
    tag_info = rng.choice(tags)
    tag = tag_info['tag']
    tag_adjs = tag_info['adjectifs']
    
    if question_type == 'tag_simple':
        # Tag seul, forme exacte
        question = tag
    
    elif question_type == 'tag_adj':
        # Tag + adjectif autorisé
        if tag_adjs:
            adj = rng.choice(tag_adjs)
            question = f"{tag} {adj}"
        else:
            question = tag
    
    elif question_type == 'tag_age':
        # Tag + critère d'âge standard
        ages_standards = [
            'femmes de moins de 30 ans',
            'hommes de plus de 40 ans',
            'enfants',
            'adolescents',
            'adultes'
        ]
        age = rng.choice(ages_standards)
        question = f"{tag} {age}"
    
    elif question_type == 'angle':
        # Angle céphalométrique avec valeur
        angles = [
            ('ANB > 5', 'classe ii squelettique'),
            ('ANB < 0', 'classe iii squelettique'),
            ('ANB entre 0 et 4', 'classe i squelettique'),
            ('SNA > 84', 'prognathisme maxillaire'),
            ('SNB < 78', 'rétrognathisme mandibulaire'),
        ]
        angle_expr, tag_attendu = rng.choice(angles)
        question = angle_expr
        tag = tag_attendu
    
    elif question_type == 'combinaison':
        # Combinaison classique
        if tag_adjs:
            adj = rng.choice(tag_adjs)
            question = f"combien de {tag} {adj}"
        else:
            question = f"combien de {tag}"
    
    return question, question


def generer_questions(tags: List[Dict], adjectifs: List[str], 
                      nb_questions: int, seed: Optional[int] = None) -> List[Tuple[str, str, str]]:
    """
    Génère la liste des questions de test.
    
    Returns:
        Liste de tuples (question, canonquestion, type)
        où type est 'ia' ou 'all'
    """
    rng = random.Random(seed)
    questions = []
    
    nb_ia = nb_questions // 2
    nb_all = nb_questions - nb_ia
    
    # Questions favorisant l'IA
    for _ in range(nb_ia):
        q, canon = generer_question_ia(tags, adjectifs, rng)
        questions.append((q, canon, 'ia'))
    
    # Questions favorisant detall
    for _ in range(nb_all):
        q, canon = generer_question_all(tags, adjectifs, rng)
        questions.append((q, canon, 'all'))
    
    # Mélanger
    rng.shuffle(questions)
    
    return questions


# =============================================================================
# EXTRACTION DES CRITÈRES
# =============================================================================

def extraire_criteres(resultat: dict) -> Set[str]:
    """Extrait les critères détectés sous forme de set pour comparaison."""
    criteres = set()
    
    for c in resultat.get('criteres', []):
        c_type = c.get('type', '')
        
        if c_type == 'tag':
            canon = c.get('canonique', c.get('label', '')).lower()
            if canon:
                criteres.add(f"tag:{canon}")
            # Ajouter les adjectifs
            for adj in c.get('adjectifs', []):
                if isinstance(adj, dict):
                    adj_val = adj.get('canonique', adj.get('valeur', '')).lower()
                else:
                    adj_val = str(adj).lower()
                if adj_val:
                    criteres.add(f"adj:{adj_val}")
        
        elif c_type == 'age':
            label = c.get('label', '').lower()
            criteres.add(f"age:{label}")
        
        elif c_type == 'sexe':
            label = c.get('label', '').lower()
            criteres.add(f"sexe:{label}")
        
        elif c_type == 'count':
            criteres.add("count:yes")
    
    # Ajouter listcount
    if resultat.get('listcount') == 'COUNT':
        criteres.add("listcount:COUNT")
    
    return criteres


def comparer_resultats(criteres_ia: Set[str], criteres_all: Set[str]) -> Tuple[str, str, str]:
    """
    Compare les critères des deux approches.
    
    Returns:
        Tuple (commun, specifique_ia, specifique_all)
    """
    commun = criteres_ia & criteres_all
    specifique_ia = criteres_ia - criteres_all
    specifique_all = criteres_all - criteres_ia
    
    return (
        ', '.join(sorted(commun)),
        ', '.join(sorted(specifique_ia)),
        ', '.join(sorted(specifique_all))
    )


# =============================================================================
# TRAITEMENT PRINCIPAL
# =============================================================================

def traiter_questions(questions: List[Tuple[str, str, str]], 
                      refs_ia: dict, refs_all: dict,
                      options_desactivees: Set[str],
                      model: str = DEFAULT_MODEL,
                      verbose: bool = False) -> List[dict]:
    """
    Traite toutes les questions avec les deux approches.
    
    Returns:
        Liste de dictionnaires avec les résultats
    """
    resultats = []
    total = len(questions)
    
    for i, (question, canon, qtype) in enumerate(questions, 1):
        print(f"  [{i}/{total}] {question[:50]}...", end=" ", flush=True)
        
        # Détection IA
        t0_ia = time.time()
        try:
            res_ia = detecter_tout_brut(
                question, refs_ia, 
                model=model,
                options_desactivees=options_desactivees,
                verbose=False, debug=False
            )
            temps_ia = (time.time() - t0_ia) * 1000
            criteres_ia = extraire_criteres(res_ia)
        except Exception as e:
            if verbose:
                print(f"\n    [ERREUR IA] {e}")
            temps_ia = 0
            criteres_ia = set()
        
        # Détection algorithmique
        t0_all = time.time()
        try:
            res_all = detecter_tout_all(question, refs_all, verbose=False, debug=False)
            temps_all = (time.time() - t0_all) * 1000
            criteres_all = extraire_criteres(res_all)
        except Exception as e:
            if verbose:
                print(f"\n    [ERREUR ALL] {e}")
            temps_all = 0
            criteres_all = set()
        
        # Comparer
        commun, spec_ia, spec_all = comparer_resultats(criteres_ia, criteres_all)
        
        resultats.append({
            'question': question,
            'canonquestion': canon,
            'optionsia': ','.join(sorted(options_desactivees)) if options_desactivees else 'detia',
            'commun': commun,
            'nomia': spec_ia,
            'tempsia': round(temps_ia, 1),
            'all': spec_all,
            'tempsall': round(temps_all, 1),
            'type': qtype
        })
        
        # Indicateur visuel
        if spec_ia and not spec_all:
            print("✓IA")
        elif spec_all and not spec_ia:
            print("✓ALL")
        elif commun and not spec_ia and not spec_all:
            print("=")
        else:
            print("~")
    
    return resultats


def ecrire_csv_resultats(resultats: List[dict], fichier_sortie: Path):
    """Écrit les résultats dans un fichier CSV."""
    with open(fichier_sortie, 'w', encoding='utf-8-sig', newline='') as f:
        writer = csv.writer(f, delimiter=';')
        
        # En-tête
        writer.writerow([f'# Généré par {__pgm__} V{__version__} - {datetime.now().strftime("%d/%m/%Y %H:%M:%S")}'])
        writer.writerow(['question', 'canonquestion', 'optionsia', 'commun', 'nomia', 'tempsia', 'all', 'tempsall'])
        
        for res in resultats:
            writer.writerow([
                res['question'],
                res['canonquestion'],
                res['optionsia'],
                res['commun'],
                res['nomia'],
                res['tempsia'],
                res['all'],
                res['tempsall']
            ])


def afficher_statistiques(resultats: List[dict]):
    """Affiche les statistiques des résultats."""
    print()
    print("═" * 70)
    print("STATISTIQUES")
    print("═" * 70)
    
    total = len(resultats)
    if total == 0:
        print("Aucun résultat")
        return
    
    # Compteurs
    ia_mieux = sum(1 for r in resultats if r['nomia'] and not r['all'])
    all_mieux = sum(1 for r in resultats if r['all'] and not r['nomia'])
    egalite = sum(1 for r in resultats if not r['nomia'] and not r['all'] and r['commun'])
    divergent = sum(1 for r in resultats if r['nomia'] and r['all'])
    vide = sum(1 for r in resultats if not r['commun'] and not r['nomia'] and not r['all'])
    
    # Par type de question
    ia_sur_qia = sum(1 for r in resultats if r['type'] == 'ia' and r['nomia'] and not r['all'])
    all_sur_qall = sum(1 for r in resultats if r['type'] == 'all' and r['all'] and not r['nomia'])
    
    # Temps moyens
    temps_ia_moyen = sum(r['tempsia'] for r in resultats) / total
    temps_all_moyen = sum(r['tempsall'] for r in resultats) / total
    
    print(f"Total questions : {total}")
    print()
    print(f"IA uniquement meilleur  : {ia_mieux:3d} ({100*ia_mieux/total:.1f}%)")
    print(f"ALL uniquement meilleur : {all_mieux:3d} ({100*all_mieux/total:.1f}%)")
    print(f"Résultats identiques    : {egalite:3d} ({100*egalite/total:.1f}%)")
    print(f"Résultats divergents    : {divergent:3d} ({100*divergent/total:.1f}%)")
    print(f"Aucune détection        : {vide:3d} ({100*vide/total:.1f}%)")
    print()
    print(f"IA meilleure sur questions 'IA' : {ia_sur_qia}/{total//2}")
    print(f"ALL meilleur sur questions 'ALL': {all_sur_qall}/{total//2}")
    print()
    print(f"Temps moyen IA  : {temps_ia_moyen:.0f} ms")
    print(f"Temps moyen ALL : {temps_all_moyen:.1f} ms")
    print(f"Ratio vitesse   : x{temps_ia_moyen/max(temps_all_moyen, 0.1):.0f}")


# =============================================================================
# AFFICHAGE AIDE
# =============================================================================

def afficher_aide():
    """Affiche l'aide avec les options disponibles."""
    print()
    print("USAGE :")
    print("─" * 60)
    print(f"  python {__pgm__} [options] [moteur]")
    print()
    print("OPTIONS DE DÉSACTIVATION (référentiels IA) :")
    print("─" * 60)
    for opt in sorted(OPTIONS_DISPONIBLES):
        descriptions = {
            'tags': "N'injecte pas la liste des tags dans le prompt IA",
            'adjs': "N'injecte pas la liste des adjectifs dans le prompt IA", 
            'ages': "N'injecte pas les patterns âge/sexe dans le prompt IA",
            'angles': "N'injecte pas les seuils ANB/SNA/SNB dans le prompt IA",
            'mapping': "Ne mappe pas détecté → canonique"
        }
        print(f"  {opt:10} : {descriptions.get(opt, '')}")
    
    print()
    print("RACCOURCIS :")
    print("─" * 60)
    print(f"  {'brut':10} : Désactive tout (mode IA sans aide)")
    print(f"  {'detia':10} : Active tout (comportement identique à detia.py)")
    
    print()
    print("OPTIONS CLI :")
    print("─" * 60)
    print(f"  {'-n N':10} : Nombre de questions (défaut: {NB_QUESTIONS_DEFAUT})")
    print(f"  {'--seed N':10} : Seed pour reproductibilité")
    print(f"  {'-v':10} : Mode verbose")
    
    print()
    print("EXEMPLES :")
    print("─" * 60)
    print(f"  python {__pgm__} brut              # 200 questions, IA mode brut")
    print(f"  python {__pgm__} tags              # Sans référentiel tags")
    print(f"  python {__pgm__} brut sonnet       # Mode brut avec Sonnet")
    print(f"  python {__pgm__} brut --seed 42    # Reproductible")
    print(f"  python {__pgm__} brut -n 50        # 50 questions")
    print()


# =============================================================================
# POINT D'ENTRÉE
# =============================================================================

def main():
    """Point d'entrée CLI."""
    print(f"╔════════════════════════════════════════════════════════════════")
    print(f"║ {__pgm__} V{__version__} - {__date__}")
    print(f"║ Comparaison IA (detiabrut) vs Algorithme (detall)")
    print(f"╚════════════════════════════════════════════════════════════════")
    
    # Vérifier les modules disponibles
    if not DETIABRUT_DISPONIBLE:
        print("[ERREUR] detiabrut.py non disponible")
        return 1
    if not DETALL_DISPONIBLE:
        print("[ERREUR] detall.py non disponible")
        return 1
    
    parser = argparse.ArgumentParser(
        description="Compare detiabrut et detall sur des questions générées",
        add_help=False
    )
    parser.add_argument('args', nargs='*', help='Options, moteur')
    parser.add_argument('-n', '--nb', type=int, default=NB_QUESTIONS_DEFAUT, help='Nombre de questions')
    parser.add_argument('--seed', type=int, default=None, help='Seed aléatoire')
    parser.add_argument('-v', '--verbose', action='store_true', help='Mode verbose')
    parser.add_argument('-h', '--help', action='store_true', help='Affiche l\'aide')
    
    args = parser.parse_args()
    
    # Aide
    if args.help or not args.args:
        afficher_aide()
        return 0
    
    # Parser les arguments
    moteur = DEFAULT_MODEL
    options_args = []
    
    modeles_ia = get_modeles_ia()
    
    for arg in args.args:
        arg_lower = arg.lower()
        if arg_lower in OPTIONS_DISPONIBLES or arg_lower in (RACCOURCI_BRUT, RACCOURCI_DETIA):
            options_args.append(arg_lower)
        elif arg_lower in modeles_ia:
            moteur = arg_lower
    
    # Calculer options désactivées
    options_desactivees = get_options_from_args(options_args)
    
    # Vérifier les clés API
    from detia import _get_model_config
    model_config = _get_model_config(moteur)
    via = model_config['via']
    if via == 'openai' and not os.environ.get('OPENAI_API_KEY'):
        print("[ERREUR] Variable OPENAI_API_KEY non définie")
        return 1
    if via == 'eden' and not os.environ.get('EDENAI_API_KEY'):
        print("[ERREUR] Variable EDENAI_API_KEY non définie")
        return 1
    
    # Afficher configuration
    print()
    print(f"Moteur IA : {moteur}")
    if options_desactivees == OPTIONS_DISPONIBLES:
        print(f"Mode IA   : BRUT (tout désactivé)")
    elif options_desactivees:
        print(f"Options désactivées : {', '.join(sorted(options_desactivees))}")
    else:
        print(f"Mode IA   : DETIA (tout activé)")
    print(f"Questions : {args.nb}")
    print(f"Seed      : {args.seed if args.seed else 'aléatoire'}")
    print()
    
    # Chemins des référentiels
    script_dir = Path(__file__).parent
    refs_dir = script_dir / "refs"
    if not refs_dir.exists():
        refs_dir = Path("c:/g/refs")
    
    # Charger les tags et adjectifs pour génération
    print("Chargement des référentiels pour génération...")
    tags = charger_tags_csv(refs_dir / "tags.csv")
    adjectifs = charger_adjectifs_csv(refs_dir / "adjectifs.csv")
    print(f"  ✓ {len(tags)} tags, {len(adjectifs)} adjectifs")
    
    if not tags:
        print("[ERREUR] Aucun tag chargé - vérifiez tags.csv")
        return 1
    
    # Charger les références pour détection
    print("Chargement des références pour détection IA...")
    refs_ia = charger_references_ia(verbose=True)
    
    print("Chargement des références pour détection ALL...")
    refs_all = charger_references_all(verbose=True)
    print()
    
    # Générer les questions
    print(f"Génération de {args.nb} questions...")
    questions = generer_questions(tags, adjectifs, args.nb, args.seed)
    print(f"  ✓ {len(questions)} questions générées")
    print()
    
    # Traiter
    print("Traitement des questions...")
    print("-" * 70)
    resultats = traiter_questions(
        questions, refs_ia, refs_all,
        options_desactivees, moteur, args.verbose
    )
    print("-" * 70)
    
    # Générer nom de fichier
    timestamp = datetime.now().strftime("%d%m%y%H%M%S")
    tests_dir = script_dir / "tests"
    if not tests_dir.exists():
        tests_dir = Path("c:/g/tests")
    tests_dir.mkdir(parents=True, exist_ok=True)
    
    fichier_sortie = tests_dir / f"vs{timestamp}.csv"
    
    # Écrire les résultats
    ecrire_csv_resultats(resultats, fichier_sortie)
    print(f"\n✓ Résultats écrits dans : {fichier_sortie.absolute()}")
    
    # Statistiques
    afficher_statistiques(resultats)
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
