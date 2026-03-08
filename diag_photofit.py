#*TO*#
__pgm__ = "diag_photofit.py"
__version__ = "0.0.0"
__date__ = "01/01/1970 00:00"

"""
Diagnostic CLI pour débugger la recherche de portraits similaires.

USAGE :
    python diag_photofit.py                                    # Affiche l'aide
    python diag_photofit.py trace DBPATIENTS DBPHOTOFIT NOM    # Trace complète pour un patient
    python diag_photofit.py audit DBPATIENTS DBPHOTOFIT        # Audit global
    python diag_photofit.py stats DBPHOTOFIT                   # Stats sur photofit.db
    python diag_photofit.py search DBPHOTOFIT IDPORTRAIT       # Recherche similaires
    python diag_photofit.py compare DBPHOTOFIT ID1 ID2         # Compare 2 portraits
    python diag_photofit.py matrix DBPHOTOFIT                  # Matrice NxN
    python diag_photofit.py anomalies DBPHOTOFIT               # Détecte anomalies
"""

import sys
import os
import argparse
import sqlite3
import struct
import math
import statistics
from pathlib import Path
from collections import Counter

DEFAULT_WEIGHT_HAIR = 0.3
DEFAULT_WEIGHT_FACE = 0.7
DEFAULT_DISTANCE_MAX = 0.5
DEFAULT_SCORE_MIN = 30
DEFAULT_MAX_RESULTS = 20
DEFAULT_SEUIL = 1000

def _deserialize_float_vector(data):
    if data is None:
        return []
    count = len(data) // 4
    return list(struct.unpack(f'<{count}f', data))

def _cosine_distance(vec1, vec2):
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

def _distance_to_score(distance, distance_max):
    if distance_max <= 0:
        return 0
    score = 100.0 * (1.0 - distance / distance_max)
    return max(0, min(100, round(score)))

def load_photofit_portraits(db_path):
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    cursor = conn.execute("SELECT idportrait, hair_embedding, face_embedding, status FROM portraits")
    portraits = {}
    for row in cursor:
        portraits[row['idportrait']] = {
            'idportrait': row['idportrait'],
            'hair_emb': _deserialize_float_vector(row['hair_embedding']),
            'face_emb': _deserialize_float_vector(row['face_embedding']),
            'hair_blob_len': len(row['hair_embedding']) if row['hair_embedding'] else 0,
            'face_blob_len': len(row['face_embedding']) if row['face_embedding'] else 0,
            'status': row['status']
        }
    conn.close()
    return portraits

def load_patients(db_path):
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    cursor = conn.execute("SELECT id, prenom, nom, sexe, age, idportrait, oripathologies FROM patients")
    patients = []
    for row in cursor:
        patients.append({
            'id': row['id'], 'prenom': row['prenom'] or '', 'nom': row['nom'] or '',
            'sexe': row['sexe'] or '', 'age': row['age'] or 0,
            'idportrait': row['idportrait'] or '', 'oripathologies': row['oripathologies'] or ''
        })
    conn.close()
    return patients

