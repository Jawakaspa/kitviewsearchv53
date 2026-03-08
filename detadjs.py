# detadjs.py V1.0.11 - 07/01/2026 13:54:48
__pgm__ = "detadjs.py"
__version__ = "1.0.11"
__date__ = "07/01/2026 13:54:48"

"""
Module de détection des adjectifs qualifiant un tag orthodontique.

Ce module analyse une question pour détecter les adjectifs associés à un tag
donné, en cherchant à proximité de la position du tag dans la question.

CHANGEMENTS V1.1.0 (07/01/2026) :
- NOUVEAU : Paramètre genre_tag pour accorder l'adjectif au genre du tag
- NOUVEAU : Champ 'forme_accordee' dans le retour (avec accents, accordé)
- FIX : Correction du bug "béance antérieure" → cherchait "beance anterieur"

ARCHITECTURE V4 - NOUVELLE STRUCTURE :
- Charge directement adjectifs.csv (colonnes: a;f;mp;fp;pas)
- Génère en mémoire la structure équivalente aux anciens synadjs.csv
- Les patterns (pas) sont des synonymes unidirectionnels vers l'adjectif
- Travaille exclusivement en français (traduction gérée en amont/aval)
- Appelé par dettags.py pour chaque tag détecté

FICHIER adjectifs.csv :
    a         : forme canonique masculine singulier
    f         : forme féminin singulier
    mp        : forme masculin pluriel
    fp        : forme féminin pluriel
    pas       : patterns adjectifs (synonymes unidirectionnels, séparés par ,)

ALGORITHME DE PROXIMITÉ :
1. On reçoit le tag détecté et sa position dans la question
2. On cherche les adjectifs compatibles avec ce tag (via liste adjs_autorises)
3. On ne garde que les adjectifs proches du tag (fenêtre de N mots)
4. Les adjectifs sont retirés du résidu

FORMAT DE SORTIE :
{
    "adjectifs": [
        {"detecte": "antérieure", "canonique": "antérieur", "forme_accordee": "antérieure", "standardise": "anterieure"},
        {"detecte": "sévère", "canonique": "sévère", "forme_accordee": "sévère", "standardise": "severe"}
    ],
    "mots_utilises": set()  # Mots à retirer du résidu
}

Usage en import (depuis dettags.py) :
    from detadjs import charger_adjectifs, detecter_adjectifs
    adjs_data = charger_adjectifs('refs/adjectifs.csv')
    resultat = detecter_adjectifs(question, adjs_autorises, position_tag, adjs_data, genre_tag='f')

Usage CLI unitaire :
    python detadjs.py "béance" "patients avec béance gauche sévère"
    
Usage CLI batch :
    python detadjs.py tests.csv
    # Le fichier doit avoir les colonnes : tag;question
    # Sortie automatique : tests_out.csv
"""

import re
import csv
import sys
import os
import json
import io
from pathlib import Path

# Import de standardise (doit être dans le même répertoire ou PYTHONPATH)
try:
    from standardise import standardise
except ImportError:
    # Fallback si standardise.py n'est pas disponible
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


# Configuration
FENETRE_PROXIMITE = 5  # Nombre de mots avant/après le tag pour chercher les adjectifs


