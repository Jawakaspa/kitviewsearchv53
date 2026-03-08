# jsonsql.py V1.1.0 - 28/01/2026 18:10:00
__pgm__ = "jsonsql.py"
__version__ = "1.1.0"
__date__ = "28/01/2026 18:10:00"

"""
Module de génération SQL à partir du JSON de détection.

Ce module transforme le JSON unifié produit par detall.py ou detia.py
en requêtes SQL exécutables sur la base de données patients.

CHANGEMENTS V1.4.0 (15/02/2026) :
- NOUVEAU : Support du critère type "id" (recherche par identifiant patient)
- Génère la clause WHERE p.id = ? pour les critères de type "id"
- La recherche par identifiant retourne toujours 0 ou 1 résultat (PRIMARY KEY)

CHANGEMENTS V1.3.0 (11/02/2026) :
- NOUVEAU : Score de ressemblance 0-100 pour les portraits similaires
- NOUVEAU : Tri des résultats par score de ressemblance décroissant (ORDER BY CASE)
- NOUVEAU : Seuil de coupure (score_min) pour exclure les portraits trop éloignés
- NOUVEAU : portrait_scores dans le résultat de generer_sql() pour le frontend
- Paramètres configurables dans communb.csv : photofit_distance_max, photofit_score_min

CHANGEMENTS V1.2.0 (11/02/2026) :
- NOUVEAU : Recherche de portraits par similarité faciale (Photofit V5.2)
- Pour idportrait >= seuil (1000) : recherche vectorielle dans photofit.db
- Pour idportrait < seuil : match exact (comportement inchangé)
- Paramètres lus depuis communb.csv (section bases)
- Logique vectorielle factorisée (cosine distance sur hair/face embeddings)

CHANGEMENTS V1.0.9 (25/01/2026) :
- FIX CRITIQUE : Pour "même tag" et "même pathologie", utilise la VALEUR SPÉCIFIQUE
  du critère (ex: "bruxisme") au lieu du premier tag/pathologie du patient référence
- Si le patient référence n'a PAS le tag/pathologie demandé, retourne clause "1=0" (aucun résultat)
- Corrige le bug où "même bruxisme que X" retournait les patients avec "béance" (premier tag)

CHANGEMENTS V5.1.1 (22/01/2026) :
- FIX CRITIQUE : Le patient de référence est maintenant INCLUS dans les résultats
- Permet l'affichage en fond jaune et l'affinement en entonnoir (même âge, même sexe, etc.)
- Suppression de la clause "AND p.id != ?" qui excluait le patient de référence

CHANGEMENTS V5.1.0 (13/01/2026) :
- NOUVEAU : Support des critères de type "meme" (similarités)
- NOUVEAU : Génération de sous-requêtes pour les comparaisons avec patient référence
- Les critères "meme" avec reference_id génèrent des clauses basées sur les valeurs du patient

CHANGEMENTS V1.1.0 (07/01/2026) :
- FIX CRITIQUE : Utilise 'forme_accordee' des adjectifs au lieu de 'canonique'
- FIX : Correction du bug "béance antérieure" → cherchait "beance anterieur"
- FIX CRITIQUE : Gère correctement BETWEEN quand valeur est une liste [val1, val2]

ARCHITECTURE :
    detall.py/detia.py → JSON → jsonsql.py → SQL → lancesql.py → Résultats

STRUCTURE DE LA BASE (simplifiée) :
    - patients : id, canontags, canonadjs, sexe, age, nom, prenom, idportrait, ...
    - pathologies : id, pathologie (forme STANDARDISÉE sans accents)
    - patients_pathologies : patient_id, pathologie_id

LOGIQUE DE RECHERCHE SIMILARITÉS :
    - même tag → canontags du patient référence
    - même pathologie → canontags + canonadjs (pathologies complètes)
    - même portrait → idportrait >= seuil : similarité faciale via photofit.db
                       idportrait < seuil : match exact p.idportrait = ?
    - même sexe → sexe
    - même âge → age ± tolérance (défaut ±3 ans)
    - même nom → nom
    - même prénom → prenom

FORMAT D'ENTRÉE avec critère "id" :
{
    "listcount": "LIST",
    "criteres": [
        {
            "type": "id",
            "detecte": "id 10122",
            "label": "Patient ID 10122",
            "sql": {"colonne": "id", "operateur": "=", "valeur": 10122}
        }
    ]
}

Usage en import :
    from jsonsql import generer_sql
    resultat = generer_sql(json_detection, verbose=True)

Usage CLI :
    python jsonsql.py '{"listcount": "COUNT", "criteres": [...]}'
    python jsonsql.py fichier.json
"""

