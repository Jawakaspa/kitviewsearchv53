# generequestion.py V1.0.2 - 20/12/2025 13:46:29
__pgm__ = "generequestion.py"
__version__ = "1.0.2"
__date__ = "20/12/2025 13:46:29"

"""
generequestion.py - Générateur de questions à partir de patients réels

Génère N questions en français garanties d'avoir au moins un patient correspondant.
La méthode "cheat" consiste à lire d'abord les données des patients puis générer
des questions qui correspondent à leurs caractéristiques.

Usage : python generequestion.py base.db N
    base.db : chemin vers la base de données SQLite
    N       : nombre de questions à générer

Fichiers d'entrée :
- base.db : base de données des patients
- templatequestion.csv : templates de questions
- tagsadjs.xlsx : pathologies et adjectifs avec accords grammaticaux
- ages.csv : critères d'âge
- angles.csv : correspondance tags ↔ angles céphalométriques

Fichier de sortie :
- questions_generees.csv : questions générées avec colonnes :
    question;type;nb_criteres;nb_resultats;ids_10
"""

import sqlite3
import pandas as pd
import random
import re
import sys
import os
from pathlib import Path
from io import StringIO


def get_script_dir() -> Path:
    """Retourne le répertoire du script."""
    return Path(__file__).parent.resolve()


def load_csv_with_comments(filepath: Path) -> pd.DataFrame:
    """Charge un CSV en ignorant les lignes de commentaires (#) et les lignes vides."""
    with open(filepath, 'r', encoding='utf-8-sig') as f:
        lines = []
        for line in f:
            stripped = line.strip()
            # Ignorer commentaires, lignes vides, et lignes avec BOM mal formé
            if stripped and not stripped.startswith('#') and not stripped.startswith('\\x'):
                lines.append(line)
    return pd.read_csv(StringIO(''.join(lines)), sep=';')


def load_templates(filepath: Path) -> pd.DataFrame:
    """Charge les templates de questions."""
    return load_csv_with_comments(filepath)