def charger_adjectifs(fichier_csv, verbose=False, debug=False):
    """
    Charge les adjectifs depuis adjectifs.csv et génère la structure de recherche.
    
    Format CSV attendu : a;f;mp;fp;pas
        a   : forme canonique (masculin singulier)
        f   : forme féminin singulier
        mp  : forme masculin pluriel
        fp  : forme féminin pluriel
        pas : patterns (synonymes unidirectionnels, séparés par virgule)
    
    Génère en mémoire une structure équivalente à l'ancien synadjs.csv :
        {stdadj: canonadj} pour chaque forme et pattern
    
    Args:
        fichier_csv: Chemin vers adjectifs.csv
        verbose: Afficher les informations de chargement
        debug: Afficher les détails complets
        
    Returns:
        Dict avec:
        - 'lookup': {stdadj: canonadj} pour recherche rapide
        - 'adjectifs': {canon_lower: {'canon': str, 'm': str, 'f': str, 'mp': str, 'fp': str, 'formes': [str], 'patterns': [str]}}
    """
    result = {
        'lookup': {},      # {stdadj: canonadj} - tri par longueur décroissante
        'adjectifs': {}    # {canon_lower: info complète}
    }
    
    if not os.path.exists(fichier_csv):
        print(f"[ERREUR] Fichier adjectifs introuvable: {os.path.abspath(fichier_csv)}")
        return result
    
    if debug:
        print(f"[DEBUG] detadjs: Chargement depuis {os.path.abspath(fichier_csv)}")
    
    # Essayer différents encodages
    encodages = ["utf-8-sig", "utf-8", "windows-1252", "iso-8859-1"]
    
    for encodage in encodages:
        try:
            with open(fichier_csv, 'r', encoding=encodage, newline='') as f:
                # Lire toutes les lignes et filtrer les commentaires
                lignes = f.readlines()
                
                # Trouver les lignes non-commentaires
                lignes_filtrees = []
                for ligne in lignes:
                    ligne_strip = ligne.strip()
                    if not ligne_strip:
                        continue
                    if ligne_strip.startswith('#'):
                        continue
                    lignes_filtrees.append(ligne)
                
                if not lignes_filtrees:
                    if debug:
                        print(f"[DEBUG] Aucune ligne de données trouvée")
                    continue
                
                # Créer un reader à partir des lignes filtrées
                reader = csv.DictReader(io.StringIO(''.join(lignes_filtrees)), delimiter=';')
                
                # Vérifier les colonnes requises
                if not reader.fieldnames:
                    continue
                    
                colonnes_requises = {'a', 'f', 'mp', 'fp', 'pas'}
                if not colonnes_requises.issubset(set(reader.fieldnames)):
                    if debug:
                        print(f"[DEBUG] Colonnes manquantes. Trouvées: {reader.fieldnames}, requises: {colonnes_requises}")
                    continue
                
                lookup_entries = []  # Liste pour tri ultérieur
                nb_adjs = 0
                
                for row in reader:
                    # Forme canonique (masculin singulier)
                    canon = (row.get('a') or '').strip()
                    if not canon:
                        continue
                    
                    canon_lower = canon.lower()
                    
                    # Toutes les formes accordées
                    forme_f = (row.get('f') or '').strip()
                    forme_mp = (row.get('mp') or '').strip()
                    forme_fp = (row.get('fp') or '').strip()
                    
                    # Patterns (synonymes unidirectionnels)
                    patterns_raw = (row.get('pas') or '').strip()
                    patterns = [p.strip() for p in patterns_raw.split(',') if p.strip()]
                    
                    # Collecter toutes les formes
                    toutes_formes = [canon]
                    if forme_f:
                        toutes_formes.append(forme_f)
                    if forme_mp:
                        toutes_formes.append(forme_mp)
                    if forme_fp:
                        toutes_formes.append(forme_fp)
                    
                    # Stocker l'info complète avec les 4 formes explicites
                    result['adjectifs'][canon_lower] = {
                        'canon': canon,
                        'formes': toutes_formes,
                        'patterns': patterns,
                        'm': canon,           # masculin singulier
                        'f': forme_f or canon,  # féminin singulier (fallback sur masculin)
                        'mp': forme_mp or canon,  # masculin pluriel
                        'fp': forme_fp or forme_f or canon  # féminin pluriel (fallback sur f puis m)
                    }
                    
                    # Créer les entrées lookup pour chaque forme et pattern
                    vus = set()
                    
                    for forme in toutes_formes + patterns:
                        if not forme:
                            continue
                        std = standardise(forme)
                        if std and std not in vus:
                            vus.add(std)
                            lookup_entries.append((std, canon))
                            if debug:
                                print(f"[DEBUG] lookup: '{std}' -> '{canon}'")
                    
                    nb_adjs += 1
                
                # Trier par longueur décroissante (multi-mots d'abord)
                lookup_entries.sort(key=lambda x: (-len(x[0].split()), -len(x[0]), x[0]))
                
                # Construire le lookup ordonné (dict conserve l'ordre en Python 3.7+)
                for std, canon in lookup_entries:
                    if std not in result['lookup']:
                        result['lookup'][std] = canon
                
                if verbose:
                    print(f"  ✓ {nb_adjs} adjectifs chargés, {len(result['lookup'])} entrées lookup")
                
                return result
                
        except (UnicodeDecodeError, UnicodeError):
            continue
        except Exception as e:
            if debug:
                print(f"[DEBUG] Erreur lecture {encodage}: {e}")
            continue
    
    print(f"[ERREUR] Impossible de lire {os.path.abspath(fichier_csv)}")
    return result