def rechercher_portraits_similaires_debug(idportrait_ref, photofit_portraits, config, debug=False):
    max_results = config['max_results']
    weight_hair = config['weight_hair']
    weight_face = config['weight_face']
    distance_max = config['distance_max']
    score_min = config['score_min']

    print(f"\n  [TRACE] _rechercher_portraits_similaires('{idportrait_ref}')")
    print(f"  [TRACE] Config: max_results={max_results}, wh={weight_hair}, wf={weight_face}, dmax={distance_max}, score_min={score_min}")

    ref = photofit_portraits.get(idportrait_ref)
    if ref is None:
        print(f"  [TRACE] PORTRAIT '{idportrait_ref}' NON TROUVE dans photofit.db")
        return [], "NOT_FOUND"
    if ref['status'] != 'ok':
        print(f"  [TRACE] Portrait '{idportrait_ref}' status='{ref['status']}' (pas 'ok')")
        return [], f"BAD_STATUS:{ref['status']}"

    print(f"  [TRACE] Portrait reference trouve, status='ok'")
    print(f"  [TRACE]   hair_emb: {len(ref['hair_emb'])} dims, face_emb: {len(ref['face_emb'])} dims")
    if ref['hair_emb']:
        norm_h = math.sqrt(sum(v*v for v in ref['hair_emb']))
        print(f"  [TRACE]   hair norme: {norm_h:.6f}")
    if ref['face_emb']:
        norm_f = math.sqrt(sum(v*v for v in ref['face_emb']))
        print(f"  [TRACE]   face norme: {norm_f:.6f}")

    candidats_ok = [p for p in photofit_portraits.values() if p['status'] == 'ok' and p['idportrait'] != idportrait_ref]
    print(f"  [TRACE] Candidats status='ok' (hors referent): {len(candidats_ok)}")

    candidats_scores = []
    for cand in candidats_ok:
        dist_hair = _cosine_distance(ref['hair_emb'], cand['hair_emb'])
        dist_face = _cosine_distance(ref['face_emb'], cand['face_emb'])
        if cand['face_emb']:
            distance = weight_hair * dist_hair + weight_face * dist_face
        else:
            distance = dist_hair
        score = _distance_to_score(distance, distance_max)
        candidats_scores.append((cand['idportrait'], score, distance, dist_hair, dist_face))

    candidats_scores.sort(key=lambda x: -x[1])

    all_scores = [c[1] for c in candidats_scores]
    if all_scores:
        print(f"\n  [TRACE] DISTRIBUTION DES SCORES ({len(all_scores)} candidats) :")
        print(f"  [TRACE]   Min={min(all_scores)}, Max={max(all_scores)}, Moy={statistics.mean(all_scores):.1f}, Med={statistics.median(all_scores):.1f}")
        above_score_min = sum(1 for s in all_scores if s >= score_min)
        above_0 = sum(1 for s in all_scores if s > 0)
        print(f"  [TRACE]   Score > 0: {above_0}, Score >= {score_min}: {above_score_min}")
        # Tranches
        for lo, hi in [(0,0),(1,10),(11,20),(21,30),(31,40),(41,50),(51,60),(61,70),(71,80),(81,90),(91,100)]:
            count = sum(1 for s in all_scores if lo <= s <= hi)
            bar = '#' * min(count, 50)
            print(f"  [TRACE]   {lo:3d}-{hi:3d}: {count:5d} {bar}")

    resultats = [(idportrait_ref, 100)]
    nb_exclus = 0
    for idp, score, dist, dh, df in candidats_scores[:max_results - 1]:
        if score >= score_min:
            resultats.append((idp, score))
        else:
            nb_exclus += 1

    print(f"\n  [TRACE] RESULTATS FINAUX : {len(resultats)} portraits (dont referent)")
    print(f"  [TRACE]   Top {max_results - 1} examines, {nb_exclus} exclus (score < {score_min})")
    if len(resultats) > 1:
        print(f"  [TRACE]   Meilleur score: {resultats[1][1]}, Dernier: {resultats[-1][1]}")

    if debug and candidats_scores:
        print(f"\n  [TRACE] TOP 10 candidats :")
        for i, (idp, score, dist, dh, df) in enumerate(candidats_scores[:10]):
            print(f"  [TRACE]   {i+1:3d}. [{score:3d}%] id={idp:10s} combined={dist:.6f} hair={dh:.6f} face={df:.6f}")

    return resultats, "OK"


