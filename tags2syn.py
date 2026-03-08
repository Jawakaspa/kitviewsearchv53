# tags2syn.py V1.0.3 - 27/12/2025 19:46:56
__pgm__ = "tags2syn.py"
__version__ = "1.0.3"
__date__ = "27/12/2025 19:46:56"

"""
Transforme tagsadjs.csv en deux fichiers de synonymes :
- syntags.csv : synonymes des tags pour dettags.py
- synadjs.csv : synonymes des adjectifs pour detadjs.py

Usage:
  python tags2syn.py                    # Exécution standard
  python tags2syn.py --verbose          # Affichage détaillé
  python tags2syn.py --debug            # Affichage complet
"""

import csv
import sys
import io
from pathlib import Path
from datetime import datetime

# Import obligatoire de standardise - pas de fallback
try:
    from standardise import standardise
except ImportError:
    print("=" * 70)
    print("ERREUR FATALE : Module standardise.py introuvable")
    print("=" * 70)
    print("  Ce module est obligatoire pour le fonctionnement de tags2syn.py")
    print("  Vérifiez que standardise.py est présent dans le même répertoire")
    print("=" * 70)
    sys.exit(1)


# ============================================================================
#                           CONSTANTES
# ============================================================================

COLONNES_REQUISES = ['canon', 'type', 'synonymes', 'adjs', 'm', 'f', 'mp', 'fp']
# Note: 'gn' peut être 'gn' ou 'Xgn' selon le fichier
VALEURS_GN_VALIDES = {'m', 'f', 'mp', 'fp', ''}

CHEMINS_POSSIBLES = [
    Path("refs/tagsadjs.csv"),
    Path("tagsadjs.csv"),
    Path(__file__).parent / "refs" / "tagsadjs.csv",
    Path("c:/g/refs/tagsadjs.csv"),
]


# ============================================================================
#                           UTILITAIRES
# ============================================================================

def filtrer_commentaires_csv(contenu: str) -> str:
    """
    Filtre les lignes de commentaire (commençant par #) d'un contenu CSV.
    Retourne un contenu nettoyé prêt pour csv.DictReader.
    """
    lignes = contenu.splitlines(keepends=True)
    lignes_filtrees = [l for l in lignes if not l.strip().startswith('#')]
    return ''.join(lignes_filtrees)


def trouver_fichier_tagsadjs() -> Path:
    """Recherche le fichier tagsadjs.csv dans les chemins possibles."""
    for chemin in CHEMINS_POSSIBLES:
        if chemin.exists():
            return chemin
    return None


def detecter_colonne_gn(entetes: list) -> str:
    """Détecte le nom de la colonne genre/nombre (gn ou Xgn)."""
    if 'gn' in entetes:
        return 'gn'
    elif 'Xgn' in entetes:
        return 'Xgn'
    return None


# ============================================================================
#                           CHARGEMENT ET VALIDATION
# ============================================================================

