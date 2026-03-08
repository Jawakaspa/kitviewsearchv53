# trouveid.py V1.0.5 - 21/01/2026 18:12:57
__pgm__ = "trouveid.py"
__version__ = "1.0.5"
__date__ = "21/01/2026 18:12:57"

"""
Module d'identification du patient de référence pour les critères "même".

Ce module enrichit le JSON de détection avec les informations du patient
référencé dans les critères de type "meme".

CHANGEMENTS V2.0.0 (21/01/2026) :
- Support de la nouvelle structure 'reference' de detmeme.py v2.1
- Résolution par nom (Prénom Nom) en plus de par ID
- Recherche floue insensible à la casse et aux accents

PIPELINE :
    detall.py/detmeme.py → JSON avec critères 'meme' + reference
      │
      ▼
    trouveid.py → Enrichit avec reference_id et reference_patient
      │
      ▼
    jsonsql.py → Génère SQL avec les valeurs du patient

STRUCTURE D'ENTRÉE (sortie de detmeme.py v2.1) :
{
    "criteres": [
        {
            "type": "meme",
            "cible": "portrait",
            "label": "Même portrait",
            "valeur": null
        }
    ],
    "reference": {
        "type": "nom",        // 'nom' ou 'id'
        "valeur": "Guillaume Moulin",
        "id": null           // Rempli si type='id'
    }
}

STRUCTURE DE SORTIE :
{
    "criteres": [
        {
            "type": "meme",
            "cible": "portrait",
            "label": "Même portrait",
            "valeur": null,
            "reference_id": 2,
            "reference_patient": {
                "id": 2,
                "prenom": "Guillaume",
                "nom": "Moulin",
                "sexe": "M",
                "age": 19,
                "canontags": "beance,bruxisme,diabete",
                "canonadjs": "...",
                "idportrait": "2",
                "oripathologies": "Béance Antérieure Gauche Modérée,Bruxisme,Diabète"
            }
        }
    ],
    "reference": {...}
}

Usage en import :
    from trouveid import enrichir_avec_reference
    json_enrichi = enrichir_avec_reference(json_detection, db_path, verbose=True)

Usage CLI :
    python trouveid.py base1000.db '{"criteres": [...], "reference": {...}}'
"""

import json
import sys
import os
import csv
import sqlite3
import re
import unicodedata
from pathlib import Path
from typing import Union, Optional


def _standardise(texte: str) -> str:
    """Normalise un texte pour comparaison (minuscules, sans accents)."""
    if not texte:
        return ""
    texte = texte.lower()
    texte = unicodedata.normalize('NFD', texte)
    texte = ''.join(char for char in texte if unicodedata.category(char) != 'Mn')
    texte = re.sub(r'\s+', ' ', texte).strip()
    return texte