import json
import sys
import os
import re
import csv
import sqlite3
import struct
import math
from pathlib import Path
from typing import Optional, List, Tuple

# Import de standardise
try:
    from standardise import standardise
except ImportError:
    import unicodedata
    def standardise(texte):
        """Version simplifiée de standardise si le module n'est pas disponible."""
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
# TOLÉRANCE POUR "MÊME ÂGE"
# =============================================================================
# Valeur par défaut : ±3 ans (comme "autour de {n} ans" dans ages.csv)
TOLERANCE_AGE_DEFAUT = 3

# =============================================================================
# CACHE CONFIGURATION COMMUNB.CSV (section bases)
# =============================================================================
_config_photofit_cache = None


def _lire_config_photofit(debug: bool = False) -> dict:
    """
    Lit les paramètres Photofit depuis communb.csv (section 'bases').
    Utilise un cache pour ne lire le fichier qu'une seule fois.
    
    Returns:
        dict avec les clés : photofit_db, max_results, weight_hair, weight_face, seuil
    """
    global _config_photofit_cache
    if _config_photofit_cache is not None:
        return _config_photofit_cache
    
    # Valeurs par défaut si communb.csv absent ou section bases manquante
    config = {
        'photofit_db': 'bases/photofit.db',
        'max_results': 20,
        'weight_hair': 0.3,
        'weight_face': 0.7,
        'seuil': 1000,
        'distance_max': 0.5,
        'score_min': 30,
    }
    
    # Chercher communb.csv : même répertoire que jsonsql.py, puis refs/
    script_dir = Path(__file__).resolve().parent
    candidates = [
        script_dir / 'refs' / 'communb.csv',
        script_dir / 'communb.csv',
    ]
    
    communb_path = None
    for candidate in candidates:
        if candidate.exists():
            communb_path = candidate
            break
    
    if communb_path is None:
        if debug:
            print(f"[DEBUG] jsonsql: communb.csv introuvable, utilisation des valeurs par défaut")
        _config_photofit_cache = config
        return config
    
    if debug:
        print(f"[DEBUG] jsonsql: Lecture config Photofit depuis {communb_path}")
    
    try:
        with open(communb_path, 'r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(
                (row for row in f if not row.startswith('#')),
                delimiter=';'
            )
            for row in reader:
                section = row.get('section', '').strip()
                parametre = row.get('parametre', '').strip()
                valeur = row.get('valeur', '').strip()
                
                if section != 'bases':
                    continue
                
                if parametre == 'photofit':
                    config['photofit_db'] = valeur
                elif parametre == 'photofit_max_results':
                    config['max_results'] = int(valeur)
                elif parametre == 'photofit_weight_hair':
                    config['weight_hair'] = float(valeur)
                elif parametre == 'photofit_weight_face':
                    config['weight_face'] = float(valeur)
                elif parametre == 'photofit_seuil':
                    config['seuil'] = int(valeur)
                elif parametre == 'photofit_distance_max':
                    config['distance_max'] = float(valeur)
                elif parametre == 'photofit_score_min':
                    config['score_min'] = int(valeur)
    except Exception as e:
        if debug:
            print(f"[DEBUG] jsonsql: Erreur lecture communb.csv : {e}")
    
    if debug:
        print(f"[DEBUG] jsonsql: Config Photofit = {config}")
    
    _config_photofit_cache = config
    return config


# =============================================================================
# RECHERCHE PHOTOFIT (similarité faciale)
# =============================================================================

def _deserialize_float_vector(data: bytes) -> List[float]:
    """Désérialise des bytes en vecteur de floats."""
    if data is None:
        return []
    count = len(data) // 4
    return list(struct.unpack(f'<{count}f', data))


def _cosine_distance(vec1: List[float], vec2: List[float]) -> float:
    """Distance cosinus entre deux vecteurs (0 = identiques)."""
    if not vec1 or not vec2 or len(vec1) != len(vec2):
        return float('inf')
    dot_product = sum(a * b for a, b in zip(vec1, vec2))
    norm1 = math.sqrt(sum(a * a for a in vec1))
    norm2 = math.sqrt(sum(b * b for b in vec2))
    if norm1 == 0 or norm2 == 0:
        return float('inf')
    similarity = dot_product / (norm1 * norm2)
    similarity = max(-1.0, min(1.0, similarity))
    return 1.0 - similarity


def _distance_to_score(distance: float, distance_max: float) -> int:
    """
    Convertit une distance cosinus pondérée en score de ressemblance 0-100.
    
    Args:
        distance: Distance pondérée (0 = identique)
        distance_max: Distance au-delà de laquelle le score est 0
        
    Returns:
        Score entier entre 0 et 100
    """
    if distance_max <= 0:
        return 0
    score = 100.0 * (1.0 - distance / distance_max)
    return max(0, min(100, round(score)))


