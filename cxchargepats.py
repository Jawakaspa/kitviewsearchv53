# cxchargepats.py V1.0.3 - 24/12/2025 17:39:09
__pgm__ = "cxchargepats.py"
__version__ = "1.0.3"
__date__ = "24/12/2025 17:39:09"

"""
Charge des patients depuis un fichier CSV simplifié vers une base SQLite.

Fonctionnalités :
- Génération automatique de oripathologies à partir de canontags + canonadjs
- Gestion des pathologies avec préfixes progressifs
- Structure simplifiée (11 colonnes dans la table patients)

Usage:
    python cxchargepats.py <fichier_patients.csv> <N>
    
Exemples:
    python cxchargepats.py pats100.csv 99       # Cherche dans data/
    python cxchargepats.py data/pats100.csv 99  # Chemin relatif
    python cxchargepats.py c:/data/pats.csv 50  # Chemin absolu
"""

import sys
import os
import sqlite3
import time
import importlib.util
from pathlib import Path


# =============================================================================
# FONCTIONS UTILITAIRES
# =============================================================================

def print_header():
    """Affiche le cartouche du programme."""
    print(f"{__pgm__} V{__version__} - {__date__}")
    print()


def find_csv_file(csv_arg):
    """
    Recherche le fichier CSV selon l'ordre de priorité.
    
    Args:
        csv_arg: Argument passé en ligne de commande
        
    Returns:
        Path vers le fichier trouvé ou None
    """
    # 1. Chemin absolu
    if os.path.isabs(csv_arg):
        p = Path(csv_arg)
        if p.exists():
            return p
        return None
    
    # 2. Chemin relatif depuis le répertoire courant
    p = Path(csv_arg)
    if p.exists():
        return p
    
    # 3. Recherche dans data/
    script_dir = Path(__file__).parent
    p = script_dir / "data" / csv_arg
    if p.exists():
        return p
    
    return None