def _trouver_patient_par_id(db_path: Path, patient_id: int, verbose=False) -> Optional[dict]:
    """Recherche un patient par son ID."""
    try:
        conn = sqlite3.connect(str(db_path))
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, prenom, nom, sexe, age, canontags, canonadjs, idportrait, oripathologies
            FROM patients
            WHERE id = ?
        """, (patient_id,))
        
        row = cursor.fetchone()
        conn.close()
        
        if row:
            patient = dict(row)
            if verbose:
                print(f"  ✓ Patient ID {patient_id} trouvé: {patient['prenom']} {patient['nom']}")
            return patient
        else:
            if verbose:
                print(f"  ✗ Patient ID {patient_id} non trouvé")
            return None
            
    except sqlite3.Error as e:
        if verbose:
            print(f"  [ERREUR] SQLite: {e}")
        return None


def _trouver_patient_par_nom(db_path: Path, nom_complet: str, verbose=False, debug=False) -> Optional[dict]:
    """
    Recherche un patient par son nom complet (prénom + nom).
    
    Stratégies de recherche :
    1. Correspondance exacte (insensible casse)
    2. Correspondance avec prénom + nom inversés
    3. Correspondance floue (sans accents)
    """
    nom_norm = _standardise(nom_complet)
    mots = nom_norm.split()
    
    if debug:
        print(f"[DEBUG] trouveid: Recherche '{nom_complet}' → normalisé: '{nom_norm}'")
    
    if len(mots) < 1:
        return None
    
    try:
        conn = sqlite3.connect(str(db_path))
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Récupérer tous les patients (pour recherche floue)
        cursor.execute("""
            SELECT id, prenom, nom, sexe, age, canontags, canonadjs, idportrait, oripathologies
            FROM patients
        """)
        
        rows = cursor.fetchall()
        conn.close()
        
        if debug:
            print(f"[DEBUG] trouveid: {len(rows)} patients dans la base")
        
        # Stratégie 1 : Correspondance exacte prénom + nom
        for row in rows:
            patient = dict(row)
            prenom_db = _standardise(patient.get('prenom', ''))
            nom_db = _standardise(patient.get('nom', ''))
            
            # Prénom Nom
            concat1 = f"{prenom_db} {nom_db}"
            # Nom Prénom
            concat2 = f"{nom_db} {prenom_db}"
            
            if nom_norm == concat1 or nom_norm == concat2:
                if verbose:
                    print(f"  ✓ Patient trouvé (exact): {patient['prenom']} {patient['nom']} (ID {patient['id']})")
                return patient
        
        # Stratégie 2 : Correspondance partielle (si 2 mots)
        if len(mots) >= 2:
            for row in rows:
                patient = dict(row)
                prenom_db = _standardise(patient.get('prenom', ''))
                nom_db = _standardise(patient.get('nom', ''))
                
                # Vérifie si les mots correspondent au prénom et nom
                if mots[0] == prenom_db and mots[-1] == nom_db:
                    if verbose:
                        print(f"  ✓ Patient trouvé (partiel): {patient['prenom']} {patient['nom']} (ID {patient['id']})")
                    return patient
                
                if mots[-1] == prenom_db and mots[0] == nom_db:
                    if verbose:
                        print(f"  ✓ Patient trouvé (partiel inversé): {patient['prenom']} {patient['nom']} (ID {patient['id']})")
                    return patient
        
        # Stratégie 3 : Recherche LIKE si un seul mot (nom de famille seul)
        if len(mots) == 1:
            for row in rows:
                patient = dict(row)
                nom_db = _standardise(patient.get('nom', ''))
                
                if mots[0] == nom_db:
                    if verbose:
                        print(f"  ✓ Patient trouvé (nom seul): {patient['prenom']} {patient['nom']} (ID {patient['id']})")
                    return patient
        
        if verbose:
            print(f"  ✗ Patient '{nom_complet}' non trouvé")
        return None
        
    except sqlite3.Error as e:
        if verbose:
            print(f"  [ERREUR] SQLite: {e}")
        return None


def enrichir_avec_reference(
    json_detection: dict,
    db_path: Union[str, Path],
    verbose: bool = False,
    debug: bool = False
) -> dict:
    """
    Enrichit le JSON de détection avec les informations du patient de référence.
    
    Args:
        json_detection: JSON produit par detall.py/detmeme.py
        db_path: Chemin vers la base SQLite
        verbose: Afficher les infos intermédiaires
        debug: Afficher tous les détails
        
    Returns:
        JSON enrichi avec reference_id et reference_patient dans chaque critère 'meme'
    """
    db_path = Path(db_path)
    
    if not db_path.exists():
        if verbose:
            print(f"[ERREUR] Base introuvable: {db_path}")
        return json_detection
    
    # Récupérer la référence
    reference = json_detection.get('reference')
    reference_meme = json_detection.get('reference_meme')  # Ancienne structure via identifier_meme
    
    ref_data = reference or reference_meme
    
    if not ref_data:
        if debug:
            print(f"[DEBUG] trouveid: Pas de référence dans le JSON")
        return json_detection
    
    if debug:
        print(f"[DEBUG] trouveid: Référence: {ref_data}")
    
    # Trouver le patient de référence
    patient_ref = None
    
    if ref_data.get('type') == 'id':
        # Référence par ID
        patient_id = ref_data.get('id')
        if patient_id:
            patient_ref = _trouver_patient_par_id(db_path, patient_id, verbose)
    else:
        # Référence par nom (type='nom' ou pas de type)
        nom_complet = ref_data.get('valeur', '')
        if nom_complet:
            patient_ref = _trouver_patient_par_nom(db_path, nom_complet, verbose, debug)
    
    if not patient_ref:
        if verbose:
            print(f"  ⚠️  Patient de référence non trouvé")
        return json_detection
    
    # Enrichir chaque critère 'meme' avec les infos du patient
    criteres = json_detection.get('criteres', [])
    
    for critere in criteres:
        if critere.get('type') == 'meme':
            critere['reference_id'] = patient_ref['id']
            critere['reference_patient'] = patient_ref
            
            if verbose:
                cible = critere.get('cible', '?')
                valeur = critere.get('valeur', '')
                valeur_str = f"={valeur}" if valeur else ""
                print(f"  ✓ Critère enrichi: même {cible}{valeur_str} → ref ID {patient_ref['id']}")
    
    if debug:
        print(f"[DEBUG] trouveid: JSON enrichi:")
        print(json.dumps(json_detection, indent=2, ensure_ascii=False))
    
    return json_detection


# =============================================================================
# MODE BATCH
# =============================================================================

# Import conditionnel de detmeme pour le mode batch
try:
    from detmeme import charger_patterns_meme, detecter_meme
    _DETMEME_BATCH = True
except ImportError:
    _DETMEME_BATCH = False


def _trouver_fichier(nom_fichier):
    """Cherche un fichier dans plusieurs répertoires possibles."""
    chemin = Path(nom_fichier)
    if chemin.exists():
        return chemin
    script_dir = Path(__file__).parent
    for rep in [Path('tests'), script_dir / 'tests']:
        candidat = rep / chemin.name
        if candidat.exists():
            return candidat
    return None


def traiter_fichier_batch(fichier_entree, db_path, verbose=False, debug=False):
    """
    Traite un fichier CSV de questions en batch.
    Pour chaque question : detmeme → enrichir_avec_reference.
    
    Format d'entrée : CSV avec colonne 'question'
    Format de sortie : question;L1;L2;...;Ln (résumé transposé)
    Fichier de sortie : [nom_entrée]trouveid.csv
    """
    if not _DETMEME_BATCH:
        print("[ERREUR] detmeme.py non disponible, batch impossible")
        return 0, None
    
    chemin_entree = Path(fichier_entree)
    nom_base = chemin_entree.stem
    module_name = Path(__pgm__).stem  # 'trouveid'
    fichier_sortie = chemin_entree.parent / f"{nom_base}{module_name}.csv"
    
    db_path = Path(db_path)
    
    print(f"Fichier d'entrée : {os.path.abspath(fichier_entree)}")
    print(f"Fichier de sortie: {os.path.abspath(fichier_sortie)}")
    print(f"Base             : {os.path.abspath(str(db_path))}")
    print()
    
    # Charger les patterns detmeme
    script_dir = Path(__file__).parent
    refs_dir = script_dir / "refs"
    communb_path = refs_dir / "communb.csv"
    commun_path = refs_dir / "commun.csv"
    config_path = str(communb_path) if communb_path.exists() else str(commun_path) if commun_path.exists() else None
    patterns_meme = charger_patterns_meme(config_path, verbose=verbose, debug=debug)
    
    # Lire le fichier d'entrée
    lignes_entree = []
    col_indices = {}  # indices des colonnes résultat/commentaire
    commentaires = []
    
    for encodage in ["utf-8-sig", "utf-8", "windows-1252"]:
        try:
            with open(fichier_entree, 'r', encoding=encodage, newline='') as f:
                reader = csv.reader(f, delimiter=';')
                for row in reader:
                    if not row:
                        continue
                    if (row[0] or '').strip().startswith('#'):
                        commentaires.append(row)
                        continue
                    if 'question' in (row[0] or '').lower():
                        # Capturer les indices des colonnes résultat et commentaire
                        for _ci, _cn in enumerate(row):
                            _cn_low = (_cn or '').strip().lower()
                            if _cn_low in ('résultat', 'resultat'):
                                col_indices['resultat'] = _ci
                            elif _cn_low == 'commentaire':
                                col_indices['commentaire'] = _ci
                        continue
                    lignes_entree.append(row)
            break
        except (UnicodeDecodeError, UnicodeError):
            continue
    
    if not lignes_entree:
        print("[ERREUR] Aucune ligne à traiter")
        return 0, None
    
    print(f"{len(lignes_entree)} question(s) à traiter")
    print("-" * 70)
    
    resultats = []
    
    for i, row in enumerate(lignes_entree):
        question = (row[0] or '').strip()
        # Extraire résultat et commentaire si présents
        _idx_res = col_indices.get('resultat', -1)
        _idx_comm = col_indices.get('commentaire', -1)
        _val_resultat = (row[_idx_res] or '').strip() if 0 <= _idx_res < len(row) else ''
        _val_commentaire = (row[_idx_comm] or '').strip() if 0 <= _idx_comm < len(row) else ''
        if not question:
            continue
        
        # Étape 1 : detmeme
        resultat_meme = detecter_meme(question, patterns_meme, verbose=False, debug=debug)
        
        # Étape 2 : enrichir avec trouveid
        json_enrichi = enrichir_avec_reference(resultat_meme, db_path, verbose=False, debug=debug)
        
        criteres = json_enrichi.get('criteres', [])
        ref = json_enrichi.get('reference', {})
        ref_str = ''
        if ref:
            ref_str = f"id:{ref['id']}" if ref.get('type') == 'id' else ref.get('valeur', '')
        
        # Construire les lignes du résumé pour le CSV
        lignes_resume = []
        if criteres:
            for j, c in enumerate(criteres, 1):
                type_c = c.get('type', '?')
                label = c.get('label', '?')
                extra = ''
                if type_c == 'meme':
                    ref_id = c.get('reference_id', '?')
                    ref_pat = c.get('reference_patient', {})
                    if ref_pat:
                        extra = f" → {ref_pat.get('prenom', '')} {ref_pat.get('nom', '')} (ID {ref_id})"
                    else:
                        extra = f" (ref non trouvée)"
                lignes_resume.append(f"[{type_c}] {label}{extra}")
        if ref_str:
            lignes_resume.append(f"Référence: {ref_str}")
        lignes_resume.append(f"Résidu: '{json_enrichi.get('residu', '')}'")
        
        resultats.append({
            'question': question,
            'resultat': _val_resultat,
            'commentaire': _val_commentaire,
            'lignes': lignes_resume
        })
        
        # Mini-résumé (toujours affiché)
        print(f"  [{i+1}/{len(lignes_entree)}] \"{question}\"")
        if criteres:
            for j, c in enumerate(criteres, 1):
                type_c = c.get('type', '?')
                label = c.get('label', '?')
                extra = ''
                if type_c == 'meme':
                    ref_id = c.get('reference_id', '?')
                    ref_pat = c.get('reference_patient', {})
                    if ref_pat:
                        extra = f" → {ref_pat.get('prenom', '')} {ref_pat.get('nom', '')} (ID {ref_id})"
                    else:
                        extra = f" (ref non trouvée)"
                print(f"        {j}. [{type_c}] {label}{extra}")
        else:
            print(f"        (aucun critère 'même')")
        if ref_str:
            print(f"        Référence: {ref_str}")
        print(f"        Résidu: '{json_enrichi.get('residu', '')}'")
        print()
    
    # Déterminer le nombre max de colonnes L
    max_l = max((len(r['lignes']) for r in resultats), default=0)
    entete_l = ['question', 'résultat', 'commentaire'] + [f'L{i+1}' for i in range(max_l)]
    
    # Écrire le fichier de sortie
    with open(fichier_sortie, 'w', encoding='utf-8-sig', newline='') as f:
        writer = csv.writer(f, delimiter=';')
        for comm in commentaires:
            while len(comm) < len(entete_l):
                comm.append('')
            writer.writerow(comm)
        writer.writerow(entete_l)
        for res in resultats:
            row = [res['question'], res.get('resultat', ''), res.get('commentaire', '')] + res['lignes']
            while len(row) < len(entete_l):
                row.append('')
            writer.writerow(row)
    
    print("-" * 70)
    print(f"✓ {len(resultats)} lignes traitées → {os.path.abspath(fichier_sortie)}")
    
    return len(resultats), fichier_sortie


# =============================================================================
# POINT D'ENTRÉE CLI
# =============================================================================

def main():
    """Point d'entrée CLI."""
    print(f"╔════════════════════════════════════════════════════════════════")
    print(f"║ {__pgm__} V{__version__} - {__date__}")
    print(f"║ Identification patient de référence pour critères 'même'")
    print(f"╚════════════════════════════════════════════════════════════════")
    print()
    
    args_list = sys.argv[1:]
    
    # Options booléennes
    verbose = '--verbose' in args_list or '-v' in args_list
    debug = '--debug' in args_list or '-d' in args_list
    show_help = '--help' in args_list or '-h' in args_list
    
    args_list = [a for a in args_list if a not in (
        '--verbose', '-v', '--debug', '-d', '--help', '-h'
    )]
    
    # Détecter base et input par extension (ordre libre, comme trouve.py)
    database = None
    input_arg = None
    
    for arg in args_list:
        if arg.endswith('.db'):
            database = arg
        else:
            input_arg = arg
    
    # Pas d'argument ou aide → afficher l'aide
    if not database or not input_arg or show_help:
        print("Usage:")
        print(f"  python {__pgm__} <base.db> '<json>'           JSON inline")
        print(f"  python {__pgm__} <base.db> <fichier.json>     Fichier JSON")
        print(f"  python {__pgm__} <base.db> <fichier.csv>      Batch (questions)")
        print()
        print("Arguments dans n'importe quel ordre (détection par extension .db)")
        print()
        print("Options:")
        print("  -v              Affichage modéré")
        print("  -d              Affichage complet")
        print()
        print("Exemples:")
        print(f'  python {__pgm__} base1000.db \'{{\"criteres\": [...], \"reference\": {{...}}}}\'')
        print(f'  python {__pgm__} base1000.db detection.json -v')
        print(f'  python {__pgm__} base1000.db testsmemein.csv')
        print(f'  python {__pgm__} quentin.csv base1964.db')
        return 1
    
    # Résoudre le chemin de la base
    db_path = database
    if not os.path.exists(db_path):
        script_dir = Path(__file__).parent
        base_in_bases = script_dir / "bases" / db_path
        if base_in_bases.exists():
            db_path = str(base_in_bases)
        else:
            print(f"[ERREUR] Base introuvable: {os.path.abspath(database)}")
            return 1
    
    # Mode batch (CSV)
    if input_arg.endswith('.csv'):
        fichier_batch = _trouver_fichier(input_arg)
        if not fichier_batch:
            print(f"[ERREUR] Fichier introuvable: {input_arg}")
            return 1
        print(f"Mode BATCH - Traitement de {fichier_batch.name}")
        print("-" * 70)
        nb, _ = traiter_fichier_batch(
            str(fichier_batch), db_path,
            verbose=verbose, debug=debug
        )
        return 0 if nb > 0 else 1
    
    # Mode JSON (fichier ou inline)
    if input_arg.endswith('.json'):
        if not os.path.exists(input_arg):
            print(f"[ERREUR] Fichier introuvable: {input_arg}")
            return 1
        with open(input_arg, 'r', encoding='utf-8') as f:
            json_detection = json.load(f)
    else:
        try:
            json_detection = json.loads(input_arg)
        except json.JSONDecodeError as e:
            print(f"[ERREUR] JSON invalide: {e}")
            return 1
    
    print(f"Base: {os.path.abspath(db_path)}")
    print()
    print("JSON d'entrée:")
    print(json.dumps(json_detection, indent=2, ensure_ascii=False))
    print()
    
    print("Enrichissement...")
    resultat = enrichir_avec_reference(
        json_detection,
        db_path,
        verbose=verbose,
        debug=debug
    )
    
    print()
    print("═" * 70)
    print("JSON ENRICHI")
    print("═" * 70)
    print(json.dumps(resultat, indent=2, ensure_ascii=False))
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