def cmd_trace(db_patients, db_photofit, nom_patient, config, verbose=False, debug=False):
    print(f"\n{'='*70}")
    print(f"  TRACE COMPLETE : 'meme portrait que {nom_patient}'")
    print(f"{'='*70}")

    patients = load_patients(db_patients)
    print(f"\n  Base patients : {os.path.abspath(db_patients)} ({len(patients)} patients)")

    nom_lower = nom_patient.lower()
    matches = [p for p in patients if nom_lower in f"{p['prenom']} {p['nom']}".lower()]

    if not matches:
        print(f"\n  Aucun patient contenant '{nom_patient}'")
        print(f"  Premiers patients :")
        for p in patients[:10]:
            print(f"    id={p['id']:5d} | {p['prenom']:15s} {p['nom']:15s} | idportrait={p['idportrait']}")
        return

    if len(matches) > 1:
        print(f"\n  {len(matches)} patients correspondent :")
        for p in matches[:10]:
            print(f"    id={p['id']:5d} | {p['prenom']:15s} {p['nom']:15s} | idportrait={p['idportrait']}")

    patient = matches[0]
    idportrait_ref = patient['idportrait']

    print(f"\n  PATIENT REFERENCE :")
    print(f"    id={patient['id']}, {patient['prenom']} {patient['nom']}, sexe={patient['sexe']}, age={patient['age']}")
    print(f"    idportrait = '{idportrait_ref}'")

    seuil = config['seuil']
    try:
        id_num = int(idportrait_ref)
    except (ValueError, TypeError):
        id_num = 0

    print(f"\n  ETAPE 1 : Test seuil (photofit_seuil={seuil})")
    print(f"    int(idportrait) = {id_num}")

    if id_num >= seuil:
        print(f"    {id_num} >= {seuil} -> CHEMIN SIMILARITE VECTORIELLE")
        chemin = "SIMILARITY"
    else:
        print(f"    {id_num} < {seuil} -> CHEMIN MATCH EXACT")
        print(f"\n    *** BUG ICI ! Ce patient ne passe PAS par la recherche vectorielle ***")
        print(f"    *** SQL genere : WHERE p.idportrait = '{idportrait_ref}' ***")
        print(f"    *** Seuls les patients avec le meme idportrait matcheront ***")
        chemin = "EXACT"

    if chemin == "EXACT":
        same = [p for p in patients if p['idportrait'] == idportrait_ref]
        print(f"\n  ETAPE 2 : Match exact idportrait='{idportrait_ref}'")
        print(f"    {len(same)} patient(s) avec ce idportrait :")
        for p in same:
            ref_marker = " <- REFERENT" if p['id'] == patient['id'] else ""
            print(f"      id={p['id']:5d} | {p['prenom']:15s} {p['nom']:15s}{ref_marker}")
        print(f"\n  RESULTAT : {len(same)} patient(s) -> d'ou le '1 patient trouve' a 100%")

        # Verifier si ce portrait existe dans photofit.db
        photofit_portraits = load_photofit_portraits(db_photofit)
        pf = photofit_portraits.get(idportrait_ref)
        if pf:
            print(f"\n  INFO : Ce portrait EXISTE dans photofit.db (status='{pf['status']}')")
            print(f"  Mais son idportrait={idportrait_ref} < seuil={seuil}")
            print(f"  -> La similarite vectorielle n'est JAMAIS utilisee pour ce patient")
        else:
            print(f"\n  INFO : Ce portrait n'existe PAS dans photofit.db")
    else:
        photofit_portraits = load_photofit_portraits(db_photofit)
        print(f"\n  Base photofit : {os.path.abspath(db_photofit)} ({len(photofit_portraits)} portraits)")
        print(f"\n  ETAPE 2 : Recherche vectorielle")

        resultats, status = rechercher_portraits_similaires_debug(
            idportrait_ref, photofit_portraits, config, debug=debug
        )

        if not resultats:
            print(f"\n  Aucun resultat vectoriel (status={status})")
            print(f"  -> FALLBACK match exact : WHERE p.idportrait = '{idportrait_ref}'")
            same = [p for p in patients if p['idportrait'] == idportrait_ref]
            print(f"  -> {len(same)} patient(s)")
        else:
            portrait_ids = set(r[0] for r in resultats)
            portrait_scores = {r[0]: r[1] for r in resultats}

            print(f"\n  ETAPE 3 : WHERE p.idportrait IN ({len(portrait_ids)} IDs)")
            matching = [p for p in patients if p['idportrait'] in portrait_ids]
            print(f"    {len(portrait_ids)} IDs photofit -> {len(matching)} patients dans base patients")

            if len(matching) != len(portrait_ids):
                print(f"\n    DIVERGENCE ! Analyse :")
                ppp = {}
                for p in matching:
                    ppp.setdefault(p['idportrait'], []).append(p)
                multi = {k: v for k, v in ppp.items() if len(v) > 1}
                if multi:
                    print(f"    Portraits partages par plusieurs patients :")
                    for idp, pats in sorted(multi.items(), key=lambda x: -len(x[1]))[:10]:
                        sc = portrait_scores.get(idp, '?')
                        names = ', '.join(f"{p['prenom']} {p['nom']}" for p in pats[:3])
                        print(f"      idportrait={idp} (score={sc}%) -> {len(pats)} patients : {names}")

                missing = portrait_ids - set(p['idportrait'] for p in matching)
                if missing:
                    print(f"    Portraits photofit sans patient : {len(missing)}")

            print(f"\n  RESULTAT FINAL : {len(matching)} patient(s)")
            if debug:
                for p in matching[:20]:
                    sc = portrait_scores.get(p['idportrait'], '?')
                    ref_marker = " <- REF" if p['id'] == patient['id'] else ""
                    print(f"    [{sc:>3}%] {p['prenom']:12s} {p['nom']:12s} idp={p['idportrait']}{ref_marker}")
    print()


