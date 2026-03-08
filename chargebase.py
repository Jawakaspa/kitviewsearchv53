# chargebase.py V1.0.0 - 13/12/2025 11:52:54
__pgm__ = "chargebase.py"
__version__ = "1.0.0"
__date__ = "13/12/2025 11:52:54"

# ╔════════════════════════════════════════════════════════════════
# ║ chargebase.py - Chargement CSV vers SQLite normalisé
# ║ 
# ║ Charge les données patients dans une base SQLite à 5 tables :
# ║   - patients : données démographiques
# ║   - tags : pathologies canoniques (standardisées)
# ║   - adjectifs : qualificatifs (standardisés)
# ║   - patients_tags : relation patients <-> tags
# ║   - patients_tags_adjectifs : relation patients_tags <-> adjectifs
# ║
# ║ Usage : chargebase.py <fichier.csv> <N>
# ╚════════════════════════════════════════════════════════════════

import sys
import os
import csv
import sqlite3
import time
from pathlib import Path

# Bibliothèque externe
try:
    from tqdm import tqdm
except ImportError:
    print("ERREUR : tqdm non installé. Installez avec : pip install tqdm --break-system-packages")
    sys.exit(1)

# Module local
try:
    from standardise import standardise
except ImportError:
    print("ERREUR : Module standardise.py non trouvé dans le répertoire courant.")
    sys.exit(1)


# ═══════════════════════════════════════════════════════════════════
# CONSTANTES
# ═══════════════════════════════════════════════════════════════════

CSV_ENCODING = "utf-8-sig"
CSV_SEPARATOR = ";"
TAG_SEPARATOR = ","
ADJ_GROUP_SEPARATOR = ","
ADJ_SEPARATOR = "|"

COLONNES_ATTENDUES = ["id", "canontags", "canonadjs", "sexe", "age", 
                       "datenaissance", "prenom", "nom", "portrait"]


# ═══════════════════════════════════════════════════════════════════
# CRÉATION DE LA BASE DE DONNÉES
# ═══════════════════════════════════════════════════════════════════

SQL_DROP_TABLES = """
DROP TABLE IF EXISTS patients_tags_adjectifs;
DROP TABLE IF EXISTS patients_tags;
DROP TABLE IF EXISTS adjectifs;
DROP TABLE IF EXISTS tags;
DROP TABLE IF EXISTS patients;
"""

SQL_CREATE_PATIENTS = """
CREATE TABLE IF NOT EXISTS patients (
    id INTEGER PRIMARY KEY,
    canontags TEXT,
    canonadjs TEXT,
    stdcanontags TEXT,
    stdcanonadjs TEXT,
    sexe TEXT,
    age DECIMAL(5, 3),
    datenaissance TEXT,
    prenom TEXT,
    nom TEXT,
    portrait TEXT
);
"""

SQL_CREATE_TAGS = """
CREATE TABLE IF NOT EXISTS tags (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    tag TEXT UNIQUE NOT NULL
);
"""

SQL_CREATE_ADJECTIFS = """
CREATE TABLE IF NOT EXISTS adjectifs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    adjectif TEXT UNIQUE NOT NULL
);
"""

SQL_CREATE_PATIENTS_TAGS = """
CREATE TABLE IF NOT EXISTS patients_tags (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    patient_id INTEGER NOT NULL,
    tag_id INTEGER NOT NULL,
    UNIQUE(patient_id, tag_id),
    FOREIGN KEY (patient_id) REFERENCES patients(id) ON DELETE CASCADE,
    FOREIGN KEY (tag_id) REFERENCES tags(id) ON DELETE CASCADE
);
"""

SQL_CREATE_PATIENTS_TAGS_ADJECTIFS = """
CREATE TABLE IF NOT EXISTS patients_tags_adjectifs (
    patient_tag_id INTEGER NOT NULL,
    adjectif_id INTEGER NOT NULL,
    PRIMARY KEY (patient_tag_id, adjectif_id),
    FOREIGN KEY (patient_tag_id) REFERENCES patients_tags(id) ON DELETE CASCADE,
    FOREIGN KEY (adjectif_id) REFERENCES adjectifs(id) ON DELETE CASCADE
);
"""

