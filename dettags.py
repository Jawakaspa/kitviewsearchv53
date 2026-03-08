# dettags.py V1.0.15 - 07/01/2026 13:54:48
__pgm__ = "dettags.py"
__version__ = "0.0.0"
__date__ = "01/01/1970 00:00"

"""
Module de détection des tags orthodontiques dans une question en langage naturel.

Ce module analyse une question pour détecter des tags (pathologies, caractéristiques)
et leurs adjectifs associés, en travaillant uniquement en français.

CHANGEMENTS V1.2.0 (05/02/2026) :
- FIX CRITIQUE : Le tracking des mots consommés utilisait un set de MOTS au lieu
  d'un set d'INDICES de position. Conséquence : quand un même mot apparaissait dans
  deux tags distincts (ex: "classe i classe II"), la 2e occurrence du mot partagé
  ("classe") était rejetée car déjà dans le set. Maintenant on traque les indices.
- FIX : Calcul de position (pos_debut/pos_fin) via indices au lieu de find() qui
  pouvait retourner la mauvaise occurrence dans la chaîne.
- AMÉLIORATION : Mode verbose enrichi (mots analysés, positions, bilan, résidu)
- AMÉLIORATION : Raccourcis CLI -v et -d, aide affichée sans argument

CHANGEMENTS V1.1.0 (07/01/2026) :
- FIX : Passe le genre du tag (gn) à detadjs pour l'accord des adjectifs
- FIX : Inclut 'forme_accordee' dans les adjectifs retournés
- FIX : Correction du bug "béance antérieure" qui ne trouvait pas de résultats

CHANGEMENTS V2.0.0 (09/02/2026) :
- NOUVEAU : Support colonne 'cat' (catégorie) dans tags.csv V2
  Catégories : pathologie, traitement, biomécanique, fonction, diagnostic,
               anatomie, matériau, gestion
- NOUVEAU : 'cat' stockée dans tags_data et incluse dans le JSON de sortie
- NOUVEAU : Statistiques par catégorie en mode verbose
- La colonne 'cat' est optionnelle (rétro-compatible tags.csv V1)

ARCHITECTURE V4 - NOUVELLE STRUCTURE :
- Charge directement tags.csv (colonnes: t;gn;as;pts;cat)
- Charge directement adjectifs.csv (colonnes: a;f;mp;fp;pas)
- Génère en mémoire les structures équivalentes aux anciens syntags.csv/synadjs.csv
- Les patterns (pts/pas) sont des synonymes unidirectionnels
- Appelle detadjs.py en interne pour chaque tag détecté

FICHIERS DE RÉFÉRENCE :
    tags.csv :
        t   : forme canonique du tag
        gn  : genre/nombre (m, f, mp, fp)
        as  : adjectifs autorisés (séparés par virgule)
        pts : patterns tags (synonymes unidirectionnels, séparés par virgule)
        cat : catégorie (optionnel V2 : pathologie, traitement, biomécanique,
              fonction, diagnostic, anatomie, matériau, gestion)
    
    adjectifs.csv :
        a   : forme canonique (masculin singulier)
        f   : forme féminin singulier
        mp  : forme masculin pluriel
        fp  : forme féminin pluriel
        pas : patterns adjectifs (synonymes unidirectionnels)

FORMAT DE SORTIE JSON :
{
    "criteres": [
        {
            "type": "tag",
            "detecte": "beance anterieure",
            "canonique": "béance",
            "label": "Béance",
            "gn": "f",
            "cat": "pathologie",
            "sql": {
                "colonne": "canontags",
                "operateur": "=",
                "valeur": "béance"
            },
            "adjectifs": [
                {
                    "detecte": "anterieure",
                    "canonique": "antérieur",
                    "forme_accordee": "antérieure",
                    "sql": {"colonne": "canonadjs", "operateur": "=", "valeur": "antérieur"}
                }
            ]
        }
    ],
    "residu": "patients avec de moins de 30 ans",
    "question_standardisee": "..."
}
"""

import re
import csv
import sys
import os
import json
import io
from pathlib import Path

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

# Import de detadjs pour la détection des adjectifs
try:
    from detadjs import charger_adjectifs, detecter_adjectifs