def _rechercher_portraits_similaires(idportrait_ref: str, config: dict,
                                      debug: bool = False) -> List[Tuple[str, int]]:
    """
    Recherche les portraits similaires dans photofit.db.
    
    Retourne une liste de tuples (idportrait, score) triés par score décroissant,
    avec le référent en premier (score=100). Les portraits sous le seuil score_min
    sont exclus.
    
    Args:
        idportrait_ref: ID du portrait de référence (str)
        config: Configuration Photofit (issue de _lire_config_photofit)
        debug: Mode debug
        
    Returns:
        Liste de (id_portrait_str, score_int). Vide si base inaccessible.
    """
    # Résoudre le chemin de photofit.db par rapport au répertoire du script
    script_dir = Path(__file__).resolve().parent
    db_path = (script_dir / config['photofit_db']).resolve()
    
    if not db_path.exists():
        if debug:
            print(f"[DEBUG] jsonsql/photofit: Base introuvable : {db_path}")
        return []
    
    max_results = config['max_results']
    weight_hair = config['weight_hair']
    weight_face = config['weight_face']
    distance_max = config['distance_max']
    score_min = config['score_min']
    
    try:
        conn = sqlite3.connect(str(db_path))
        conn.row_factory = sqlite3.Row
        
        # Récupérer le portrait de référence
        cursor = conn.cursor()
        cursor.execute("""
            SELECT idportrait, hair_embedding, face_embedding
            FROM portraits 
            WHERE idportrait = ? AND status = 'ok'
        """, (idportrait_ref,))
        
        ref_row = cursor.fetchone()
        if ref_row is None:
            if debug:
                print(f"[DEBUG] jsonsql/photofit: Portrait '{idportrait_ref}' non trouvé dans photofit.db")
            conn.close()
            return []
        
        ref_hair = _deserialize_float_vector(ref_row['hair_embedding'])
        ref_face = _deserialize_float_vector(ref_row['face_embedding'])
        
        # Récupérer tous les candidats (sauf le référent)
        cursor.execute("""
            SELECT idportrait, hair_embedding, face_embedding
            FROM portraits 
            WHERE status = 'ok' AND idportrait != ?
        """, (idportrait_ref,))
        
        candidats_scores = []
        for row in cursor.fetchall():
            cand_hair = _deserialize_float_vector(row['hair_embedding'])
            cand_face = _deserialize_float_vector(row['face_embedding'])
            
            dist_hair = _cosine_distance(ref_hair, cand_hair)
            dist_face = _cosine_distance(ref_face, cand_face)
            
            if cand_face:
                distance = weight_hair * dist_hair + weight_face * dist_face
            else:
                distance = dist_hair
            
            score = _distance_to_score(distance, distance_max)
            candidats_scores.append((str(row['idportrait']), score, distance))
        
        conn.close()
        
        # Trier par score décroissant (= distance croissante)
        candidats_scores.sort(key=lambda x: -x[1])
        
        # Référent en premier (score 100), puis les N-1 meilleurs au-dessus du seuil
        resultats = [(idportrait_ref, 100)]
        nb_exclus = 0
        
        for idp, score, dist in candidats_scores[:max_results - 1]:
            if score >= score_min:
                resultats.append((idp, score))
            else:
                nb_exclus += 1
        
        if debug:
            print(f"[DEBUG] jsonsql/photofit: {len(resultats)} portraits (dont référent) "
                  f"pour '{idportrait_ref}' (seuil score_min={score_min})")
            if nb_exclus > 0:
                print(f"[DEBUG] jsonsql/photofit: {nb_exclus} portrait(s) exclus (score < {score_min})")
            if candidats_scores:
                print(f"[DEBUG] jsonsql/photofit: Score max={candidats_scores[0][1]}, "
                      f"dist min={candidats_scores[0][2]:.6f}")
                dernier = resultats[-1] if len(resultats) > 1 else (idportrait_ref, 100)
                print(f"[DEBUG] jsonsql/photofit: Score min retenu={dernier[1]}")
        
        return resultats
        
    except Exception as e:
        if debug:
            print(f"[DEBUG] jsonsql/photofit: Erreur recherche similarité : {e}")
        return []


