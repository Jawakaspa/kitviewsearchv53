# pipeline.py V1.0.10 - 02/01/2026 20:44:36
__pgm__ = "pipeline.py"
__version__ = "1.0.10"
__date__ = "02/01/2026 20:44:36"

"""
Pipeline unifié de génération des fichiers de référence KITVIEW.

COMMANDES :
  questions (ou quest)  Génère des questions de test depuis la base patients
  audit                 Compare les résultats detall vs detia
  status                Affiche l'état des fichiers générés
  help                  Affiche l'aide

NOTE : La commande 'synonymes' a été supprimée (V2.1)
       Les lookups sont générés en mémoire depuis tags.csv et adjectifs.csv

USAGE :
    python pipeline.py help
    python pipeline.py status
    python pipeline.py quest bases/base1000.db 100
    python pipeline.py audit 1000 verbose
"""

import os
import sys
import csv
import sqlite3
import random
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, List, Tuple
import io

# =============================================================================
# CONFIGURATION
# =============================================================================

CHEMINS_REFS = [Path("refs"), Path("c:/g/refs")]
CHEMINS_BASES = [Path("bases"), Path("c:/g/bases")]
CHEMINS_TESTS = [Path("tests"), Path("c:/g/tests")]

DISTRIBUTION_QUESTIONS = {
    'nb_total': 100,
    'pct_count': 30,
    'pct_angles': 10,   # 10% des questions avec angle
    'pct_ages': 20,     # 20% des questions avec critère d'âge
    'complexite': {1: 30, 2: 40, 3: 20, 4: 10}
}


def trouver_dossier(chemins: List[Path]) -> Optional[Path]:
    for chemin in chemins:
        if chemin.exists():
            return chemin.resolve()
    return None


def trouver_dossier_refs() -> Optional[Path]:
    return trouver_dossier(CHEMINS_REFS)


def trouver_dossier_tests() -> Optional[Path]:
    return trouver_dossier(CHEMINS_TESTS)


def lire_csv_utf8(chemin: Path) -> Tuple[List[str], List[Dict]]:
    """
    Lit un fichier CSV avec gestion des encodages et filtrage des commentaires.
    
    Gère aussi les cas de BOM mal encodé (\\xef\\xbb\\xbf littéral).
    """
    encodages = ["utf-8-sig", "utf-8", "windows-1252"]
    for enc in encodages:
        try:
            with open(chemin, 'r', encoding=enc, newline='') as f:
                lignes = []
                for l in f:
                    ligne = l.strip()
                    # Ignorer lignes vides
                    if not ligne:
                        continue
                    # Ignorer commentaires
                    if ligne.startswith('#'):
                        continue
                    # Ignorer BOM mal encodé littéralement
                    if ligne.startswith('\\xef\\xbb\\xbf') or ligne.startswith(r'\xef\xbb\xbf'):
                        continue
                    lignes.append(l)
                
                if not lignes:
                    return [], []
                reader = csv.DictReader(io.StringIO(''.join(lignes)), delimiter=';')
                return list(reader.fieldnames or []), list(reader)
        except (UnicodeDecodeError, UnicodeError):
            continue
    return [], []


# =============================================================================
# GÉNÉRATION DE QUESTIONS TEST
# =============================================================================

