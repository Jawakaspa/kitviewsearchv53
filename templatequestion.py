# templatequestion.py V1.0.0 - 19/12/2025 16:45:04
__pgm__ = "templatequestion.py"
__version__ = "1.0.0"
__date__ = "19/12/2025 16:45:04"

"""
templatequestion.py - Générateur de templates de questions style "cadavre exquis"

Génère 100 templates de questions pour la recherche de patients orthodontiques.
Répartition :
- 30 COUNT / 70 LIST
- 10 avec angles (ANB, SNA, SNB)
- 25 templates à 1 critère
- 25 templates à 2 critères  
- 25 templates à 3 critères
- 25 templates à 4 critères

Fichiers d'entrée :
- tagsadjs.xlsx : pathologies et adjectifs
- ages.csv : critères d'âge/sexe
- angles.csv : critères d'angles céphalométriques
- cadavreexquis.csv : composants de phrases

Fichier de sortie :
- templatequestion.csv : 100 templates générés
"""

import pandas as pd
import random
import os
import sys
from pathlib import Path


def get_script_dir() -> Path:
    """Retourne le répertoire du script."""
    return Path(__file__).parent.resolve()


def load_csv_with_comments(filepath: Path) -> pd.DataFrame:
    """Charge un CSV en ignorant les lignes de commentaires (#)."""
    with open(filepath, 'r', encoding='utf-8-sig') as f:
        lines = [line for line in f if not line.strip().startswith('#')]
    
    from io import StringIO
    return pd.read_csv(StringIO(''.join(lines)), sep=';')