def _construire_pathologie_complete(tag_canonique: str, adjectifs: list) -> str:
    """
    Construit la pathologie complète (tag + adjectifs triés) et la standardise.
    """
    adjs_accordes = []
    for adj in adjectifs:
        if isinstance(adj, dict):
            adj_forme = adj.get('forme_accordee', adj.get('canonique', adj.get('valeur', '')))
        else:
            adj_forme = str(adj)
        if adj_forme:
            adjs_accordes.append(adj_forme)
    
    adjs_tries = sorted(adjs_accordes)
    
    if adjs_tries:
        pathologie = tag_canonique + ' ' + ' '.join(adjs_tries)
    else:
        pathologie = tag_canonique
    
    return standardise(pathologie)


def _generer_clause_tag(critere: dict, alias_counter: int) -> tuple:
    """
    Génère la clause SQL pour un critère de type 'tag'.
    """
    tag_canonique = critere.get('canonique', '')
    adjectifs = critere.get('adjectifs', [])
    
    pathologie = _construire_pathologie_complete(tag_canonique, adjectifs)
    
    pp_alias = f"pp{alias_counter}"
    pa_alias = f"pa{alias_counter}"
    
    join_clause = f"""
        JOIN patients_pathologies {pp_alias} ON p.id = {pp_alias}.patient_id
        JOIN pathologies {pa_alias} ON {pp_alias}.pathologie_id = {pa_alias}.id"""
    
    where_clause = f"{pa_alias}.pathologie = ?"
    
    return join_clause, where_clause, [pathologie], alias_counter + 1


def _generer_clause_sexe(critere: dict) -> tuple:
    """
    Génère la clause SQL pour un critère de type 'sexe'.
    """
    sql_info = critere.get('sql', {})
    valeur = sql_info.get('valeur', '')
    
    if valeur.upper() in ('M', 'MASCULIN', 'HOMME', 'H'):
        valeur = 'M'
    elif valeur.upper() in ('F', 'FEMININ', 'FÉMININ', 'FEMME'):
        valeur = 'F'
    
    return "p.sexe = ?", [valeur]


def _generer_clause_age(critere: dict) -> tuple:
    """
    Génère la clause SQL pour un critère de type 'age'.
    """
    sql_info = critere.get('sql', {})
    operateur = sql_info.get('operateur', '=')
    valeur = sql_info.get('valeur', 0)
    
    operateurs_valides = {'=', '<', '>', '<=', '>=', '!=', '<>', 'BETWEEN'}
    if operateur.upper() not in operateurs_valides:
        operateur = '='
    
    if operateur.upper() == 'BETWEEN':
        if isinstance(valeur, list) and len(valeur) >= 2:
            val1, val2 = valeur[0], valeur[1]
        else:
            val1 = valeur
            val2 = sql_info.get('valeur2', valeur)
        return f"p.age BETWEEN ? AND ?", [val1, val2]
    
    return f"p.age {operateur} ?", [valeur]


def _generer_clause_id(critere: dict, debug=False) -> tuple:
    """
    Génère la clause SQL pour un critère de type 'id'.
    
    Recherche par identifiant : p.id = ?
    Retourne toujours 0 ou 1 résultat (PRIMARY KEY).
    """
    sql_info = critere.get('sql', {})
    valeur = sql_info.get('valeur', '')
    
    if not valeur and valeur != 0:
        if debug:
            print(f"[DEBUG] jsonsql: Critère id sans valeur, ignoré")
        return "", []
    
    return "p.id = ?", [valeur]