SQL_CREATE_INDEXES = """
CREATE INDEX IF NOT EXISTS idx_patients_sexe ON patients(sexe);
CREATE INDEX IF NOT EXISTS idx_patients_age ON patients(age);
CREATE INDEX IF NOT EXISTS idx_tags_tag ON tags(tag);
CREATE INDEX IF NOT EXISTS idx_adjectifs_adjectif ON adjectifs(adjectif);
CREATE INDEX IF NOT EXISTS idx_patients_tags_patient ON patients_tags(patient_id);
CREATE INDEX IF NOT EXISTS idx_patients_tags_tag ON patients_tags(tag_id);
CREATE INDEX IF NOT EXISTS idx_pta_patient_tag ON patients_tags_adjectifs(patient_tag_id);
CREATE INDEX IF NOT EXISTS idx_pta_adjectif ON patients_tags_adjectifs(adjectif_id);
"""


def creer_structure_base(conn: sqlite3.Connection) -> None:
    """Crée la structure complète de la base de données."""
    cursor = conn.cursor()
    
    # Suppression des tables existantes
    cursor.executescript(SQL_DROP_TABLES)
    
    # Création des tables
    cursor.execute(SQL_CREATE_PATIENTS)
    cursor.execute(SQL_CREATE_TAGS)
    cursor.execute(SQL_CREATE_ADJECTIFS)
    cursor.execute(SQL_CREATE_PATIENTS_TAGS)
    cursor.execute(SQL_CREATE_PATIENTS_TAGS_ADJECTIFS)
    
    # Création des index
    cursor.executescript(SQL_CREATE_INDEXES)
    
    conn.commit()


# ═══════════════════════════════════════════════════════════════════
# FONCTIONS UTILITAIRES
# ═══════════════════════════════════════════════════════════════════

def compter_lignes_utiles(fichier_csv: str) -> int:
    """Compte les lignes utiles (non vides, ne commençant pas par #)."""
    count = 0
    with open(fichier_csv, "r", encoding=CSV_ENCODING) as f:
        reader = csv.reader(f, delimiter=CSV_SEPARATOR)
        for row in reader:
            if row and not row[0].strip().startswith("#"):
                count += 1
    # Soustraire 1 pour l'en-tête
    return count - 1 if count > 0 else 0


def parser_tags_adjs(canontags: str, canonadjs: str) -> list:
    """
    Parse les tags et leurs adjectifs associés.
    
    Retourne une liste de tuples : [(tag, [adj1, adj2, ...]), ...]
    
    Exemple :
        canontags = "bruxisme,avulsion,Classe III"
        canonadjs = ",immédiate,"
        -> [("bruxisme", []), ("avulsion", ["immédiate"]), ("Classe III", [])]
    """
    # Parser les tags
    tags = [t.strip() for t in canontags.split(TAG_SEPARATOR)] if canontags.strip() else []
    
    # Parser les groupes d'adjectifs
    adj_groups = canonadjs.split(ADJ_GROUP_SEPARATOR) if canonadjs else []
    
    # Compléter avec des groupes vides si nécessaire
    while len(adj_groups) < len(tags):
        adj_groups.append("")
    
    # Construire la liste de résultats
    result = []
    for i, tag in enumerate(tags):
        if not tag:
            continue
        adj_str = adj_groups[i] if i < len(adj_groups) else ""
        adjs = [a.strip() for a in adj_str.split(ADJ_SEPARATOR) if a.strip()]
        result.append((tag, adjs))
    
    return result


def standardiser_liste(items: list, sep: str) -> str:
    """Standardise une liste d'items et les rejoint avec le séparateur."""
    return sep.join(standardise(item) for item in items if item)


# ═══════════════════════════════════════════════════════════════════
# CHARGEMENT DES DONNÉES
# ═══════════════════════════════════════════════════════════════════

