# cherche.py V1.0.7 - 28/11/2025 18:25:50
__pgm__ = "cherche.py"
__version__ = "1.0.7"
__date__ = "28/11/2025 18:25:50"

# ╔════════════════════════════════════════════════════════════════
# ║ cherche.py v2.2.1 - Recherche patients en français
# ║ 
# ║ CORRECTION v2.2.1:
# ║   - Mode COUNT retourne patients=[] au lieu de None
# ║   - Évite les erreurs JS "Cannot read properties of null"
# ║
# ║ NOUVEAU v2.2.0:
# ║   - Mode batch : python cherche.py base.db fichier.csv [--verbose]
# ║   - Nouveau format de logs partagé avec suche.py (logrecherche.csv)
# ║   - 18 colonnes dont module, languesaisie, langueutilisee, etc.
# ║
# ║ v2.1.0:
# ║   - Ajout colonne 'sql' : requête SQL complète exécutée
# ║   - Ajout colonne 'description_filtres' : description lisible
# ║
# ║ Usages :
# ║   - Import    : from cherche import chercher
# ║   - Unitaire  : python cherche.py base.db "question" [--verbose]
# ║   - Batch     : python cherche.py base.db fichier.csv [--verbose]
# ╚════════════════════════════════════════════════════════════════

import sys
import os
import csv
import json
import time
from typing import Dict, Any, Tuple, List, Optional
from datetime import datetime

# Import de l'orchestrateur de détection
from identall import charger_references, identifier_tout

# Import des utilitaires communs
from dbutils import (
    RACINE, BASES_DIR, LOGS_DIR,
    resoudre_chemin_base,
    extraire_pathologies_sql,
    extraire_criteres_age_sexe,
    extraire_labels_patho,
    extraire_labels_ages,
    construire_sql_complet,
    executer_recherche,
    compter_resultats
)


# ============================================================================
# CONFIGURATION
# ============================================================================

LOG_FILE = os.path.join(LOGS_DIR, "logrecherche.csv")
TESTS_DIR = os.path.join(RACINE, "tests")


# ============================================================================
# GESTION DES LOGS
# ============================================================================

def _init_log_file():
    """Initialise le fichier de logs s'il n'existe pas."""
    if not os.path.exists(LOGS_DIR):
        os.makedirs(LOGS_DIR)
    
    if not os.path.exists(LOG_FILE):
        timestamp = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        with open(LOG_FILE, 'w', encoding='utf-8-sig', newline='') as f:
            f.write(f"# logrecherche.csv V1.0.0 - {timestamp}\n")
            writer = csv.writer(f, delimiter=';')
            writer.writerow([
                'module', 'timestamp', 'temps_ms', 'languesaisie', 'langueutilisee',
                'modulelangue', 'questionoriginale', 'question', 'filtres', 'sql', 'tri',
                'base', 'mode', 'nb_patients', 'pathologies', 'ages', 'residu', 'erreur'
            ])


def _log_recherche(question_originale: str, question: str, base: str, mode: str, 
                   nb_patients: int, temps_ms: int, pathologies: List[str], 
                   ages: List[str], residu: str, filtres: dict, sql: str,
                   erreur: str = ""):
    """Ajoute une ligne au fichier de logs."""
    _init_log_file()
    
    timestamp = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    pathologies_str = ", ".join(pathologies) if pathologies else ""
    ages_str = ", ".join(ages) if ages else ""
    filtres_json = json.dumps(filtres, ensure_ascii=False) if filtres else ""
    
    try:
        with open(LOG_FILE, 'a', encoding='utf-8-sig', newline='') as f:
            writer = csv.writer(f, delimiter=';')
            writer.writerow([
                __pgm__,              # module
                timestamp,            # timestamp
                temps_ms,             # temps_ms
                'fr',                 # languesaisie (toujours fr pour cherche.py)
                'fr',                 # langueutilisee (toujours fr pour cherche.py)
                '',                   # modulelangue (vide pour cherche.py)
                question_originale,   # questionoriginale
                question,             # question (traduite/nettoyée)
                filtres_json,         # filtres (JSON)
                sql,                  # sql
                '',                   # tri (usage futur)
                base,                 # base
                mode,                 # mode
                nb_patients,          # nb_patients
                pathologies_str,      # pathologies
                ages_str,             # ages
                residu,               # residu
                erreur                # erreur
            ])
    except Exception as e:
        print(f"[WARNING] Impossible d'écrire dans le log: {e}")