def _generer_clause_meme(critere: dict, alias_counter: int, debug=False) -> Tuple[str, str, list, int, Optional[dict]]:
    """
    Génère la clause SQL pour un critère de type 'meme' (similarité).
    
    Args:
        critere: Critère de type 'meme' avec reference_patient
        alias_counter: Compteur pour les alias de tables
        debug: Mode debug
        
    Returns:
        Tuple (join_clause, where_clause, params, next_counter, portrait_scores)
        portrait_scores: dict {idportrait_str: score_int} ou None si pas de portrait
    """
    cible = critere.get('cible', '')
    ref_patient = critere.get('reference_patient', {})
    ref_id = critere.get('reference_id')
    
    if not ref_id or not ref_patient:
        if debug:
            print(f"[DEBUG] jsonsql: Critère meme sans référence, ignoré")
        return "", "", [], alias_counter, None
    
    join_clause = ""
    where_clause = ""
    params = []
    portrait_scores = None
    
    if cible == 'sexe':
        # Même sexe que le patient référence
        sexe_ref = ref_patient.get('sexe', '')
        if sexe_ref:
            where_clause = "p.sexe = ?"
            params = [sexe_ref]
            if debug:
                print(f"[DEBUG] jsonsql: même sexe → sexe = '{sexe_ref}'")
    
    elif cible == 'age':
        # Même âge ± tolérance
        age_ref = ref_patient.get('age', 0)
        if age_ref:
            tolerance = TOLERANCE_AGE_DEFAUT
            where_clause = "p.age BETWEEN ? AND ?"
            params = [age_ref - tolerance, age_ref + tolerance]
            if debug:
                print(f"[DEBUG] jsonsql: même âge → age BETWEEN {age_ref - tolerance} AND {age_ref + tolerance}")
    
    elif cible == 'nom':
        # Même nom
        nom_ref = ref_patient.get('nom', '')
        if nom_ref:
            where_clause = "LOWER(p.nom) = LOWER(?)"
            params = [nom_ref]
            if debug:
                print(f"[DEBUG] jsonsql: même nom → nom = '{nom_ref}'")
    
    elif cible == 'prenom':
        # Même prénom
        prenom_ref = ref_patient.get('prenom', '')
        if prenom_ref:
            where_clause = "LOWER(p.prenom) = LOWER(?)"
            params = [prenom_ref]
            if debug:
                print(f"[DEBUG] jsonsql: même prénom → prenom = '{prenom_ref}'")
    
    elif cible == 'portrait':
        # Même portrait — hybride : similarité faciale OU match exact
        idportrait_ref = ref_patient.get('idportrait', '')
        if idportrait_ref:
            config = _lire_config_photofit(debug=debug)
            seuil = config['seuil']
            
            # Déterminer si le portrait est dans la plage Photofit
            try:
                id_num = int(idportrait_ref)
            except (ValueError, TypeError):
                id_num = 0
            
            if id_num >= seuil:
                # ── RECHERCHE PAR SIMILARITÉ FACIALE ──
                resultats = _rechercher_portraits_similaires(
                    idportrait_ref, config, debug=debug
                )
                
                if resultats:
                    ids = [r[0] for r in resultats]
                    portrait_scores = {r[0]: r[1] for r in resultats}
                    
                    placeholders = ','.join(['?' for _ in ids])
                    where_clause = f"p.idportrait IN ({placeholders})"
                    params = ids
                    if debug:
                        print(f"[DEBUG] jsonsql: même portrait (similarité) → "
                              f"idportrait IN ({len(ids)} IDs, scores: "
                              f"{portrait_scores[ids[0]]}→{portrait_scores[ids[-1]]})")
                else:
                    # Fallback match exact si photofit.db indisponible
                    where_clause = "p.idportrait = ?"
                    params = [idportrait_ref]
                    if debug:
                        print(f"[DEBUG] jsonsql: même portrait (fallback exact) → "
                              f"idportrait = '{idportrait_ref}'")
            else:
                # ── MATCH EXACT (placeholders 1-999) ──
                where_clause = "p.idportrait = ?"
                params = [idportrait_ref]
                if debug:
                    print(f"[DEBUG] jsonsql: même portrait (exact) → "
                          f"idportrait = '{idportrait_ref}'")
    
    elif cible == 'tag':
        # Même tag (canontags) - tag spécifique demandé OU au moins un tag en commun
        # V1.0.9 FIX : Si une valeur spécifique est demandée, l'utiliser !
        valeur_specifique = critere.get('valeur', '')
        canontags_ref = ref_patient.get('canontags', '')
        
        if valeur_specifique:
            # CAS 1 : Tag spécifique demandé (ex: "même bruxisme que X")
            tag_std = standardise(valeur_specifique)
            tags_ref = [standardise(t.strip()) for t in canontags_ref.split(',') if t.strip()]
            
            # Vérifier si le patient référence a bien ce tag
            patient_a_ce_tag = any(tag_std in t for t in tags_ref)
            
            if patient_a_ce_tag:
                pp_alias = f"pp{alias_counter}"
                pa_alias = f"pa{alias_counter}"
                
                join_clause = f"""
        JOIN patients_pathologies {pp_alias} ON p.id = {pp_alias}.patient_id
        JOIN pathologies {pa_alias} ON {pp_alias}.pathologie_id = {pa_alias}.id"""
                
                where_clause = f"{pa_alias}.pathologie LIKE ?"
                params = [f"{tag_std}%"]
                alias_counter += 1
                
                if debug:
                    print(f"[DEBUG] jsonsql: même tag '{valeur_specifique}' → pathologie LIKE '{tag_std}%' (patient ref l'a)")
            else:
                where_clause = "1 = 0"  # Toujours faux
                params = []
                if debug:
                    print(f"[DEBUG] jsonsql: même tag '{valeur_specifique}' → PATIENT REF N'A PAS CE TAG ! Clause: 1=0")
        
        elif canontags_ref:
            # CAS 2 : Pas de valeur spécifique → comportement original (premier tag)
            tags = [t.strip() for t in canontags_ref.split(',') if t.strip()]
            if tags:
                for tag in tags:
                    tag_std = standardise(tag)
                    if tag_std:
                        pp_alias = f"pp{alias_counter}"
                        pa_alias = f"pa{alias_counter}"
                        
                        join_clause = f"""
        JOIN patients_pathologies {pp_alias} ON p.id = {pp_alias}.patient_id
        JOIN pathologies {pa_alias} ON {pp_alias}.pathologie_id = {pa_alias}.id"""
                        
                        where_clause = f"{pa_alias}.pathologie LIKE ?"
                        params = [f"{tag_std}%"]
                        alias_counter += 1
                        
                        if debug:
                            print(f"[DEBUG] jsonsql: même tag → pathologie LIKE '{tag_std}%'")
                        break  # Premier tag seulement pour l'instant
    
    elif cible == 'pathologie':
        # Même pathologie complète (canontags + canonadjs)
        # V1.0.9 FIX : Si une valeur spécifique est demandée, l'utiliser !
        valeur_specifique = critere.get('valeur', '')
        canontags_ref = ref_patient.get('canontags', '')
        canonadjs_ref = ref_patient.get('canonadjs', '')
        oripathologies_ref = ref_patient.get('oripathologies', '')
        
        if valeur_specifique:
            patho_std = standardise(valeur_specifique)
            
            pathologies_ref = [standardise(p.strip()) for p in oripathologies_ref.split(',') if p.strip()]
            patient_a_cette_patho = patho_std in pathologies_ref
            
            if patient_a_cette_patho:
                pp_alias = f"pp{alias_counter}"
                pa_alias = f"pa{alias_counter}"
                
                join_clause = f"""
        JOIN patients_pathologies {pp_alias} ON p.id = {pp_alias}.patient_id
        JOIN pathologies {pa_alias} ON {pp_alias}.pathologie_id = {pa_alias}.id"""
                
                where_clause = f"{pa_alias}.pathologie = ?"
                params = [patho_std]
                alias_counter += 1
                
                if debug:
                    print(f"[DEBUG] jsonsql: même pathologie '{valeur_specifique}' → pathologie = '{patho_std}' (patient ref l'a)")
            else:
                where_clause = "1 = 0"  # Toujours faux
                params = []
                if debug:
                    print(f"[DEBUG] jsonsql: même pathologie '{valeur_specifique}' → PATIENT REF N'A PAS CETTE PATHO ! Clause: 1=0")
        
        elif oripathologies_ref:
            pathologies = [p.strip() for p in oripathologies_ref.split(',') if p.strip()]
            if pathologies:
                patho_std = standardise(pathologies[0])
                if patho_std:
                    pp_alias = f"pp{alias_counter}"
                    pa_alias = f"pa{alias_counter}"
                    
                    join_clause = f"""
        JOIN patients_pathologies {pp_alias} ON p.id = {pp_alias}.patient_id
        JOIN pathologies {pa_alias} ON {pp_alias}.pathologie_id = {pa_alias}.id"""
                    
                    where_clause = f"{pa_alias}.pathologie = ?"
                    params = [patho_std]
                    alias_counter += 1
                    
                    if debug:
                        print(f"[DEBUG] jsonsql: même pathologie → pathologie = '{patho_std}'")
        
        elif canontags_ref:
            tags = [t.strip() for t in canontags_ref.split(',') if t.strip()]
            adjs_list = [a.strip() for a in canonadjs_ref.split('|') if a.strip()] if canonadjs_ref else []
            
            if tags:
                tag = tags[0]
                adj = adjs_list[0] if adjs_list else ''
                
                if adj:
                    patho_std = standardise(f"{tag} {adj}")
                else:
                    patho_std = standardise(tag)
                
                pp_alias = f"pp{alias_counter}"
                pa_alias = f"pa{alias_counter}"
                
                join_clause = f"""
        JOIN patients_pathologies {pp_alias} ON p.id = {pp_alias}.patient_id
        JOIN pathologies {pa_alias} ON {pp_alias}.pathologie_id = {pa_alias}.id"""
                
                where_clause = f"{pa_alias}.pathologie = ?"
                params = [patho_std]
                alias_counter += 1
                
                if debug:
                    print(f"[DEBUG] jsonsql: même pathologie (fallback) → pathologie = '{patho_std}'")
    
    return join_clause, where_clause, params, alias_counter, portrait_scores


