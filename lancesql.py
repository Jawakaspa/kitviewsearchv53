# lancesql.py V1.0.4 - 04/01/2026 08:22:35
__pgm__ = "lancesql.py"
__version__ = "1.0.4"
__date__ = "04/01/2026 08:22:35"

"""
Module d'exécution SQL sur la base de données patients.

Ce module exécute les requêtes SQL générées par jsonsql.py
et retourne les résultats formatés.

ARCHITECTURE :
    detall.py/detia.py → JSON → jsonsql.py → SQL → lancesql.py → Résultats
                                                          ↓
                                                    base{N}.db

FORMAT D'ENTRÉE (sortie de jsonsql.py) :
{
    "sql": "SELECT ...",
    "params": [...],
    "listcount": "COUNT|LIST",
    "debug_clauses": [...]
}

FORMAT DE SORTIE :
{
    "nb": 42,                    # Nombre de résultats
    "ids": [1, 5, 12, ...],      # Liste des IDs (si LIST)
    "patients": [...],           # Détails patients (si LIST et demandé)
    "temps_ms": 12.5,            # Temps d'exécution
    "sql_execute": "SELECT ..."  # SQL exécuté (debug)
}

Usage en import :
    from lancesql import executer_sql
    resultat = executer_sql(sql_dict, db_path, verbose=True)

Usage CLI :
    python lancesql.py query.json bases/base100.db
    python lancesql.py '{"sql": "...", "params": [...]}' bases/base100.db
"""

import json
import sys
import os
import sqlite3
import time
from pathlib import Path
from typing import Optional, Union


def executer_sql(
    sql_dict: dict,
    db_path: Union[str, Path],
    include_details: bool = True,
    verbose: bool = False,
    debug: bool = False
) -> dict:
    """
    Exécute une requête SQL sur la base de données.
    
    Args:
        sql_dict: Dictionnaire avec 'sql', 'params', 'listcount'
        db_path: Chemin vers la base SQLite
        include_details: Inclure les détails des patients (prenom, nom, etc.)
        verbose: Afficher les informations intermédiaires
        debug: Afficher tous les détails
        
    Returns:
        dict: {
            "nb": int,
            "ids": list[int],
            "patients": list[dict],  # Si include_details
            "temps_ms": float,
            "sql_execute": str
        }
    """
    sql = sql_dict.get('sql', '')
    params = sql_dict.get('params', [])
    listcount = sql_dict.get('listcount', 'LIST')
    
    if not sql:
        return {
            "nb": 0,
            "ids": [],
            "patients": [],
            "temps_ms": 0,
            "erreur": "SQL vide"
        }
    
    db_path = Path(db_path)
    if not db_path.exists():
        return {
            "nb": 0,
            "ids": [],
            "patients": [],
            "temps_ms": 0,
            "erreur": f"Base introuvable: {db_path}"
        }
    
    if debug:
        print(f"[DEBUG] lancesql: Base: {db_path.resolve()}")
        print(f"[DEBUG] lancesql: SQL: {sql}")
        print(f"[DEBUG] lancesql: Params: {params}")
    
    # Exécution
    start_time = time.perf_counter()
    
    try:
        conn = sqlite3.connect(str(db_path))
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute(sql, params)
        rows = cursor.fetchall()
        
        conn.close()
        
    except sqlite3.Error as e:
        return {
            "nb": 0,
            "ids": [],
            "patients": [],
            "temps_ms": 0,
            "erreur": f"Erreur SQL: {e}",
            "sql_execute": sql
        }
    
    end_time = time.perf_counter()
    temps_ms = (end_time - start_time) * 1000
    
    # Formater les résultats
    if listcount == 'COUNT':
        # Mode COUNT : une seule ligne avec 'nb'
        nb = rows[0]['nb'] if rows else 0
        resultat = {
            "nb": nb,
            "ids": [],
            "patients": [],
            "temps_ms": round(temps_ms, 2),
            "sql_execute": sql
        }
    else:
        # Mode LIST : liste de patients
        ids = []
        patients = []
        
        for row in rows:
            patient_id = row['id']
            ids.append(patient_id)
            
            if include_details:
                patients.append({
                    "id": patient_id,
                    "prenom": row['prenom'] if 'prenom' in row.keys() else '',
                    "nom": row['nom'] if 'nom' in row.keys() else '',
                    "sexe": row['sexe'] if 'sexe' in row.keys() else '',
                    "age": row['age'] if 'age' in row.keys() else 0,
                    "idportrait": row['idportrait'] if 'idportrait' in row.keys() else '',
                    "oripathologies": row['oripathologies'] if 'oripathologies' in row.keys() else '',
                    "canontags": row['canontags'] if 'canontags' in row.keys() else '',
                    "canonadjs": row['canonadjs'] if 'canonadjs' in row.keys() else ''
                })
        
        resultat = {
            "nb": len(ids),
            "ids": ids,
            "patients": patients if include_details else [],
            "temps_ms": round(temps_ms, 2),
            "sql_execute": sql
        }
    
    if verbose or debug:
        print(f"  ✓ {resultat['nb']} résultat(s) en {temps_ms:.2f}ms")
    
    return resultat