# ============================================================================
# FONCTIONS UTILITAIRES
# ============================================================================

def _extraire_marqueurs(question: str) -> Tuple[str, str, dict]:
    """Extrait les marqueurs depuis la question."""
    mode = 'sc'
    options = {'verbose': False, 'help': False}
    question_clean = question
    
    if '-?' in question:
        options['help'] = True
        return (mode, '', options)
    
    if '-sp' in question:
        mode = 'sp'
        question_clean = question_clean.replace('-sp', ' ')
    elif '-se' in question:
        mode = 'se'
        question_clean = question_clean.replace('-se', ' ')
    elif '-sc' in question:
        mode = 'sc'
        question_clean = question_clean.replace('-sc', ' ')
    
    if '-d' in question:
        options['verbose'] = True
        question_clean = question_clean.replace('-d', ' ')
    
    question_clean = ' '.join(question_clean.split())
    return (mode, question_clean, options)


def _afficher_aide():
    """Affiche l'aide sur les marqueurs."""
    print()
    print("═" * 70)
    print("AIDE - MARQUEURS DISPONIBLES")
    print("═" * 70)
    print()
    print("  -sc   Mode classique (défaut)")
    print("  -sp   Mode progressif [Phase 2+]")
    print("  -se   Mode enlever [Phase 2+]")
    print("  -d    Force le mode debug")
    print("  -?    Affiche cette aide")
    print()


def _construire_description_filtres(filtres: dict) -> str:
    """
    Construit une description lisible des filtres appliqués.
    """
    parties = []
    
    # Pathologies
    labels_patho = extraire_labels_patho(filtres)
    if labels_patho:
        parties.append(", ".join(labels_patho))
    
    # Âges
    labels_ages = extraire_labels_ages(filtres)
    if labels_ages:
        parties.append(" + ".join(labels_ages))
    
    # Sexe
    criteres = filtres.get('criteres', [])
    for critere in criteres:
        if critere.get('type') == 'sexe':
            sexe_val = critere.get('valeur', '')
            if sexe_val == 'F':
                parties.append("femmes")
            elif sexe_val == 'M':
                parties.append("hommes")
    
    if not parties:
        return "aucun critère"
    
    return " + ".join(parties)


def _formater_sql_complet(sql: str, params: tuple) -> str:
    """
    Formate le SQL avec les paramètres substitués pour affichage.
    """
    sql_affichage = sql
    for param in params:
        if isinstance(param, str):
            sql_affichage = sql_affichage.replace('?', f"'{param}'", 1)
        else:
            sql_affichage = sql_affichage.replace('?', str(param), 1)
    return sql_affichage


# ============================================================================
# FONCTION PRINCIPALE
# ============================================================================

