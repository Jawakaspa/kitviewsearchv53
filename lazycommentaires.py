# lazycommentaires.py V1.0.0 - 30/12/2025 06:57:17
__pgm__ = "lazycommentaires.py"
__version__ = "1.0.0"
__date__ = "30/12/2025 06:57:17"

# ╔════════════════════════════════════════════════════════════════════════════╗
# ║ lazycommentaires.py                                                        ║
# ║ Gestionnaire de commentaires multilingues avec traduction paresseuse       ║
# ║                                                                            ║
# ║ Charge commentaires.csv en mémoire et traduit à la demande via DeepL      ║
# ║ si la traduction n'existe pas encore. Sauvegarde immédiatement.           ║
# ║                                                                            ║
# ║ Usage (module) :                                                           ║
# ║   from lazycommentaires import get_commentaire                             ║
# ║   texte = get_commentaire("bruxisme", "en")                                ║
# ║                                                                            ║
# ║ Usage (CLI) :                                                              ║
# ║   python lazycommentaires.py                    → Affiche statistiques     ║
# ║   python lazycommentaires.py bruxisme en        → Récupère traduction      ║
# ║   python lazycommentaires.py --stats            → Statistiques détaillées  ║
# ╚════════════════════════════════════════════════════════════════════════════╝

import csv
import sys
import os
import io
from pathlib import Path
from datetime import datetime

# ══════════════════════════════════════════════════════════════════════════════
# CONFIGURATION
# ══════════════════════════════════════════════════════════════════════════════

# Chemin par défaut du fichier commentaires (relatif au script)
CHEMIN_COMMENTAIRES = "refs/commentaires.csv"

# Colonne clé pour la recherche (identifiant de la pathologie)
COLONNE_CLE = "oripathologie"

# Colonne source (français) pour les traductions
COLONNE_SOURCE = "fr"

# Colonnes de langue cibles (toutes sauf fr)
COLONNES_LANGUES = ['en', 'de', 'es', 'it', 'ja', 'pt', 'pl', 'ro', 'th', 'ar', 'cn']

# Mapping codes langue internes → codes DeepL
CODES_DEEPL = {
    "fr": "FR",
    "en": "EN-GB",
    "de": "DE",
    "es": "ES",
    "it": "IT",
    "pt": "PT-PT",
    "pl": "PL",
    "ro": "RO",
    "ja": "JA",
    "ar": "AR",
    "cn": "ZH-HANS",
    "th": "TH"
}

# ══════════════════════════════════════════════════════════════════════════════
# CACHE MÉMOIRE
# ══════════════════════════════════════════════════════════════════════════════

# Cache global : {oripathologie_lower: {colonne: valeur}}
_cache_commentaires = {}

# Métadonnées du cache
_cache_colonnes = []
_cache_commentaires_lignes = []  # Lignes de commentaires (#)
_cache_charge = False
_chemin_fichier = None

# Statistiques
_stats = {
    "lectures": 0,
    "traductions_deepl": 0,
    "traductions_echouees": 0,
    "sauvegardes": 0
}

# ══════════════════════════════════════════════════════════════════════════════
# UTILITAIRES CSV
# ══════════════════════════════════════════════════════════════════════════════

def _lire_csv_filtre_commentaires(chemin: Path) -> tuple:
    """
    Lit un fichier CSV en filtrant les lignes de commentaires (#).
    
    Returns:
        tuple: (liste de dict, liste des noms de colonnes, liste des commentaires)
    """
    if not chemin.exists():
        print(f"[ERREUR] Fichier non trouvé : {chemin}")
        return [], [], []
    
    commentaires = []
    lignes_data = []
    
    with open(chemin, 'r', encoding='utf-8-sig') as f:
        for ligne in f:
            ligne_strip = ligne.strip()
            if ligne_strip.startswith('#'):
                commentaires.append(ligne.rstrip('\n\r'))
            elif ligne_strip:
                lignes_data.append(ligne)
    
    if not lignes_data:
        print(f"[ERREUR] Fichier vide ou uniquement des commentaires : {chemin}")
        return [], [], commentaires
    
    # Parser les lignes de données
    contenu = io.StringIO(''.join(lignes_data))
    reader = csv.DictReader(contenu, delimiter=';')
    colonnes = reader.fieldnames or []
    
    rows = []
    for row in reader:
        rows.append(row)
    
    return rows, colonnes, commentaires


