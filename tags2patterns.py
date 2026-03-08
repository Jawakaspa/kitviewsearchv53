# tags2patterns.py V1.0.0 - 27/12/2025 22:09:00
__pgm__ = "tags2patterns.py"
__version__ = "1.0.0"
__date__ = "27/12/2025 22:09:00"

"""
Transforme tagsadjs.csv en deux fichiers de patterns :
- patternstagsfr.csv : synonymes des tags pour dettags.py
- patternsadjsfr.csv : synonymes des adjectifs pour detadjs.py

Usage:
  python tags2patterns.py                    # Exécution standard
  python tags2patterns.py --verbose          # Affichage détaillé
  python tags2patterns.py --debug            # Affichage complet
"""

import sys
import csv
import io
from pathlib import Path
from datetime import datetime

# Import obligatoire de standardise - pas de fallback
try:
    from standardise import standardise
except ImportError:
    print("=" * 70)
    print("ERREUR FATALE : Module 'standardise.py' introuvable")
    print("=" * 70)
    print("Ce module est obligatoire. Vérifiez qu'il est présent dans :")
    print("  - Le répertoire courant")
    print("  - Le répertoire du script")
    print("  - Le PYTHONPATH")
    sys.exit(1)


# Colonnes obligatoires
COLONNES_OBLIGATOIRES = ['canon', 'type', 'Xgn', 'synonymes', 'adjs', 'm', 'f', 'mp', 'fp']

# Valeurs valides pour Xgn
VALEURS_XGN_VALIDES = {'m', 'f', 'mp', 'fp', ''}


def filtrer_lignes_commentaires(contenu: str) -> str:
    """
    Filtre les lignes de commentaires (commençant par #) d'un contenu CSV.
    Retourne le contenu nettoyé.
    """
    lignes = contenu.splitlines(keepends=True)
    lignes_filtrees = [ligne for ligne in lignes if not ligne.lstrip().startswith('#')]
    return ''.join(lignes_filtrees)