def generer_sql(json_detection: dict, limit: int = None, offset: int = 0, 
                verbose: bool = False, debug: bool = False) -> dict:
    """
    Génère une requête SQL à partir du JSON de détection.
    
    Args:
        json_detection: JSON produit par detall.py ou detia.py
        limit: Nombre maximum de résultats à retourner (None = pas de limite)
        offset: Décalage pour la pagination (défaut: 0)
        verbose: Afficher les informations intermédiaires
        debug: Afficher tous les détails
        
    Returns:
        dict: {
            "sql": str,
            "params": list,
            "listcount": str,
            "debug_clauses": list,
            "portrait_scores": dict  # Optionnel, {idportrait: score_0_100}
        }
    """
    listcount = json_detection.get('listcount', 'LIST')
    criteres = json_detection.get('criteres', [])
    
    if debug:
        print(f"[DEBUG] jsonsql: listcount={listcount}, {len(criteres)} critère(s)")
    
    join_clauses = []
    where_clauses = []
    params = []
    debug_clauses = []
    alias_counter = 1
    portrait_scores = None  # V1.3.0 : scores de similarité portrait
    
    for critere in criteres:
        type_critere = critere.get('type', '')
        
        if type_critere == 'count':
            if debug:
                print(f"[DEBUG] jsonsql: Critère count ignoré (informatif)")
            continue
        
        elif type_critere == 'meme':
            # Gestion des critères de similarité
            join_clause, where_clause, crit_params, alias_counter, crit_portrait_scores = _generer_clause_meme(
                critere, alias_counter, debug=debug
            )
            
            # V1.3.0 : Capturer les scores de portrait si présents
            if crit_portrait_scores is not None:
                portrait_scores = crit_portrait_scores
            
            if join_clause:
                join_clauses.append(join_clause)
            if where_clause:
                where_clauses.append(where_clause)
                params.extend(crit_params)
                
                cible = critere.get('cible', '?')
                ref_patient = critere.get('reference_patient', {})
                ref_nom = f"{ref_patient.get('prenom', '')} {ref_patient.get('nom', '')}".strip()
                debug_str = f"meme {cible} que {ref_nom} (ID {critere.get('reference_id', '?')})"
                debug_clauses.append(debug_str)
                
                if verbose or debug:
                    print(f"  ✓ {debug_str}")
            else:
                if debug:
                    print(f"[DEBUG] jsonsql: Critère meme sans clause générée")
                    
        elif type_critere == 'tag':
            join_clause, where_clause, crit_params, alias_counter = _generer_clause_tag(
                critere, alias_counter
            )
            join_clauses.append(join_clause)
            where_clauses.append(where_clause)
            params.extend(crit_params)
            
            tag = critere.get('canonique', '?')
            adjs = critere.get('adjectifs', [])
            adjs_display = [a.get('forme_accordee', a.get('canonique', '')) for a in adjs]
            debug_str = f"tag: {tag}"
            if adjs_display:
                debug_str += f" + [{', '.join(adjs_display)}]"
            debug_str += f" → pathologie = '{crit_params[0]}'"
            debug_clauses.append(debug_str)
            
            if verbose or debug:
                print(f"  ✓ {debug_str}")
                
        elif type_critere == 'sexe':
            where_clause, crit_params = _generer_clause_sexe(critere)
            where_clauses.append(where_clause)
            params.extend(crit_params)
            
            debug_str = f"sexe = '{crit_params[0]}'"
            debug_clauses.append(debug_str)
            
            if verbose or debug:
                print(f"  ✓ {debug_str}")
                
        elif type_critere == 'age':
            where_clause, crit_params = _generer_clause_age(critere)
            where_clauses.append(where_clause)
            params.extend(crit_params)
            
            operateur = critere.get('sql', {}).get('operateur', '=')
            valeur = critere.get('sql', {}).get('valeur', 0)
            if operateur.upper() == 'BETWEEN':
                if isinstance(valeur, list) and len(valeur) >= 2:
                    debug_str = f"age BETWEEN {valeur[0]} AND {valeur[1]}"
                else:
                    valeur2 = critere.get('sql', {}).get('valeur2', valeur)
                    debug_str = f"age BETWEEN {valeur} AND {valeur2}"
            else:
                debug_str = f"age {operateur} {valeur}"
            debug_clauses.append(debug_str)
            
            if verbose or debug:
                print(f"  ✓ {debug_str}")
        
        elif type_critere == 'id':
            # V1.4.0 : Recherche par identifiant patient
            where_clause, crit_params = _generer_clause_id(critere, debug=debug)
            if where_clause:
                where_clauses.append(where_clause)
                params.extend(crit_params)
                
                debug_str = f"id = {crit_params[0]}"
                debug_clauses.append(debug_str)
                
                if verbose or debug:
                    print(f"  ✓ {debug_str}")
        
        else:
            if debug:
                print(f"[DEBUG] jsonsql: Type de critère inconnu: '{type_critere}'")
    
    # Construire la requête finale
    if listcount == 'COUNT':
        select_clause = "SELECT COUNT(DISTINCT p.id) as nb"
    else:
        select_clause = "SELECT DISTINCT p.id, p.prenom, p.nom, p.sexe, p.age, p.idportrait, p.oripathologies, p.canontags, p.canonadjs"
    
    from_clause = "FROM patients p"
    
    joins_str = ''.join(join_clauses)
    
    if where_clauses:
        where_str = "WHERE " + " AND ".join(where_clauses)
    else:
        where_str = ""
    
    sql = f"{select_clause}\n{from_clause}{joins_str}"
    if where_str:
        sql += f"\n{where_str}"
    
    if listcount != 'COUNT':
        # V1.3.0 : ORDER BY score de similarité portrait si disponible
        if portrait_scores and len(portrait_scores) > 1:
            case_parts = []
            for rank, (idp, score) in enumerate(
                sorted(portrait_scores.items(), key=lambda x: -x[1])
            ):
                case_parts.append(f"WHEN '{idp}' THEN {rank}")
            order_case = "ORDER BY CASE p.idportrait " + " ".join(case_parts) + " ELSE 9999 END"
            sql += f"\n{order_case}"
            if debug:
                print(f"[DEBUG] jsonsql: ORDER BY CASE portrait (tri par score décroissant)")
        else:
            sql += "\nORDER BY p.id"
        
        if limit is not None and limit > 0:
            sql += "\nLIMIT ?"
            params.append(limit)
            if offset > 0:
                sql += " OFFSET ?"
                params.append(offset)
    
    if debug:
        print(f"[DEBUG] jsonsql: SQL généré:")
        print(sql)
        print(f"[DEBUG] jsonsql: Params: {params}")
        if portrait_scores:
            print(f"[DEBUG] jsonsql: portrait_scores: {portrait_scores}")
    
    result = {
        "sql": sql,
        "params": params,
        "listcount": listcount,
        "debug_clauses": debug_clauses
    }
    
    # V1.3.0 : Ajouter les scores de similarité portrait si disponibles
    if portrait_scores:
        result["portrait_scores"] = portrait_scores
    
    return result