def load_tagsadjs(filepath: Path) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Charge tagsadjs.xlsx et retourne deux DataFrames : tags et adjectifs.
    Ajoute la colonne 'article' aux tags basée sur le genre (Xgn).
    """
    df = pd.read_excel(filepath, engine='openpyxl')
    
    # Séparer tags (type='p') et adjectifs (type='a')
    tags = df[df['type'] == 'p'].copy()
    adjs = df[df['type'] == 'a'].copy()
    
    # Ajouter la colonne article aux tags basée sur Xgn
    def get_article(xgn):
        if pd.isna(xgn):
            return "un"
        xgn = str(xgn).lower().strip()
        if xgn == 'f':
            return "une"
        elif xgn == 'm':
            return "un"
        elif xgn == 'fp':
            return "des"
        elif xgn == 'mp':
            return "des"
        else:
            return "un"
    
    tags['article'] = tags['Xgn'].apply(get_article)
    
    return tags, adjs


def load_ages(filepath: Path) -> pd.DataFrame:
    """Charge ages.csv."""
    return load_csv_with_comments(filepath)


def load_angles(filepath: Path) -> pd.DataFrame:
    """Charge angles.csv."""
    return load_csv_with_comments(filepath)


def load_cadavreexquis(filepath: Path) -> dict:
    """
    Charge cadavreexquis.csv et retourne un dictionnaire par catégorie.
    """
    df = load_csv_with_comments(filepath)
    
    result = {}
    for categorie in df['categorie'].unique():
        result[categorie] = df[df['categorie'] == categorie]['texte'].tolist()
    
    return result


def get_adj_for_tag(tag_row: pd.Series, adjs_df: pd.DataFrame) -> tuple[str, str] | None:
    """
    Retourne un adjectif compatible avec le tag et sa forme accordée.
    Retourne (adj_canon, adj_accorde) ou None si pas d'adjectif disponible.
    """
    if pd.isna(tag_row.get('adjs')) or str(tag_row.get('adjs')).strip() == '':
        return None
    
    # Liste des adjectifs possibles pour ce tag
    possible_adjs = [a.strip() for a in str(tag_row['adjs']).split(',')]
    
    # Genre du tag
    xgn = str(tag_row.get('Xgn', 'm')).lower().strip() if pd.notna(tag_row.get('Xgn')) else 'm'
    
    # Choisir un adjectif au hasard
    adj_canon = random.choice(possible_adjs)
    
    # Chercher l'adjectif dans la table des adjectifs
    adj_row = adjs_df[adjs_df['canon'].str.lower().str.strip() == adj_canon.lower().strip()]
    
    if adj_row.empty:
        # Adjectif non trouvé, retourner tel quel
        return (adj_canon, adj_canon)
    
    adj_row = adj_row.iloc[0]
    
    # Accorder l'adjectif selon le genre du tag
    if xgn == 'f' and pd.notna(adj_row.get('f')):
        return (adj_canon, adj_row['f'])
    elif xgn == 'm' and pd.notna(adj_row.get('m')):
        return (adj_canon, adj_row['m'])
    elif xgn == 'fp' and pd.notna(adj_row.get('fp')):
        return (adj_canon, adj_row['fp'])
    elif xgn == 'mp' and pd.notna(adj_row.get('mp')):
        return (adj_canon, adj_row['mp'])
    else:
        return (adj_canon, adj_canon)


def get_random_fin(composants: dict) -> str:
    """Retourne une fin de phrase aléatoire, en gérant les valeurs vides."""
    fins = [f for f in composants.get('fin', ['?']) if f and str(f).strip() and str(f) != 'nan']
    if not fins:
        return ""
    return random.choice(fins)


def generate_template_1_critere(
    composants: dict,
    tags: pd.DataFrame,
    adjs: pd.DataFrame,
    ages: pd.DataFrame,
    is_count: bool,
    has_angle: bool
) -> tuple[str, int]:
    """
    Génère un template avec 1 critère.
    Retourne (template, nb_criteres).
    """
    # Choisir le début
    if is_count:
        debut = random.choice(composants['debut_count'])
        # COUNT : le début contient déjà la liaison
        if has_angle:
            template = f"{debut} {{ANG}}"
        else:
            choice = random.choice(['tag', 'tag_adj', 'age'])
            if choice == 'age':
                template = f"{debut} {{AGE}}"
            elif choice == 'tag_adj':
                template = f"{debut} {{T1}} {{A1}}"
            else:
                template = f"{debut} {{T1}}"
    else:
        debut = random.choice(composants['debut_list'])
        # LIST : ajouter une liaison appropriée
        if has_angle:
            template = f"{debut} patients avec {{ANG}}"
        else:
            choice = random.choice(['tag', 'tag_adj', 'age'])
            if choice == 'age':
                template = f"{debut} {{AGE}}"
            elif choice == 'tag_adj':
                template = f"{debut} patients avec {{T1}} {{A1}}"
            else:
                template = f"{debut} patients avec {{T1}}"
    
    nb_criteres = 1
    
    # Ajouter fin
    fin = get_random_fin(composants)
    if fin:
        template = f"{template}{fin}"
    
    return template, nb_criteres


def generate_template_2_criteres(
    composants: dict,
    tags: pd.DataFrame,
    adjs: pd.DataFrame,
    ages: pd.DataFrame,
    is_count: bool,
    has_angle: bool
) -> tuple[str, int]:
    """
    Génère un template avec 2 critères (au moins 1 tag avec adjectif).
    Retourne (template, nb_criteres).
    """
    connecteur = random.choice(composants['connecteur'])
    
    # Structures possibles : TAG+ADJ + TAG, TAG+ADJ + AGE, AGE + TAG+ADJ, TAG+ADJ + ANG
    structures = [
        ('tag_adj', 'tag'),
        ('tag_adj', 'age'),
        ('age', 'tag_adj'),
        ('tag_adj', 'tag_adj'),
    ]
    
    if has_angle:
        structures = [('tag_adj', 'angle'), ('angle', 'tag_adj')]
    
    struct = random.choice(structures)
    
    parts = []
    tag_num = 1
    
    for crit_type in struct:
        if crit_type == 'tag_adj':
            parts.append(f"{{T{tag_num}}} {{A{tag_num}}}")
            tag_num += 1
        elif crit_type == 'tag':
            parts.append(f"{{T{tag_num}}}")
            tag_num += 1
        elif crit_type == 'age':
            parts.append("{AGE}")
        elif crit_type == 'angle':
            parts.append("{ANG}")
    
    # Construire le template selon le type
    if is_count:
        debut = random.choice(composants['debut_count'])
        template = f"{debut} {parts[0]} {connecteur} {parts[1]}"
    else:
        debut = random.choice(composants['debut_list'])
        liaison = random.choice(composants['liaison'])
        template = f"{debut} {liaison} {parts[0]} {connecteur} {parts[1]}"
    
    fin = get_random_fin(composants)
    if fin:
        template = f"{template}{fin}"
    
    return template, 2


def generate_template_3_criteres(
    composants: dict,
    tags: pd.DataFrame,
    adjs: pd.DataFrame,
    ages: pd.DataFrame,
    is_count: bool,
    has_angle: bool
) -> tuple[str, int]:
    """
    Génère un template avec 3 critères (au moins 1 tag avec adjectif).
    Retourne (template, nb_criteres).
    """
    connecteur1 = random.choice(composants['connecteur'])
    connecteur2 = random.choice(composants['connecteur'])
    
    # Structures avec au moins 1 tag+adj
    structures = [
        ('tag_adj', 'tag', 'age'),
        ('tag_adj', 'tag_adj', 'tag'),
        ('age', 'tag_adj', 'tag'),
        ('tag_adj', 'age', 'tag'),
        ('tag', 'tag_adj', 'tag'),
    ]
    
    if has_angle:
        structures = [
            ('tag_adj', 'tag', 'angle'),
            ('angle', 'tag_adj', 'tag'),
            ('tag_adj', 'angle', 'age'),
        ]
    
    struct = random.choice(structures)
    
    parts = []
    tag_num = 1
    
    for crit_type in struct:
        if crit_type == 'tag_adj':
            parts.append(f"{{T{tag_num}}} {{A{tag_num}}}")
            tag_num += 1
        elif crit_type == 'tag':
            parts.append(f"{{T{tag_num}}}")
            tag_num += 1
        elif crit_type == 'age':
            parts.append("{AGE}")
        elif crit_type == 'angle':
            parts.append("{ANG}")
    
    # Construire le template selon le type
    if is_count:
        debut = random.choice(composants['debut_count'])
        template = f"{debut} {parts[0]} {connecteur1} {parts[1]} {connecteur2} {parts[2]}"
    else:
        debut = random.choice(composants['debut_list'])
        liaison = random.choice(composants['liaison'])
        template = f"{debut} {liaison} {parts[0]} {connecteur1} {parts[1]} {connecteur2} {parts[2]}"
    
    fin = get_random_fin(composants)
    if fin:
        template = f"{template}{fin}"
    
    return template, 3


def generate_template_4_criteres(
    composants: dict,
    tags: pd.DataFrame,
    adjs: pd.DataFrame,
    ages: pd.DataFrame,
    is_count: bool,
    has_angle: bool
) -> tuple[str, int]:
    """
    Génère un template avec 4 critères (au moins 1 tag avec adjectif).
    Retourne (template, nb_criteres).
    """
    connecteur1 = random.choice(composants['connecteur'])
    connecteur2 = random.choice(composants['connecteur'])
    connecteur3 = random.choice(composants['connecteur'])
    
    # Structures avec au moins 1 tag+adj
    structures = [
        ('tag_adj', 'tag', 'tag', 'age'),
        ('tag_adj', 'tag_adj', 'tag', 'tag'),
        ('age', 'tag_adj', 'tag', 'tag'),
        ('tag', 'tag_adj', 'age', 'tag'),
        ('tag_adj', 'tag', 'tag_adj', 'age'),
    ]
    
    if has_angle:
        structures = [
            ('tag_adj', 'tag', 'tag', 'angle'),
            ('angle', 'tag_adj', 'tag', 'tag'),
        ]
    
    struct = random.choice(structures)
    
    parts = []
    tag_num = 1
    
    for crit_type in struct:
        if crit_type == 'tag_adj':
            parts.append(f"{{T{tag_num}}} {{A{tag_num}}}")
            tag_num += 1
        elif crit_type == 'tag':
            parts.append(f"{{T{tag_num}}}")
            tag_num += 1
        elif crit_type == 'age':
            parts.append("{AGE}")
        elif crit_type == 'angle':
            parts.append("{ANG}")
    
    # Construire le template selon le type
    if is_count:
        debut = random.choice(composants['debut_count'])
        template = f"{debut} {parts[0]} {connecteur1} {parts[1]} {connecteur2} {parts[2]} {connecteur3} {parts[3]}"
    else:
        debut = random.choice(composants['debut_list'])
        liaison = random.choice(composants['liaison'])
        template = f"{debut} {liaison} {parts[0]} {connecteur1} {parts[1]} {connecteur2} {parts[2]} {connecteur3} {parts[3]}"
    
    fin = get_random_fin(composants)
    if fin:
        template = f"{template}{fin}"
    
    return template, 4


def generate_all_templates(
    composants: dict,
    tags: pd.DataFrame,
    adjs: pd.DataFrame,
    ages: pd.DataFrame
) -> list[dict]:
    """
    Génère les 100 templates selon la répartition demandée.
    """
    templates = []
    
    # Répartition COUNT/LIST (30/70) et angles (10 répartis aléatoirement)
    count_indices = set(random.sample(range(100), 30))
    angle_indices = set(random.sample(range(100), 10))
    
    # Générateurs par tranche
    generators = [
        (range(0, 25), generate_template_1_critere),    # 1 critère
        (range(25, 50), generate_template_2_criteres),  # 2 critères
        (range(50, 75), generate_template_3_criteres),  # 3 critères
        (range(75, 100), generate_template_4_criteres), # 4 critères
    ]
    
    for tranche, generator in generators:
        for i in tranche:
            is_count = i in count_indices
            has_angle = i in angle_indices
            
            template_str, nb_criteres = generator(
                composants, tags, adjs, ages, is_count, has_angle
            )
            
            templates.append({
                'id': i + 1,
                'nb_criteres': nb_criteres,
                'type': 'COUNT' if is_count else 'LIST',
                'has_angle': 'OUI' if has_angle else 'NON',
                'template': template_str
            })
    
    return templates


def clean_template(template: str) -> str:
    """Nettoie le template : espaces multiples, ponctuation."""
    import re
    # Supprimer les espaces multiples
    template = re.sub(r'\s+', ' ', template)
    # Supprimer espace avant ponctuation
    template = re.sub(r'\s+([?.,!])', r'\1', template)
    # Supprimer espace après apostrophe
    template = re.sub(r"'\s+", "'", template)
    return template.strip()


def save_templates(templates: list[dict], filepath: Path) -> None:
    """Sauvegarde les templates en CSV UTF-8-SIG."""
    df = pd.DataFrame(templates)
    
    # Nettoyer les templates
    df['template'] = df['template'].apply(clean_template)
    
    # Sauvegarder avec BOM
    df.to_csv(filepath, sep=';', index=False, encoding='utf-8-sig')
    print(f"[INFO] Fichier sauvegardé : {filepath.resolve()}")


def save_tagsadjs_enrichi(tags: pd.DataFrame, adjs: pd.DataFrame, filepath: Path) -> None:
    """
    Sauvegarde le fichier tagsadjs enrichi avec la colonne article.
    """
    # Recombiner tags et adjs
    df = pd.concat([tags, adjs], ignore_index=True)
    
    # Sauvegarder en xlsx
    df.to_excel(filepath, index=False, engine='openpyxl')
    print(f"[INFO] Fichier enrichi sauvegardé : {filepath.resolve()}")


def print_stats(templates: list[dict]) -> None:
    """Affiche les statistiques de génération."""
    df = pd.DataFrame(templates)
    
    print("\n" + "=" * 60)
    print("STATISTIQUES DE GÉNÉRATION")
    print("=" * 60)
    
    print(f"\nTotal templates : {len(templates)}")
    
    print(f"\nPar type :")
    print(df['type'].value_counts().to_string())
    
    print(f"\nAvec angle :")
    print(df['has_angle'].value_counts().to_string())
    
    print(f"\nPar nombre de critères :")
    print(df['nb_criteres'].value_counts().sort_index().to_string())
    
    print("\n" + "=" * 60)


def main():
    """Point d'entrée principal."""
    print(f"{__pgm__} V{__version__} - {__date__}")
    print("=" * 60)
    
    script_dir = get_script_dir()
    
    # Chemins des fichiers
    tagsadjs_path = script_dir / "tagsadjs.xlsx"
    ages_path = script_dir / "ages.csv"
    angles_path = script_dir / "angles.csv"
    cadavre_path = script_dir / "cadavreexquis.csv"
    output_path = script_dir / "templatequestion.csv"
    enrichi_path = script_dir / "tagsadjs_enrichi.xlsx"
    
    # Vérifier l'existence des fichiers
    for path in [tagsadjs_path, ages_path, angles_path, cadavre_path]:
        if not path.exists():
            print(f"[ERREUR] Fichier introuvable : {path.resolve()}")
            sys.exit(1)
        print(f"[INFO] Fichier trouvé : {path.resolve()}")
    
    # Charger les données
    print("\n[INFO] Chargement des données...")
    tags, adjs = load_tagsadjs(tagsadjs_path)
    print(f"  - Tags : {len(tags)} pathologies")
    print(f"  - Adjectifs : {len(adjs)} adjectifs")
    
    ages = load_ages(ages_path)
    print(f"  - Âges : {len(ages)} expressions")
    
    angles = load_angles(angles_path)
    print(f"  - Angles : {len(angles)} patterns")
    
    composants = load_cadavreexquis(cadavre_path)
    for cat, items in composants.items():
        print(f"  - {cat} : {len(items)} éléments")
    
    # Générer les templates
    print("\n[INFO] Génération des 100 templates...")
    templates = generate_all_templates(composants, tags, adjs, ages)
    
    # Afficher les statistiques
    print_stats(templates)
    
    # Sauvegarder
    print("\n[INFO] Sauvegarde des fichiers...")
    save_templates(templates, output_path)
    save_tagsadjs_enrichi(tags, adjs, enrichi_path)
    
    # Afficher quelques exemples
    print("\n[INFO] Exemples de templates générés :")
    print("-" * 60)
    for t in random.sample(templates, min(10, len(templates))):
        print(f"  [{t['id']:3d}] ({t['type']:5s}, {t['nb_criteres']} crit) {t['template']}")
    
    print("\n" + "=" * 60)
    print("[OK] Génération terminée avec succès !")
    print("=" * 60)


if __name__ == "__main__":
    main()