def charger_tagsadjs(fichier_csv: str | Path, verbose: bool = False, debug: bool = False) -> tuple:
    """
    Charge et valide le fichier tagsadjs.csv.
    
    Args:
        fichier_csv: Chemin vers le fichier
        verbose: Affichage détaillé
        debug: Affichage complet
        
    Returns:
        (tags, adjectifs, avertissements)
        - tags: liste de dicts pour les lignes type='p'
        - adjectifs: dict {canon_lower: dict_adjectif}
        - avertissements: liste des warnings
        
    Raises:
        SystemExit si erreur fatale
    """
    fichier = Path(fichier_csv)
    
    if not fichier.exists():
        print("=" * 70)
        print("ERREUR FATALE : Fichier introuvable")
        print("=" * 70)
        print(f"  Fichier : {fichier.absolute()}")
        sys.exit(1)
    
    if verbose or debug:
        print(f"[INFO] Chargement de {fichier.absolute()}")
    
    # Lecture du fichier avec gestion encodage
    contenu = None
    encodings = ['utf-8-sig', 'utf-8', 'latin-1', 'windows-1252']
    
    for enc in encodings:
        try:
            with open(fichier, 'r', encoding=enc) as f:
                contenu = f.read()
            if debug:
                print(f"[DEBUG] Encodage détecté : {enc}")
            break
        except UnicodeDecodeError:
            continue
    
    if contenu is None:
        print("=" * 70)
        print("ERREUR FATALE : Impossible de lire le fichier")
        print("=" * 70)
        print(f"  Fichier : {fichier.absolute()}")
        print("  Encodages testés :", ", ".join(encodings))
        sys.exit(1)
    
    # Filtrer les commentaires
    contenu_filtre = filtrer_lignes_commentaires(contenu)
    
    # Parser le CSV
    reader = csv.DictReader(io.StringIO(contenu_filtre), delimiter=';')
    
    # Vérification colonnes obligatoires
    colonnes_presentes = reader.fieldnames or []
    colonnes_manquantes = [c for c in COLONNES_OBLIGATOIRES if c not in colonnes_presentes]
    
    if colonnes_manquantes:
        print("=" * 70)
        print("ERREUR FATALE : Colonnes obligatoires manquantes")
        print("=" * 70)
        for col in colonnes_manquantes:
            print(f"  ✗ Colonne '{col}' absente")
        print()
        print("Colonnes présentes :", ", ".join(colonnes_presentes))
        sys.exit(1)
    
    tags = []
    adjectifs = {}
    erreurs = []
    avertissements = []
    patterns_vus = {}  # pattern -> (canon, num_ligne)
    
    lignes = list(reader)
    
    for num_ligne, row in enumerate(lignes, start=2):  # +2 car header + 0-indexed
        canon = row.get('canon', '').strip()
        type_val = row.get('type', '').strip().lower()
        xgn = row.get('Xgn', '').strip()
        synonymes_raw = row.get('synonymes', '').strip()
        adjs_raw = row.get('adjs', '').strip()
        
        # Vérification Xgn
        if xgn and xgn not in VALEURS_XGN_VALIDES:
            erreurs.append(f"Ligne {num_ligne}: Valeur Xgn invalide '{xgn}' pour '{canon}' (valeurs autorisées: m, f, mp, fp, vide)")
        
        # Traitement des synonymes avec détection doublons
        synonymes_liste = [s.strip() for s in synonymes_raw.split(',') if s.strip()]
        
        # Ajouter le canon comme premier "synonyme" pour la recherche
        tous_synonymes = [canon] + synonymes_liste
        
        for syn in tous_synonymes:
            pattern = standardise(syn)
            if not pattern:
                continue
                
            if pattern in patterns_vus:
                canon_precedent, ligne_precedente = patterns_vus[pattern]
                if canon_precedent != canon:  # Conflit inter-lignes seulement
                    erreurs.append(
                        f"Ligne {num_ligne}: Pattern '{pattern}' (de '{syn}') déjà utilisé "
                        f"pour '{canon_precedent}' (ligne {ligne_precedente})"
                    )
            else:
                patterns_vus[pattern] = (canon, num_ligne)
        
        if type_val == 'p':
            # Tag/pathologie
            tags.append({
                'canon': canon,
                'xgn': xgn,
                'synonymes': synonymes_liste,
                'adjs': [a.strip() for a in adjs_raw.split(',') if a.strip()],
                'ligne': num_ligne
            })
        elif type_val == 'a':
            # Adjectif
            m = row.get('m', '').strip()
            f = row.get('f', '').strip()
            mp = row.get('mp', '').strip()
            fp = row.get('fp', '').strip()
            
            adjectifs[canon.lower()] = {
                'canon': canon,
                'synonymes': synonymes_liste,
                'm': m,
                'f': f,
                'mp': mp,
                'fp': fp,
                'ligne': num_ligne,
                'utilise': False  # Pour tracker si utilisé
            }
    
    if debug:
        print(f"[DEBUG] {len(tags)} tags chargés, {len(adjectifs)} adjectifs chargés")
    
    # Vérification correspondance adjectifs
    adjs_utilises = set()
    
    for tag in tags:
        for adj in tag['adjs']:
            adj_lower = adj.lower()
            adjs_utilises.add(adj_lower)
            
            if adj_lower not in adjectifs:
                erreurs.append(
                    f"Ligne {tag['ligne']}: Adjectif '{adj}' utilisé pour '{tag['canon']}' "
                    f"n'a pas de définition (type=a)"
                )
            else:
                adjectifs[adj_lower]['utilise'] = True
    
    # Avertissements pour adjectifs non utilisés
    for adj_key, adj_data in adjectifs.items():
        if not adj_data['utilise']:
            avertissements.append(
                f"Adjectif '{adj_data['canon']}' défini (ligne {adj_data['ligne']}) mais jamais utilisé"
            )
    
    # Affichage erreurs et arrêt si nécessaire
    if erreurs:
        print("=" * 70)
        print("ERREURS DÉTECTÉES - ARRÊT DU TRAITEMENT")
        print("=" * 70)
        for err in erreurs:
            print(f"  ✗ {err}")
        sys.exit(1)
    
    # Affichage avertissements
    if avertissements and (verbose or debug):
        print("-" * 70)
        print("AVERTISSEMENTS (le traitement continue)")
        print("-" * 70)
        for warn in avertissements:
            print(f"  ⚠ {warn}")
        print()
    
    return tags, adjectifs, avertissements