except ImportError:
    # Si detadjs n'est pas disponible, on définit des stubs
    def charger_adjectifs(*args, **kwargs):
        return {'lookup': {}, 'adjectifs': {}}
    def detecter_adjectifs(*args, **kwargs):
        return {'adjectifs': [], 'mots_utilises': set()}


def charger_tags(fichier_tags, fichier_adjs=None, verbose=False, debug=False):
    """
    Charge les tags depuis tags.csv et les adjectifs depuis adjectifs.csv.
    Génère en mémoire les structures de recherche.
    
    Format tags.csv attendu : t;gn;as;pts[;cat]
        t   : forme canonique du tag
        gn  : genre/nombre (m, f, mp, fp)
        as  : adjectifs autorisés (séparés par virgule)
        pts : patterns (synonymes unidirectionnels, séparés par virgule)
        cat : catégorie (optionnel V2)
    
    Args:
        fichier_tags: Chemin vers tags.csv
        fichier_adjs: Chemin vers adjectifs.csv (optionnel)
        verbose: Afficher les résultats
        debug: Afficher les détails
        
    Returns:
        Tuple (tags_data, adjs_data)
        - tags_data: Dict avec 'lookup' et 'tags'
        - adjs_data: Dict des adjectifs
    """
    tags_data = {
        'lookup': [],
        'tags': {}
    }
    
    if not os.path.exists(fichier_tags):
        print(f"[ERREUR] Fichier introuvable: {os.path.abspath(fichier_tags)}")
        return tags_data, {}
    
    if debug:
        print(f"[DEBUG] dettags: Chargement depuis {os.path.abspath(fichier_tags)}")
    
    encodages = ["utf-8-sig", "utf-8", "windows-1252", "iso-8859-1"]
    
    for encodage in encodages:
        try:
            with open(fichier_tags, 'r', encoding=encodage, newline='') as f:
                lignes = f.readlines()
                
                lignes_filtrees = []
                for ligne in lignes:
                    ligne_strip = ligne.strip()
                    if not ligne_strip:
                        continue
                    if ligne_strip.startswith('#'):
                        continue
                    lignes_filtrees.append(ligne)
                
                if not lignes_filtrees:
                    continue
                
                reader = csv.DictReader(io.StringIO(''.join(lignes_filtrees)), delimiter=';')
                
                if not reader.fieldnames:
                    continue
                
                colonnes_requises = {'t', 'gn', 'as', 'pts'}
                if not colonnes_requises.issubset(set(reader.fieldnames)):
                    continue
                
                lookup_entries = []
                nb_tags = 0
                
                for row in reader:
                    canon = (row.get('t') or '').strip()
                    if not canon:
                        continue
                    
                    canon_lower = canon.lower()
                    gn = (row.get('gn') or 'm').strip().lower()  # Défaut: masculin
                    
                    adjs_raw = (row.get('as') or '').strip()
                    adjs_autorises = [a.strip() for a in adjs_raw.split(',') if a.strip()]
                    
                    patterns_raw = (row.get('pts') or '').strip()
                    patterns = [p.strip() for p in patterns_raw.split(',') if p.strip()]
                    
                    # Stocker avec le genre et la catégorie
                    cat = (row.get('cat') or '').strip().lower()  # V2 : catégorie (optionnel)
                    tags_data['tags'][canon_lower] = {
                        'canon': canon,
                        'gn': gn,  # IMPORTANT : genre pour l'accord
                        'cat': cat,  # V2 : catégorie (pathologie, traitement, etc.)
                        'adjs_autorises': adjs_autorises,
                        'patterns': patterns
                    }
                    
                    vus = set()
                    
                    std_canon = standardise(canon)
                    if std_canon:
                        nb_mots = len(std_canon.split())
                        lookup_entries.append((std_canon, canon, nb_mots))
                        vus.add(std_canon)
                    
                    for pattern in patterns:
                        if not pattern:
                            continue
                        std = standardise(pattern)
                        if std and std not in vus:
                            vus.add(std)
                            nb_mots = len(std.split())
                            lookup_entries.append((std, canon, nb_mots))
                    
                    nb_tags += 1
                
                lookup_entries.sort(key=lambda x: (-x[2], -len(x[0]), x[0]))
                
                seen = set()
                unique_lookup = []
                for std, canon, nb_mots in lookup_entries:
                    if std not in seen:
                        seen.add(std)
                        unique_lookup.append({'stdtag': std, 'canontag': canon, 'nb_mots': nb_mots})
                
                tags_data['lookup'] = unique_lookup
                
                if verbose:
                    print(f"  ✓ {nb_tags} tag(s) chargé(s), {len(unique_lookup)} entrées lookup")
                    # V2 : stats par catégorie
                    cats = {}
                    for info in tags_data['tags'].values():
                        c = info.get('cat', '') or '(sans catégorie)'
                        cats[c] = cats.get(c, 0) + 1
                    if any(c != '(sans catégorie)' for c in cats):
                        parts = [f"{c}={n}" for c, n in sorted(cats.items()) if c != '(sans catégorie)']
                        print(f"    Catégories : {', '.join(parts)}")
                
                break
                
        except (UnicodeDecodeError, UnicodeError):
            continue
        except Exception as e:
            if debug:
                print(f"[DEBUG] Erreur lecture {encodage}: {e}")
            continue
    
    # Charger les adjectifs
    adjs_data = {'lookup': {}, 'adjectifs': {}}
    if fichier_adjs and os.path.exists(fichier_adjs):
        adjs_data = charger_adjectifs(fichier_adjs, verbose=verbose, debug=debug)
    
    return tags_data, adjs_data


