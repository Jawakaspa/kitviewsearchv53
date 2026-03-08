#*TO*#
__pgm__ = "ajout_colonne_langue.py"
__version__ = "0.0.0"
__date__ = "01/01/1970 00:00"

# ╔════════════════════════════════════════════════════════════════════════════╗
# ║ ajout_colonne_langue.py                                                     ║
# ║ Ajoute une colonne langue à des fichiers CSV de traduction                  ║
# ║                                                                             ║
# ║ Usage :                                                                     ║
# ║   python ajout_colonne_langue.py ja                    → Ajoute ja à tous   ║
# ║   python ajout_colonne_langue.py ja syntags.csv        → Ajoute ja à un     ║
# ║   python ajout_colonne_langue.py ja --list             → Liste les fichiers ║
# ║   python ajout_colonne_langue.py ja --dry-run          → Simule sans écrire ║
# ║                                                                             ║
# ║ La colonne est ajoutée après la dernière colonne langue existante.          ║
# ║ Si la colonne existe déjà, le fichier est ignoré.                           ║
# ╚════════════════════════════════════════════════════════════════════════════╝

import csv
import sys
import os
from pathlib import Path

# Colonnes langue connues (ordre d'apparition typique)
COLONNES_LANGUE = ['fr', 'en', 'de', 'th', 'es', 'it', 'pt', 'pl', 'ro', 'ar', 'cn', 'ja']

# Répertoire par défaut des fichiers de référence
REPERTOIRE_REFS = "refs"

# Fichiers CSV typiquement concernés par les traductions
FICHIERS_TRADUCTION = [
    "glossaire.csv",
    "syntags.csv", 
    "synadjs.csv",
    "motsvides.csv",
    "phrases_chatbot.csv"
]


def detecter_colonnes_langue(colonnes: list) -> list:
    """
    Détecte les colonnes langue présentes dans l'en-tête.
    
    Args:
        colonnes: Liste des noms de colonnes
    
    Returns:
        Liste des codes langue trouvés (dans l'ordre d'apparition)
    """
    langues_trouvees = []
    for col in colonnes:
        col_lower = col.lower().strip()
        if col_lower in COLONNES_LANGUE:
            langues_trouvees.append(col_lower)
    return langues_trouvees


def position_insertion(colonnes: list, nouvelle_langue: str) -> int:
    """
    Détermine la position où insérer la nouvelle colonne langue.
    
    Stratégie : après la dernière colonne langue existante.
    
    Args:
        colonnes: Liste des noms de colonnes
        nouvelle_langue: Code de la nouvelle langue
    
    Returns:
        Index de la position d'insertion
    """
    derniere_pos = -1
    for i, col in enumerate(colonnes):
        if col.lower().strip() in COLONNES_LANGUE:
            derniere_pos = i
    
    # Si aucune colonne langue trouvée, ajouter à la fin
    if derniere_pos == -1:
        return len(colonnes)
    
    return derniere_pos + 1


def ajouter_colonne(chemin: Path, langue: str, dry_run: bool = False) -> dict:
    """
    Ajoute une colonne langue à un fichier CSV.
    
    Args:
        chemin: Chemin du fichier CSV
        langue: Code langue à ajouter (ex: 'ja')
        dry_run: Si True, simule sans écrire
    
    Returns:
        Dict avec le résultat: {'status': 'added'|'exists'|'no_lang'|'error', 'message': str}
    """
    chemin = Path(chemin).resolve()
    
    if not chemin.exists():
        return {'status': 'error', 'message': f"Fichier non trouvé: {chemin}"}
    
    try:
        # Lire le fichier complet
        lignes = []
        colonnes = []
        commentaires_debut = []
        
        with open(chemin, 'r', encoding='utf-8-sig') as f:
            contenu = f.read()
        
        # Séparer les lignes
        lignes_brutes = contenu.splitlines()
        
        # Extraire les commentaires du début
        idx_debut_donnees = 0
        for i, ligne in enumerate(lignes_brutes):
            if ligne.strip().startswith('#'):
                commentaires_debut.append(ligne)
                idx_debut_donnees = i + 1
            elif ligne.strip():
                # Première ligne non-commentaire = en-tête
                idx_debut_donnees = i
                break
        
        if idx_debut_donnees >= len(lignes_brutes):
            return {'status': 'error', 'message': "Fichier vide ou que des commentaires"}
        
        # Parser l'en-tête
        ligne_entete = lignes_brutes[idx_debut_donnees]
        colonnes = [c.strip() for c in ligne_entete.split(';')]
        
        # Vérifier si des colonnes langue existent
        langues_existantes = detecter_colonnes_langue(colonnes)
        if not langues_existantes:
            return {'status': 'no_lang', 'message': "Aucune colonne langue détectée"}
        
        # Vérifier si la langue existe déjà
        if langue.lower() in [l.lower() for l in langues_existantes]:
            return {'status': 'exists', 'message': f"Colonne '{langue}' déjà présente"}
        
        # Déterminer la position d'insertion
        pos = position_insertion(colonnes, langue)
        
        # Insérer la nouvelle colonne dans l'en-tête
        nouvelles_colonnes = colonnes[:pos] + [langue] + colonnes[pos:]
        
        # Traiter toutes les lignes de données
        nouvelles_lignes = []
        
        # Commentaires de début
        for comm in commentaires_debut:
            nouvelles_lignes.append(comm)
        
        # En-tête
        nouvelles_lignes.append(';'.join(nouvelles_colonnes))
        
        # Données (ajouter une cellule vide à la position)
        for i in range(idx_debut_donnees + 1, len(lignes_brutes)):
            ligne = lignes_brutes[i]
            if not ligne.strip():
                nouvelles_lignes.append(ligne)
                continue
            
            # Parser la ligne
            cellules = ligne.split(';')
            # Ajuster si la ligne a moins de colonnes que l'en-tête
            while len(cellules) < len(colonnes):
                cellules.append('')
            
            # Insérer une cellule vide à la position
            nouvelles_cellules = cellules[:pos] + [''] + cellules[pos:]
            nouvelles_lignes.append(';'.join(nouvelles_cellules))
        
        if dry_run:
            return {
                'status': 'added', 
                'message': f"[DRY-RUN] Colonne '{langue}' serait ajoutée en position {pos+1} (après {colonnes[pos-1] if pos > 0 else 'début'})"
            }
        
        # Écrire le fichier
        with open(chemin, 'w', encoding='utf-8-sig', newline='') as f:
            f.write('\n'.join(nouvelles_lignes))
            if not nouvelles_lignes[-1].endswith('\n'):
                f.write('\n')
        
        return {
            'status': 'added',
            'message': f"Colonne '{langue}' ajoutée en position {pos+1} (après {colonnes[pos-1] if pos > 0 else 'début'})"
        }
        
    except Exception as e:
        return {'status': 'error', 'message': str(e)}