def _get_forme_accordee(adjs_data, canon_adj, genre_tag):
    """
    Retourne la forme accordée d'un adjectif selon le genre du tag.
    
    Args:
        adjs_data: Données des adjectifs
        canon_adj: Forme canonique de l'adjectif (masculin singulier)
        genre_tag: Genre du tag (m, f, mp, fp)
        
    Returns:
        Forme accordée de l'adjectif (avec accents)
    """
    adjectifs_info = adjs_data.get('adjectifs', {})
    adj_info = adjectifs_info.get(canon_adj.lower(), {})
    
    if not adj_info:
        # Adjectif non trouvé, retourner le canonique
        return canon_adj
    
    # Mapper le genre vers la colonne correspondante
    # m -> masculin singulier (a)
    # f -> féminin singulier (f)
    # mp -> masculin pluriel (mp)
    # fp -> féminin pluriel (fp)
    genre_map = {
        'm': 'm',
        'f': 'f',
        'mp': 'mp',
        'fp': 'fp'
    }
    
    genre_cle = genre_map.get(genre_tag, 'm')  # Défaut: masculin singulier
    forme = adj_info.get(genre_cle, adj_info.get('canon', canon_adj))
    
    return forme if forme else canon_adj


def detecter_adjectifs(question, adjs_autorises, position_tag, adjs_data, 
                       genre_tag='m', mots_deja_utilises=None, verbose=False, debug=False):
    """
    Détecte les adjectifs associés à un tag dans une question.
    
    L'algorithme cherche les adjectifs compatibles avec le tag donné,
    dans une fenêtre de proximité autour de la position du tag.
    
    Args:
        question: Texte de la question (forme originale ou standardisée)
        adjs_autorises: Liste des adjectifs autorisés pour ce tag (formes canoniques)
        position_tag: Dict {'debut': int, 'fin': int} position du tag dans la question standardisée
        adjs_data: Données des adjectifs (retournées par charger_adjectifs)
        genre_tag: Genre du tag (m, f, mp, fp) pour accorder l'adjectif - NOUVEAU V1.1.0
        mots_deja_utilises: Set des mots déjà utilisés par d'autres détections (optionnel)
        verbose: Afficher les résultats intermédiaires
        debug: Afficher tous les détails
        
    Returns:
        dict: {
            'adjectifs': [
                {
                    'detecte': str,         # Forme détectée dans la question
                    'canonique': str,       # Forme canonique (masculin singulier)
                    'forme_accordee': str,  # Forme accordée au genre du tag (NOUVEAU)
                    'standardise': str      # Forme standardisée (sans accents)
                },
                ...
            ],
            'mots_utilises': set()  # Mots à retirer du résidu
        }
    """
    question_norm = standardise(question)
    mots_question = question_norm.split()
    
    if debug:
        print(f"[DEBUG] detadjs: Question normalisée: '{question_norm}'")
        print(f"[DEBUG] detadjs: Adjectifs autorisés: {adjs_autorises}")
        print(f"[DEBUG] detadjs: Position tag: {position_tag}")
        print(f"[DEBUG] detadjs: Genre tag: {genre_tag}")
        if mots_deja_utilises:
            print(f"[DEBUG] detadjs: Mots déjà utilisés: {mots_deja_utilises}")
    
    if not adjs_autorises:
        return {'adjectifs': [], 'mots_utilises': set()}
    
    lookup = adjs_data.get('lookup', {})
    adjectifs_info = adjs_data.get('adjectifs', {})
    
    # Construire la liste des entrées lookup applicables à ce tag
    # On filtre pour ne garder que les adjectifs autorisés
    adjs_autorises_lower = set(a.lower() for a in adjs_autorises)
    
    entries_applicables = []
    for stdadj, canonadj in lookup.items():
        if canonadj.lower() in adjs_autorises_lower:
            entries_applicables.append((stdadj, canonadj))
    
    if debug:
        print(f"[DEBUG] detadjs: {len(entries_applicables)} entrées lookup applicables")
    
    if not entries_applicables:
        return {'adjectifs': [], 'mots_utilises': set()}
    
    # Trouver l'index du mot du tag dans la question
    pos_debut = position_tag.get('debut', 0) if position_tag else 0
    
    # Calculer l'index du mot à partir de la position caractère
    texte_avant = question_norm[:pos_debut]
    mots_avant = len(texte_avant.split()) if texte_avant.strip() else 0
    index_tag = mots_avant
    
    if debug:
        print(f"[DEBUG] detadjs: Index du tag dans les mots: {index_tag}")
    
    # Définir la fenêtre de recherche
    debut_fenetre = max(0, index_tag - FENETRE_PROXIMITE)
    fin_fenetre = min(len(mots_question), index_tag + FENETRE_PROXIMITE + 1)
    
    if debug:
        print(f"[DEBUG] detadjs: Fenêtre de recherche: mots[{debut_fenetre}:{fin_fenetre}]")
        print(f"[DEBUG] detadjs: Mots dans la fenêtre: {mots_question[debut_fenetre:fin_fenetre]}")
    
    adjectifs_detectes = []
    mots_utilises = set()
    
    # Intégrer les mots déjà utilisés pour ne pas les réutiliser
    mots_exclus = set(mots_deja_utilises) if mots_deja_utilises else set()
    
    # Chercher chaque adjectif dans la fenêtre (déjà triés par longueur décroissante)
    for stdadj, canonadj in entries_applicables:
        mots_adj = stdadj.split()
        
        # Chercher dans la fenêtre
        for i in range(debut_fenetre, fin_fenetre - len(mots_adj) + 1):
            # Vérifier si les mots correspondent et ne sont pas déjà utilisés
            match = True
            mots_candidats = []
            
            for j, mot_adj in enumerate(mots_adj):
                idx = i + j
                if idx >= len(mots_question):
                    match = False
                    break
                mot_question = mots_question[idx]
                # Vérifier contre mots_utilises ET mots_exclus (mots déjà pris par d'autres tags)
                if mot_question != mot_adj or mot_question in mots_utilises or mot_question in mots_exclus:
                    match = False
                    break
                mots_candidats.append(mot_question)
            
            if match and mots_candidats:
                # Adjectif trouvé !
                # Calculer la forme accordée selon le genre du tag
                forme_accordee = _get_forme_accordee(adjs_data, canonadj, genre_tag)
                
                adjectifs_detectes.append({
                    'detecte': ' '.join(mots_candidats),
                    'canonique': canonadj,
                    'forme_accordee': forme_accordee,  # NOUVEAU V1.1.0
                    'standardise': stdadj
                })
                
                for mot in mots_candidats:
                    mots_utilises.add(mot)
                
                if verbose or debug:
                    print(f"  ✓ Adjectif détecté: '{stdadj}' → canonique='{canonadj}', accordé='{forme_accordee}' (genre={genre_tag})")
                
                break  # Passer à l'adjectif suivant
    
    if debug:
        print(f"[DEBUG] detadjs: {len(adjectifs_detectes)} adjectif(s) détecté(s)")
        print(f"[DEBUG] detadjs: Mots utilisés: {mots_utilises}")
    
    return {
        'adjectifs': adjectifs_detectes,
        'mots_utilises': mots_utilises
    }