def chercher(
    question: str,
    base_path: str,
    mode: str = 'sc',
    limit: int = 100,
    offset: int = 0,
    verbose: bool = False,
    references: dict = None,
    question_originale: str = None
) -> dict:
    """
    Point d'entrée principal pour chercher des patients.
    
    Args:
        question: Question en langage naturel (nettoyée des marqueurs)
        base_path: Chemin vers base SQLite
        mode: Mode de recherche ('sc' en Phase 1)
        limit: Nombre max de patients à retourner (défaut 100)
        offset: Décalage pour pagination (défaut 0)
        verbose: Mode debug
        references: Dict des références (optionnel, chargé si None)
        question_originale: Question originale avec marqueurs (pour logs)
    
    Returns:
        dict avec nb_patients, patients, message, temps_ms, filtres, sql, etc.
    """
    start_time = time.time()
    base_name = os.path.basename(base_path)
    
    # Si question_originale non fournie, utiliser question
    if question_originale is None:
        question_originale = question
    
    # Résultat par défaut
    resultat = {
        'mode': mode,
        'listcount': 'LIST',
        'nb_patients': 0,
        'nb_returned': 0,
        'patients': [],
        'message': '',
        'temps_ms': 0,
        'filtres': {},
        'description_filtres': '',
        'sql': '',
        'sql_params': [],
        'limit': limit,
        'offset': offset,
        'erreur': None
    }
    
    try:
        if verbose:
            print(f"[DEBUG] cherche.py v{__version__}")
            print(f"[DEBUG] Question: '{question}'")
            print(f"[DEBUG] Base: {base_path}")
            print(f"[DEBUG] Limit: {limit}, Offset: {offset}")
        
        # Résoudre le chemin de la base
        db_path = resoudre_chemin_base(base_path)
        
        if not os.path.exists(db_path):
            erreur = f"Base introuvable: {db_path}"
            resultat['erreur'] = erreur
            resultat['message'] = f"Erreur: {erreur}"
            _log_recherche(question_originale, question, base_name, mode, 0, 0, 
                          [], [], '', {}, '', erreur)
            return resultat
        
        # Charger les références si non fournies
        if references is None:
            if verbose:
                print(f"[DEBUG] Chargement des références...")
            references = charger_references(verbose=verbose)
        
        # Identifier tous les critères
        if verbose:
            print(f"[DEBUG] === IDENTIFICATION ===")
        
        filtres, residu = identifier_tout(question, references, verbose=verbose, debug=verbose)
        resultat['filtres'] = filtres
        
        # Description lisible des filtres
        resultat['description_filtres'] = _construire_description_filtres(filtres)
        
        if verbose:
            print(f"[DEBUG] Filtres: {filtres}")
            print(f"[DEBUG] Description: {resultat['description_filtres']}")
            print(f"[DEBUG] Résidu: '{residu}'")
        
        # Vérifier s'il y a des critères
        pathologies_sql = extraire_pathologies_sql(filtres, verbose)
        criteres_age_sexe = extraire_criteres_age_sexe(filtres, verbose)
        
        if not pathologies_sql and not criteres_age_sexe:
            if verbose:
                print("[DEBUG] Aucun critère détecté → 0 patient")
            temps_ms = int((time.time() - start_time) * 1000)
            resultat['temps_ms'] = temps_ms
            resultat['message'] = f"Aucun critère détecté ({temps_ms}ms)"
            resultat['description_filtres'] = "aucun critère"
            _log_recherche(question_originale, question, base_name, mode, 0, temps_ms, 
                          [], [], residu, filtres, '', "")
            return resultat
        
        # Compter le nombre total (sans limit)
        if verbose:
            print(f"[DEBUG] === COMPTAGE ===")
        
        nb_total = compter_resultats(db_path, filtres, verbose)
        
        # Exécuter la recherche avec limit/offset
        if verbose:
            print(f"[DEBUG] === RECHERCHE SQL ===")
        
        listcount = filtres.get('listcount', 'LIST')
        resultat['listcount'] = listcount
        
        # Capturer le SQL et les paramètres
        sql = ''
        params = ()
        patients = []
        
        if listcount == 'LIST' and nb_total > 0:
            sql, params = construire_sql_complet(filtres, limit=limit, offset=offset, verbose=verbose)
            patients = executer_recherche(db_path, sql, params, as_dict=True, verbose=verbose)
        elif listcount == 'COUNT':
            sql, params = construire_sql_complet(filtres, limit=None, offset=None, verbose=verbose)
            sql = sql.replace("SELECT *", "SELECT COUNT(*)")
            if "LIMIT" in sql:
                sql = sql[:sql.index("LIMIT")].strip()
        
        # Stocker SQL et params dans le résultat
        resultat['sql'] = sql
        resultat['sql_params'] = list(params) if params else []
        
        # Formater le SQL complet pour les logs
        sql_complet = _formater_sql_complet(sql, params) if sql else ''
        
        if verbose:
            print(f"[DEBUG] SQL: {sql}")
            print(f"[DEBUG] Params: {params}")
            print(f"[DEBUG] SQL complet: {sql_complet}")
        
        # Construire le résultat
        temps_ms = int((time.time() - start_time) * 1000)
        
        # Message de résultat
        if nb_total == 0:
            message = "Aucun patient trouvé"
        elif nb_total == 1:
            message = "1 patient trouvé"
        else:
            message = f"{nb_total} patients trouvés"
        message += f" ({temps_ms}ms)"
        
        resultat.update({
            'nb_patients': nb_total,
            'nb_returned': len(patients),
            # ╔═══════════════════════════════════════════════════════════════
            # ║ CORRECTION v2.2.1 : Toujours retourner [] et non None
            # ║ pour éviter les erreurs JS côté client
            # ╚═══════════════════════════════════════════════════════════════
            'patients': patients if listcount == 'LIST' else [],
            'message': message,
            'temps_ms': temps_ms
        })
        
        # Logger la recherche
        labels_patho = extraire_labels_patho(filtres)
        labels_ages = extraire_labels_ages(filtres)
        
        _log_recherche(
            question_originale=question_originale,
            question=question,
            base=base_name,
            mode=mode,
            nb_patients=nb_total,
            temps_ms=temps_ms,
            pathologies=labels_patho,
            ages=labels_ages,
            residu=residu,
            filtres=filtres,
            sql=sql_complet,
            erreur=""
        )
        
        return resultat
        
    except Exception as e:
        erreur = str(e)
        temps_ms = int((time.time() - start_time) * 1000)
        
        resultat['erreur'] = erreur
        resultat['message'] = f"Erreur: {erreur}"
        resultat['temps_ms'] = temps_ms
        
        _log_recherche(question_originale, question, base_name, mode, 0, temps_ms, 
                      [], [], '', {}, '', erreur)
        
        if verbose:
            print(f"[DEBUG] ERREUR: {erreur}")
            import traceback
            traceback.print_exc()
        
        return resultat