def charger_tagsadjs(fichier_csv, verbose=False, debug=False):
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
        SystemExit en cas d'erreur fatale
    """
    fichier_path = Path(fichier_csv)
    erreurs = []
    avertissements = []
    
    if not fichier_path.exists():
        print("=" * 70)
        print("ERREUR FATALE : Fichier introuvable")
        print("=" * 70)
        print(f"  Fichier : {fichier_path.absolute()}")
        print("=" * 70)
        sys.exit(1)
    
    # Lecture avec gestion d'encodage
    contenu = None
    for encoding in ['utf-8-sig', 'utf-8', 'latin-1']:
        try:
            with open(fichier_path, 'r', encoding=encoding) as f:
                contenu = f.read()
            break
        except UnicodeDecodeError:
            continue
    
    if contenu is None:
        print("=" * 70)
        print("ERREUR FATALE : Impossible de lire le fichier")
        print("=" * 70)
        print(f"  Fichier : {fichier_path.absolute()}")
        print("  Encodages testés : utf-8-sig, utf-8, latin-1")
        print("=" * 70)
        sys.exit(1)
    
    # Filtrer les commentaires
    contenu_filtre = filtrer_commentaires_csv(contenu)
    
    # Parser le CSV
    reader = csv.DictReader(io.StringIO(contenu_filtre), delimiter=';')
    entetes = reader.fieldnames
    
    if debug:
        print(f"[DEBUG] Colonnes détectées : {entetes}")
    
    # Vérifier les colonnes requises
    colonne_gn = detecter_colonne_gn(entetes)
    colonnes_manquantes = []
    
    for col in COLONNES_REQUISES:
        if col not in entetes:
            colonnes_manquantes.append(col)
    
    if colonne_gn is None:
        colonnes_manquantes.append('gn (ou Xgn)')
    
    if colonnes_manquantes:
        print("=" * 70)
        print("ERREUR FATALE : Colonnes manquantes")
        print("=" * 70)
        for col in colonnes_manquantes:
            print(f"  ✗ {col}")
        print("=" * 70)
        sys.exit(1)
    
    # Charger les données
    tags = []
    adjectifs = {}
    synonymes_vus = {}  # {synonyme_std: (canon, num_ligne)}
    adjectifs_utilises = set()  # Adjectifs référencés dans 'adjs'
    
    num_ligne = 1  # L'en-tête est ligne 1
    
    for row in reader:
        num_ligne += 1
        
        canon = row.get('canon', '').strip()
        type_val = row.get('type', '').strip().lower()
        gn = row.get(colonne_gn, '').strip().lower()
        synonymes_raw = row.get('synonymes', '').strip()
        adjs_raw = row.get('adjs', '').strip()
        
        # Validation du genre/nombre
        if gn and gn not in VALEURS_GN_VALIDES:
            erreurs.append(f"Ligne {num_ligne}: Valeur gn invalide '{gn}' pour '{canon}' (attendu: m, f, mp, fp ou vide)")
        
        # Parser les synonymes
        synonymes = []
        if synonymes_raw:
            synonymes = [s.strip() for s in synonymes_raw.split(',') if s.strip()]
        
        # Parser les adjectifs associés
        adjs_liste = []
        if adjs_raw:
            adjs_liste = [a.strip().lower() for a in adjs_raw.split(',') if a.strip()]
            adjectifs_utilises.update(adjs_liste)
        
        # Vérifier les doublons de synonymes ENTRE LIGNES DIFFÉRENTES
        # Les doublons dans la même ligne sont normaux (ex: béance et beance)
        # Le canon lui-même compte comme un synonyme
        tous_synonymes = [canon] + synonymes
        synonymes_std_ligne = set()  # Pour détecter doublons dans la même ligne
        
        for syn in tous_synonymes:
            syn_std = standardise(syn)
            
            # Ignorer les doublons dans la même ligne (c'est voulu)
            if syn_std in synonymes_std_ligne:
                continue
            synonymes_std_ligne.add(syn_std)
            
            if syn_std in synonymes_vus:
                canon_existant, ligne_existante = synonymes_vus[syn_std]
                # Erreur seulement si c'est une ligne DIFFÉRENTE
                if ligne_existante != num_ligne:
                    erreurs.append(
                        f"Ligne {num_ligne}: Synonyme '{syn}' (standardisé: '{syn_std}') "
                        f"déjà utilisé pour '{canon_existant}' (ligne {ligne_existante})"
                    )
            else:
                synonymes_vus[syn_std] = (canon, num_ligne)
        
        # Créer l'entrée
        entree = {
            'canon': canon,
            'type': type_val,
            'gn': gn,
            'synonymes': synonymes,
            'adjs': adjs_liste,
            'm': row.get('m', '').strip(),
            'f': row.get('f', '').strip(),
            'mp': row.get('mp', '').strip(),
            'fp': row.get('fp', '').strip(),
            'num_ligne': num_ligne
        }
        
        if type_val == 'p':
            tags.append(entree)
        elif type_val == 'a':
            adjectifs[canon.lower()] = entree
    
    if verbose:
        print(f"  Chargé : {len(tags)} tags, {len(adjectifs)} adjectifs")
    
    # Vérifier que tous les adjectifs utilisés sont définis
    adjectifs_definis = set(adjectifs.keys())
    adjectifs_manquants = adjectifs_utilises - adjectifs_definis
    
    for adj in sorted(adjectifs_manquants):
        erreurs.append(f"Adjectif '{adj}' utilisé dans 'adjs' mais non défini (pas de ligne type=a)")
    
    # Vérifier les adjectifs définis mais jamais utilisés
    adjectifs_inutilises = adjectifs_definis - adjectifs_utilises
    for adj in sorted(adjectifs_inutilises):
        ligne = adjectifs[adj]['num_ligne']
        avertissements.append(f"Adjectif '{adj}' défini (ligne {ligne}) mais jamais utilisé dans 'adjs'")
    
    # Afficher les erreurs si présentes
    if erreurs:
        print("=" * 70)
        print("ERREURS DÉTECTÉES - ARRÊT DU TRAITEMENT")
        print("=" * 70)
        for err in erreurs:
            print(f"  ✗ {err}")
        print("=" * 70)
        sys.exit(1)
    
    # Afficher les avertissements
    if avertissements and verbose:
        print("-" * 70)
        print("AVERTISSEMENTS (le traitement continue)")
        print("-" * 70)
        for warn in avertissements:
            print(f"  ⚠ {warn}")
        print("-" * 70)
    
    return tags, adjectifs, avertissements


# ============================================================================
#                           GÉNÉRATION DES FICHIERS
# ============================================================================

def generer_syntags(tags, fichier_sortie, verbose=False, debug=False):
    """
    Génère syntags.csv à partir des tags.
    
    Format: stdtag;canontag;frsynonyme
    
    Args:
        tags: Liste des tags chargés
        fichier_sortie: Chemin du fichier de sortie
        verbose: Affichage détaillé
        debug: Affichage complet
        
    Returns:
        Nombre de lignes générées
    """
    lignes = []
    vus = set()  # Pour éviter les doublons
    
    for tag in tags:
        canon = tag['canon']
        
        # Ajouter le canon lui-même
        tous_synonymes = [canon] + tag['synonymes']
        
        for syn in tous_synonymes:
            syn = syn.strip()
            if not syn:
                continue
            
            std = standardise(syn)
            cle = (std, canon.lower())
            
            if cle not in vus:
                vus.add(cle)
                lignes.append({
                    'stdtag': std,
                    'canontag': canon,
                    'frsynonyme': syn
                })
                
                if debug:
                    print(f"[DEBUG] syntag: '{std}' -> '{canon}' (fr: '{syn}')")
    
    # Tri par nombre de mots décroissant (multi-mots d'abord)
    lignes.sort(key=lambda x: (-len(x['stdtag'].split()), x['stdtag']))
    
    # Écriture du fichier
    fichier_path = Path(fichier_sortie)
    fichier_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(fichier_path, 'w', encoding='utf-8-sig', newline='') as f:
        # Commentaire d'en-tête
        f.write(f"# Généré par {__pgm__} V{__version__}\n")
        f.write(f"# Date : {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n")
        f.write(f"# Nombre de lignes : {len(lignes)}\n")
        
        writer = csv.DictWriter(f, fieldnames=['stdtag', 'canontag', 'frsynonyme'], delimiter=';')
        writer.writeheader()
        writer.writerows(lignes)
    
    if verbose:
        print(f"✓ {len(lignes)} lignes générées → {fichier_path.absolute()}")
    
    return len(lignes)


def generer_synadjs(tags, adjectifs, fichier_sortie, verbose=False, debug=False):
    """
    Génère synadjs.csv à partir des tags et adjectifs.
    
    Format: stdadj;canonadj;canontag;frsynadj
    
    Pour chaque tag ayant des adjectifs, génère les lignes pour:
    - La forme accordée selon le genre du tag
    - Le canon de l'adjectif
    - Chaque synonyme de l'adjectif
    - Les autres formes accordées (m, f, mp, fp)
    
    Args:
        tags: Liste des tags chargés
        adjectifs: Dict des adjectifs {canon_lower: dict}
        fichier_sortie: Chemin du fichier de sortie
        verbose: Affichage détaillé
        debug: Affichage complet
        
    Returns:
        Nombre de lignes générées
    """
    lignes = []
    vus = set()  # Pour éviter les doublons
    
    for tag in tags:
        if not tag['adjs']:
            continue
        
        canon_tag = tag['canon']
        gn_tag = tag['gn']  # Genre/nombre du tag
        
        for adj_nom in tag['adjs']:
            adj_nom_lower = adj_nom.lower()
            
            if adj_nom_lower not in adjectifs:
                # Ne devrait pas arriver car vérifié dans charger_tagsadjs
                continue
            
            adj = adjectifs[adj_nom_lower]
            canon_adj = adj['canon']
            
            # Collecter toutes les formes à ajouter
            formes_a_ajouter = set()
            
            # 1. Le canon de l'adjectif
            formes_a_ajouter.add(canon_adj)
            
            # 2. Les synonymes de l'adjectif
            for syn in adj['synonymes']:
                if syn.strip():
                    formes_a_ajouter.add(syn.strip())
            
            # 3. Les formes accordées (m, f, mp, fp)
            for forme in ['m', 'f', 'mp', 'fp']:
                val = adj.get(forme, '').strip()
                if val:
                    formes_a_ajouter.add(val)
            
            # 4. La forme accordée selon le genre du tag (priorité)
            if gn_tag and adj.get(gn_tag):
                formes_a_ajouter.add(adj[gn_tag].strip())
            
            # Générer les lignes
            for forme in formes_a_ajouter:
                if not forme:
                    continue
                
                std = standardise(forme)
                cle = (std, canon_adj.lower(), canon_tag.lower())
                
                if cle not in vus:
                    vus.add(cle)
                    lignes.append({
                        'stdadj': std,
                        'canonadj': canon_adj,
                        'canontag': canon_tag,
                        'frsynadj': forme
                    })
                    
                    if debug:
                        print(f"[DEBUG] synadj: '{std}' -> adj='{canon_adj}', tag='{canon_tag}' (fr: '{forme}')")
    
    # Tri par longueur décroissante
    lignes.sort(key=lambda x: (-len(x['stdadj']), x['stdadj']))
    
    # Écriture du fichier
    fichier_path = Path(fichier_sortie)
    fichier_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(fichier_path, 'w', encoding='utf-8-sig', newline='') as f:
        # Commentaire d'en-tête
        f.write(f"# Généré par {__pgm__} V{__version__}\n")
        f.write(f"# Date : {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n")
        f.write(f"# Nombre de lignes : {len(lignes)}\n")
        
        writer = csv.DictWriter(f, fieldnames=['stdadj', 'canonadj', 'canontag', 'frsynadj'], delimiter=';')
        writer.writeheader()
        writer.writerows(lignes)
    
    if verbose:
        print(f"✓ {len(lignes)} lignes générées → {fichier_path.absolute()}")
    
    return len(lignes)


# ============================================================================
#                           FONCTION PRINCIPALE
# ============================================================================

def generer_synonymes(fichier_entree, dossier_sortie=None, verbose=False, debug=False):
    """
    Fonction principale de génération des fichiers de synonymes.
    
    Peut être importée depuis un autre programme:
        from tags2syn import generer_synonymes
        nb_tags, nb_adjs = generer_synonymes('tagsadjs.csv', 'refs/', verbose=True)
    
    Args:
        fichier_entree: Chemin vers tagsadjs.csv
        dossier_sortie: Dossier de sortie (None = même dossier que l'entrée)
        verbose: Affichage détaillé
        debug: Affichage complet
        
    Returns:
        (nb_tags, nb_adjs) - Nombre de lignes générées dans chaque fichier
    """
    fichier_path = Path(fichier_entree)
    
    # Déterminer le dossier de sortie
    if dossier_sortie:
        sortie_path = Path(dossier_sortie)
    else:
        sortie_path = fichier_path.parent
    
    if verbose:
        print(f"Fichier source : {fichier_path.absolute()}")
        print(f"Dossier sortie : {sortie_path.absolute()}")
        print()
    
    # Charger et valider
    if verbose:
        print("Chargement de tagsadjs.csv...")
    
    tags, adjectifs, avertissements = charger_tagsadjs(
        fichier_entree, verbose=verbose, debug=debug
    )
    
    if verbose:
        print()
    
    # Générer syntags.csv
    if verbose:
        print("Génération de syntags.csv...")
    
    fichier_syntags = sortie_path / "syntags.csv"
    nb_tags = generer_syntags(tags, fichier_syntags, verbose=verbose, debug=debug)
    
    # Générer synadjs.csv
    if verbose:
        print("Génération de synadjs.csv...")
    
    fichier_synadjs = sortie_path / "synadjs.csv"
    nb_adjs = generer_synadjs(tags, adjectifs, fichier_synadjs, verbose=verbose, debug=debug)
    
    return nb_tags, nb_adjs


# ============================================================================
#                           MAIN
# ============================================================================

def main():
    """Point d'entrée principal."""
    print(f"{__pgm__} V{__version__} - {__date__}")
    print()
    
    # Gestion des arguments
    verbose = '--verbose' in sys.argv or '-v' in sys.argv
    debug = '--debug' in sys.argv or '-d' in sys.argv
    
    if debug:
        verbose = True  # Debug implique verbose
    
    # Trouver le fichier tagsadjs.csv
    fichier_entree = None
    
    # Vérifier si un fichier est passé en argument
    for arg in sys.argv[1:]:
        if not arg.startswith('-'):
            fichier_entree = Path(arg)
            break
    
    # Sinon chercher dans les chemins par défaut
    if fichier_entree is None:
        fichier_entree = trouver_fichier_tagsadjs()
    
    if fichier_entree is None or not fichier_entree.exists():
        print("=" * 70)
        print("ERREUR : Fichier tagsadjs.csv introuvable")
        print("=" * 70)
        print("Chemins recherchés :")
        for chemin in CHEMINS_POSSIBLES:
            existe = "✓" if chemin.exists() else "✗"
            print(f"  {existe} {chemin.absolute()}")
        print()
        print("Usage:")
        print("  python tags2syn.py                    # Recherche auto")
        print("  python tags2syn.py chemin/tagsadjs.csv")
        print("  python tags2syn.py --verbose")
        print("  python tags2syn.py --debug")
        print("=" * 70)
        sys.exit(1)
    
    # Déterminer le dossier de sortie (même que l'entrée)
    dossier_sortie = fichier_entree.parent
    
    # Générer les fichiers
    try:
        nb_tags, nb_adjs = generer_synonymes(
            fichier_entree,
            dossier_sortie,
            verbose=verbose,
            debug=debug
        )
        
        print()
        print("=" * 70)
        print("TRAITEMENT TERMINÉ AVEC SUCCÈS")
        print("=" * 70)
        print(f"  syntags.csv : {nb_tags} lignes")
        print(f"  synadjs.csv : {nb_adjs} lignes")
        print("=" * 70)
        
    except Exception as e:
        print("=" * 70)
        print("ERREUR INATTENDUE")
        print("=" * 70)
        print(f"  {type(e).__name__}: {e}")
        print("=" * 70)
        if debug:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