def _sauvegarder_csv(chemin: Path, rows: list, colonnes: list, commentaires: list = None):
    """
    Sauvegarde un fichier CSV en UTF-8-BOM avec point-virgule.
    """
    global _stats
    
    with open(chemin, 'w', encoding='utf-8-sig', newline='') as f:
        # Écrire l'en-tête
        f.write(';'.join(colonnes) + '\n')
        
        # Écrire les commentaires après l'en-tête
        if commentaires:
            for comm in commentaires:
                f.write(comm + '\n')
        
        # Écrire les données
        for row in rows:
            ligne = [str(row.get(col, '')) for col in colonnes]
            f.write(';'.join(ligne) + '\n')
    
    _stats["sauvegardes"] += 1
    print(f"[DEBUG] commentaires.csv sauvegardé : {chemin}")

# ══════════════════════════════════════════════════════════════════════════════
# TRADUCTION DEEPL
# ══════════════════════════════════════════════════════════════════════════════

def _traduire_deepl(texte: str, langue_cible: str) -> str:
    """
    Traduit un texte du français vers la langue cible via DeepL.
    
    Returns:
        Texte traduit ou chaîne vide si échec
    """
    global _stats
    
    if not texte or not texte.strip():
        return ""
    
    if langue_cible == COLONNE_SOURCE:
        return texte
    
    try:
        import deepl
        api_key = os.environ.get('DEEPL_API_KEY')
        if not api_key:
            print(f"[WARNING] DEEPL_API_KEY non définie - traduction impossible")
            _stats["traductions_echouees"] += 1
            return ""
        
        translator = deepl.Translator(api_key)
        
        code_source = CODES_DEEPL.get(COLONNE_SOURCE, "FR")
        code_cible = CODES_DEEPL.get(langue_cible, langue_cible.upper())
        
        result = translator.translate_text(
            texte,
            source_lang=code_source,
            target_lang=code_cible
        )
        
        _stats["traductions_deepl"] += 1
        print(f"[DEBUG] DeepL: '{texte[:30]}...' → {langue_cible}: '{result.text[:30]}...'")
        
        return result.text
        
    except ImportError:
        print(f"[WARNING] Module deepl non installé - traduction impossible")
        _stats["traductions_echouees"] += 1
        return ""
    except Exception as e:
        print(f"[WARNING] Erreur DeepL pour '{texte[:30]}...' → {langue_cible}: {e}")
        _stats["traductions_echouees"] += 1
        return ""

# ══════════════════════════════════════════════════════════════════════════════
# CHARGEMENT DU CACHE
# ══════════════════════════════════════════════════════════════════════════════

def _charger_commentaires(chemin: Path = None):
    """
    Charge le fichier commentaires.csv en mémoire.
    Appelé automatiquement au premier accès.
    """
    global _cache_commentaires, _cache_colonnes, _cache_commentaires_lignes
    global _cache_charge, _chemin_fichier
    
    if chemin is None:
        chemin = Path(__file__).parent / CHEMIN_COMMENTAIRES
    
    chemin = chemin.resolve()
    _chemin_fichier = chemin
    
    if not chemin.exists():
        print(f"[ERREUR] Fichier commentaires non trouvé : {chemin}")
        _cache_charge = True
        return
    
    rows, colonnes, commentaires = _lire_csv_filtre_commentaires(chemin)
    
    _cache_colonnes = colonnes
    _cache_commentaires_lignes = commentaires
    _cache_commentaires = {}
    
    # Indexer par la colonne clé (oripathologie)
    for row in rows:
        cle = row.get(COLONNE_CLE, '').strip().lower()
        if cle:
            _cache_commentaires[cle] = {k: v.strip() if v else '' for k, v in row.items()}
    
    _cache_charge = True
    print(f"[DEBUG] commentaires.csv chargé : {len(_cache_commentaires)} entrées depuis {chemin}")