def cmd_audit(db_patients, db_photofit, config, verbose=False, debug=False):
    print(f"\n{'='*70}")
    print(f"  AUDIT GLOBAL")
    print(f"{'='*70}")

    patients = load_patients(db_patients)
    photofit_portraits = load_photofit_portraits(db_photofit)
    seuil = config['seuil']
    total = len(patients)

    print(f"\n  Base patients : {os.path.abspath(db_patients)} ({total} patients)")
    print(f"  Base photofit : {os.path.abspath(db_photofit)} ({len(photofit_portraits)} portraits)")
    print(f"  Seuil         : {seuil}")

    chemin_sim, chemin_exact, sans_portrait = [], [], []
    for p in patients:
        idp = p['idportrait']
        if not idp:
            sans_portrait.append(p)
            continue
        try:
            id_num = int(idp)
        except (ValueError, TypeError):
            sans_portrait.append(p)
            continue
        if id_num >= seuil:
            chemin_sim.append(p)
        else:
            chemin_exact.append(p)

    print(f"\n  REPARTITION DES CHEMINS :")
    print(f"    Similarite (idportrait >= {seuil}) : {len(chemin_sim):5d} ({len(chemin_sim)/total*100:.1f}%)")
    print(f"    Match exact (idportrait < {seuil})  : {len(chemin_exact):5d} ({len(chemin_exact)/total*100:.1f}%)")
    print(f"    Sans portrait valide               : {len(sans_portrait):5d} ({len(sans_portrait)/total*100:.1f}%)")

    if chemin_sim:
        found = sum(1 for p in chemin_sim if photofit_portraits.get(p['idportrait'], {}).get('status') == 'ok')
        print(f"\n  PATIENTS SIMILARITE ({len(chemin_sim)}) :")
        print(f"    Dans photofit.db status=ok : {found}")
        print(f"    Absents/status!=ok         : {len(chemin_sim) - found}")

    if chemin_exact:
        unique_ids = set(p['idportrait'] for p in chemin_exact)
        in_pf = sum(1 for idp in unique_ids if idp in photofit_portraits)
        print(f"\n  PATIENTS MATCH EXACT ({len(chemin_exact)}) :")
        print(f"    idportrait distincts       : {len(unique_ids)}")
        print(f"    Aussi dans photofit.db     : {in_pf}")
        if in_pf > 0:
            print(f"    *** Ces {in_pf} portraits POURRAIENT utiliser la similarite ***")
            print(f"    *** mais leur idportrait < {seuil} les en empeche ***")

    # Distribution
    id_nums = []
    for p in patients:
        try:
            id_nums.append(int(p['idportrait']))
        except:
            pass
    if id_nums:
        print(f"\n  DISTRIBUTION idportrait :")
        print(f"    Min={min(id_nums)}, Max={max(id_nums)}, Med={statistics.median(id_nums):.0f}")
        for lo, hi in [(0,99),(100,499),(500,999),(1000,1999),(2000,4999),(5000,9999),(10000,99999)]:
            count = sum(1 for n in id_nums if lo <= n <= hi)
            if count > 0:
                marker = " <- EXACT" if hi < seuil else " <- SIMILARITE"
                print(f"    {lo:6d}-{hi:6d} : {count:5d}{marker}")

    # Test rapide
    import random
    print(f"\n  TEST RAPIDE (3 patients par chemin) :")
    if chemin_sim:
        sample = random.sample(chemin_sim, min(3, len(chemin_sim)))
        for p in sample:
            ref = photofit_portraits.get(p['idportrait'])
            if ref and ref['status'] == 'ok':
                cands = [pp for pp in photofit_portraits.values() if pp['status'] == 'ok' and pp['idportrait'] != p['idportrait']]
                scores = []
                for c in cands:
                    dh = _cosine_distance(ref['hair_emb'], c['hair_emb'])
                    df = _cosine_distance(ref['face_emb'], c['face_emb'])
                    d = config['weight_hair']*dh + config['weight_face']*df if c['face_emb'] else dh
                    scores.append(_distance_to_score(d, config['distance_max']))
                ab30 = sum(1 for s in scores if s >= 30)
                print(f"    [SIM] {p['prenom']:12s} {p['nom']:12s} (idp={p['idportrait']}) : moy={statistics.mean(scores):.1f}, max={max(scores)}, >=30: {ab30}/{len(scores)}")
            else:
                print(f"    [SIM] {p['prenom']:12s} {p['nom']:12s} (idp={p['idportrait']}) : PAS DANS PHOTOFIT")
    if chemin_exact:
        sample = random.sample(chemin_exact, min(3, len(chemin_exact)))
        for p in sample:
            m = sum(1 for pp in patients if pp['idportrait'] == p['idportrait'])
            pf = "OUI" if p['idportrait'] in photofit_portraits else "NON"
            print(f"    [EXA] {p['prenom']:12s} {p['nom']:12s} (idp={p['idportrait']}) : {m} match(es), photofit={pf}")
    print()