def detecter_tags(question, tags_data, adjs_data=None, verbose=False, debug=False):
    """
    Détecte les tags orthodontiques et leurs adjectifs dans une question.
    
    CHANGEMENT V1.1.0 : Passe le genre du tag à detadjs pour l'accord.
    
    Args:
        question: Texte de la question en langage naturel
        tags_data: Dict retourné par charger_tags
        adjs_data: Dict des adjectifs (optionnel)
        verbose: Afficher les résultats intermédiaires
        debug: Afficher tous les détails
        
    Returns:
        dict: {'criteres': [...], 'residu': str, 'question_standardisee': str}
    """
    question_norm = standardise(question)
    mots_question = question_norm.split()
    indices_utilises = set()  # FIX: on traque les INDICES de position, pas les mots
    criteres_detectes = []
    
    if debug:
        print(f"[DEBUG] dettags: Question originale: '{question}'")
        print(f"[DEBUG] dettags: Question normalisée: '{question_norm}'")
        print(f"[DEBUG] dettags: Mots indexés: {list(enumerate(mots_question))}")
    
    if adjs_data is None:
        adjs_data = {'lookup': {}, 'adjectifs': {}}
    
    lookup = tags_data.get('lookup', [])
    tags_info = tags_data.get('tags', {})
    
    if debug:
        print(f"[DEBUG] dettags: {len(lookup)} entrées lookup à tester")
    
    if verbose:
        print(f"  Analyse de {len(mots_question)} mot(s): {mots_question}")
        print(f"  Recherche parmi {len(lookup)} patterns de tags...")
    
    # Parcourir les tags (déjà triés par longueur décroissante)
    for tag_entry in lookup:
        stdtag = tag_entry['stdtag']
        canontag = tag_entry['canontag']
        mots_tag = stdtag.split()
        
        # Chercher le tag dans la question
        for i in range(len(mots_question) - len(mots_tag) + 1):
            match = True
            indices_candidats = []
            
            for j, mot_tag in enumerate(mots_tag):
                idx = i + j
                mot_question = mots_question[idx]
                
                # FIX: tester l'INDICE, pas le mot lui-même
                if mot_question != mot_tag or idx in indices_utilises:
                    match = False
                    break
                indices_candidats.append(idx)
            
            if match and indices_candidats:
                texte_detecte = ' '.join(mots_question[idx] for idx in indices_candidats)
                
                # Calculer la position exacte dans la chaîne normalisée
                # en comptant les caractères des mots + espaces précédents
                premier_idx = indices_candidats[0]
                pos_debut = sum(len(mots_question[k]) + 1 for k in range(premier_idx))
                pos_fin = pos_debut + len(texte_detecte)
                position_tag = {'debut': pos_debut, 'fin': pos_fin}
                
                if debug:
                    print(f"[DEBUG] dettags: Tag trouvé: '{texte_detecte}' aux indices {indices_candidats}, position texte [{pos_debut}:{pos_fin}]")
                
                if verbose:
                    print(f"  → Candidat trouvé: '{texte_detecte}' (mots aux positions {indices_candidats})")
                
                # FIX: marquer les INDICES comme utilisés
                for idx in indices_candidats:
                    indices_utilises.add(idx)
                
                # Récupérer les adjectifs autorisés ET LE GENRE pour ce tag
                tag_info = tags_info.get(canontag.lower(), {})
                adjs_autorises = tag_info.get('adjs_autorises', [])
                genre_tag = tag_info.get('gn', 'm')  # NOUVEAU V1.1.0 : récupérer le genre
                cat_tag = tag_info.get('cat', '')  # V2 : catégorie
                
                if debug:
                    print(f"[DEBUG] dettags: Genre du tag '{canontag}': {genre_tag}")
                
                # Chercher les adjectifs associés AVEC LE GENRE
                adjectifs_enrichis = []
                if adjs_data.get('lookup'):
                    # Construire le set de mots utilisés pour compatibilité detadjs
                    mots_utilises_pour_adjs = set(mots_question[idx] for idx in indices_utilises)
                    resultat_adjs = detecter_adjectifs(
                        question_norm, adjs_autorises, position_tag, adjs_data,
                        genre_tag=genre_tag,  # NOUVEAU V1.1.0 : passer le genre
                        mots_deja_utilises=mots_utilises_pour_adjs,
                        verbose=verbose, debug=debug
                    )
                    
                    # Convertir les adjectifs au format enrichi avec forme accordée
                    for adj in resultat_adjs.get('adjectifs', []):
                        adjectifs_enrichis.append({
                            'detecte': adj['detecte'],
                            'canonique': adj['canonique'],
                            'forme_accordee': adj.get('forme_accordee', adj['canonique']),  # NOUVEAU V1.1.0
                            'sql': {
                                'colonne': 'canonadjs',
                                'operateur': '=',
                                'valeur': adj['canonique']
                            }
                        })
                    
                    # Marquer les indices des mots d'adjectifs comme utilisés
                    for mot_adj in resultat_adjs.get('mots_utilises', set()):
                        for k, m in enumerate(mots_question):
                            if m == mot_adj and k not in indices_utilises:
                                indices_utilises.add(k)
                                break
                
                # Créer le critère
                critere = {
                    'type': 'tag',
                    'detecte': texte_detecte,
                    'canonique': canontag,
                    'label': canontag,
                    'gn': genre_tag,  # NOUVEAU V1.1.0 : inclure le genre dans le critère
                    'cat': cat_tag,  # V2 : catégorie (pathologie, traitement, etc.)
                    'sql': {
                        'colonne': 'canontags',
                        'operateur': '=',
                        'valeur': canontag
                    }
                }
                
                if adjectifs_enrichis:
                    critere['adjectifs'] = adjectifs_enrichis
                
                criteres_detectes.append(critere)
                
                if verbose or debug:
                    adjs_str = ', '.join([a['forme_accordee'] for a in adjectifs_enrichis]) if adjectifs_enrichis else 'aucun'
                    cat_str = f" [{cat_tag}]" if cat_tag else ""
                    print(f"  ✓ Tag: '{texte_detecte}' → '{canontag}' (genre={genre_tag}){cat_str} [adjs: {adjs_str}]")
                
                break
    
    # Calculer le résidu (mots dont l'indice n'est PAS dans indices_utilises)
    residu = ' '.join([mots_question[k] for k in range(len(mots_question)) if k not in indices_utilises])
    
    if verbose:
        print(f"  Bilan: {len(criteres_detectes)} tag(s) détecté(s), {len(indices_utilises)}/{len(mots_question)} mots consommés")
        if residu:
            print(f"  Résidu non consommé: '{residu}'")
    
    if debug:
        print(f"[DEBUG] dettags: {len(criteres_detectes)} critère(s) détecté(s)")
        print(f"[DEBUG] dettags: Indices utilisés: {sorted(indices_utilises)}")
        mots_utilises_debug = {k: mots_question[k] for k in sorted(indices_utilises)}
        print(f"[DEBUG] dettags: Mots consommés: {mots_utilises_debug}")
        print(f"[DEBUG] dettags: Résidu: '{residu}'")
    
    return {
        'criteres': criteres_detectes,
        'residu': residu,
        'question_standardisee': question_norm
    }