def generer_patternstagsfr(tags: list, fichier_sortie: str | Path, 
                            verbose: bool = False, debug: bool = False) -> int:
    """
    Génère patternstagsfr.csv.
    
    Format: canontag;synonyme;pattern
    Trié par longueur décroissante de pattern.
    
    Returns:
        Nombre de lignes générées
    """
    fichier = Path(fichier_sortie)
    lignes = []
    patterns_generes = set()  # Éviter doublons
    
    for tag in tags:
        canon = tag['canon']
        tous_synonymes = [canon] + tag['synonymes']
        
        for syn in tous_synonymes:
            pattern = standardise(syn)
            if not pattern:
                continue
            
            # Éviter les doublons de pattern pour le même canon
            cle = (canon, pattern)
            if cle in patterns_generes:
                continue
            patterns_generes.add(cle)
            
            lignes.append({
                'canontag': canon,
                'synonyme': syn,
                'pattern': pattern
            })
    
    # Tri par longueur décroissante de pattern
    lignes.sort(key=lambda x: (-len(x['pattern']), x['pattern']))
    
    # Écriture du fichier
    now = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    
    with open(fichier, 'w', encoding='utf-8-sig', newline='') as f:
        f.write(f"# patternstagsfr.csv - Généré le {now}\n")
        f.write(f"# {len(lignes)} lignes générées par tags2patterns.py\n")
        
        writer = csv.DictWriter(f, fieldnames=['canontag', 'synonyme', 'pattern'], 
                                delimiter=';', extrasaction='ignore')
        writer.writeheader()
        writer.writerows(lignes)
    
    if verbose or debug:
        print(f"✓ {len(lignes)} lignes générées → {fichier.absolute()}")
    
    return len(lignes)


def generer_patternsadjsfr(tags: list, adjectifs: dict, fichier_sortie: str | Path,
                            verbose: bool = False, debug: bool = False) -> int:
    """
    Génère patternsadjsfr.csv.
    
    Format: canonadj;canontag;synonyme;pattern
    
    Pour chaque tag ayant des adjectifs :
    - Pour chaque adjectif de la colonne adjs
    - Créer des lignes avec les 4 formes conjuguées (sans doublons)
    - Créer des lignes pour chaque synonyme de l'adjectif
    
    Returns:
        Nombre de lignes générées
    """
    fichier = Path(fichier_sortie)
    lignes = []
    patterns_generes = set()  # Éviter doublons (canonadj, canontag, pattern)
    
    for tag in tags:
        if not tag['adjs']:
            continue
        
        canontag = tag['canon']
        
        for adj_nom in tag['adjs']:
            adj_key = adj_nom.lower()
            
            if adj_key not in adjectifs:
                # Ne devrait pas arriver (vérifié dans charger_tagsadjs)
                continue
            
            adj = adjectifs[adj_key]
            canonadj = adj['canon']
            
            # 1. Les 4 formes conjuguées (sans doublons)
            formes = set()
            for forme in [adj['m'], adj['f'], adj['mp'], adj['fp']]:
                if forme:
                    formes.add(forme)
            
            for forme in formes:
                pattern = standardise(forme)
                if not pattern:
                    continue
                
                cle = (canonadj, canontag, pattern)
                if cle in patterns_generes:
                    continue
                patterns_generes.add(cle)
                
                lignes.append({
                    'canonadj': canonadj,
                    'canontag': canontag,
                    'synonyme': forme,
                    'pattern': pattern
                })
            
            # 2. Les synonymes de l'adjectif
            for syn in adj['synonymes']:
                pattern = standardise(syn)
                if not pattern:
                    continue
                
                cle = (canonadj, canontag, pattern)
                if cle in patterns_generes:
                    continue
                patterns_generes.add(cle)
                
                lignes.append({
                    'canonadj': canonadj,
                    'canontag': canontag,
                    'synonyme': syn,
                    'pattern': pattern
                })
    
    # Tri par longueur décroissante de pattern
    lignes.sort(key=lambda x: (-len(x['pattern']), x['pattern']))
    
    # Écriture du fichier
    now = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    
    with open(fichier, 'w', encoding='utf-8-sig', newline='') as f:
        f.write(f"# patternsadjsfr.csv - Généré le {now}\n")
        f.write(f"# {len(lignes)} lignes générées par tags2patterns.py\n")
        
        writer = csv.DictWriter(f, fieldnames=['canonadj', 'canontag', 'synonyme', 'pattern'],
                                delimiter=';', extrasaction='ignore')
        writer.writeheader()
        writer.writerows(lignes)
    
    if verbose or debug:
        print(f"✓ {len(lignes)} lignes générées → {fichier.absolute()}")
    
    return len(lignes)