def cmd_stats(db_photofit, verbose=False, debug=False):
    print(f"\n{'='*60}")
    print(f"  STATS PHOTOFIT : {os.path.abspath(db_photofit)}")
    print(f"{'='*60}\n")
    portraits = load_photofit_portraits(db_photofit)
    total = len(portraits)
    print(f"Total portraits : {total}")
    statuts = Counter(p['status'] for p in portraits.values())
    print(f"\nStatuts :")
    for s, c in statuts.most_common():
        print(f"  {s!r:15s} : {c:5d} ({c/total*100:.1f}%)")
    ok = [p for p in portraits.values() if p['status'] == 'ok']
    hn = sum(1 for p in ok if not p['hair_emb'])
    fn = sum(1 for p in ok if not p['face_emb'])
    print(f"\nParmi {len(ok)} status=ok : hair_null={hn}, face_null={fn}")
    if verbose and ok:
        hn2 = [math.sqrt(sum(v*v for v in p['hair_emb'])) for p in ok if p['hair_emb']]
        fn2 = [math.sqrt(sum(v*v for v in p['face_emb'])) for p in ok if p['face_emb']]
        if hn2:
            print(f"  Hair normes: min={min(hn2):.4f}, max={max(hn2):.4f}, moy={statistics.mean(hn2):.4f}")
        if fn2:
            print(f"  Face normes: min={min(fn2):.4f}, max={max(fn2):.4f}, moy={statistics.mean(fn2):.4f}")
    print()


def cmd_search(db_photofit, idportrait, config, top_n=20, show_all=False, csv_output=False, verbose=False, debug=False):
    portraits = load_photofit_portraits(db_photofit)
    resultats, status = rechercher_portraits_similaires_debug(idportrait, portraits, config, debug=debug)
    if not resultats:
        print(f"\n  Aucun resultat (status={status})")
        return
    displayed = resultats if show_all else resultats[:top_n]
    if csv_output:
        print("rang;idportrait;score")
        for i, (idp, score) in enumerate(displayed, 1):
            print(f"{i};{idp};{score}")
    else:
        print(f"\n  {'Rang':>4s} {'IDPortrait':>12s} {'Score':>6s}")
        print(f"  {'-'*4} {'-'*12} {'-'*6}")
        for i, (idp, score) in enumerate(displayed, 1):
            m = " <- REF" if i == 1 else ""
            print(f"  {i:4d} {idp:>12s} {score:5d}%{m}")


def cmd_compare(db_photofit, id1, id2, config, verbose=False, debug=False):
    print(f"\n  COMPARAISON : {id1} vs {id2}")
    portraits = load_photofit_portraits(db_photofit)
    p1, p2 = portraits.get(id1), portraits.get(id2)
    if not p1:
        print(f"  Portrait '{id1}' non trouve !"); return
    if not p2:
        print(f"  Portrait '{id2}' non trouve !"); return
    dh = _cosine_distance(p1['hair_emb'], p2['hair_emb'])
    df = _cosine_distance(p1['face_emb'], p2['face_emb'])
    combined = config['weight_hair']*dh + config['weight_face']*df
    score = _distance_to_score(combined, config['distance_max'])
    print(f"  Hair dist={dh:.6f}, Face dist={df:.6f}, Combined={combined:.6f}, Score={score}%")
    if p1['face_emb'] and p2['face_emb'] and p1['face_emb'] == p2['face_emb']:
        print(f"  !! face_embeddings IDENTIQUES !!")


def cmd_matrix(db_photofit, config, n=10, verbose=False, debug=False):
    print(f"\n  MATRICE {n}x{n}")
    portraits = load_photofit_portraits(db_photofit)
    valid = [p for p in portraits.values() if p['status'] == 'ok' and p['hair_emb'] and p['face_emb']][:n]
    if len(valid) < 2:
        print("  Pas assez de portraits."); return
    ids = [p['idportrait'][:12] for p in valid]
    print(f"{'':12s}" + "".join(f"{id:>8s}" for id in ids))
    for i, pi in enumerate(valid):
        row = f"{ids[i]:12s}"
        for j, pj in enumerate(valid):
            if i == j:
                row += f"{'---':>8s}"
            else:
                dh = _cosine_distance(pi['hair_emb'], pj['hair_emb'])
                df = _cosine_distance(pi['face_emb'], pj['face_emb'])
                d = config['weight_hair']*dh + config['weight_face']*df
                row += f"{_distance_to_score(d, config['distance_max']):7d}%"
        print(row)