def load_tagsadjs(filepath: Path) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Charge tagsadjs.xlsx et retourne tags et adjectifs."""
    df = pd.read_excel(filepath, engine='openpyxl')
    tags = df[df['type'] == 'p'].copy()
    adjs = df[df['type'] == 'a'].copy()
    return tags, adjs


def load_angles(filepath: Path) -> pd.DataFrame:
    """Charge angles.csv."""
    return load_csv_with_comments(filepath)


def load_ages(filepath: Path) -> pd.DataFrame:
    """Charge ages.csv."""
    return load_csv_with_comments(filepath)


def connect_db(db_path: Path) -> sqlite3.Connection:
    """Connecte à la base de données."""
    if not db_path.exists():
        print(f"[ERREUR] Base de données introuvable : {db_path.resolve()}")
        sys.exit(1)
    return sqlite3.connect(db_path)


def get_all_patients(conn: sqlite3.Connection) -> pd.DataFrame:
    """Récupère tous les patients de la base."""
    query = """
        SELECT id, prenom, nom, sexe, age, canontags, canonadjs
        FROM patients
    """
    return pd.read_sql_query(query, conn)


def parse_patient_tags(canontags: str, canonadjs: str) -> list[dict]:
    """
    Parse les tags et adjectifs d'un patient.
    Retourne une liste de dict : [{'tag': 'béance', 'adjs': ['sévère', 'latéral']}, ...]
    Les tags sont normalisés en minuscules pour correspondre au système de détection.
    """
    if pd.isna(canontags) or not canontags.strip():
        return []
    
    tags_list = [t.strip().lower() for t in canontags.split(',')]  # Normaliser en minuscules
    adjs_list = canonadjs.split(',') if pd.notna(canonadjs) and canonadjs.strip() else [''] * len(tags_list)
    
    # S'assurer que les listes ont la même longueur
    while len(adjs_list) < len(tags_list):
        adjs_list.append('')
    
    result = []
    for i, tag in enumerate(tags_list):
        tag_adjs = []
        if i < len(adjs_list) and adjs_list[i].strip():
            # Normaliser les adjectifs en minuscules aussi
            tag_adjs = [a.strip().lower() for a in adjs_list[i].split('|') if a.strip()]
        result.append({'tag': tag.strip(), 'adjs': tag_adjs})
    
    return result


def build_angle_mapping(angles_df: pd.DataFrame) -> dict:
    """
    Construit un mapping tag_canonique → infos angle.
    Retourne : {tag_lower: {'angle': 'ANB/SNA/SNB', 'operator': '>/</BETWEEN', 'seuil': ...}}
    """
    mapping = {}
    
    for _, row in angles_df.iterrows():
        tag = str(row['tag_canonique']).lower().strip()
        expression = str(row['expression'])
        operateur = str(row['operateur'])
        seuil = str(row['seuil'])
        
        # Déterminer l'angle (ANB, SNA, SNB) à partir de l'expression
        if 'anb' in expression.lower():
            angle = 'ANB'
        elif 'sna' in expression.lower():
            angle = 'SNA'
        elif 'snb' in expression.lower():
            angle = 'SNB'
        else:
            continue
        
        if tag not in mapping:
            mapping[tag] = {
                'angle': angle,
                'operator': operateur,
                'seuil': seuil,
                'expressions': []
            }
        
        # Extraire une expression simple pour la génération
        # Prendre la première expression de la liste
        first_expr = expression.split('|')[0].strip()
        mapping[tag]['expressions'].append(first_expr)
    
    return mapping


def generate_angle_expression(angle_info: dict) -> str:
    """
    Génère une expression d'angle pour une question.
    Les expressions doivent correspondre EXACTEMENT aux patterns de angles.csv.
    Ex: "ANB > 5", "SNA < 78", "ANB entre 2 et 4"
    
    Note: Les angles sont écrits en MAJUSCULES dans les questions (convention médicale)
    mais le système de détection les normalise en minuscules.
    """
    angle = angle_info['angle']  # ANB, SNA, SNB
    operator = angle_info['operator']
    seuil = angle_info['seuil']
    
    # Convertir le seuil en int (c'est une string depuis le CSV)
    def parse_seuil(s):
        try:
            return int(float(str(s)))
        except (ValueError, TypeError):
            return 4  # Valeur par défaut
    
    if operator == '>':
        # Générer une valeur au-dessus du seuil pour que la condition soit vraie
        # Ex: seuil ANB > 4, on génère une valeur > 4 (ex: 5, 6, 7)
        seuil_int = parse_seuil(seuil)
        val = seuil_int + random.randint(1, 4)
        # Patterns reconnus: "anb > {n}" ou "anb>{n}"
        return f"{angle} > {val}"
        
    elif operator == '<':
        # Générer une valeur en-dessous du seuil
        # Ex: seuil ANB < 0, on génère une valeur < 0 (ex: -1, -2, -3)
        seuil_int = parse_seuil(seuil)
        val = seuil_int - random.randint(1, 4)
        # Patterns reconnus: "anb < {n}" ou "anb<{n}"
        return f"{angle} < {val}"
        
    elif operator == 'BETWEEN':
        if ',' in str(seuil):
            parts = str(seuil).split(',')
            val1 = int(float(parts[0].strip()))
            val2 = int(float(parts[1].strip()))
            # Pattern reconnu: "anb entre {n} et {n}"
            return f"{angle} entre {val1} et {val2}"
        else:
            return f"{angle} = {seuil}"
    else:
        return f"{angle} = {seuil}"


def normalize_tag(tag: str) -> str:
    """Normalise un tag pour la comparaison."""
    import unicodedata
    tag = tag.lower().strip()
    # Supprimer les accents
    tag = unicodedata.normalize('NFD', tag)
    tag = ''.join(c for c in tag if unicodedata.category(c) != 'Mn')
    return tag


def get_tag_article(tag: str, tags_df: pd.DataFrame) -> str:
    """Récupère l'article approprié pour un tag."""
    tag_lower = normalize_tag(tag)
    
    for _, row in tags_df.iterrows():
        if normalize_tag(str(row['canon'])) == tag_lower:
            xgn = str(row.get('Xgn', 'm')).lower().strip() if pd.notna(row.get('Xgn')) else 'm'
            if xgn == 'f':
                return 'une'
            elif xgn in ('fp', 'mp'):
                return 'des'
            else:
                return 'un'
    
    # Par défaut
    return 'un'