def generer_synonymes(fichier_entree: str | Path, dossier_sortie: str | Path = None,
                      verbose: bool = False, debug: bool = False) -> tuple:
    """
    Fonction principale - peut être importée.
    
    Args:
        fichier_entree: Chemin vers tagsadjs.csv
        dossier_sortie: Dossier de sortie (défaut: même que entrée)
        verbose: Affichage détaillé
        debug: Affichage complet
        
    Returns:
        (nb_tags, nb_adjs) - nombre de lignes générées pour chaque fichier
    """
    fichier_entree = Path(fichier_entree)
    
    if dossier_sortie is None:
        dossier_sortie = fichier_entree.parent
    else:
        dossier_sortie = Path(dossier_sortie)
        dossier_sortie.mkdir(parents=True, exist_ok=True)
    
    # Chargement et validation
    tags, adjectifs, avertissements = charger_tagsadjs(fichier_entree, verbose, debug)
    
    if verbose or debug:
        print(f"[INFO] {len(tags)} tags, {len(adjectifs)} adjectifs chargés")
        if avertissements:
            print(f"[INFO] {len(avertissements)} avertissement(s)")
        print()
    
    # Génération des fichiers
    fichier_tags = dossier_sortie / "patternstagsfr.csv"
    fichier_adjs = dossier_sortie / "patternsadjsfr.csv"
    
    nb_tags = generer_patternstagsfr(tags, fichier_tags, verbose, debug)
    nb_adjs = generer_patternsadjsfr(tags, adjectifs, fichier_adjs, verbose, debug)
    
    return nb_tags, nb_adjs


def trouver_tagsadjs() -> Path | None:
    """
    Recherche tagsadjs.csv dans les chemins possibles.
    
    Returns:
        Path du fichier trouvé ou None
    """
    chemins_possibles = [
        Path("refs/tagsadjs.csv"),
        Path("tagsadjs.csv"),
        Path(__file__).parent / "refs" / "tagsadjs.csv",
        Path("c:/g/refs/tagsadjs.csv"),
    ]
    
    for chemin in chemins_possibles:
        if chemin.exists():
            return chemin
    
    return None


def main():
    """Point d'entrée CLI."""
    print(f"{__pgm__} V{__version__} - {__date__}")
    print()
    
    # Parsing des arguments
    verbose = '--verbose' in sys.argv
    debug = '--debug' in sys.argv
    
    if debug:
        verbose = True  # debug implique verbose
    
    # Recherche du fichier source
    fichier_source = trouver_tagsadjs()
    
    if fichier_source is None:
        print("=" * 70)
        print("ERREUR FATALE : Fichier tagsadjs.csv introuvable")
        print("=" * 70)
        print("Chemins recherchés :")
        print("  - refs/tagsadjs.csv")
        print("  - tagsadjs.csv")
        print("  - <script>/refs/tagsadjs.csv")
        print("  - c:/g/refs/tagsadjs.csv")
        sys.exit(1)
    
    print(f"Fichier source : {fichier_source.absolute()}")
    print()
    
    # Exécution
    try:
        nb_tags, nb_adjs = generer_synonymes(fichier_source, verbose=verbose, debug=debug)
        
        print()
        print("=" * 70)
        print("TRAITEMENT TERMINÉ AVEC SUCCÈS")
        print("=" * 70)
        print(f"  • patternstagsfr.csv : {nb_tags} lignes")
        print(f"  • patternsadjsfr.csv : {nb_adjs} lignes")
        
    except Exception as e:
        print("=" * 70)
        print("ERREUR INATTENDUE")
        print("=" * 70)
        print(f"  {type(e).__name__}: {e}")
        if debug:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