def cmd_anomalies(db_photofit, config, verbose=False, debug=False):
    print(f"\n  ANOMALIES : {os.path.abspath(db_photofit)}")
    portraits = load_photofit_portraits(db_photofit)
    ok = {k: v for k, v in portraits.items() if v['status'] == 'ok'}
    count = 0
    print(f"\n1. Embeddings manquants/nuls (status=ok)")
    for idp, p in ok.items():
        issues = []
        if not p['hair_emb']: issues.append("hair=VIDE")
        elif all(v == 0.0 for v in p['hair_emb']): issues.append("hair=ZERO")
        if not p['face_emb']: issues.append("face=VIDE")
        elif all(v == 0.0 for v in p['face_emb']): issues.append("face=ZERO")
        if issues:
            print(f"  {idp:12s} : {', '.join(issues)}")
            count += 1
    if count == 0:
        print("  OK")
    print(f"\n2. Tailles")
    hs = set(p['hair_blob_len'] for p in ok.values() if p['hair_blob_len'] > 0)
    fs = set(p['face_blob_len'] for p in ok.values() if p['face_blob_len'] > 0)
    print(f"  Hair: {hs} {'OK' if len(hs) <= 1 else 'HETEROGENE!'}")
    print(f"  Face: {fs} {'OK' if len(fs) <= 1 else 'HETEROGENE!'}")
    print(f"\n3. Doublons face_embedding")
    fh = {}
    for idp, p in ok.items():
        if p['face_emb']:
            h = hash(tuple(round(v, 6) for v in p['face_emb']))
            fh.setdefault(h, []).append(idp)
    dupes = {h: ids for h, ids in fh.items() if len(ids) > 1}
    if dupes:
        for i, (h, ids) in enumerate(dupes.items()):
            print(f"  Groupe {i+1} ({len(ids)} identiques) : {ids[:5]}")
    else:
        print("  OK")
    print(f"\n  Total anomalies: {count}")