def charger_donnees(conn: sqlite3.Connection, fichier_csv: str, n_lignes: int) -> dict:
    """
    Charge les données du CSV dans la base SQLite.
    
    Retourne un dictionnaire de statistiques.
    """
    cursor = conn.cursor()
    
    # Dictionnaires pour gérer les IDs
    tags_ids = {}       # tag_std -> id
    adjs_ids = {}       # adj_std -> id
    
    # Statistiques
    stats = {
        "patients": 0,
        "tags_distincts": 0,
        "adjs_distincts": 0,
        "assoc_patient_tag": 0,
        "assoc_tag_adj": 0
    }
    
    with open(fichier_csv, "r", encoding=CSV_ENCODING) as f:
        # Lire toutes les lignes et filtrer les commentaires
        lignes_fichier = []
        for ligne in f:
            ligne_strip = ligne.strip()
            if ligne_strip and not ligne_strip.startswith("#"):
                lignes_fichier.append(ligne)
        
        # Reconstruire un fichier virtuel pour DictReader
        import io
        contenu = "".join(lignes_fichier)
        f_virtuel = io.StringIO(contenu)
        
        reader = csv.DictReader(f_virtuel, delimiter=CSV_SEPARATOR)
        
        # Vérifier les colonnes
        colonnes_presentes = reader.fieldnames
        for col in COLONNES_ATTENDUES:
            if col not in colonnes_presentes:
                raise ValueError(f"Colonne manquante dans le CSV : {col}")
        
        # Charger n_lignes
        lignes = []
        for row in reader:
            lignes.append(row)
            if len(lignes) >= n_lignes:
                break
        
        # Barre de progression
        for row in tqdm(lignes, desc="Chargement", unit="patient", 
                        bar_format="[{bar:20}] {percentage:3.0f}% - Patient {n}/{total}"):
            
            patient_id = int(row["id"])
            canontags = row["canontags"].strip()
            canonadjs = row["canonadjs"].strip()
            sexe = row["sexe"].strip()
            age = float(row["age"]) if row["age"] else None
            datenaissance = row["datenaissance"].strip()
            prenom = row["prenom"].strip()
            nom = row["nom"].strip()
            portrait = row["portrait"].strip()
            
            # Parser tags et adjectifs
            tags_adjs = parser_tags_adjs(canontags, canonadjs)
            
            # Construire les versions standardisées
            tags_list = [t for t, _ in tags_adjs]
            stdcanontags = standardiser_liste(tags_list, TAG_SEPARATOR)
            
            # Pour stdcanonadjs, on reconstruit la même structure
            std_adj_groups = []
            for _, adjs in tags_adjs:
                std_adjs = [standardise(a) for a in adjs]
                std_adj_groups.append(ADJ_SEPARATOR.join(std_adjs))
            stdcanonadjs = ADJ_GROUP_SEPARATOR.join(std_adj_groups)
            
            # Insérer le patient
            cursor.execute("""
                INSERT INTO patients (id, canontags, canonadjs, stdcanontags, stdcanonadjs,
                                      sexe, age, datenaissance, prenom, nom, portrait)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (patient_id, canontags, canonadjs, stdcanontags, stdcanonadjs,
                  sexe, age, datenaissance, prenom, nom, portrait))
            
            stats["patients"] += 1
            
            # Traiter chaque tag et ses adjectifs
            for tag, adjs in tags_adjs:
                tag_std = standardise(tag)
                
                # Insérer ou récupérer le tag
                if tag_std not in tags_ids:
                    cursor.execute("INSERT OR IGNORE INTO tags (tag) VALUES (?)", (tag_std,))
                    cursor.execute("SELECT id FROM tags WHERE tag = ?", (tag_std,))
                    tags_ids[tag_std] = cursor.fetchone()[0]
                    stats["tags_distincts"] += 1
                
                tag_id = tags_ids[tag_std]
                
                # Insérer la relation patient-tag
                cursor.execute("""
                    INSERT INTO patients_tags (patient_id, tag_id)
                    VALUES (?, ?)
                """, (patient_id, tag_id))
                
                patient_tag_id = cursor.lastrowid
                stats["assoc_patient_tag"] += 1
                
                # Traiter les adjectifs
                for adj in adjs:
                    adj_std = standardise(adj)
                    
                    # Insérer ou récupérer l'adjectif
                    if adj_std not in adjs_ids:
                        cursor.execute("INSERT OR IGNORE INTO adjectifs (adjectif) VALUES (?)", (adj_std,))
                        cursor.execute("SELECT id FROM adjectifs WHERE adjectif = ?", (adj_std,))
                        adjs_ids[adj_std] = cursor.fetchone()[0]
                        stats["adjs_distincts"] += 1
                    
                    adj_id = adjs_ids[adj_std]
                    
                    # Insérer la relation patient_tag-adjectif
                    cursor.execute("""
                        INSERT INTO patients_tags_adjectifs (patient_tag_id, adjectif_id)
                        VALUES (?, ?)
                    """, (patient_tag_id, adj_id))
                    
                    stats["assoc_tag_adj"] += 1
    
    conn.commit()
    return stats


# ═══════════════════════════════════════════════════════════════════
# POINT D'ENTRÉE
# ═══════════════════════════════════════════════════════════════════

def main():
    """Point d'entrée principal du programme."""
    print(f"{__pgm__} V{__version__} - {__date__}")
    print()
    
    # Vérifier les arguments
    if len(sys.argv) != 3:
        print(f"Usage : {__pgm__} <fichier.csv> <N>")
        print()
        print("  <fichier.csv> : fichier source des patients")
        print("  <N>           : nombre de lignes à charger")
        print()
        print("Exemple : chargebase.py pats100.csv 50")
        sys.exit(1)
    
    fichier_csv = sys.argv[1]
    try:
        n_lignes = int(sys.argv[2])
    except ValueError:
        print(f"ERREUR : '{sys.argv[2]}' n'est pas un nombre valide.")
        sys.exit(1)
    
    if n_lignes <= 0:
        print("ERREUR : Le nombre de lignes doit être positif.")
        sys.exit(1)
    
    # Chemin absolu du fichier CSV
    fichier_csv_abs = str(Path(fichier_csv).resolve())
    
    # Vérifier que le fichier existe
    if not os.path.exists(fichier_csv_abs):
        print(f"ERREUR : Fichier non trouvé : {fichier_csv_abs}")
        sys.exit(1)
    
    # Compter les lignes utiles
    lignes_utiles = compter_lignes_utiles(fichier_csv_abs)
    
    if lignes_utiles == 0:
        print(f"ERREUR : Le fichier {fichier_csv_abs} ne contient aucune donnée.")
        sys.exit(1)
    
    if n_lignes > lignes_utiles:
        print(f"ERREUR : Demande de {n_lignes} lignes mais le fichier n'en contient que {lignes_utiles}.")
        sys.exit(1)
    
    # Déterminer le nom de la base
    repertoire = Path(fichier_csv_abs).parent
    nom_base = f"base{n_lignes}.db"
    chemin_base = repertoire / nom_base
    chemin_base_abs = str(chemin_base.resolve())
    
    # Afficher les informations
    print(f"Fichier source    : {fichier_csv_abs}")
    print(f"Lignes utiles     : {lignes_utiles}")
    print(f"Lignes à charger  : {n_lignes}")
    print(f"Base cible        : {chemin_base_abs}")
    print()
    
    # Supprimer la base si elle existe
    if chemin_base.exists():
        chemin_base.unlink()
    
    # Créer la base et charger les données
    debut = time.perf_counter()
    
    conn = sqlite3.connect(chemin_base_abs)
    conn.execute("PRAGMA foreign_keys = ON")
    
    try:
        creer_structure_base(conn)
        stats = charger_donnees(conn, fichier_csv_abs, n_lignes)
    except Exception as e:
        conn.rollback()
        print(f"\nERREUR : {e}")
        sys.exit(1)
    finally:
        conn.close()
    
    duree = time.perf_counter() - debut
    
    # Afficher le résumé
    print()
    print(f"✓ Chargement terminé en {duree:.3f} s")
    print(f"  - Patients                  : {stats['patients']}")
    print(f"  - Tags distincts            : {stats['tags_distincts']}")
    print(f"  - Adjectifs distincts       : {stats['adjs_distincts']}")
    print(f"  - Associations patient-tag  : {stats['assoc_patient_tag']}")
    print(f"  - Associations tag-adjectif : {stats['assoc_tag_adj']}")


if __name__ == "__main__":
    main()