def get_adj_accord(adj: str, tag: str, tags_df: pd.DataFrame, adjs_df: pd.DataFrame) -> str:
    """Retourne l'adjectif accordé selon le genre du tag."""
    # Trouver le genre du tag
    tag_lower = normalize_tag(tag)
    xgn = 'm'
    
    for _, row in tags_df.iterrows():
        if normalize_tag(str(row['canon'])) == tag_lower:
            xgn = str(row.get('Xgn', 'm')).lower().strip() if pd.notna(row.get('Xgn')) else 'm'
            break
    
    # Trouver l'adjectif et l'accorder
    adj_lower = normalize_tag(adj)
    
    for _, row in adjs_df.iterrows():
        if normalize_tag(str(row['canon'])) == adj_lower:
            if xgn == 'f' and pd.notna(row.get('f')):
                return str(row['f'])
            elif xgn == 'm' and pd.notna(row.get('m')):
                return str(row['m'])
            elif xgn == 'fp' and pd.notna(row.get('fp')):
                return str(row['fp'])
            elif xgn == 'mp' and pd.notna(row.get('mp')):
                return str(row['mp'])
    
    return adj  # Retourner tel quel si non trouvé


def generate_age_criterion(patient_age: float, ages_df: pd.DataFrame) -> str:
    """
    Génère un critère d'âge correspondant au patient.
    Les expressions doivent correspondre EXACTEMENT aux patterns de ages.csv.
    """
    age_int = int(patient_age)
    
    # Options basées sur ages.csv (patterns reconnus)
    options = []
    
    # Option 1 : fourchette (pattern: "entre {n} et {n} ans")
    min_age = max(0, age_int - random.randint(2, 5))
    max_age = age_int + random.randint(2, 5)
    options.append(f"entre {min_age} et {max_age} ans")
    
    # Option 2 : moins de / plus de (patterns: "moins de {n} ans", "plus de {n} ans")
    if age_int < 50:
        options.append(f"moins de {age_int + random.randint(3, 8)} ans")
    if age_int > 10:
        options.append(f"plus de {max(0, age_int - random.randint(3, 8))} ans")
    
    # Option 3 : catégories d'âge (patterns exacts de ages.csv)
    if age_int < 12:
        options.extend(["enfants", "enfant"])
    if age_int < 18:
        options.extend(["mineurs", "mineur"])
    if 12 <= age_int < 18:
        options.extend(["adolescents", "adolescent"])
    if age_int >= 18:
        options.extend(["adultes", "adulte", "majeurs"])
    if 18 <= age_int < 25:
        options.append("jeunes adultes")
    
    # Option 4 : âge exact (pattern: "{n} ans")
    options.append(f"{age_int} ans")
    
    return random.choice(options)


def generate_sex_criterion(sexe: str) -> str:
    """Génère un critère de sexe."""
    if sexe == 'M':
        return random.choice(['hommes', 'garçons', 'de sexe masculin'])
    else:
        return random.choice(['femmes', 'filles', 'de sexe féminin'])


def count_matching_patients(conn: sqlite3.Connection, criteria: dict) -> tuple[int, list[int]]:
    """
    Compte les patients correspondant aux critères et retourne les IDs.
    criteria : {'tags': [...], 'age_min': ..., 'age_max': ..., 'sexe': ...}
    Utilise stdcanontags (normalisé) pour la recherche.
    """
    query = "SELECT id FROM patients WHERE 1=1"
    params = []
    
    # Critères de tags - utiliser stdcanontags pour la recherche normalisée
    for tag_info in criteria.get('tags', []):
        tag = tag_info['tag'].lower()  # S'assurer que c'est en minuscules
        # Recherche insensible à la casse dans stdcanontags
        query += " AND LOWER(stdcanontags) LIKE ?"
        params.append(f"%{tag}%")
        
        # Si adjectif spécifié - utiliser stdcanonadjs
        if tag_info.get('adj'):
            adj = tag_info['adj'].lower()
            query += " AND LOWER(stdcanonadjs) LIKE ?"
            params.append(f"%{adj}%")
    
    # Critères d'âge
    if 'age_min' in criteria:
        query += " AND age >= ?"
        params.append(criteria['age_min'])
    if 'age_max' in criteria:
        query += " AND age <= ?"
        params.append(criteria['age_max'])
    
    # Critère de sexe
    if 'sexe' in criteria:
        query += " AND sexe = ?"
        params.append(criteria['sexe'])
    
    cursor = conn.cursor()
    cursor.execute(query, params)
    ids = [row[0] for row in cursor.fetchall()]
    
    return len(ids), ids[:10]