# Alias pour compatibilité avec server.py
cherche = chercher


# ============================================================================
# TRAITEMENT BATCH
# ============================================================================

def _traiter_fichier_batch(db_path: str, input_csv: str, verbose: bool = False) -> int:
    """
    Traite un fichier CSV de tests et génère le fichier de sortie.
    
    Args:
        db_path: Chemin vers la base de données
        input_csv: Chemin du fichier d'entrée
        verbose: Affiche les informations de debug
        
    Returns:
        Nombre de lignes traitées
    """
    # Résoudre le chemin du fichier d'entrée
    if not os.path.isabs(input_csv):
        # Chercher dans plusieurs répertoires
        candidats = [
            input_csv,
            os.path.join(TESTS_DIR, input_csv),
            os.path.join(RACINE, input_csv),
            os.path.join('.', input_csv),
        ]
        input_path = None
        for candidat in candidats:
            if os.path.exists(candidat):
                input_path = candidat
                break
        
        if input_path is None:
            print(f"ERREUR : Fichier d'entrée introuvable : {input_csv}")
            print(f"  Répertoires cherchés : ., {TESTS_DIR}, {RACINE}")
            return 0
    else:
        input_path = input_csv
        if not os.path.exists(input_path):
            print(f"ERREUR : Fichier d'entrée {os.path.abspath(input_path)} introuvable")
            return 0
    
    # Construire le nom de sortie (remplacer 'in.csv' par 'out.csv')
    input_basename = os.path.basename(input_path)
    input_dir = os.path.dirname(input_path)
    
    if input_basename.endswith("in.csv"):
        output_basename = input_basename[:-6] + "out.csv"
    else:
        base, ext = os.path.splitext(input_basename)
        output_basename = base + "_out" + ext
    
    output_path = os.path.join(input_dir if input_dir else TESTS_DIR, output_basename)
    
    print(f"Fichier d'entrée  : {os.path.abspath(input_path)}")
    print(f"Fichier de sortie : {os.path.abspath(output_path)}")
    print()
    
    # Charger les références une seule fois
    print("Chargement des références...")
    references = charger_references(verbose=verbose)
    print()
    
    # Lire le fichier d'entrée
    questions = []
    commentaires = []
    encodages = ["utf-8-sig", "utf-8", "windows-1252", "iso-8859-1"]
    
    for encodage in encodages:
        try:
            with open(input_path, "r", encoding=encodage, newline="") as f:
                reader = csv.reader(f, delimiter=";")
                for row in reader:
                    # Conserver les commentaires
                    if row and (row[0] or "").startswith("#"):
                        commentaires.append(row)
                        continue
                    
                    # Ignorer les lignes vides
                    if not row:
                        continue
                    
                    # Ignorer l'en-tête
                    if (row[0] or "").lower() == "question":
                        continue
                    
                    question = (row[0] or "").strip()
                    if question:
                        questions.append(question)
            break
        except (UnicodeDecodeError, UnicodeError):
            continue
        except Exception as e:
            print(f"ERREUR lecture {os.path.abspath(input_path)}: {e}")
            return 0
    
    print(f"{len(questions)} question(s) à traiter")
    print("-" * 70)
    
    # Traiter chaque question
    resultats = []
    
    for i, question in enumerate(questions, 1):
        # Extraire les marqueurs
        mode, question_clean, options = _extraire_marqueurs(question)
        
        # Exécuter la recherche
        resultat = chercher(
            question=question_clean,
            base_path=db_path,
            mode=mode,
            limit=100,
            offset=0,
            verbose=verbose or options['verbose'],
            references=references,
            question_originale=question
        )
        
        nb_patients = resultat.get('nb_patients', 0)
        description = resultat.get('description_filtres', '')
        temps_ms = resultat.get('temps_ms', 0)
        
        resultats.append({
            'question': question,
            'trouvés': nb_patients,
            'filtres': description,
            'temps_ms': temps_ms
        })
        
        # Affichage console
        if nb_patients > 0:
            print(f"✓ [{i}/{len(questions)}] {nb_patients:4d} patient(s) - {question[:60]}...")
        else:
            print(f"  [{i}/{len(questions)}]    0 patient   - {question[:60]}...")
    
    print("-" * 70)
    
    # Écrire le fichier de sortie
    try:
        with open(output_path, "w", encoding="utf-8-sig", newline="") as f:
            writer = csv.writer(f, delimiter=";")
            
            # Cartouche
            timestamp = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
            f.write(f"# {output_basename} V1.0.0 - {timestamp}\n")
            
            # En-tête
            writer.writerow(["question", "trouvés", "filtres", "temps_ms"])
            
            # Données
            for res in resultats:
                writer.writerow([res['question'], res['trouvés'], res['filtres'], res['temps_ms']])
        
        print(f"✓ Fichier de sortie : {os.path.abspath(output_path)}")
        
        # Statistiques
        total = len(resultats)
        avec_patients = sum(1 for res in resultats if res['trouvés'] > 0)
        temps_total = sum(res['temps_ms'] for res in resultats)
        print(f"  {avec_patients}/{total} questions avec patient(s)")
        print(f"  Temps total : {temps_total}ms (moyenne {temps_total//total}ms/question)")
        
    except Exception as e:
        print(f"ERREUR écriture {os.path.abspath(output_path)}: {e}")
        return 0
    
    return len(resultats)