def cmd_calibrate(db_photofit, config, verbose=False, debug=False):
    """Teste plusieurs valeurs de distance_max pour trouver la config optimale."""
    print(f"\n{'='*70}")
    print(f"  CALIBRATION distance_max")
    print(f"{'='*70}")

    portraits = load_photofit_portraits(db_photofit)
    ok = [p for p in portraits.values() if p['status'] == 'ok' and p['hair_emb'] and p['face_emb']]
    print(f"\n  Portraits status=ok avec embeddings : {len(ok)}")

    import random
    sample = random.sample(ok, min(5, len(ok)))
    wh = config['weight_hair']
    wf = config['weight_face']

    # D'abord calculer les distances brutes pour l'échantillon
    print(f"\n  DISTANCES BRUTES (5 portraits echantillons vs tous) :")
    all_distances = []
    for ref in sample:
        dists = []
        for cand in ok:
            if cand['idportrait'] == ref['idportrait']:
                continue
            dh = _cosine_distance(ref['hair_emb'], cand['hair_emb'])
            df = _cosine_distance(ref['face_emb'], cand['face_emb'])
            d = wh * dh + wf * df
            dists.append(d)
            all_distances.append(d)
        if dists:
            print(f"    {ref['idportrait']:>10s} : min={min(dists):.4f}, max={max(dists):.4f}, "
                  f"moy={statistics.mean(dists):.4f}, med={statistics.median(dists):.4f}, "
                  f"p5={sorted(dists)[int(len(dists)*0.05)]:.4f}, p95={sorted(dists)[int(len(dists)*0.95)]:.4f}")

    if all_distances:
        all_distances.sort()
        print(f"\n  DISTRIBUTION GLOBALE des distances ({len(all_distances)} paires) :")
        print(f"    Min    = {all_distances[0]:.6f}")
        print(f"    P1     = {all_distances[int(len(all_distances)*0.01)]:.6f}")
        print(f"    P5     = {all_distances[int(len(all_distances)*0.05)]:.6f}")
        print(f"    P10    = {all_distances[int(len(all_distances)*0.10)]:.6f}")
        print(f"    P25    = {all_distances[int(len(all_distances)*0.25)]:.6f}")
        print(f"    Median = {all_distances[int(len(all_distances)*0.50)]:.6f}")
        print(f"    P75    = {all_distances[int(len(all_distances)*0.75)]:.6f}")
        print(f"    P90    = {all_distances[int(len(all_distances)*0.90)]:.6f}")
        print(f"    Max    = {all_distances[-1]:.6f}")

    # Tester plusieurs distance_max
    dmax_values = [0.3, 0.5, 0.7, 1.0, 1.2, 1.5, 2.0]
    score_min_values = [10, 20, 30, 40, 50]

    print(f"\n  SIMULATION : combien de resultats >= score_min pour chaque (dmax, score_min)")
    print(f"  (moyenne sur {len(sample)} patients echantillons, max_results=20)")
    print()
    header = f"  {'dmax':>6s}" + "".join(f"  sm>={sm:<3d}" for sm in score_min_values)
    print(header)
    print("  " + "-" * (len(header) - 2))

    best_config = None
    best_count = 0

    for dmax in dmax_values:
        counts_by_sm = {}
        for sm in score_min_values:
            total_matches = 0
            for ref in sample:
                scores = []
                for cand in ok:
                    if cand['idportrait'] == ref['idportrait']:
                        continue
                    dh = _cosine_distance(ref['hair_emb'], cand['hair_emb'])
                    df = _cosine_distance(ref['face_emb'], cand['face_emb'])
                    d = wh * dh + wf * df
                    s = _distance_to_score(d, dmax)
                    scores.append(s)
                scores.sort(reverse=True)
                # Appliquer max_results=20 puis score_min
                top = scores[:19]  # 19 candidats + referent
                matches = sum(1 for s in top if s >= sm)
                total_matches += matches
            avg = total_matches / len(sample)
            counts_by_sm[sm] = avg

            # Chercher la config qui donne ~10-15 resultats en moyenne
            if 8 <= avg <= 15 and (best_config is None or abs(avg - 12) < abs(best_count - 12)):
                best_config = (dmax, sm)
                best_count = avg

        row = f"  {dmax:6.1f}"
        for sm in score_min_values:
            row += f"  {counts_by_sm[sm]:6.1f}"
        print(row)

    if best_config:
        print(f"\n  RECOMMANDATION : distance_max={best_config[0]}, score_min={best_config[1]}")
        print(f"  (donne ~{best_count:.0f} resultats en moyenne, ideal pour 10-15 similaires)")
    else:
        # Fallback: montrer la config avec le plus de resultats raisonnables
        print(f"\n  Aucune config ne donne 8-15 resultats. Voir le tableau ci-dessus.")
        print(f"  Suggestion : augmenter distance_max et/ou baisser score_min")

    # Test detaille avec la meilleure config trouvee
    if best_config:
        dmax, sm = best_config
        print(f"\n  TEST DETAILLE avec dmax={dmax}, score_min={sm} :")
        for ref in sample:
            scores = []
            for cand in ok:
                if cand['idportrait'] == ref['idportrait']:
                    continue
                dh = _cosine_distance(ref['hair_emb'], cand['hair_emb'])
                df = _cosine_distance(ref['face_emb'], cand['face_emb'])
                d = wh * dh + wf * df
                s = _distance_to_score(d, dmax)
                scores.append((cand['idportrait'], s))
            scores.sort(key=lambda x: -x[1])
            top = [(idp, s) for idp, s in scores[:19] if s >= sm]
            print(f"    {ref['idportrait']:>10s} : {len(top)} resultats, "
                  f"scores: {', '.join(f'{s}%' for _, s in top[:5])}{'...' if len(top) > 5 else ''}")

    print()


def show_help():
    print(f"{__pgm__} V{__version__} - {__date__}")
    print()
    print("Diagnostic portraits similaires - Trace le chemin EXACT de jsonsql.py")
    print()
    print("Commandes :")
    print(f"  python {__pgm__} trace     DBPATIENTS DBPHOTOFIT NOM")
    print(f"  python {__pgm__} audit     DBPATIENTS DBPHOTOFIT")
    print(f"  python {__pgm__} stats     DBPHOTOFIT")
    print(f"  python {__pgm__} search    DBPHOTOFIT IDPORTRAIT")
    print(f"  python {__pgm__} compare   DBPHOTOFIT ID1 ID2")
    print(f"  python {__pgm__} matrix    DBPHOTOFIT")
    print(f"  python {__pgm__} anomalies DBPHOTOFIT")
    print(f"  python {__pgm__} calibrate DBPHOTOFIT              # Trouve le bon distance_max")
    print()
    print("Options : -n 20, --all, --wh 0.3, --wf 0.7, --dmax 0.5, --seuil 1000, --score-min 30, --csv, -v, -d")
    print()
    print("Exemples :")
    print(f"  python {__pgm__} trace bases/base1964.db bases/photofit.db Simon")
    print(f"  python {__pgm__} trace bases/base1964.db bases/photofit.db Nouredine -d")
    print(f"  python {__pgm__} trace bases/base1964.db bases/photofit.db Anita")
    print(f"  python {__pgm__} audit bases/base1964.db bases/photofit.db -v")
    print(f"  python {__pgm__} stats bases/photofit.db -v")
    print(f"  python {__pgm__} search bases/photofit.db 1000 -n 50")
    print(f"  python {__pgm__} anomalies bases/photofit.db")
    print(f"  python {__pgm__} calibrate bases/photofit.db")