def executer_depuis_json_detection(
    json_detection: dict,
    db_path: Union[str, Path],
    verbose: bool = False,
    debug: bool = False
) -> dict:
    """
    Pipeline complet : JSON détection → SQL → Exécution → Résultats.
    
    Args:
        json_detection: JSON produit par detall.py ou detia.py
        db_path: Chemin vers la base SQLite
        verbose: Afficher les informations intermédiaires
        debug: Afficher tous les détails
        
    Returns:
        dict: Résultats de l'exécution
    """
    # Import de jsonsql
    try:
        from jsonsql import generer_sql
    except ImportError:
        # Fallback : chercher dans le même répertoire
        script_dir = Path(__file__).parent
        sys.path.insert(0, str(script_dir))
        from jsonsql import generer_sql
    
    # Générer le SQL
    if verbose:
        print("Génération SQL...")
    sql_dict = generer_sql(json_detection, verbose=verbose, debug=debug)
    
    # Exécuter
    if verbose:
        print("\nExécution SQL...")
    resultat = executer_sql(sql_dict, db_path, verbose=verbose, debug=debug)
    
    # Ajouter les infos de debug
    resultat['debug_clauses'] = sql_dict.get('debug_clauses', [])
    
    return resultat


def main():
    """Point d'entrée CLI."""
    print(f"╔════════════════════════════════════════════════════════════════")
    print(f"║ {__pgm__} V{__version__} - {__date__}")
    print(f"║ Exécution SQL sur base patients")
    print(f"╚════════════════════════════════════════════════════════════════")
    print()
    
    import argparse
    parser = argparse.ArgumentParser(
        description="Exécute une requête SQL sur la base de données"
    )
    parser.add_argument('input', help='JSON inline ou chemin vers fichier .json')
    parser.add_argument('database', help='Chemin vers la base SQLite')
    parser.add_argument('--verbose', action='store_true', help='Affichage modéré')
    parser.add_argument('--debug', action='store_true', help='Affichage complet')
    parser.add_argument('--no-details', action='store_true', help='Ne pas inclure les détails patients')
    
    args = parser.parse_args()
    
    # Charger le JSON
    if args.input.endswith('.json'):
        if not os.path.exists(args.input):
            print(f"[ERREUR] Fichier introuvable: {args.input}")
            return 1
        with open(args.input, 'r', encoding='utf-8') as f:
            sql_dict = json.load(f)
    else:
        try:
            sql_dict = json.loads(args.input)
        except json.JSONDecodeError as e:
            print(f"[ERREUR] JSON invalide: {e}")
            return 1
    
    # Vérifier la base
    if not os.path.exists(args.database):
        print(f"[ERREUR] Base introuvable: {args.database}")
        return 1
    
    print(f"Base: {os.path.abspath(args.database)}")
    print()
    
    # Détecter le type de JSON (sql_dict ou json_detection)
    if 'sql' in sql_dict:
        # C'est un sql_dict (sortie de jsonsql.py)
        print("Mode: Exécution SQL directe")
        resultat = executer_sql(
            sql_dict, 
            args.database,
            include_details=not args.no_details,
            verbose=args.verbose, 
            debug=args.debug
        )
    elif 'criteres' in sql_dict:
        # C'est un json_detection (sortie de detall.py/detia.py)
        print("Mode: Pipeline complet (JSON → SQL → Exécution)")
        resultat = executer_depuis_json_detection(
            sql_dict,
            args.database,
            verbose=args.verbose,
            debug=args.debug
        )
    else:
        print("[ERREUR] Format JSON non reconnu (ni sql_dict, ni json_detection)")
        return 1
    
    # Afficher le résultat
    print()
    print("═" * 70)
    print("RÉSULTAT")
    print("═" * 70)
    print(f"Nombre: {resultat['nb']}")
    print(f"Temps: {resultat['temps_ms']}ms")
    
    if resultat.get('ids'):
        print(f"IDs: {','.join(map(str, resultat['ids'][:20]))}" + 
              (f"... (+{len(resultat['ids'])-20})" if len(resultat['ids']) > 20 else ""))
    
    if resultat.get('patients') and not args.no_details:
        print(f"\nExtrait (10 premiers):")
        for p in resultat['patients'][:10]:
            print(f"  {p['id']}: {p['prenom']} {p['nom']} ({p['sexe']}, {p['age']:.1f} ans)")
    
    if resultat.get('erreur'):
        print(f"\n[ERREUR] {resultat['erreur']}")
    
    if args.debug and resultat.get('debug_clauses'):
        print(f"\nClauses debug:")
        for clause in resultat['debug_clauses']:
            print(f"  - {clause}")
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