def clean_question(question: str) -> str:
    """
    Nettoie une question des résidus de placeholders et connecteurs orphelins.
    """
    # Supprimer les placeholders restants
    question = re.sub(r'\{[A-Z]+\d*\}', '', question)
    
    # Supprimer les connecteurs orphelins en fin de partie
    # Patterns : "et ?", "avec ?", "plus ?", "ainsi que ?", etc.
    orphan_patterns = [
        r'\s+et\s*[?.]',
        r'\s+avec\s*[?.]',
        r'\s+plus\s*[?.]',
        r'\s+ainsi que\s*[?.]',
        r'\s+ayant également\s*[?.]',
        r'\s+présentant aussi\s*[?.]',
        r'\s+associé à\s*[?.]',
        r'\s+combiné avec\s*[?.]',
        r'\s+et qui ont\s*[?.]',
        r',\s+avec\s*[?.]',
        r',\s+et\s*[?.]',
        # En milieu de phrase aussi
        r'\s+et\s+et\s+',
        r'\s+avec\s+avec\s+',
        r'\s+plus\s+plus\s+',
        r',\s*,',
    ]
    
    for pattern in orphan_patterns:
        question = re.sub(pattern, lambda m: m.group()[-1] if m.group()[-1] in '?.' else ' ', question)
    
    # Supprimer les doubles connecteurs
    question = re.sub(r'\s+(et|avec|plus)\s+\1\s+', r' \1 ', question)
    
    # Nettoyer les espaces multiples
    question = re.sub(r'\s+', ' ', question)
    
    # Supprimer espace avant ponctuation
    question = re.sub(r'\s+([?.,!])', r'\1', question)
    
    # Supprimer les connecteurs en début après "les"
    question = re.sub(r'les\s+(et|avec|plus)\s+', 'les ', question)
    
    return question.strip()


def fill_template(template: str, criteria: list[dict], age_str: str | None, 
                  angle_str: str | None, tags_df: pd.DataFrame, adjs_df: pd.DataFrame) -> str:
    """
    Remplit un template avec les critères réels.
    """
    result = template
    
    tag_idx = 1
    for crit in criteria:
        if crit['type'] == 'tag':
            tag = crit['tag']
            adj = crit.get('adj', '')
            
            result = result.replace(f"{{T{tag_idx}}}", tag)
            if adj:
                adj_accorde = get_adj_accord(adj, tag, tags_df, adjs_df)
                result = result.replace(f"{{A{tag_idx}}}", adj_accorde)
            else:
                result = result.replace(f" {{A{tag_idx}}}", "")  # Avec l'espace avant
                result = result.replace(f"{{A{tag_idx}}}", "")
            tag_idx += 1
    
    # Remplacer {AGE}
    if age_str:
        result = result.replace("{AGE}", age_str)
    else:
        result = result.replace(" {AGE}", "")
        result = result.replace("{AGE}", "")
    
    # Remplacer {ANG}
    if angle_str:
        result = result.replace("{ANG}", angle_str)
    else:
        result = result.replace(" {ANG}", "")
        result = result.replace("{ANG}", "")
    
    # Nettoyer la question
    result = clean_question(result)
    
    return result