def main():
    print(f"{__pgm__} V{__version__} - {__date__}")
    if len(sys.argv) < 2:
        show_help()
        return

    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument('command', nargs='?', default=None)
    parser.add_argument('args', nargs='*')
    parser.add_argument('-n', '--top', type=int, default=20)
    parser.add_argument('--all', action='store_true')
    parser.add_argument('--wh', type=float, default=DEFAULT_WEIGHT_HAIR)
    parser.add_argument('--wf', type=float, default=DEFAULT_WEIGHT_FACE)
    parser.add_argument('--dmax', type=float, default=DEFAULT_DISTANCE_MAX)
    parser.add_argument('--seuil', type=int, default=DEFAULT_SEUIL)
    parser.add_argument('--score-min', type=int, default=DEFAULT_SCORE_MIN)
    parser.add_argument('--csv', action='store_true')
    parser.add_argument('-v', '--verbose', action='store_true')
    parser.add_argument('-d', '--debug', action='store_true')
    parser.add_argument('-h', '--help', action='store_true')
    args = parser.parse_args()

    if args.help or args.command is None:
        show_help()
        return

    config = {
        'max_results': args.top if args.command == 'search' else DEFAULT_MAX_RESULTS,
        'weight_hair': args.wh, 'weight_face': args.wf,
        'distance_max': args.dmax, 'score_min': args.score_min, 'seuil': args.seuil,
    }

    cmd = args.command.lower()
    if cmd == 'trace':
        if len(args.args) < 3:
            print(f"Usage : python {__pgm__} trace DBPATIENTS DBPHOTOFIT NOM"); return
        for db in args.args[:2]:
            if not os.path.exists(db):
                print(f"ERREUR : '{db}' non trouve !"); return
        cmd_trace(args.args[0], args.args[1], ' '.join(args.args[2:]), config, args.verbose, args.debug)
    elif cmd == 'audit':
        if len(args.args) < 2:
            print(f"Usage : python {__pgm__} audit DBPATIENTS DBPHOTOFIT"); return
        for db in args.args[:2]:
            if not os.path.exists(db):
                print(f"ERREUR : '{db}' non trouve !"); return
        cmd_audit(args.args[0], args.args[1], config, args.verbose, args.debug)
    elif cmd == 'stats':
        if not args.args or not os.path.exists(args.args[0]):
            print("ERREUR : DBPHOTOFIT requis et existant"); return
        cmd_stats(args.args[0], args.verbose, args.debug)
    elif cmd == 'search':
        if len(args.args) < 2 or not os.path.exists(args.args[0]):
            print("ERREUR : DBPHOTOFIT IDPORTRAIT requis"); return
        cmd_search(args.args[0], args.args[1], config, args.top, args.all, args.csv, args.verbose, args.debug)
    elif cmd == 'compare':
        if len(args.args) < 3 or not os.path.exists(args.args[0]):
            print("ERREUR : DBPHOTOFIT ID1 ID2 requis"); return
        cmd_compare(args.args[0], args.args[1], args.args[2], config, args.verbose, args.debug)
    elif cmd == 'matrix':
        if not args.args or not os.path.exists(args.args[0]):
            print("ERREUR : DBPHOTOFIT requis"); return
        cmd_matrix(args.args[0], config, args.top, args.verbose, args.debug)
    elif cmd == 'anomalies':
        if not args.args or not os.path.exists(args.args[0]):
            print("ERREUR : DBPHOTOFIT requis"); return
        cmd_anomalies(args.args[0], config, args.verbose, args.debug)
    elif cmd == 'calibrate':
        if not args.args or not os.path.exists(args.args[0]):
            print("ERREUR : DBPHOTOFIT requis"); return
        cmd_calibrate(args.args[0], config, args.verbose, args.debug)
    else:
        print(f"Commande inconnue: '{cmd}'"); show_help()


if __name__ == "__main__":
    main()