def main():
    """Point d'entrée CLI."""
    print(f"╔════════════════════════════════════════════════════════════════")
    print(f"║ {__pgm__} V{__version__} - {__date__}")
    print(f"║ Génération SQL à partir du JSON de détection")
    print(f"║ V1.4.0 : Support critère 'id' (identifiant patient)")
    print(f"╚════════════════════════════════════════════════════════════════")
    print()
    
    import argparse
    parser = argparse.ArgumentParser(
        description="Génère une requête SQL à partir du JSON de détection"
    )
    parser.add_argument('input', help='JSON inline ou chemin vers fichier .json')
    parser.add_argument('--verbose', action='store_true', help='Affichage modéré')
    parser.add_argument('--debug', action='store_true', help='Affichage complet')
    
    args = parser.parse_args()
    
    # Charger le JSON
    if args.input.endswith('.json'):
        if not os.path.exists(args.input):
            print(f"[ERREUR] Fichier introuvable: {args.input}")
            return 1
        with open(args.input, 'r', encoding='utf-8') as f:
            json_detection = json.load(f)
    else:
        try:
            json_detection = json.loads(args.input)
        except json.JSONDecodeError as e:
            print(f"[ERREUR] JSON invalide: {e}")
            return 1
    
    print("JSON d'entrée:")
    print(json.dumps(json_detection, indent=2, ensure_ascii=False))
    print()
    
    print("Génération SQL...")
    resultat = generer_sql(json_detection, verbose=args.verbose, debug=args.debug)
    
    print()
    print("═" * 70)
    print("REQUÊTE SQL GÉNÉRÉE")
    print("═" * 70)
    print(resultat['sql'])
    print()
    print(f"Paramètres: {resultat['params']}")
    print(f"Mode: {resultat['listcount']}")
    print()
    print("Clauses debug:")
    for clause in resultat['debug_clauses']:
        print(f"  - {clause}")
    
    # V1.3.0 : Afficher les scores de portrait si présents
    if 'portrait_scores' in resultat:
        scores = resultat['portrait_scores']
        print()
        print(f"Scores de similarité portrait ({len(scores)} portraits) :")
        for idp, score in sorted(scores.items(), key=lambda x: -x[1]):
            if score == 100:
                label = "🟡 RÉFÉRENT"
            elif score >= 80:
                label = "🟢 Excellent"
            elif score >= 60:
                label = "🔵 Bon"
            elif score >= 40:
                label = "🟠 Moyen"
            else:
                label = "⚪ Faible"
            print(f"  Portrait {idp:>6s} : {score:3d}/100  {label}")
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