def charger_patients_avec_tags(db_path: Path, limite: int = 200) -> List[Dict]:
    """Charge des patients avec leurs tags depuis la base (méthode cheat)."""
    if not db_path.exists():
        return []
    
    patients = []
    try:
        conn = sqlite3.connect(str(db_path))
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, sexe, age, canontags, canonadjs
            FROM patients
            WHERE canontags IS NOT NULL AND canontags != ''
            ORDER BY RANDOM()
            LIMIT ?
        """, (limite,))
        
        for row in cursor.fetchall():
            # Nettoyer les tags et adjs (enlever les | qui sont des patterns)
            canontags = row['canontags'] or ''
            canonadjs = row['canonadjs'] or ''
            
            # Nettoyer : enlever tout ce qui contient | (ce sont des patterns, pas des valeurs)
            tags_clean = ','.join(
                t.strip() for t in canontags.split(',') 
                if t.strip() and '|' not in t
            )
            adjs_clean = ','.join(
                a.strip() for a in canonadjs.split(',') 
                if a.strip() and '|' not in a
            )
            
            if tags_clean:  # Garder seulement si au moins un tag valide
                patients.append({
                    'id': row['id'],
                    'sexe': row['sexe'],
                    'age': row['age'],
                    'canontags': tags_clean,
                    'canonadjs': adjs_clean
                })
        
        conn.close()
    except Exception as e:
        print(f"[ERREUR] Chargement patients: {e}")
    
    return patients


def charger_angles(dossier_refs: Path) -> List[Dict]:
    """
    Charge les patterns d'angles depuis angles.csv.
    
    Retourne une liste utilisable pour générer des questions avec angles.
    Chaque angle a :
    - type_angle : ANB, SNA, SNB
    - operateur_texte : expressions pour générer la question
    - tag_canonique : le tag résultant
    - seuil : valeur de référence
    """
    chemin = dossier_refs / "angles.csv"
    if not chemin.exists():
        return []
    
    angles = []
    _, rows = lire_csv_utf8(chemin)
    
    for row in rows:
        expr = (row.get('expression') or '').strip()
        operateur = (row.get('operateur') or '').strip().upper()
        seuil_str = (row.get('seuil') or '').strip()
        tag = (row.get('tag_canonique') or '').strip()
        label = (row.get('label') or '').strip()
        
        if not expr or not tag:
            continue
        
        # Identifier le type d'angle (ANB, SNA, SNB)
        type_angle = None
        expr_lower = expr.lower()
        if 'anb' in expr_lower:
            type_angle = 'ANB'
        elif 'sna' in expr_lower:
            type_angle = 'SNA'
        elif 'snb' in expr_lower:
            type_angle = 'SNB'
        
        if not type_angle:
            continue
        
        # Parser le seuil
        seuil = None
        if seuil_str:
            if ',' in seuil_str and '{' not in seuil_str:
                # Plage comme "0,4" → (0, 4)
                parts = seuil_str.split(',')
                if len(parts) == 2:
                    try:
                        seuil = (float(parts[0]), float(parts[1]))
                    except ValueError:
                        pass
            elif '{' not in seuil_str:
                try:
                    seuil = float(seuil_str)
                except ValueError:
                    pass
        
        if seuil is None:
            continue
        
        angles.append({
            'type_angle': type_angle,
            'operateur': operateur,
            'seuil': seuil,
            'tag_canonique': tag,
            'label': label
        })
    
    return angles


def generer_expression_angle(angle: Dict) -> Tuple[str, int]:
    """
    Génère une expression naturelle pour un angle avec une valeur cohérente.
    
    Returns:
        Tuple (expression textuelle, valeur utilisée)
    """
    type_angle = angle['type_angle']
    operateur = angle['operateur']
    seuil = angle['seuil']
    
    # Générer une valeur cohérente avec la condition
    if operateur == '>':
        # Valeur supérieure au seuil
        valeur = int(seuil) + random.randint(1, 4)
    elif operateur == '<':
        # Valeur inférieure au seuil
        valeur = int(seuil) - random.randint(1, 4)
    elif operateur == 'BETWEEN':
        # Valeur dans la plage
        if isinstance(seuil, tuple):
            valeur = random.randint(int(seuil[0]), int(seuil[1]))
        else:
            valeur = int(seuil)
    else:
        valeur = int(seuil) if not isinstance(seuil, tuple) else int(seuil[0])
    
    # Générer l'expression textuelle
    templates = {
        '>': [
            f"{type_angle} > {valeur}",
            f"{type_angle} supérieur à {valeur}",
            f"{type_angle} plus de {valeur}",
        ],
        '<': [
            f"{type_angle} < {valeur}",
            f"{type_angle} inférieur à {valeur}",
            f"{type_angle} moins de {valeur}",
        ],
        'BETWEEN': [
            f"{type_angle} = {valeur}",
            f"{type_angle} de {valeur}",
        ]
    }
    
    expressions = templates.get(operateur, [f"{type_angle} = {valeur}"])
    return random.choice(expressions), valeur


def generer_question_depuis_patient(patient: Dict, angles: List[Dict], nb_criteres: int, 
                                     is_count: bool, inclure_angle: bool = False,
                                     inclure_age: bool = False) -> Dict:
    """
    Génère une question à partir d'un patient réel.
    
    Args:
        patient: Données du patient
        angles: Liste des patterns d'angles disponibles
        nb_criteres: Nombre de critères à inclure
        is_count: True pour COUNT, False pour LIST
        inclure_angle: Si True, un des critères sera un angle
        inclure_age: Si True, un des critères sera l'âge
    """
    parts = []
    criteres = []
    a_angle = False
    a_age = False
    a_sexe = False
    
    if is_count:
        parts.append(random.choice(["Combien de patients", "Nombre de patients"]))
        criteres.append({'type': 'count'})
    
    tags_patient = [t.strip() for t in patient['canontags'].split(',') if t.strip()]
    adjs_patient = [a.strip() for a in patient['canonadjs'].split(',') if a.strip()]
    
    criteres_possibles = []
    
    # Angle (si demandé et disponible)
    angle_utilise = None
    if inclure_angle and angles:
        angle = random.choice(angles)
        expression, valeur = generer_expression_angle(angle)
        criteres_possibles.append({
            'type': 'angle',
            'expression': expression,
            'tag_canonique': angle['tag_canonique'],
            'valeur': valeur,
            'priorite': 1  # Haute priorité
        })
        angle_utilise = angle
    
    # Âge (si demandé ou par hasard)
    if patient['age'] and patient['age'] > 0:
        age = int(patient['age'])
        ops = [
            (f"de moins de {age + 5} ans", '<', age + 5),
            (f"de plus de {max(1, age - 5)} ans", '>=', max(1, age - 5)),
            ("adultes", '>=', 18) if age >= 18 else ("enfants", '<', 12)
        ]
        priorite = 2 if inclure_age else 5  # Haute priorité si demandé
        criteres_possibles.append({'type': 'age', 'val': random.choice(ops), 'priorite': priorite})
    
    # Tags (exclure les tags qui correspondent à l'angle si angle utilisé)
    tags_exclus = set()
    if angle_utilise:
        tags_exclus.add(angle_utilise['tag_canonique'].lower())
    
    for tag in tags_patient[:3]:
        if tag.lower() not in tags_exclus:
            criteres_possibles.append({'type': 'tag', 'val': tag, 'priorite': 3})
    
    # Sexe
    if patient['sexe'] in ('M', 'F'):
        label = "femmes" if patient['sexe'] == 'F' else "hommes"
        criteres_possibles.append({'type': 'sexe', 'val': (label, patient['sexe']), 'priorite': 4})
    
    # Trier par priorité puis mélanger au sein de chaque priorité
    criteres_possibles.sort(key=lambda x: (x.get('priorite', 10), random.random()))
    
    selectionnes = criteres_possibles[:nb_criteres]
    
    for c in selectionnes:
        if c['type'] == 'angle':
            parts.append(f"avec {c['expression']}")
            criteres.append({
                'type': 'angle',
                'expression': c['expression'],
                'tag_canonique': c['tag_canonique']
            })
            a_angle = True
        elif c['type'] == 'tag':
            tag = c['val']
            adj = None
            if adjs_patient and random.random() < 0.3:
                adj = random.choice(adjs_patient)
                parts.append(f"avec {tag} {adj}")
            else:
                parts.append(f"avec {tag}")
            criteres.append({'type': 'tag', 'canonique': tag, 'adjectif': adj})
        elif c['type'] == 'age':
            txt, op, val = c['val']
            parts.append(txt)
            criteres.append({'type': 'age', 'operateur': op, 'valeur': int(val)})
            a_age = True
        elif c['type'] == 'sexe':
            label, code = c['val']
            parts.append(label)
            criteres.append({'type': 'sexe', 'valeur': code})
            a_sexe = True
    
    question = ' '.join(parts) + ' ?'
    listcount = 'COUNT' if is_count else 'LIST'
    
    # Extraire tags attendus (incluant ceux des angles)
    tags_attendus = []
    criteres_sql = []
    
    for c in criteres:
        if c['type'] == 'tag':
            tags_attendus.append(c['canonique'])
            criteres_sql.append({'colonne': 'canontags', 'operateur': '=', 'valeur': c['canonique']})
            if c.get('adjectif'):
                criteres_sql.append({'colonne': 'canonadjs', 'operateur': '=', 'valeur': c['adjectif']})
        elif c['type'] == 'angle':
            tags_attendus.append(c['tag_canonique'])
            criteres_sql.append({'colonne': 'canontags', 'operateur': '=', 'valeur': c['tag_canonique']})
        elif c['type'] == 'age':
            criteres_sql.append({'colonne': 'age', 'operateur': c['operateur'], 'valeur': c['valeur']})
        elif c['type'] == 'sexe':
            criteres_sql.append({'colonne': 'sexe', 'operateur': '=', 'valeur': c['valeur']})
    
    adjs_attendus = [c['adjectif'] for c in criteres if c['type'] == 'tag' and c.get('adjectif')]
    
    return {
        'fr': question,
        'listcount': listcount,
        'nb_criteres': len([c for c in criteres if c['type'] != 'count']),
        'tags': ', '.join(tags_attendus),
        'adjectifs': ', '.join(adjs_attendus),
        'criteres_sql': criteres_sql,
        'a_angle': a_angle,
        'a_age': a_age,
        'a_sexe': a_sexe
    }


def extraire_nb_patients_base(db_path: Path) -> str:
    """
    Extrait le nombre de patients du nom de la base.
    
    Exemples :
        base1000.db → "1000"
        pats500.db → "500"
        base25000.db → "25000"
    """
    import re
    nom = db_path.stem  # Sans extension
    # Chercher un nombre dans le nom
    match = re.search(r'(\d+)', nom)
    if match:
        return match.group(1)
    return "0"


def rechercher_patients_correspondants(db_path: Path, criteres_sql: List[Dict], limite: int = 10) -> Tuple[int, List[int]]:
    """
    Exécute une requête SQL basée sur les critères et retourne le nombre de résultats
    et les IDs des premiers patients correspondants.
    
    Args:
        db_path: Chemin vers la base SQLite
        criteres_sql: Liste de critères avec {colonne, operateur, valeur}
        limite: Nombre max d'IDs à retourner
        
    Returns:
        Tuple (nb_total, liste_ids)
    """
    if not criteres_sql:
        return 0, []
    
    try:
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        
        # Construire la clause WHERE
        conditions = []
        params = []
        
        for c in criteres_sql:
            col = c.get('colonne', '')
            op = c.get('operateur', '=')
            val = c.get('valeur', '')
            
            if not col or val == '' or val is None:
                continue
            
            if col == 'canontags':
                # Recherche dans une liste séparée par virgules
                conditions.append(f"(',' || COALESCE(canontags,'') || ',' LIKE ?)")
                params.append(f'%,{val},%')
            elif col == 'canonadjs':
                conditions.append(f"(',' || COALESCE(canonadjs,'') || ',' LIKE ?)")
                params.append(f'%,{val},%')
            elif col == 'age':
                if op == '<':
                    conditions.append("age < ?")
                elif op == '>=':
                    conditions.append("age >= ?")
                elif op == '<=':
                    conditions.append("age <= ?")
                elif op == '>':
                    conditions.append("age > ?")
                else:
                    conditions.append("age = ?")
                params.append(val)
            elif col == 'sexe':
                conditions.append("sexe = ?")
                params.append(val)
        
        if not conditions:
            conn.close()
            return 0, []
        
        where_clause = " AND ".join(conditions)
        
        # Compter le total
        sql_count = f"SELECT COUNT(*) FROM patients WHERE {where_clause}"
        cursor.execute(sql_count, params)
        nb_total = cursor.fetchone()[0]
        
        # Récupérer les IDs
        sql_ids = f"SELECT id FROM patients WHERE {where_clause} LIMIT ?"
        cursor.execute(sql_ids, params + [limite])
        ids = [row[0] for row in cursor.fetchall()]
        
        conn.close()
        return nb_total, ids
        
    except Exception as e:
        return 0, []


def etape_3_questions(dossier_refs: Path, dossier_tests: Path, db_path: Path, 
                      nb_questions: int = 100, verbose: bool = False):
    """Exécute l'étape 3 : génération des questions de test."""
    print("\n" + "=" * 70)
    print("ÉTAPE 3 : Génération des questions de test")
    print("=" * 70 + "\n")
    
    if not db_path or not db_path.exists():
        print(f"[ERREUR] Base non trouvée: {db_path}")
        return {'erreur': 'Base non trouvée'}
    
    # Extraire le nombre de patients pour le nommage
    nb_pats = extraire_nb_patients_base(db_path)
    
    print(f"Base de données: {db_path}")
    print(f"Identifiant base: {nb_pats}")
    print(f"Nombre de questions: {nb_questions}")
    print()
    
    # Charger les patients
    patients = charger_patients_avec_tags(db_path, limite=nb_questions * 2)
    if not patients:
        print("[ERREUR] Aucun patient avec tags dans la base")
        return {'erreur': 'Aucun patient avec tags'}
    
    print(f"✓ {len(patients)} patients chargés avec tags")
    
    # Charger les angles
    angles = charger_angles(dossier_refs)
    print(f"✓ {len(angles)} patterns d'angles chargés")
    if angles and verbose:
        types_angles = set(a['type_angle'] for a in angles)
        print(f"  Types: {', '.join(sorted(types_angles))}")
    print()
    
    # Distribution des complexités
    distribution = []
    for nb_crit, pct in DISTRIBUTION_QUESTIONS['complexite'].items():
        distribution.extend([nb_crit] * (pct * nb_questions // 100))
    while len(distribution) < nb_questions:
        distribution.append(2)
    random.shuffle(distribution)
    
    # Distribution des angles : 10% des questions
    pct_angles = DISTRIBUTION_QUESTIONS.get('pct_angles', 10)
    nb_angles_cible = max(1, pct_angles * nb_questions // 100)
    indices_avec_angle = set(random.sample(range(nb_questions), 
                                            min(nb_angles_cible, nb_questions)))
    
    # Distribution des âges : 20% des questions
    pct_ages = DISTRIBUTION_QUESTIONS.get('pct_ages', 20)
    nb_ages_cible = max(1, pct_ages * nb_questions // 100)
    # Éviter de superposer trop avec les angles
    indices_restants = [i for i in range(nb_questions) if i not in indices_avec_angle]
    nb_ages_a_ajouter = min(nb_ages_cible, len(indices_restants))
    indices_avec_age = set(random.sample(indices_restants, nb_ages_a_ajouter))
    # Ajouter aussi quelques âges aux questions avec angles
    indices_avec_age.update(random.sample(list(indices_avec_angle), 
                                          min(nb_ages_cible // 3, len(indices_avec_angle))))
    
    # Générer les questions
    questions = []
    pct_count = DISTRIBUTION_QUESTIONS['pct_count']
    
    # Stats
    stats = {
        'count': 0,
        'list': 0,
        'angles': 0,
        'ages': 0,
        'sexes': 0,
        'par_nb_criteres': {1: 0, 2: 0, 3: 0, 4: 0}
    }
    
    for i, patient in enumerate(patients[:nb_questions]):
        is_count = random.random() < (pct_count / 100)
        nb_criteres = distribution[i] if i < len(distribution) else 2
        inclure_angle = (i in indices_avec_angle) and angles
        inclure_age = (i in indices_avec_age)
        
        q = generer_question_depuis_patient(patient, angles, nb_criteres, is_count, 
                                            inclure_angle, inclure_age)
        
        # Extraire les critères SQL et faire la vraie recherche
        criteres_sql = q.pop('criteres_sql', [])
        nb_reponses, ids_patients = rechercher_patients_correspondants(db_path, criteres_sql, limite=10)
        
        q['nb_reponses'] = nb_reponses
        q['10patients_id'] = ','.join(str(id) for id in ids_patients)
        
        # Extraire les flags et les convertir en 0/1
        a_angle = q.pop('a_angle', False)
        a_age = q.pop('a_age', False)
        a_sexe = q.pop('a_sexe', False)
        
        # Ajouter les colonnes 0/1
        q['sexe'] = 1 if a_sexe else 0
        q['age'] = 1 if a_age else 0
        q['angles'] = 1 if a_angle else 0
        
        questions.append(q)
        
        # Mise à jour stats
        if is_count:
            stats['count'] += 1
        else:
            stats['list'] += 1
        
        if a_angle:
            stats['angles'] += 1
        if a_age:
            stats['ages'] += 1
        if a_sexe:
            stats['sexes'] += 1
        
        nb_crit_reel = q['nb_criteres']
        if nb_crit_reel in stats['par_nb_criteres']:
            stats['par_nb_criteres'][nb_crit_reel] += 1
        
        if verbose and (i + 1) % 50 == 0:
            print(f"  {i + 1}/{nb_questions} questions générées...")
    
    # Nom du fichier avec le nombre de patients : qpatsNNNNin.csv
    fichier_sortie = dossier_tests / f"qpats{nb_pats}in.csv"
    now = datetime.now().strftime('%d/%m/%Y %H:%M:%S')
    
    with open(fichier_sortie, 'w', encoding='utf-8-sig', newline='') as f:
        f.write(f"# qpats{nb_pats}in.csv généré par {__pgm__} V{__version__}\n")
        f.write(f"# Date: {now}\n")
        f.write(f"# Base: {db_path.name}\n")
        f.write(f"# Questions: {len(questions)}\n")
        
        fieldnames = ['fr', 'listcount', 'nb_criteres', 'nb_reponses', '10patients_id', 'tags', 'adjectifs', 'sexe', 'age', 'angles']
        writer = csv.DictWriter(f, fieldnames=fieldnames, delimiter=';', extrasaction='ignore')
        writer.writeheader()
        writer.writerows(questions)
    
    print(f"✓ {len(questions)} questions générées → {fichier_sortie}")
    print()
    
    # Stats détaillées
    total = len(questions)
    print("  Répartition:")
    print(f"    - COUNT: {stats['count']} ({100*stats['count']//total}%)")
    print(f"    - LIST: {stats['list']} ({100*stats['list']//total}%)")
    print()
    print(f"    - SEXES: {stats['sexes']} ({100*stats['sexes']//total}%)")
    print(f"    - AGES: {stats['ages']} ({100*stats['ages']//total}%)")
    print(f"    - ANGLES: {stats['angles']} ({100*stats['angles']//total}%)")
    print()
    print("  Par nombre de critères:")
    for nb, count in sorted(stats['par_nb_criteres'].items()):
        if count > 0:
            print(f"    - {nb} critère(s): {count} ({100*count//total}%)")
    
    # Stats sur nb_reponses
    nb_rep_moy = sum(q['nb_reponses'] for q in questions) / len(questions)
    nb_rep_min = min(q['nb_reponses'] for q in questions)
    nb_rep_max = max(q['nb_reponses'] for q in questions)
    print()
    print(f"  Réponses: min={nb_rep_min}, max={nb_rep_max}, moy={nb_rep_moy:.1f}")
    
    return {
        'nb_questions': len(questions), 
        'fichier': str(fichier_sortie), 
        'nb_pats': nb_pats,
        'stats': stats
    }


# =============================================================================
# ÉTAPE 4 : AUDIT DE CONCORDANCE
# =============================================================================

def charger_resultats_detection(fichier: Path) -> List[Dict]:
    """Charge un fichier de résultats de détection."""
    if not fichier.exists():
        return []
    
    _, rows = lire_csv_utf8(fichier)
    return rows


def calculer_concordance_tags(tags1: str, tags2: str) -> Tuple[bool, float]:
    """
    Calcule la concordance entre deux listes de tags.
    
    Returns:
        (concordance_exacte: bool, concordance_partielle: float 0-1)
    """
    set1 = set(t.strip().lower() for t in tags1.split(',') if t.strip())
    set2 = set(t.strip().lower() for t in tags2.split(',') if t.strip())
    
    if not set1 and not set2:
        return True, 1.0
    
    if set1 == set2:
        return True, 1.0
    
    # Concordance partielle (Jaccard)
    if not set1 or not set2:
        return False, 0.0
    
    intersection = len(set1 & set2)
    union = len(set1 | set2)
    jaccard = intersection / union if union > 0 else 0
    
    return False, jaccard


def etape_4_audit(dossier_tests: Path, nb_pats: str = None, verbose: bool = False):
    """Exécute l'étape 4 : audit de concordance detall vs detia."""
    print("\n" + "=" * 70)
    print("ÉTAPE 4 : Audit de concordance (detall vs detia)")
    print("=" * 70 + "\n")
    
    # Chercher les fichiers avec le bon pattern
    # Si nb_pats spécifié : qpatsNNNNout.csv et qpatsNNNNout_ia.csv
    # Sinon : chercher automatiquement ou fallback sur testsquestions*
    
    fichier_detall = None
    fichier_detia = None
    
    if nb_pats:
        fichier_detall = dossier_tests / f"qpats{nb_pats}out.csv"
        fichier_detia = dossier_tests / f"qpats{nb_pats}out_ia.csv"
    else:
        # Chercher les fichiers qpats*out.csv les plus récents
        fichiers_out = list(dossier_tests.glob("qpats*out.csv"))
        fichiers_out = [f for f in fichiers_out if '_ia' not in f.name]
        
        if fichiers_out:
            # Prendre le plus récent
            fichier_detall = max(fichiers_out, key=lambda f: f.stat().st_mtime)
            # Extraire le numéro pour trouver le fichier IA correspondant
            import re
            match = re.search(r'qpats(\d+)out\.csv', fichier_detall.name)
            if match:
                nb_pats = match.group(1)
                fichier_detia = dossier_tests / f"qpats{nb_pats}out_ia.csv"
        
        # Fallback sur l'ancien format
        if not fichier_detall or not fichier_detall.exists():
            fichier_detall = dossier_tests / "testsquestionsout.csv"
            fichier_detia = dossier_tests / "testsquestionsout_ia.csv"
    
    if not fichier_detall.exists():
        print(f"[ERREUR] Fichier detall non trouvé: {fichier_detall}")
        print("  → Lancez d'abord: python detall.py tests/testsquestionsin.csv")
        return {'erreur': 'Fichier detall manquant'}
    
    if not fichier_detia.exists():
        print(f"[ERREUR] Fichier detia non trouvé: {fichier_detia}")
        print("  → Lancez d'abord: python detia.py tests/testsquestionsin.csv")
        return {'erreur': 'Fichier detia manquant'}
    
    print(f"Fichier detall: {fichier_detall}")
    print(f"Fichier detia : {fichier_detia}")
    print()
    
    # Charger les résultats
    resultats_detall = charger_resultats_detection(fichier_detall)
    resultats_detia = charger_resultats_detection(fichier_detia)
    
    if len(resultats_detall) != len(resultats_detia):
        print(f"[WARN] Nombre de lignes différent: detall={len(resultats_detall)}, detia={len(resultats_detia)}")
    
    print(f"✓ {len(resultats_detall)} lignes detall")
    print(f"✓ {len(resultats_detia)} lignes detia")
    print()
    
    # Construire index par question (colonne 'fr' ou 'question' pour compatibilité)
    index_detia = {}
    for r in resultats_detia:
        q = (r.get('fr') or r.get('question') or '').strip()
        if q:
            index_detia[q] = r
    
    # Calculer les métriques
    audits = []
    total_listcount_ok = 0
    total_tags_exact = 0
    total_tags_partiel = 0.0
    total_latency_detall = 0
    total_latency_detia = 0
    nb_comparaisons = 0
    
    for row_detall in resultats_detall:
        question = (row_detall.get('fr') or row_detall.get('question') or '').strip()
        if not question:
            continue
        
        row_detia = index_detia.get(question)
        if not row_detia:
            continue
        
        nb_comparaisons += 1
        
        # Concordance listcount
        lc_detall = row_detall.get('listcount', 'LIST')
        lc_detia = row_detia.get('listcount', 'LIST')
        listcount_ok = lc_detall == lc_detia
        if listcount_ok:
            total_listcount_ok += 1
        
        # Concordance tags
        tags_detall = row_detall.get('tags', '')
        tags_detia = row_detia.get('tags', '')
        tags_exact, tags_partiel = calculer_concordance_tags(tags_detall, tags_detia)
        if tags_exact:
            total_tags_exact += 1
        total_tags_partiel += tags_partiel
        
        # Latences
        try:
            lat_detall = float(row_detall.get('latency_ms', 0) or 0)
            lat_detia = float(row_detia.get('latency_ms', 0) or 0)
        except (ValueError, TypeError):
            lat_detall, lat_detia = 0, 0
        
        total_latency_detall += lat_detall
        total_latency_detia += lat_detia
        
        audits.append({
            'question': question,
            'listcount_ok': 'OUI' if listcount_ok else 'NON',
            'tags_exact': 'OUI' if tags_exact else 'NON',
            'tags_jaccard': f"{tags_partiel:.2f}",
            'tags_detall': tags_detall,
            'tags_detia': tags_detia,
            'latency_detall': f"{lat_detall:.0f}",
            'latency_detia': f"{lat_detia:.0f}",
            'ecart_latency': f"{lat_detia - lat_detall:.0f}"
        })
        
        if verbose and nb_comparaisons <= 5:
            print(f"  Q: {question[:50]}...")
            print(f"    listcount: {lc_detall} vs {lc_detia} → {'✓' if listcount_ok else '✗'}")
            print(f"    tags: {tags_detall} vs {tags_detia} → {tags_partiel:.2f}")
    
    # Calculer les pourcentages
    if nb_comparaisons > 0:
        pct_listcount = 100 * total_listcount_ok / nb_comparaisons
        pct_tags_exact = 100 * total_tags_exact / nb_comparaisons
        pct_tags_partiel = 100 * total_tags_partiel / nb_comparaisons
        avg_latency_detall = total_latency_detall / nb_comparaisons
        avg_latency_detia = total_latency_detia / nb_comparaisons
    else:
        pct_listcount = pct_tags_exact = pct_tags_partiel = 0
        avg_latency_detall = avg_latency_detia = 0
    
    # Écrire le fichier d'audit (avec numéro si disponible)
    if nb_pats:
        fichier_audit = dossier_tests / f"audit{nb_pats}.csv"
    else:
        fichier_audit = dossier_tests / "audit_concordance.csv"
    now = datetime.now().strftime('%d/%m/%Y %H:%M:%S')
    
    with open(fichier_audit, 'w', encoding='utf-8-sig', newline='') as f:
        f.write(f"# audit_concordance.csv généré par {__pgm__} V{__version__}\n")
        f.write(f"# Date: {now}\n")
        f.write(f"# Comparaisons: {nb_comparaisons}\n")
        f.write(f"# Concordance listcount: {pct_listcount:.1f}%\n")
        f.write(f"# Concordance tags exacte: {pct_tags_exact:.1f}%\n")
        f.write(f"# Concordance tags partielle (Jaccard): {pct_tags_partiel:.1f}%\n")
        f.write(f"# Latence moyenne detall: {avg_latency_detall:.0f}ms\n")
        f.write(f"# Latence moyenne detia: {avg_latency_detia:.0f}ms\n")
        
        fieldnames = ['question', 'listcount_ok', 'tags_exact', 'tags_jaccard', 
                     'tags_detall', 'tags_detia', 'latency_detall', 'latency_detia', 'ecart_latency']
        writer = csv.DictWriter(f, fieldnames=fieldnames, delimiter=';')
        writer.writeheader()
        writer.writerows(audits)
    
    print("=" * 70)
    print("RÉSUMÉ DE L'AUDIT")
    print("=" * 70)
    print(f"  Comparaisons effectuées : {nb_comparaisons}")
    print()
    print(f"  Concordance listcount   : {pct_listcount:.1f}% ({total_listcount_ok}/{nb_comparaisons})")
    print(f"  Concordance tags exacte : {pct_tags_exact:.1f}% ({total_tags_exact}/{nb_comparaisons})")
    print(f"  Concordance tags Jaccard: {pct_tags_partiel:.1f}%")
    print()
    print(f"  Latence moyenne detall  : {avg_latency_detall:.0f}ms")
    print(f"  Latence moyenne detia   : {avg_latency_detia:.0f}ms")
    print(f"  Écart moyen             : {avg_latency_detia - avg_latency_detall:.0f}ms")
    print()
    print(f"✓ Audit complet → {fichier_audit}")
    
    return {
        'nb_comparaisons': nb_comparaisons,
        'pct_listcount': pct_listcount,
        'pct_tags_exact': pct_tags_exact,
        'pct_tags_jaccard': pct_tags_partiel,
        'avg_latency_detall': avg_latency_detall,
        'avg_latency_detia': avg_latency_detia,
        'fichier': str(fichier_audit)
    }


# =============================================================================
# AFFICHAGE STATUS
# =============================================================================

def afficher_status(dossier_refs: Path, dossier_tests: Path):
    """Affiche l'état des fichiers du pipeline."""
    print("\n" + "=" * 70)
    print("STATUS DES FICHIERS")
    print("=" * 70)
    print(f"\nDossier refs : {dossier_refs}")
    print(f"Dossier tests: {dossier_tests}")
    print()
    
    # Fichiers de référence (nouvelle architecture)
    print("[RÉFÉRENCES]")
    fichiers_refs = [
        ('tags.csv', 'Tags avec patterns (t;gn;as;pts)'),
        ('adjectifs.csv', 'Adjectifs avec formes (a;f;mp;fp;pas)'),
        ('ages.csv', 'Patterns âge/sexe'),
        ('angles.csv', 'Seuils céphalométriques'),
        ('ia.csv', 'Configuration moteurs IA'),
    ]
    
    for nom, desc in fichiers_refs:
        chemin = dossier_refs / nom
        if chemin.exists():
            taille = chemin.stat().st_size
            mtime = datetime.fromtimestamp(chemin.stat().st_mtime)
            print(f"  ✓ {nom:20} {taille:>8} bytes  {mtime.strftime('%d/%m %H:%M')}  ({desc})")
        else:
            print(f"  ✗ {nom:20} MANQUANT  ({desc})")
    print()
    
    # Fichiers de test
    print("[TESTS]")
    # Chercher les fichiers qpats*.csv
    fichiers_qpats = list(dossier_tests.glob("qpats*.csv")) if dossier_tests.exists() else []
    fichiers_audit = list(dossier_tests.glob("audit*.csv")) if dossier_tests.exists() else []
    
    if fichiers_qpats or fichiers_audit:
        for f in sorted(fichiers_qpats + fichiers_audit):
            taille = f.stat().st_size
            mtime = datetime.fromtimestamp(f.stat().st_mtime)
            print(f"  ✓ {f.name:25} {taille:>8} bytes  {mtime.strftime('%d/%m %H:%M')}")
    else:
        print("  (aucun fichier de test trouvé)")
        print("  → Générez des questions avec: python pipeline.py quest bases/baseN.db")


def afficher_aide():
    """Affiche l'aide du pipeline."""
    print(f"""
╔══════════════════════════════════════════════════════════════════════╗
║ {__pgm__} V{__version__} - Pipeline de génération KITVIEW
╚══════════════════════════════════════════════════════════════════════╝

COMMANDES DISPONIBLES :

  questions (ou quest) Génère des questions de test depuis la base patients
  audit                Compare les résultats detall vs detia
  status               Affiche l'état des fichiers générés
  help                 Cette aide

NOTE : La commande 'synonymes' a été supprimée car les fichiers syn*.csv
       ne sont plus utilisés. Les lookups sont générés en mémoire à la volée
       depuis tags.csv et adjectifs.csv.

═══════════════════════════════════════════════════════════════════════
                         EXEMPLES D'UTILISATION
═══════════════════════════════════════════════════════════════════════

  # Voir l'état des fichiers
  python pipeline.py status

  # Générer 100 questions depuis base1000.db
  python pipeline.py questions bases/base1000.db
  → Crée tests/qpats1000in.csv

  # Générer 50 questions (ordre des paramètres libre)
  python pipeline.py quest 50 bases/pats500.db verbose
  python pipeline.py questions verbose bases/base1000.db 75

  # Lancer l'audit pour la base 1000
  python pipeline.py audit 1000
  → Compare qpats1000out.csv et qpats1000out_ia.csv
  → Crée tests/audit1000.csv

  # Audit avec détails
  python pipeline.py audit 1000 verbose

═══════════════════════════════════════════════════════════════════════
                       WORKFLOW COMPLET TYPIQUE
═══════════════════════════════════════════════════════════════════════

  1. python pipeline.py quest bases/base1000.db 100
  2. python detall.py tests/qpats1000in.csv
  3. python detia.py tests/qpats1000in.csv
  4. python pipeline.py audit 1000 verbose

═══════════════════════════════════════════════════════════════════════

PARAMÈTRES (ordre libre, sans --) :

  bases/xxx.db      Chemin vers la base SQLite
  100, 50...        Nombre (questions à générer ou n° base pour audit)
  verbose           Affichage détaillé

FICHIERS DE RÉFÉRENCE (nouvelle architecture) :
  refs/tags.csv       : Tags avec patterns (colonnes: t;gn;as;pts)
  refs/adjectifs.csv  : Adjectifs avec formes (colonnes: a;f;mp;fp;pas)
  refs/ages.csv       : Patterns âge/sexe
  refs/angles.csv     : Seuils céphalométriques

CONVENTION DE NOMMAGE :
  Base            : bases/base1000.db
  Questions       : tests/qpats1000in.csv (colonne 'fr')
  Sortie detall   : tests/qpats1000out.csv
  Sortie detia    : tests/qpats1000out_ia.csv
  Audit           : tests/audit1000.csv
""")


# =============================================================================
# PARSING INTELLIGENT DES ARGUMENTS
# =============================================================================

def parser_arguments(args: List[str]) -> Dict:
    """
    Parse les arguments de façon intelligente, sans -- et dans n'importe quel ordre.
    
    Détection automatique :
    - Commande : questions/quest, audit, status, help
    - Base : tout ce qui finit par .db
    - Nombre : entier seul (pour nb questions ou numéro base)
    - verbose : le mot "verbose"
    
    Exemples :
        ['quest', 'bases/base1000.db', '50']
        ['audit', '1000', 'verbose']
    """
    result = {
        'commande': None,
        'base': None,
        'nombre': None,
        'verbose': False,
        'help': False
    }
    
    commandes_valides = {
        'questions': 'questions', 'quest': 'questions', 'q': 'questions',
        'audit': 'audit', 'aud': 'audit',
        'status': 'status', 'stat': 'status', 's': 'status',
        'help': 'help', 'aide': 'help', 'h': 'help', '?': 'help'
    }
    
    for arg in args:
        arg_lower = arg.lower().strip()
        
        # Nettoyer les -- si présents (compatibilité)
        if arg_lower.startswith('--'):
            arg_lower = arg_lower[2:]
        elif arg_lower.startswith('-'):
            arg_lower = arg_lower[1:]
        
        # Commande ?
        if arg_lower in commandes_valides:
            result['commande'] = commandes_valides[arg_lower]
            continue
        
        # Verbose ?
        if arg_lower in ('verbose', 'v'):
            result['verbose'] = True
            continue
        
        # Base de données ? (finit par .db)
        if arg.endswith('.db'):
            result['base'] = arg
            continue
        
        # Nombre ? (entier)
        try:
            result['nombre'] = int(arg_lower)
            continue
        except ValueError:
            pass
        
        # Chemin vers une base sans .db spécifié ?
        if 'base' in arg_lower or 'pats' in arg_lower:
            # Peut-être un chemin incomplet
            if not arg.endswith('.db'):
                arg = arg + '.db'
            result['base'] = arg
            continue
    
    return result


# =============================================================================
# POINT D'ENTRÉE
# =============================================================================

def main():
    print(f"╔════════════════════════════════════════════════════════════════")
    print(f"║ {__pgm__} V{__version__} - {__date__}")
    print(f"║ Pipeline de génération KITVIEW")
    print(f"╚════════════════════════════════════════════════════════════════")
    
    # Parser les arguments
    args = parser_arguments(sys.argv[1:])
    
    # Trouver les dossiers
    dossier_refs = trouver_dossier_refs()
    dossier_tests = trouver_dossier_tests()
    
    if not dossier_refs:
        print("\n[ERREUR] Dossier refs non trouvé")
        return 1
    
    # Aide ou pas de commande
    if args['commande'] == 'help' or args['commande'] is None:
        afficher_aide()
        return 0
    
    # STATUS
    if args['commande'] == 'status':
        afficher_status(dossier_refs, dossier_tests or Path("tests"))
        return 0
    
    # QUESTIONS
    if args['commande'] == 'questions':
        if not dossier_tests:
            dossier_tests = Path("tests")
            dossier_tests.mkdir(exist_ok=True)
        
        db_path = None
        if args['base']:
            db_path = Path(args['base'])
        else:
            # Chercher une base automatiquement
            for chemin in CHEMINS_BASES:
                if chemin.exists():
                    bases = list(chemin.glob("base*.db")) + list(chemin.glob("pats*.db"))
                    if bases:
                        db_path = bases[0]
                        print(f"[INFO] Base auto-détectée : {db_path}")
                        break
        
        if not db_path or not db_path.exists():
            print("[ERREUR] Base non trouvée.")
            print("  Spécifiez le chemin : python pipeline.py questions bases/base1000.db")
            return 1
        
        nb_questions = args['nombre'] if args['nombre'] else 100
        etape_3_questions(dossier_refs, dossier_tests, db_path, nb_questions=nb_questions, verbose=args['verbose'])
        return 0
    
    # AUDIT
    if args['commande'] == 'audit':
        if not dossier_tests:
            dossier_tests = Path("tests")
        
        nb_pats = str(args['nombre']) if args['nombre'] else None
        etape_4_audit(dossier_tests, nb_pats=nb_pats, verbose=args['verbose'])
        return 0
    
    print(f"[ERREUR] Commande non reconnue")
    afficher_aide()
    return 1


if __name__ == '__main__':
    sys.exit(main())