def lister_fichiers_refs(repertoire: str = REPERTOIRE_REFS) -> list:
    """
    Liste les fichiers CSV de traduction dans le répertoire refs.
    
    Returns:
        Liste des chemins absolus des fichiers trouvés
    """
    rep = Path(repertoire).resolve()
    fichiers = []
    
    if not rep.exists():
        print(f"[ATTENTION] Répertoire non trouvé: {rep}")
        return fichiers
    
    for nom in FICHIERS_TRADUCTION:
        chemin = rep / nom
        if chemin.exists():
            fichiers.append(chemin)
    
    # Chercher aussi d'autres CSV avec des colonnes langue
    for csv_file in rep.glob("*.csv"):
        if csv_file not in fichiers:
            # Vérifier si le fichier contient des colonnes langue
            try:
                with open(csv_file, 'r', encoding='utf-8-sig') as f:
                    # Sauter les commentaires
                    for line in f:
                        if not line.strip().startswith('#') and line.strip():
                            colonnes = [c.strip().lower() for c in line.split(';')]
                            if any(col in COLONNES_LANGUE for col in colonnes):
                                fichiers.append(csv_file)
                            break
            except:
                pass
    
    return fichiers


def main():
    """Point d'entrée principal."""
    print(f"{__pgm__} V{__version__} - {__date__}")
    print(f"Chemin : {Path(__file__).resolve()}")
    print()
    
    # Parser les arguments
    args = sys.argv[1:]
    
    if not args:
        print("Usage:")
        print(f"  python {__pgm__} <langue>              → Ajoute la langue à tous les CSV de refs/")
        print(f"  python {__pgm__} <langue> fichier.csv  → Ajoute la langue à un fichier spécifique")
        print(f"  python {__pgm__} <langue> --list       → Liste les fichiers qui seraient traités")
        print(f"  python {__pgm__} <langue> --dry-run    → Simule sans modifier")
        print()
        print("Exemples:")
        print(f"  python {__pgm__} ja")
        print(f"  python {__pgm__} ja refs/syntags.csv")
        print(f"  python {__pgm__} ja --dry-run")
        return
    
    langue = args[0].lower()
    
    # Valider le code langue
    if len(langue) != 2:
        print(f"[ERREUR] Code langue invalide: '{langue}' (doit être 2 caractères)")
        return
    
    print(f"Langue à ajouter : {langue}")
    print()
    
    # Options
    dry_run = '--dry-run' in args
    list_only = '--list' in args
    
    # Fichiers à traiter
    fichiers = []
    
    # Fichier spécifique fourni ?
    for arg in args[1:]:
        if arg.endswith('.csv'):
            fichiers.append(Path(arg).resolve())
    
    # Sinon, lister les fichiers du répertoire refs
    if not fichiers:
        fichiers = lister_fichiers_refs()
    
    if not fichiers:
        print("[INFO] Aucun fichier CSV de traduction trouvé.")
        return
    
    print(f"Fichiers à traiter : {len(fichiers)}")
    print("-" * 60)
    
    if list_only:
        for f in fichiers:
            print(f"  {f}")
        return
    
    # Traiter chaque fichier
    resultats = {'added': 0, 'exists': 0, 'no_lang': 0, 'error': 0}
    
    for chemin in fichiers:
        result = ajouter_colonne(chemin, langue, dry_run)
        status = result['status']
        resultats[status] = resultats.get(status, 0) + 1
        
        # Affichage avec indicateur visuel
        if status == 'added':
            icone = '✅'
        elif status == 'exists':
            icone = '⏭️'
        elif status == 'no_lang':
            icone = '⚠️'
        else:
            icone = '❌'
        
        print(f"{icone} {chemin.name}: {result['message']}")
    
    # Résumé
    print()
    print("=" * 60)
    print("RÉSUMÉ")
    print("=" * 60)
    print(f"  Colonnes ajoutées : {resultats['added']}")
    print(f"  Déjà présentes    : {resultats['exists']}")
    print(f"  Sans col. langue  : {resultats['no_lang']}")
    print(f"  Erreurs           : {resultats['error']}")


if __name__ == "__main__":
    main()