def identifier_tags(residu, tags_data, adjs_data, filtres, verbose=False, debug=False):
    """
    Wrapper de compatibilité avec signature standard pour detall.py.
    """
    if debug:
        print(f"[DEBUG] identifier_tags: Analyse du résidu: '{residu}'")
    
    resultat = detecter_tags(residu, tags_data, adjs_data, verbose=verbose, debug=debug)
    
    if 'criteres' not in filtres:
        filtres['criteres'] = []
    
    for critere in resultat['criteres']:
        filtres['criteres'].append(critere)
    
    return filtres, resultat['residu']


def traiter_fichier_batch(fichier_entree, tags_data, adjs_data, verbose=False, debug=False):
    """
    Traite un fichier de test batch et génère [nom_entrée]dettags.csv.
    
    Format de sortie : question;L1;L2;...;Ln (résumé transposé)
    """
    chemin_entree = Path(fichier_entree)
    nom_base = chemin_entree.stem
    module_name = Path(__pgm__).stem  # 'dettags'
    fichier_sortie = chemin_entree.parent / f"{nom_base}{module_name}.csv"
    
    print(f"Fichier d'entrée : {os.path.abspath(fichier_entree)}")
    print(f"Fichier de sortie: {os.path.abspath(fichier_sortie)}")
    print()
    
    lignes_entree = []
    col_indices = {}  # indices des colonnes résultat/commentaire
    commentaires = []
    
    encodages = ["utf-8-sig", "utf-8", "windows-1252"]
    
    for encodage in encodages:
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
        print(f"[ERREUR] Aucune ligne à traiter")
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
        
        resultat = detecter_tags(question, tags_data, adjs_data, verbose=verbose, debug=debug)
        
        tags = []
        adjectifs = []
        adjs_accordes = []
        
        for critere in resultat['criteres']:
            tags.append(critere.get('canonique', ''))
            for adj in critere.get('adjectifs', []):
                adjectifs.append(adj.get('canonique', ''))
                adjs_accordes.append(adj.get('forme_accordee', adj.get('canonique', '')))
        
        # Construire les lignes du résumé pour le CSV
        lignes_resume = []
        if resultat['criteres']:
            for j, c in enumerate(resultat['criteres'], 1):
                label = c.get('canonique', c.get('label', '?'))
                cat = c.get('cat', '')
                cat_str = f" ({cat})" if cat else ''
                adjs = c.get('adjectifs', [])
                adjs_str = ''
                if adjs:
                    adjs_noms = ', '.join(a.get('canonique', str(a)) if isinstance(a, dict) else str(a) for a in adjs)
                    adjs_str = f" [{adjs_noms}]"
                lignes_resume.append(f"[tag] {label}{cat_str}{adjs_str}")
        lignes_resume.append(f"Résidu: '{resultat['residu']}'")
        
        resultats.append({
            'question': question,
            'resultat': _val_resultat,
            'commentaire': _val_commentaire,
            'lignes': lignes_resume
        })
        
        # Mini-résumé pour chaque question (toujours affiché)
        print(f"  [{i+1}/{len(lignes_entree)}] \"{question}\"")
        if resultat['criteres']:
            for j, c in enumerate(resultat['criteres'], 1):
                label = c.get('canonique', c.get('label', '?'))
                cat = c.get('cat', '')
                cat_str = f" ({cat})" if cat else ''
                adjs = c.get('adjectifs', [])
                adjs_str = ''
                if adjs:
                    adjs_noms = ', '.join(a.get('canonique', str(a)) if isinstance(a, dict) else str(a) for a in adjs)
                    adjs_str = f" [{adjs_noms}]"
                print(f"        {j}. [tag] {label}{cat_str}{adjs_str}")
        else:
            print(f"        (aucun tag)")
        print(f"        Résidu: '{resultat['residu']}'")
        print()
    
    # Déterminer le nombre max de colonnes L
    max_l = max((len(r['lignes']) for r in resultats), default=0)
    entete_l = ['question', 'résultat', 'commentaire'] + [f'L{i+1}' for i in range(max_l)]
    
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