# ============================================================================
# POINT D'ENTRÉE CLI
# ============================================================================

def main():
    """Point d'entrée CLI."""
    print(f"{__pgm__} V{__version__} - {__date__}")
    print()
    
    if len(sys.argv) < 3:
        print("Usage:")
        print(f"  python {__pgm__} <base.db> \"question\" [--verbose]")
        print(f"  python {__pgm__} <base.db> <fichier.csv> [--verbose]")
        print()
        print("Options:")
        print("  --verbose, -v   Mode debug")
        print("  --limit=N       Limite de résultats (défaut: 100)")
        print("  --offset=N      Décalage pagination (défaut: 0)")
        print("  -d              Mode debug (dans la question)")
        print("  -?              Aide sur les marqueurs")
        print()
        print("Exemples:")
        print(f"  python {__pgm__} base55.db \"femmes avec bruxisme\"")
        print(f"  python {__pgm__} base25000.db testscherchein.csv")
        print(f"  python {__pgm__} base55.db \"béance -d\"")
        print()
        print(f"Logs: {LOG_FILE}")
        return 1
    
    base_path = sys.argv[1]
    question_or_file = sys.argv[2]
    
    verbose = "--verbose" in sys.argv or "-v" in sys.argv
    
    # Extraire limit et offset des arguments
    limit = 100
    offset = 0
    for arg in sys.argv:
        if arg.startswith('--limit='):
            try:
                limit = int(arg.split('=')[1])
            except ValueError:
                pass
        if arg.startswith('--offset='):
            try:
                offset = int(arg.split('=')[1])
            except ValueError:
                pass
    
    # Résoudre le chemin de la base
    db_path = resoudre_chemin_base(base_path)
    
    if not os.path.exists(db_path):
        print(f"ERREUR : Base de données {os.path.abspath(db_path)} introuvable")
        return 1
    
    print(f"Base: {os.path.abspath(db_path)}")
    
    # ═══════════════════════════════════════════════════════════════
    # DÉTECTION DU MODE : batch si .csv, sinon unitaire
    # ═══════════════════════════════════════════════════════════════
    
    if question_or_file.endswith('.csv'):
        # Mode BATCH
        print(f"Mode: BATCH")
        print()
        
        nb_lignes = _traiter_fichier_batch(db_path, question_or_file, verbose=verbose)
        return 0 if nb_lignes > 0 else 1
    
    else:
        # Mode UNITAIRE
        question = question_or_file
        
        # Garder la question originale avant nettoyage
        question_originale = question
        
        # Extraire les marqueurs de la question
        mode, question_clean, options = _extraire_marqueurs(question)
        
        if options['help']:
            _afficher_aide()
            return 0
        
        if options['verbose']:
            verbose = True
        
        print(f"Question: {question_clean}")
        print(f"Mode: {mode}")
        print()
        
        # Chercher
        resultat = chercher(
            question=question_clean,
            base_path=db_path,
            mode=mode,
            limit=limit,
            offset=offset,
            verbose=verbose,
            question_originale=question_originale
        )
        
        # Afficher le résultat
        print("═" * 70)
        print("RÉSULTAT")
        print("═" * 70)
        print()
        
        if resultat['erreur']:
            print(f"❌ ERREUR: {resultat['erreur']}")
            return 1
        
        print(f"✓ {resultat['message']}")
        print()
        
        print(f"📋 Filtres: {resultat['description_filtres']}")
        print()
        
        if resultat['sql']:
            print(f"🔍 SQL: {resultat['sql']}")
            if resultat['sql_params']:
                print(f"   Params: {resultat['sql_params']}")
            print()
        
        # Afficher les patients
        patients = resultat.get('patients') or []
        if patients:
            nb_afficher = min(10, len(patients))
            print(f"Patients (affichage des {nb_afficher} premiers sur {resultat['nb_returned']} retournés):")
            print()
            
            for i, p in enumerate(patients[:nb_afficher], 1):
                nom = f"{p.get('oriprenom', '')} {p.get('orinom', '')}".strip()
                age = int(p.get('age', 0)) if p.get('age') else '?'
                sexe = p.get('sexe', '?')
                patho = p.get('oripathologies', '') or '(aucune)'
                
                print(f"  {i}. {nom}, {sexe}, {age} ans - {patho}")
            
            if len(patients) > nb_afficher:
                print(f"  ... et {len(patients) - nb_afficher} autre(s) dans cette page")
            
            if resultat['nb_patients'] > resultat['nb_returned']:
                print(f"  (Total: {resultat['nb_patients']} patients, affichés: {resultat['nb_returned']})")
        
        print()
        print(f"⏱️  Temps: {resultat['temps_ms']}ms")
        print(f"📝 Log: {LOG_FILE}")
        
        return 0


if __name__ == "__main__":
    sys.exit(main())