def generate_questions(
    conn: sqlite3.Connection,
    templates_df: pd.DataFrame,
    tags_df: pd.DataFrame,
    adjs_df: pd.DataFrame,
    angles_df: pd.DataFrame,
    ages_df: pd.DataFrame,
    n_questions: int
) -> list[dict]:
    """
    Génère N questions avec la méthode "cheat".
    """
    # Récupérer tous les patients
    patients = get_all_patients(conn)
    print(f"[INFO] {len(patients)} patients dans la base")
    
    # Construire le mapping angles
    angle_mapping = build_angle_mapping(angles_df)
    print(f"[INFO] {len(angle_mapping)} tags d'angle configurés")
    
    # Répartition cible (approximative)
    # 10% avec angles, 30% COUNT, répartis par nb_criteres
    target_angles = max(1, n_questions // 10)
    target_count = max(1, n_questions * 30 // 100)
    
    # Séparer les templates par type et par has_angle
    templates_angle = templates_df[templates_df['has_angle'] == 'OUI']
    templates_no_angle = templates_df[templates_df['has_angle'] == 'NON']
    templates_count = templates_df[templates_df['type'] == 'COUNT']
    templates_list = templates_df[templates_df['type'] == 'LIST']
    
    questions = []
    used_patient_combos = set()  # Pour éviter les doublons
    
    # Phase 1 : Générer les questions avec angles
    print(f"\n[INFO] Phase 1 : Génération de {target_angles} questions avec angles...")
    
    # Trouver les patients qui ont des tags correspondant à des angles
    patients_with_angles = []
    for _, patient in patients.iterrows():
        parsed = parse_patient_tags(patient['canontags'], patient['canonadjs'])
        for tag_info in parsed:
            tag_lower = normalize_tag(tag_info['tag'])
            if tag_lower in angle_mapping:
                patients_with_angles.append({
                    'patient': patient,
                    'parsed_tags': parsed,
                    'angle_tag': tag_info,
                    'angle_info': angle_mapping[tag_lower]
                })
    
    print(f"[INFO] {len(patients_with_angles)} patients avec tags d'angle trouvés")
    
    angle_count = 0
    for pwa in random.sample(patients_with_angles, min(target_angles * 2, len(patients_with_angles))):
        if angle_count >= target_angles:
            break
        
        patient = pwa['patient']
        parsed_tags = pwa['parsed_tags']
        angle_tag = pwa['angle_tag']
        angle_info = pwa['angle_info']
        
        # Choisir un template avec angle
        if templates_angle.empty:
            continue
        template_row = templates_angle.sample(1).iloc[0]
        template = template_row['template']
        nb_criteres = template_row['nb_criteres']
        q_type = template_row['type']
        
        # Générer l'expression d'angle
        angle_str = generate_angle_expression(angle_info)
        
        # Construire les critères
        criteria = [{'type': 'tag', 'tag': angle_tag['tag'], 'adj': random.choice(angle_tag['adjs']) if angle_tag['adjs'] else None}]
        search_criteria = {'tags': [{'tag': angle_tag['tag'], 'adj': criteria[0].get('adj')}]}
        
        # Ajouter d'autres tags si nécessaire
        other_tags = [t for t in parsed_tags if t['tag'] != angle_tag['tag']]
        tags_needed = nb_criteres - 1  # -1 pour l'angle
        
        for t in other_tags[:tags_needed]:
            adj = random.choice(t['adjs']) if t['adjs'] and random.random() > 0.5 else None
            criteria.append({'type': 'tag', 'tag': t['tag'], 'adj': adj})
            search_criteria['tags'].append({'tag': t['tag'], 'adj': adj})
        
        # Optionnellement ajouter âge
        age_str = None
        if '{AGE}' in template:
            age_str = generate_age_criterion(patient['age'], ages_df)
            age_int = int(patient['age'])
            search_criteria['age_min'] = max(0, age_int - 5)
            search_criteria['age_max'] = age_int + 5
        
        # Compter les patients correspondants
        nb_results, ids = count_matching_patients(conn, search_criteria)
        
        if nb_results > 0:
            question = fill_template(template, criteria, age_str, angle_str, tags_df, adjs_df)
            
            # Vérifier que la question est valide
            if '{' in question or len(question) < 20:
                continue
            
            # Vérifier qu'il n'y a pas de patterns mal formés
            bad_patterns = ['les de ', 'les entre ', 'les avec ', 'les et ']
            if any(bp in question.lower() for bp in bad_patterns):
                continue
            
            # Éviter les doublons
            if question not in used_patient_combos:
                used_patient_combos.add(question)
                questions.append({
                    'question': question,
                    'type': q_type,
                    'nb_criteres': nb_criteres,
                    'nb_resultats': nb_results,
                    'ids_10': ','.join(map(str, ids))
                })
                angle_count += 1
                print(f"  [{angle_count}/{target_angles}] {question[:60]}... ({nb_results} résultats)")
    
    # Phase 2 : Générer les autres questions (sans angles)
    remaining = n_questions - len(questions)
    print(f"\n[INFO] Phase 2 : Génération de {remaining} questions sans angles...")
    
    # Trier les patients par nombre de tags (décroissant) pour faciliter les questions complexes
    patients_sorted = []
    for _, patient in patients.iterrows():
        parsed = parse_patient_tags(patient['canontags'], patient['canonadjs'])
        patients_sorted.append({'patient': patient, 'parsed_tags': parsed, 'nb_tags': len(parsed)})
    patients_sorted.sort(key=lambda x: x['nb_tags'], reverse=True)
    
    # Répartition par nombre de critères - sélectionner des templates adaptés
    attempts = 0
    max_attempts = n_questions * 10  # Limite de tentatives
    
    while len(questions) < n_questions and attempts < max_attempts:
        attempts += 1
        
        # Choisir un patient au hasard
        ps = random.choice(patients_sorted)
        patient = ps['patient']
        parsed_tags = ps['parsed_tags']
        
        if len(parsed_tags) < 1:
            continue
        
        # Déterminer le nombre de critères possible
        max_tags = len(parsed_tags)
        
        # Choisir un template compatible avec le nombre de tags du patient
        # Filtrer les templates sans angle avec nb_criteres <= max_tags + 1 (pour l'âge)
        compatible_templates = templates_no_angle[
            (templates_no_angle['nb_criteres'] <= max_tags + 1)
        ]
        
        if compatible_templates.empty:
            continue
        
        template_row = compatible_templates.sample(1).iloc[0]
        template = template_row['template']
        nb_crit = template_row['nb_criteres']
        q_type = template_row['type']
        
        # Compter les placeholders dans le template
        tags_needed = len(re.findall(r'\{T\d+\}', template))
        has_age = '{AGE}' in template
        
        # Vérifier qu'on a assez de tags
        if tags_needed > len(parsed_tags):
            continue
        
        # Construire les critères
        criteria = []
        search_criteria = {'tags': []}
        
        # Sélectionner des tags du patient
        tags_to_use = random.sample(parsed_tags, min(tags_needed, len(parsed_tags)))
        
        for t in tags_to_use:
            # Décider si on ajoute un adjectif (50% de chance si disponible)
            use_adj = random.random() > 0.5 and t['adjs']
            adj = random.choice(t['adjs']) if use_adj else None
            
            criteria.append({'type': 'tag', 'tag': t['tag'], 'adj': adj})
            search_criteria['tags'].append({'tag': t['tag'], 'adj': adj})
        
        # Ajouter critère d'âge si nécessaire
        age_str = None
        if has_age:
            age_str = generate_age_criterion(patient['age'], ages_df)
            age_int = int(patient['age'])
            search_criteria['age_min'] = max(0, age_int - 5)
            search_criteria['age_max'] = age_int + 5
        
        # Compter les patients correspondants
        nb_results, ids = count_matching_patients(conn, search_criteria)
        
        if nb_results > 0:
            question = fill_template(template, criteria, age_str, None, tags_df, adjs_df)
            
            # Vérifier que la question est valide (pas de placeholders restants, pas trop courte)
            if '{' in question or len(question) < 20:
                continue
            
            # Vérifier qu'il n'y a pas de patterns mal formés comme "les de", "les entre"
            bad_patterns = ['les de ', 'les entre ', 'les avec ', 'les et ']
            if any(bp in question.lower() for bp in bad_patterns):
                continue
            
            # Éviter les doublons
            if question not in used_patient_combos:
                used_patient_combos.add(question)
                questions.append({
                    'question': question,
                    'type': q_type,
                    'nb_criteres': nb_crit,
                    'nb_resultats': nb_results,
                    'ids_10': ','.join(map(str, ids))
                })
                
                if len(questions) % 10 == 0:
                    print(f"  [{len(questions)}/{n_questions}] générées...")
    
    if len(questions) < n_questions:
        print(f"[ATTENTION] Seulement {len(questions)} questions générées sur {n_questions} demandées")
    
    return questions


def save_questions(questions: list[dict], filepath: Path) -> None:
    """Sauvegarde les questions générées en CSV."""
    df = pd.DataFrame(questions)
    df.to_csv(filepath, sep=';', index=False, encoding='utf-8-sig')
    print(f"[INFO] Fichier sauvegardé : {filepath.resolve()}")


def print_stats(questions: list[dict]) -> None:
    """Affiche les statistiques de génération."""
    df = pd.DataFrame(questions)
    
    print("\n" + "=" * 60)
    print("STATISTIQUES DE GÉNÉRATION")
    print("=" * 60)
    
    print(f"\nTotal questions : {len(questions)}")
    
    print(f"\nPar type :")
    print(df['type'].value_counts().to_string())
    
    print(f"\nPar nombre de critères :")
    print(df['nb_criteres'].value_counts().sort_index().to_string())
    
    print(f"\nNombre moyen de résultats : {df['nb_resultats'].mean():.1f}")
    print(f"Min résultats : {df['nb_resultats'].min()}")
    print(f"Max résultats : {df['nb_resultats'].max()}")
    
    print("\n" + "=" * 60)


def main():
    """Point d'entrée principal."""
    print(f"{__pgm__} V{__version__} - {__date__}")
    print("=" * 60)
    
    # Vérifier les arguments
    if len(sys.argv) < 3:
        print(f"Usage : python {__pgm__} base.db N")
        print("  base.db : chemin vers la base de données SQLite")
        print("  N       : nombre de questions à générer")
        sys.exit(1)
    
    db_path = Path(sys.argv[1])
    n_questions = int(sys.argv[2])
    
    print(f"[INFO] Base de données : {db_path.resolve()}")
    print(f"[INFO] Questions à générer : {n_questions}")
    
    script_dir = get_script_dir()
    
    # Chemins des fichiers
    templates_path = script_dir / "templatequestion.csv"
    tagsadjs_path = script_dir / "tagsadjs.xlsx"
    ages_path = script_dir / "ages.csv"
    angles_path = script_dir / "angles.csv"
    
    # Nom du fichier de sortie basé sur le nom de la base
    db_name = db_path.stem  # ex: "base100" -> "base100"
    output_path = script_dir / f"testspats{db_name.replace('base', '')}.csv"  # ex: testspats100.csv
    
    # Vérifier l'existence des fichiers
    for path in [db_path, templates_path, tagsadjs_path, ages_path, angles_path]:
        if not path.exists():
            print(f"[ERREUR] Fichier introuvable : {path.resolve()}")
            sys.exit(1)
        print(f"[INFO] Fichier trouvé : {path.resolve()}")
    
    # Charger les données
    print("\n[INFO] Chargement des données...")
    templates = load_templates(templates_path)
    print(f"  - Templates : {len(templates)}")
    
    tags_df, adjs_df = load_tagsadjs(tagsadjs_path)
    print(f"  - Tags : {len(tags_df)}")
    print(f"  - Adjectifs : {len(adjs_df)}")
    
    ages_df = load_ages(ages_path)
    print(f"  - Âges : {len(ages_df)}")
    
    angles_df = load_angles(angles_path)
    print(f"  - Angles : {len(angles_df)}")
    
    # Connexion à la base
    conn = connect_db(db_path)
    
    # Générer les questions
    questions = generate_questions(
        conn, templates, tags_df, adjs_df, angles_df, ages_df, n_questions
    )
    
    conn.close()
    
    # Afficher les statistiques
    print_stats(questions)
    
    # Sauvegarder
    save_questions(questions, output_path)
    
    # Afficher quelques exemples
    print("\n[INFO] Exemples de questions générées :")
    print("-" * 60)
    for q in random.sample(questions, min(10, len(questions))):
        print(f"  [{q['type']:5s}, {q['nb_criteres']} crit, {q['nb_resultats']:3d} rés] {q['question'][:70]}")
    
    print("\n" + "=" * 60)
    print("[OK] Génération terminée avec succès !")
    print("=" * 60)


if __name__ == "__main__":
    main()