def trouver_fichier_batch(nom_fichier):
    """Cherche un fichier batch dans plusieurs répertoires possibles."""
    chemin = Path(nom_fichier)
    if chemin.exists():
        return chemin
    
    repertoires = [
        Path('.'),
        Path('tests'),
        Path('c:/g/tests'),
        Path('c:/cx/tests'),
    ]
    
    nom_seul = Path(nom_fichier).name
    
    for rep in repertoires:
        chemin_candidat = rep / nom_seul
        if chemin_candidat.exists():
            return chemin_candidat
    
    return None


def main():
    """Point d'entrée CLI."""
    print(f"╔════════════════════════════════════════════════════════════════")
    print(f"║ {__pgm__} V{__version__} - {__date__}")
    print(f"║ Détection des tags orthodontiques + adjectifs")
    print(f"║ V2.0.0 : Support catégories (cat), tracking par indices")
    print(f"╚════════════════════════════════════════════════════════════════")
    print()
    
    import argparse
    parser = argparse.ArgumentParser(
        description="Détecte les tags et adjectifs dans une question"
    )
    parser.add_argument('question', nargs='?', help='Question en langage naturel OU fichier .csv')
    parser.add_argument('-v', '--verbose', action='store_true', help='Affichage modéré')
    parser.add_argument('-d', '--debug', action='store_true', help='Affichage complet')
    
    args = parser.parse_args()
    
    if not args.question:
        parser.print_help()
        print()
        print("Exemples :")
        print(f'  python {__pgm__} "classe i classe II" -v')
        print(f'  python {__pgm__} "béance antérieure" -d')
        print(f'  python {__pgm__} testtagsin.csv -v')
        return 0
    
    script_dir = Path(__file__).parent
    tags_path = script_dir / "refs" / "tags.csv"
    adjs_path = script_dir / "refs" / "adjectifs.csv"
    
    if not tags_path.exists():
        for alt in [Path("c:/g/refs/tags.csv"), Path("c:/cx/refs/tags.csv")]:
            if alt.exists():
                tags_path = alt
                break
    if not adjs_path.exists():
        for alt in [Path("c:/g/refs/adjectifs.csv"), Path("c:/cx/refs/adjectifs.csv")]:
            if alt.exists():
                adjs_path = alt
                break
    
    print("Chargement des références...")
    tags_data, adjs_data = charger_tags(
        str(tags_path), 
        str(adjs_path),
        verbose=True,
        debug=args.debug
    )
    print()
    
    est_fichier_batch = args.question.endswith('.csv')
    
    if est_fichier_batch:
        fichier_batch = trouver_fichier_batch(args.question)
        
        if fichier_batch is None:
            print(f"[ERREUR] Fichier non trouvé : {args.question}")
            return 1
        
        print(f"Mode BATCH - Traitement de {fichier_batch.absolute()}")
        print("-" * 70)
        
        nb_lignes, _ = traiter_fichier_batch(
            str(fichier_batch),
            tags_data,
            adjs_data,
            verbose=args.verbose,
            debug=args.debug
        )
        return 0 if nb_lignes > 0 else 1
    
    else:
        print(f"Question: \"{args.question}\"")
        print()
        
        resultat = detecter_tags(
            args.question,
            tags_data,
            adjs_data,
            verbose=args.verbose,
            debug=args.debug
        )
        
        print()
        print("═" * 70)
        print("RÉSUMÉ")
        print("═" * 70)
        print(f"Nb critères : {len(resultat['criteres'])}")
        
        for i, c in enumerate(resultat['criteres'], 1):
            label = c.get('canonique', '?')
            genre = c.get('gn', '?')
            cat = c.get('cat', '')
            adjs = c.get('adjectifs', [])
            adjs_str = f" [{', '.join(a.get('forme_accordee', a.get('canonique', '')) for a in adjs)}]" if adjs else ""
            cat_str = f" ({cat})" if cat else ""
            print(f"  {i}. {label} (genre={genre}){cat_str}{adjs_str}")
        
        print(f"\nRésidu: '{resultat['residu']}'")
        
        print()
        print("═" * 70)
        print("RÉSULTAT (JSON)")
        print("═" * 70)
        print(json.dumps(resultat, indent=2, ensure_ascii=False))
        
        return 0


if __name__ == '__main__':
    sys.exit(main())