def _sauvegarder_cache():
    """
    Sauvegarde le cache en mémoire vers le fichier CSV.
    """
    global _chemin_fichier, _cache_commentaires, _cache_colonnes, _cache_commentaires_lignes
    
    if not _chemin_fichier:
        print("[ERREUR] Chemin fichier non défini - sauvegarde impossible")
        return
    
    # Convertir le cache dict → liste de rows
    rows = []
    for cle_fr, data in sorted(_cache_commentaires.items()):
        rows.append(data)
    
    _sauvegarder_csv(_chemin_fichier, rows, _cache_colonnes, _cache_commentaires_lignes)

# ══════════════════════════════════════════════════════════════════════════════
# API PUBLIQUE
# ══════════════════════════════════════════════════════════════════════════════

def get_commentaire(oripathologie: str, langue: str) -> str:
    """
    Récupère le commentaire pour une pathologie dans une langue donnée.
    
    Si la traduction n'existe pas, traduit via DeepL depuis le français,
    sauvegarde dans le CSV, et retourne la traduction.
    
    Args:
        oripathologie: Identifiant de la pathologie (colonne 'oripathologie')
        langue: Code langue (fr, en, de, es, it, ja, pt, pl, ro, th, ar, cn)
    
    Returns:
        str: Le commentaire traduit, ou chaîne vide si introuvable/échec
    """
    global _stats, _cache_charge, _cache_commentaires
    
    # Chargement paresseux du cache
    if not _cache_charge:
        _charger_commentaires()
    
    _stats["lectures"] += 1
    
    # Normaliser la clé
    cle = oripathologie.strip().lower()
    
    # Vérifier si la pathologie existe
    if cle not in _cache_commentaires:
        print(f"[WARNING] Pathologie inconnue : '{oripathologie}'")
        return ""
    
    data = _cache_commentaires[cle]
    
    # Vérifier si la langue est valide
    if langue not in _cache_colonnes:
        print(f"[WARNING] Langue inconnue : '{langue}'")
        return ""
    
    # Récupérer la valeur existante
    valeur = data.get(langue, '').strip()
    
    # Si la valeur existe, la retourner directement
    if valeur:
        return valeur
    
    # === LAZY TRANSLATION ===
    # La valeur est vide → traduire depuis le français
    
    texte_fr = data.get(COLONNE_SOURCE, '').strip()
    if not texte_fr:
        print(f"[WARNING] Pas de texte français pour '{oripathologie}'")
        return ""
    
    # Cas spécial : si on demande le français, retourner directement
    if langue == COLONNE_SOURCE:
        return texte_fr
    
    # Traduire via DeepL
    traduction = _traduire_deepl(texte_fr, langue)
    
    if traduction:
        # Mettre à jour le cache
        _cache_commentaires[cle][langue] = traduction
        
        # Sauvegarder immédiatement
        _sauvegarder_cache()
        
        return traduction
    
    # Échec de traduction → retourner chaîne vide
    return ""


def get_stats() -> dict:
    """
    Retourne les statistiques d'utilisation.
    
    Returns:
        dict: {lectures, traductions_deepl, traductions_echouees, sauvegardes}
    """
    return _stats.copy()


def get_nb_commentaires() -> int:
    """
    Retourne le nombre total de commentaires chargés.
    """
    global _cache_charge
    
    if not _cache_charge:
        _charger_commentaires()
    
    return len(_cache_commentaires)


def get_langues_disponibles() -> list:
    """
    Retourne la liste des langues disponibles.
    """
    return [COLONNE_SOURCE] + COLONNES_LANGUES