def traiter_fichier_batch(fichier_entree, adjs_data, tags_data=None, verbose=False, debug=False):
    """
    Traite un fichier de test batch et génère [nom_entrée]detadjs.csv.
    
    Format d'entrée : tag;question
    Format de sortie : tag;question;L1;L2;...;Ln (résumé transposé)
    """
    chemin_entree = Path(fichier_entree)
    nom_base = chemin_entree.stem
    module_name = Path(__pgm__).stem  # 'detadjs'
    fichier_sortie = chemin_entree.parent / f"{nom_base}{module_name}.csv"
    
    print(f"Fichier d'entrée : {os.path.abspath(fichier_entree)}")
    print(f"Fichier de sortie: {os.path.abspath(fichier_sortie)}")
    print()
    
    # Lire le fichier d'entrée
    lignes_entree = []
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
                    if 'tag' in (row[0] or '').lower() and 'question' in (row[1] if len(row) > 1 else '').lower():
                        continue
                    lignes_entree.append(row)
            break
        except (UnicodeDecodeError, UnicodeError):
            continue
    
    if not lignes_entree:
        print(f"[ERREUR] Aucune ligne à traiter")
        return 0, None
    
    print(f"{len(lignes_entree)} ligne(s) à traiter")
    print("-" * 70)
    
    resultats = []
    
    for idx, row in enumerate(lignes_entree):
        tag = (row[0] or '').strip() if len(row) > 0 else ''
        question = (row[1] or '').strip() if len(row) > 1 else ''
        
        if not question:
            continue
        
        if not tag:
            resultats.append({
                'tag': '',
                'question': question,
                'lignes': ['(pas de tag)']
            })
            continue
        
        # Récupérer les adjectifs autorisés et le genre pour ce tag
        adjs_autorises = []
        genre_tag = 'm'  # Défaut
        if tags_data:
            tag_lower = tag.lower()
            for t, info in tags_data.get('tags', {}).items():
                if t == tag_lower or info.get('canon', '').lower() == tag_lower:
                    adjs_autorises = info.get('adjs_autorises', [])
                    genre_tag = info.get('gn', 'm')
                    break
        
        # Si pas de tags_data ou pas d'adjs spécifiés, utiliser tous les adjectifs
        if not adjs_autorises:
            adjs_autorises = list(adjs_data.get('adjectifs', {}).keys())
        
        # Simuler une position (début de la question pour le test)
        question_norm = standardise(question)
        tag_norm = standardise(tag)
        pos = question_norm.find(tag_norm)
        position_tag = {'debut': pos, 'fin': pos + len(tag_norm)} if pos >= 0 else {'debut': 0, 'fin': 0}
        
        # Détecter les adjectifs
        resultat = detecter_adjectifs(
            question, adjs_autorises, position_tag, adjs_data,
            genre_tag=genre_tag,
            verbose=verbose, debug=debug
        )
        
        adjs = resultat['adjectifs']
        
        # Construire les lignes du résumé pour le CSV
        lignes_resume = []
        if adjs:
            for j, a in enumerate(adjs, 1):
                canon = a.get('canonique', '?')
                accord = a.get('forme_accordee', '')
                accord_str = f" → {accord}" if accord != canon else ''
                lignes_resume.append(f"[adj] {canon}{accord_str}")
        else:
            lignes_resume.append("(aucun adjectif)")
        
        resultats.append({
            'tag': tag,
            'question': question,
            'lignes': lignes_resume
        })
        
        # Mini-résumé pour chaque question (toujours affiché)
        print(f"  [{idx+1}/{len(lignes_entree)}] \"{question}\" (tag: {tag})")
        if adjs:
            for j, a in enumerate(adjs, 1):
                canon = a.get('canonique', '?')
                accord = a.get('forme_accordee', '')
                accord_str = f" → {accord}" if accord != canon else ''
                print(f"        {j}. [adj] {canon}{accord_str}")
        else:
            print(f"        (aucun adjectif)")
        print()
    
    # Déterminer le nombre max de colonnes L
    max_l = max((len(r['lignes']) for r in resultats), default=0)
    entete_l = ['tag', 'question'] + [f'L{i+1}' for i in range(max_l)]
    
    # Écrire le fichier de sortie
    with open(fichier_sortie, 'w', encoding='utf-8-sig', newline='') as f:
        writer = csv.writer(f, delimiter=';')
        
        for comm in commentaires:
            while len(comm) < len(entete_l):
                comm.append('')
            writer.writerow(comm)
        
        writer.writerow(entete_l)
        
        for res in resultats:
            row = [res['tag'], res['question']] + res['lignes']
            while len(row) < len(entete_l):
                row.append('')
            writer.writerow(row)
    
    print("-" * 70)
    print(f"✓ {len(resultats)} lignes traitées → {os.path.abspath(fichier_sortie)}")
    
    return len(resultats), fichier_sortie