def load_standardise_module():
    """
    Charge dynamiquement le module standardise.py.
    
    Recherche dans l'ordre :
    1. Répertoire courant
    2. Répertoire parent
    
    Returns:
        Module standardise ou None si non trouvé
    """
    script_dir = Path(__file__).parent
    
    # Chemins à tester
    paths_to_try = [
        script_dir / "standardise.py",
        script_dir.parent / "standardise.py",
    ]
    
    for module_path in paths_to_try:
        if module_path.exists():
            spec = importlib.util.spec_from_file_location("standardise", module_path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            print(f"[INFO] Module standardise chargé depuis : {module_path.absolute()}")
            return module
    
    return None


# Chargement global du module standardise
_standardise_module = None


def standardise(text):
    """
    Wrapper pour la fonction standardise du module externe.
    
    Args:
        text: Texte à standardiser
        
    Returns:
        Texte standardisé
    """
    global _standardise_module
    
    if _standardise_module is None:
        _standardise_module = load_standardise_module()
        if _standardise_module is None:
            print("[ERREUR] Module standardise.py introuvable !")
            sys.exit(1)
    
    return _standardise_module.standardise(text)


def parse_date(date_str):
    """
    Parse une date JJ/MM/AAAA ou YYYY-MM-DD vers format ISO.
    
    Args:
        date_str: Date en format JJ/MM/AAAA ou YYYY-MM-DD
        
    Returns:
        Date au format YYYY-MM-DD ou chaîne vide si invalide
    """
    if not date_str or date_str.strip() == "":
        return ""
    
    date_str = date_str.strip()
    
    # Format JJ/MM/AAAA
    if "/" in date_str:
        parts = date_str.split("/")
        if len(parts) == 3:
            try:
                jour = int(parts[0])
                mois = int(parts[1])
                annee = int(parts[2])
                return f"{annee:04d}-{mois:02d}-{jour:02d}"
            except ValueError:
                return ""
    
    # Format YYYY-MM-DD (déjà ISO)
    if "-" in date_str and len(date_str) == 10:
        return date_str
    
    return ""


def parse_float(value, default=0.0):
    """
    Parse un float avec gestion d'erreur.
    
    Args:
        value: Valeur à parser
        default: Valeur par défaut si erreur
        
    Returns:
        Float parsé ou valeur par défaut
    """
    if value is None or str(value).strip() == "":
        return default
    try:
        # Gérer la virgule française
        return float(str(value).replace(",", "."))
    except (ValueError, TypeError):
        return default


def parse_int(value, default=0):
    """
    Parse un int avec gestion d'erreur.
    
    Args:
        value: Valeur à parser
        default: Valeur par défaut si erreur
        
    Returns:
        Int parsé ou valeur par défaut
    """
    if value is None or str(value).strip() == "":
        return default
    try:
        return int(float(str(value).replace(",", ".")))
    except (ValueError, TypeError):
        return default


# =============================================================================
# GÉNÉRATION DE ORIPATHOLOGIES
# =============================================================================

def generate_oripathologies(canontags, canonadjs):
    """
    Génère oripathologies à partir de canontags et canonadjs.
    
    Pour chaque position i :
    - Prend le tag[i]
    - Prend les adjectifs correspondants (séparés par |)
    - Trie les adjectifs alphabétiquement
    - Concatène : tag + " " + adjs triés
    
    Args:
        canontags: Tags séparés par virgule (ex: "béance,Bruxisme")
        canonadjs: Adjectifs séparés par virgule, multiples par | (ex: "latérale,nocturne|sévère")
        
    Returns:
        oripathologies générées (ex: "béance latérale,Bruxisme nocturne sévère")
    """
    if not canontags or canontags.strip() == "":
        return ""
    
    tags = [t.strip() for t in canontags.split(",") if t.strip()]
    
    # Gérer le cas où canonadjs est vide ou absent
    if not canonadjs or canonadjs.strip() == "":
        adjs_list = [""] * len(tags)
    else:
        adjs_list = [a.strip() for a in canonadjs.split(",")]
    
    # Compléter avec des chaînes vides si nécessaire
    while len(adjs_list) < len(tags):
        adjs_list.append("")
    
    pathologies = []
    
    for i, tag in enumerate(tags):
        if i < len(adjs_list) and adjs_list[i]:
            # Séparer les adjectifs multiples par |
            adjs = [a.strip() for a in adjs_list[i].split("|") if a.strip()]
            # Trier alphabétiquement
            adjs.sort()
            # Concaténer
            pathologie = tag + " " + " ".join(adjs)
        else:
            pathologie = tag
        
        pathologies.append(pathologie.strip())
    
    return ",".join(pathologies)


# =============================================================================
# GESTION BASE DE DONNÉES
# =============================================================================

def create_db_and_tables(db_path):
    """
    Crée la base de données et les tables.
    
    Args:
        db_path: Chemin vers la base de données
        
    Returns:
        Connexion SQLite
    """
    # Supprimer la base existante si elle existe
    if os.path.exists(db_path):
        os.remove(db_path)
        print(f"[INFO] Base existante supprimée : {db_path}")
    
    # Créer le répertoire si nécessaire
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Table patients (11 colonnes)
    cursor.execute("""
        CREATE TABLE patients (
            id INTEGER PRIMARY KEY,
            canontags TEXT,
            canonadjs TEXT,
            sexe TEXT,
            age DECIMAL(5, 3),
            datenaissance DATE,
            prenom TEXT,
            nom TEXT,
            idportrait TEXT,
            oripathologies TEXT,
            pathologies TEXT
        )
    """)
    
    # Table pathologies
    cursor.execute("""
        CREATE TABLE pathologies (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            pathologie TEXT UNIQUE NOT NULL
        )
    """)
    
    # Table de jointure patients_pathologies
    cursor.execute("""
        CREATE TABLE patients_pathologies (
            patient_id INTEGER NOT NULL,
            pathologie_id INTEGER NOT NULL,
            PRIMARY KEY (patient_id, pathologie_id),
            FOREIGN KEY (patient_id) REFERENCES patients(id) ON DELETE CASCADE,
            FOREIGN KEY (pathologie_id) REFERENCES pathologies(id) ON DELETE CASCADE
        )
    """)
    
    conn.commit()
    print(f"[INFO] Base créée : {db_path}")
    
    return conn


def create_indexes(conn):
    """
    Crée les index de performance.
    
    Args:
        conn: Connexion SQLite
    """
    cursor = conn.cursor()
    
    indexes = [
        "CREATE INDEX idx_patients_sexe ON patients(sexe)",
        "CREATE INDEX idx_patients_age ON patients(age)",
        "CREATE INDEX idx_patients_datenaissance ON patients(datenaissance)",
        "CREATE INDEX idx_patients_pathologies_patient_id ON patients_pathologies(patient_id)",
        "CREATE INDEX idx_patients_pathologies_pathologie_id ON patients_pathologies(pathologie_id)",
        "CREATE INDEX idx_pathologies_nom ON pathologies(pathologie)",
    ]
    
    for idx_sql in indexes:
        cursor.execute(idx_sql)
    
    conn.commit()
    print(f"[INFO] {len(indexes)} index créés")


# =============================================================================
# GESTION DES PATHOLOGIES
# =============================================================================

def get_or_create_pathology_id(cursor, pathology_name):
    """
    Récupère ou crée une pathologie et retourne son ID.
    
    Args:
        cursor: Curseur SQLite
        pathology_name: Nom de la pathologie (normalisé)
        
    Returns:
        ID de la pathologie
    """
    cursor.execute("SELECT id FROM pathologies WHERE pathologie = ?", (pathology_name,))
    row = cursor.fetchone()
    
    if row:
        return row[0]
    
    cursor.execute("INSERT INTO pathologies (pathologie) VALUES (?)", (pathology_name,))
    return cursor.lastrowid


def insert_pathology_with_prefixes(cursor, patient_id, pathology_name, linked_pathologies):
    """
    Insère une pathologie ET tous ses préfixes progressifs, avec liaisons patient.
    
    Args:
        cursor: Curseur SQLite
        patient_id: ID du patient
        pathology_name: Nom de la pathologie normalisée
        linked_pathologies: Set pour collecter toutes les pathologies liées
    """
    words = pathology_name.split()
    
    # Générer tous les préfixes progressifs
    for i in range(1, len(words) + 1):
        prefix = " ".join(words[:i])
        
        # Récupérer ou créer l'ID de ce préfixe
        pathology_id = get_or_create_pathology_id(cursor, prefix)
        
        # Créer la liaison patient-pathologie (ignore si existe déjà)
        try:
            cursor.execute(
                "INSERT OR IGNORE INTO patients_pathologies (patient_id, pathologie_id) VALUES (?, ?)",
                (patient_id, pathology_id)
            )
        except sqlite3.IntegrityError:
            pass
        
        # Ajouter au set des pathologies liées
        linked_pathologies.add(prefix)


# =============================================================================
# CHARGEMENT DES PATIENTS
# =============================================================================

def detect_encoding(file_path):
    """
    Détecte l'encodage d'un fichier.
    
    Args:
        file_path: Chemin du fichier
        
    Returns:
        Tuple (encodage, contenu)
    """
    encodings = ['utf-8-sig', 'utf-8', 'cp1252', 'iso-8859-1']
    
    for encoding in encodings:
        try:
            with open(file_path, 'r', encoding=encoding) as f:
                content = f.read()
                return encoding, content
        except (UnicodeDecodeError, UnicodeError):
            continue
    
    raise ValueError(f"Impossible de décoder le fichier : {file_path}")


def progress_bar(current, total, width=40):
    """
    Génère une barre de progression.
    
    Args:
        current: Valeur actuelle
        total: Valeur totale
        width: Largeur de la barre
        
    Returns:
        Chaîne de la barre de progression
    """
    if total == 0:
        return ""
    
    percent = current / total
    filled = int(width * percent)
    bar = "█" * filled + "░" * (width - filled)
    
    return f"[{bar}] {percent*100:.0f}% - Ligne {current}/{total}"


def charge_patients(conn, csv_file, N):
    """
    Charge les patients depuis un fichier CSV.
    
    Args:
        conn: Connexion SQLite
        csv_file: Chemin du fichier CSV
        N: Nombre de patients à charger
        
    Returns:
        Tuple (patients_chargés, pathologies_uniques, liaisons_total)
    """
    cursor = conn.cursor()
    
    # Détecter l'encodage
    encoding, content = detect_encoding(csv_file)
    
    if encoding != 'utf-8-sig':
        print(f"[WARNING] Encodage détecté : {encoding} (attendu : utf-8-sig)")
    else:
        print(f"[INFO] Encodage : {encoding}")
    
    lines = content.split('\n')
    
    # Filtrer les lignes de commentaires et vides
    data_lines = []
    header_line = None
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
        if line.startswith('#'):
            continue
        if header_line is None:
            header_line = line
        else:
            data_lines.append(line)
    
    if not header_line:
        print("[ERREUR] Pas d'en-tête trouvée dans le CSV")
        return 0, 0, 0
    
    # Valider les colonnes
    headers = [h.strip() for h in header_line.split(';')]
    expected_headers = ['id', 'canontags', 'canonadjs', 'sexe', 'age', 'datenaissance', 'prenom', 'nom', 'idportrait']
    
    print(f"[INFO] Colonnes trouvées : {headers}")
    print(f"[INFO] Colonnes attendues : {expected_headers}")
    
    if len(headers) != len(expected_headers):
        print(f"[ERREUR] Nombre de colonnes incorrect : {len(headers)} (attendu : {len(expected_headers)})")
        return 0, 0, 0
    
    # Créer un mapping nom -> index
    col_idx = {name: i for i, name in enumerate(headers)}
    
    # Vérifier que toutes les colonnes attendues sont présentes
    missing = [h for h in expected_headers if h not in col_idx]
    if missing:
        print(f"[ERREUR] Colonnes manquantes : {missing}")
        return 0, 0, 0
    
    # Limiter au nombre demandé
    total_to_process = min(N, len(data_lines))
    print(f"[INFO] Patients à charger : {total_to_process} (demandé : {N}, disponibles : {len(data_lines)})")
    print()
    
    patients_loaded = 0
    liaisons_total = 0
    
    start_time = time.time()
    
    for i, line in enumerate(data_lines[:total_to_process]):
        # Afficher la progression
        print(f"\r{progress_bar(i + 1, total_to_process)}", end="", flush=True)
        
        fields = line.split(';')
        
        if len(fields) != len(expected_headers):
            print(f"\n[WARNING] Ligne {i+1} ignorée : {len(fields)} colonnes au lieu de {len(expected_headers)}")
            continue
        
        # Extraire les valeurs par nom de colonne
        patient_id = parse_int(fields[col_idx['id']])
        canontags = fields[col_idx['canontags']].strip()
        canonadjs = fields[col_idx['canonadjs']].strip()
        sexe = fields[col_idx['sexe']].strip()
        age = parse_float(fields[col_idx['age']])
        datenaissance = parse_date(fields[col_idx['datenaissance']])
        prenom = fields[col_idx['prenom']].strip()
        nom = fields[col_idx['nom']].strip()
        idportrait = fields[col_idx['idportrait']].strip()
        
        # Générer oripathologies
        oripathologies = generate_oripathologies(canontags, canonadjs)
        
        # Set pour collecter toutes les pathologies liées à ce patient
        linked_pathologies = set()
        
        # Traiter chaque pathologie de oripathologies
        if oripathologies:
            for patho in oripathologies.split(','):
                patho = patho.strip()
                if patho:
                    # Normaliser
                    patho_normalized = standardise(patho)
                    if patho_normalized:
                        # Insérer avec tous les préfixes
                        insert_pathology_with_prefixes(cursor, patient_id, patho_normalized, linked_pathologies)
        
        # Reconstituer le champ pathologies (liste triée sans doublons)
        pathologies_list = sorted(linked_pathologies)
        pathologies_str = ", ".join(pathologies_list)
        
        liaisons_total += len(linked_pathologies)
        
        # Insérer le patient
        cursor.execute("""
            INSERT INTO patients (id, canontags, canonadjs, sexe, age, datenaissance, prenom, nom, idportrait, oripathologies, pathologies)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (patient_id, canontags, canonadjs, sexe, age, datenaissance, prenom, nom, idportrait, oripathologies, pathologies_str))
        
        conn.commit()
        patients_loaded += 1
    
    print()  # Nouvelle ligne après la barre de progression
    
    # Compter les pathologies uniques
    cursor.execute("SELECT COUNT(*) FROM pathologies")
    pathologies_count = cursor.fetchone()[0]
    
    elapsed = time.time() - start_time
    
    # Afficher les statistiques
    print()
    print("=" * 60)
    print("Chargement terminé")
    print(f"  ✔ Patients chargés : {patients_loaded}/{total_to_process}")
    print(f"  ✔ Pathologies uniques (avec préfixes) : {pathologies_count}")
    print(f"  ✔ Liaisons patient-pathologie : {liaisons_total}")
    print(f"  ⏱ Durée : {elapsed:.2f}s")
    print("=" * 60)
    
    # Debug : afficher quelques exemples de pathologies
    print()
    print("[DEBUG] Exemples de pathologies dans la base :")
    cursor.execute("SELECT pathologie FROM pathologies ORDER BY pathologie LIMIT 10")
    for row in cursor.fetchall():
        print(f"  - '{row[0]}'")
    
    return patients_loaded, pathologies_count, liaisons_total


# =============================================================================
# MAIN
# =============================================================================

def main():
    """Point d'entrée principal."""
    print_header()
    
    # Vérifier les arguments
    if len(sys.argv) != 3:
        print("Usage: python cxchargepats.py <fichier_patients.csv> <N>")
        print()
        print("Exemples:")
        print("  python cxchargepats.py pats100.csv 99       # Cherche dans data/")
        print("  python cxchargepats.py data/pats100.csv 99  # Chemin relatif")
        print("  python cxchargepats.py c:/data/pats.csv 50  # Chemin absolu")
        sys.exit(1)
    
    csv_arg = sys.argv[1]
    try:
        N = int(sys.argv[2])
    except ValueError:
        print(f"[ERREUR] N doit être un entier : {sys.argv[2]}")
        sys.exit(1)
    
    # Rechercher le fichier CSV
    csv_file = find_csv_file(csv_arg)
    if csv_file is None:
        print(f"[ERREUR] Fichier CSV introuvable : {csv_arg}")
        print(f"  Recherché dans :")
        print(f"    - Chemin absolu/relatif")
        print(f"    - data/{csv_arg}")
        sys.exit(1)
    
    print(f"[INFO] Fichier CSV : {csv_file.absolute()}")
    print(f"[INFO] Patients demandés : {N}")
    
    # Déterminer le chemin de la base
    script_dir = Path(__file__).parent
    db_path = script_dir / "bases" / f"base{N}.db"
    
    print(f"[INFO] Base de données : {db_path.absolute()}")
    print()
    
    # Créer la base et les tables
    conn = create_db_and_tables(db_path)
    
    # Charger les patients
    charge_patients(conn, csv_file, N)
    
    # Créer les index
    create_indexes(conn)
    
    # Fermer la connexion
    conn.close()
    
    print()
    print(f"[OK] Traitement terminé : {db_path.absolute()}")


if __name__ == "__main__":
    main()