def get_taux_remplissage() -> dict:
    """
    Calcule le taux de remplissage par langue.
    
    Returns:
        dict: {langue: {"rempli": n, "total": n, "pct": float}}
    """
    global _cache_charge, _cache_commentaires
    
    if not _cache_charge:
        _charger_commentaires()
    
    total = len(_cache_commentaires)
    if total == 0:
        return {}
    
    stats = {}
    toutes_langues = [COLONNE_SOURCE] + COLONNES_LANGUES
    
    for langue in toutes_langues:
        rempli = sum(1 for data in _cache_commentaires.values() 
                     if data.get(langue, '').strip())
        stats[langue] = {
            "rempli": rempli,
            "total": total,
            "pct": round(rempli * 100 / total, 1)
        }
    
    return stats


def recharger():
    """
    Force le rechargement du fichier CSV.
    Utile si le fichier a été modifié externement.
    """
    global _cache_charge
    _cache_charge = False
    _charger_commentaires()

# ══════════════════════════════════════════════════════════════════════════════
# INTERFACE CLI
# ══════════════════════════════════════════════════════════════════════════════

def afficher_aide():
    """Affiche l'aide."""
    aide = f"""
{__pgm__} V{__version__} - Gestionnaire de commentaires multilingues

SYNOPSIS
  python {__pgm__} [OPTIONS] [PATHOLOGIE] [LANGUE]

MODES D'UTILISATION

  1. STATISTIQUES (défaut)
     python {__pgm__}
     python {__pgm__} --stats
     
  2. RÉCUPÉRER UN COMMENTAIRE
     python {__pgm__} bruxisme en     → Commentaire en anglais
     python {__pgm__} "apnée du sommeil" de  → Commentaire en allemand
     
  3. AIDE
     python {__pgm__} -h

LANGUES SUPPORTÉES
  {', '.join([COLONNE_SOURCE] + COLONNES_LANGUES)}

FONCTIONNEMENT
  - Charge refs/commentaires.csv en mémoire
  - Si traduction manquante → traduit via DeepL depuis le français
  - Sauvegarde immédiatement le fichier après chaque traduction
  - En cas d'échec DeepL → retourne chaîne vide (lazy retry au prochain appel)
"""
    print(aide)


def afficher_stats_detaillees():
    """Affiche les statistiques détaillées."""
    print()
    print("=" * 70)
    print("STATISTIQUES COMMENTAIRES")
    print("=" * 70)
    
    nb = get_nb_commentaires()
    print(f"  Nombre de commentaires : {nb}")
    print()
    
    print("  Taux de remplissage par langue :")
    taux = get_taux_remplissage()
    for langue, data in sorted(taux.items(), key=lambda x: -x[1]["pct"]):
        barre = "█" * int(data["pct"] / 5) + "░" * (20 - int(data["pct"] / 5))
        print(f"    {langue:3} [{barre}] {data['pct']:5.1f}% ({data['rempli']}/{data['total']})")
    
    print()
    print("  Statistiques de session :")
    stats = get_stats()
    print(f"    Lectures             : {stats['lectures']}")
    print(f"    Traductions DeepL    : {stats['traductions_deepl']}")
    print(f"    Traductions échouées : {stats['traductions_echouees']}")
    print(f"    Sauvegardes          : {stats['sauvegardes']}")


def main():
    """Point d'entrée principal."""
    print(f"{__pgm__} V{__version__} - {__date__}")
    print(f"Chemin : {Path(__file__).resolve()}")
    
    args = sys.argv[1:]
    
    # Aide
    if '-h' in args or '--help' in args:
        afficher_aide()
        return
    
    # Stats détaillées
    if not args or '--stats' in args:
        afficher_stats_detaillees()
        return
    
    # Mode récupération de commentaire
    if len(args) >= 2:
        pathologie = args[0]
        langue = args[1]
        
        print(f"\nRecherche : '{pathologie}' en '{langue}'")
        print("-" * 50)
        
        resultat = get_commentaire(pathologie, langue)
        
        if resultat:
            print(f"Résultat : {resultat}")
        else:
            print("Résultat : (vide)")
        
        print()
        print("Statistiques :")
        stats = get_stats()
        print(f"  Traductions DeepL : {stats['traductions_deepl']}")
        print(f"  Sauvegardes       : {stats['sauvegardes']}")
    else:
        afficher_aide()


if __name__ == "__main__":
    main()