def main():
    """Point d'entrée CLI."""
    print(f"╔════════════════════════════════════════════════════════════════")
    print(f"║ {__pgm__} V{__version__} - {__date__}")
    print(f"║ Détection des adjectifs qualifiant un tag orthodontique")
    print(f"║ NOUVEAU V1.1.0 : Accord en genre (m/f/mp/fp)")
    print(f"╚════════════════════════════════════════════════════════════════")
    print()
    
    # Analyse des arguments
    args = sys.argv[1:]
    
    verbose = '--verbose' in args
    debug = '--debug' in args
    args = [a for a in args if a not in ('--verbose', '--debug')]
    
    if len(args) < 1:
        print("Usage:")
        print(f"  python {__pgm__} \"tag\" \"question\"        # Test unitaire")
        print(f"  python {__pgm__} fichier.csv              # Test batch")
        print()
        print("Options:")
        print("  --verbose   Affichage modéré (résultats)")
        print("  --debug     Affichage complet (tout)")
        print()
        print("Exemples:")
        print(f"  python {__pgm__} \"béance\" \"patients avec béance gauche sévère\"")
        print(f"  python {__pgm__} tests_adjs.csv")
        return 1
    
    # Déterminer le mode (batch ou unitaire)
    est_batch = args[0].endswith('.csv')
    
    # Chercher le fichier adjectifs.csv
    chemins_possibles = [
        Path("refs/adjectifs.csv"),
        Path("adjectifs.csv"),
        Path(__file__).parent / "refs" / "adjectifs.csv",
        Path("c:/g/refs/adjectifs.csv"),
        Path("c:/cx/refs/adjectifs.csv"),
    ]
    
    adjs_path = None
    for chemin in chemins_possibles:
        if chemin.exists():
            adjs_path = str(chemin)
            break
    
    if not adjs_path:
        print("[ERREUR] Fichier adjectifs.csv introuvable")
        print("  Chemins testés:")
        for c in chemins_possibles:
            print(f"    - {os.path.abspath(c)}")
        return 1
    
    print(f"Fichier adjectifs.csv: {os.path.abspath(adjs_path)}")
    print()
    
    # Charger les adjectifs
    adjs_data = charger_adjectifs(adjs_path, verbose=verbose, debug=debug)
    
    if not adjs_data.get('lookup'):
        print("[ERREUR] Aucun adjectif chargé")
        return 1
    
    print()
    
    if est_batch:
        # Mode batch
        fichier_batch = args[0]
        
        # Chercher le fichier
        chemins_fichier = [
            Path(fichier_batch),
            Path("tests") / fichier_batch,
            Path(__file__).parent / "tests" / fichier_batch,
        ]
        
        fichier_trouve = None
        for chemin in chemins_fichier:
            if chemin.exists():
                fichier_trouve = str(chemin)
                break
        
        if not fichier_trouve:
            print(f"[ERREUR] Fichier introuvable: {fichier_batch}")
            return 1
        
        nb_lignes, _ = traiter_fichier_batch(
            fichier_trouve, adjs_data,
            verbose=verbose, debug=debug
        )
        return 0 if nb_lignes > 0 else 1
    
    else:
        # Mode unitaire : tag et question
        if len(args) < 2:
            print("[ERREUR] Mode unitaire requiert: tag et question")
            print(f"  Exemple: python {__pgm__} \"béance\" \"patients avec béance gauche\"")
            return 1
        
        tag = args[0]
        question = args[1]
        
        print(f"Tag      : \"{tag}\"")
        print(f"Question : \"{question}\"")
        print()
        
        # Trouver la position du tag
        question_norm = standardise(question)
        tag_norm = standardise(tag)
        pos = question_norm.find(tag_norm)
        position_tag = {'debut': pos, 'fin': pos + len(tag_norm)} if pos >= 0 else {'debut': 0, 'fin': 0}
        
        # Pour le test CLI, utiliser tous les adjectifs comme autorisés
        # et genre féminin par défaut pour "béance"
        adjs_autorises = list(adjs_data.get('adjectifs', {}).keys())
        
        # Détecter le genre du tag (simple heuristique pour le test CLI)
        genre_tag = 'f' if tag.lower() in ['béance', 'beance', 'classe', 'occlusion', 'malocclusion'] else 'm'
        
        # Détecter les adjectifs
        resultat = detecter_adjectifs(
            question, adjs_autorises, position_tag, adjs_data,
            genre_tag=genre_tag,
            verbose=verbose, debug=debug
        )
        
        # Afficher le résultat
        print()
        print("═" * 70)
        print("RÉSULTAT (JSON)")
        print("═" * 70)
        
        # Convertir set en list pour JSON
        resultat_json = {
            'adjectifs': resultat['adjectifs'],
            'mots_utilises': list(resultat['mots_utilises'])
        }
        print(json.dumps(resultat_json, indent=2, ensure_ascii=False))
        
        return 0


if __name__ == '__main__':
    sys.exit(main())
