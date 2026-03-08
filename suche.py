# suche.py V1.0.18 - 03/12/2025 19:43:16
__pgm__ = "suche.py"
__version__ = "1.0.18"
__date__ = "03/12/2025 19:43:16"

# ╔════════════════════════════════════════════════════════════════
# ║ suche.py v2.3.1 - Wrapper multilingue pour cherche.py
# ║ 
# ║ CORRECTION v2.3.1 (15/12/2025) :
# ║   - Ne prendre que le PREMIER terme des traductions (split virgule)
# ║   - Corrige l'affichage japonais qui listait tous les synonymes
# ║
# ║ NOUVEAU v2.3.0 (15/12/2025) :
# ║   - Traduction des filtres (description_filtres) vers la langue de réponse
# ║   - RÉACTIVÉ : Traduction des pathologies patients via lookup glossaire
# ║   - Pas d'appel API pour les pathologies (lookup pur = rapide)
# ║   - Exemple: "Bruxisme, Beance" → "歯軋り, 開咬" si réponse en japonais
# ║
# ║ CORRECTION v2.2.1 (03/12/2025) :
# ║   - DÉSACTIVÉ : Traduction pathologies côté serveur (trop lent)
# ║   - Les pathologies sont TOUJOURS retournées en français
# ║   - TODO: Traduction côté client (mapping JSON)
# ║
# ║ NOUVEAUTÉ v2.2.0 (03/12/2025) :
# ║   - AUTO-RETRY : Si 0 résultat avec langue imposée → relance en Auto
# ║   - Ajoute retry_info dans la réponse pour affichage bandeau client
# ║
# ║ CORRECTION v2.1.3 (29/11/2025) :
# ║   - Indexation par TOUS les synonymes (pas juste le standard)
# ║   - Traduction de 'pathologies' ET 'oripathologies' pour l'affichage web
# ║
# ║ CORRECTION v2.1.2 (29/11/2025) :
# ║   - Mapping pathoori indexé par colonne 'standard' (terme normalisé)
# ║   - traduire_pathologie() utilise standardise() avant lookup
# ║   - Les pathologies de la base sont normalisées avant traduction
# ║   - DeepL n'est appelé que si la pathologie n'est pas dans pathoori
# ║
# ║ CORRECTION v2.1.1 (29/11/2025) :
# ║   - BUG CRITIQUE : pathoori.csv et messages.csv n'étaient pas chargés
# ║   - Cause : csv.DictReader utilisait la ligne de commentaire comme en-têtes
# ║   - Solution : Filtrer les lignes # AVANT de créer le DictReader
# ║   - Résultat : Les pathologies utilisent maintenant le mapping pré-traduit
# ║                au lieu d'appeler DeepL pour chaque pathologie
# ║
# ║ NOUVEAU v2.1.0 :
# ║   - Mode batch : python suche.py base.db fichier.csv [--verbose]
# ║   - Ajout génération de logs dans logrecherche.csv
# ║   - Format partagé avec cherche.py (18 colonnes)
# ║   - CSV batch : colonne 'langue' optionnelle (sinon Auto)
# ║
# ║ v2.0.0 :
# ║   - Utilise pathoori.csv (au lieu de ps.csv)
# ║   - Intégration traduire.py pour fallback sans DeepL
# ║   - Support langues non natives via traduction à la volée
# ║   - response_lang pour forcer réponse en français
# ║
# ║ Usages :
# ║   - Import    : from suche import sucher
# ║   - Unitaire  : python suche.py base.db "question" [--lang=XX] [--verbose]
# ║   - Batch     : python suche.py base.db fichier.csv [--verbose]
# ╚════════════════════════════════════════════════════════════════

import sys
import os
import csv
import json
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime

# Import du module de traduction multi-fournisseurs
try:
    from traduire import (
        traduire, detecter_langue, est_langue_native, 
        get_fallback_langue, LANGUES_NATIVES
    )
    TRADUIRE_DISPONIBLE = True
except ImportError:
    TRADUIRE_DISPONIBLE = False
    LANGUES_NATIVES = ['fr', 'en', 'de', 'es', 'it', 'pt', 'pl', 'ro', 'th', 'ar', 'cn', 'ja']


# ════════════════════════════════════════════════════════════════
# CONFIGURATION
# ════════════════════════════════════════════════════════════════

# Clé API DeepL depuis variable d'environnement
DEEPL_API_KEY_ENV = os.environ.get('DEEPL_API_KEY', '')

# Chemins
RACINE = r"c:\g"
LOGS_DIR = os.path.join(RACINE, "logs")
TESTS_DIR = os.path.join(RACINE, "tests")
LOG_FILE = os.path.join(LOGS_DIR, "logrecherche.csv")


# ════════════════════════════════════════════════════════════════
# GESTION DES LOGS
# ════════════════════════════════════════════════════════════════

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


def _log_recherche(question_originale: str, question_fr: str, base: str, mode: str,
                   nb_patients: int, temps_ms: int, pathologies: List[str],
                   ages: List[str], residu: str, filtres: dict, sql: str,
                   languesaisie: str, langueutilisee: str, modulelangue: str,
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
                languesaisie,         # languesaisie
                langueutilisee,       # langueutilisee
                modulelangue,         # modulelangue
                question_originale,   # questionoriginale
                question_fr,          # question (traduite en français)
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


# ════════════════════════════════════════════════════════════════
# CHARGEMENT DES FICHIERS DE RÉFÉRENCE
# ════════════════════════════════════════════════════════════════

def charger_pathologies_multilingues(pathoori_path: str, verbose: bool = False) -> Dict[str, dict]:
    """
    Charge pathoori.csv avec toutes les traductions de pathologies.
    
    CORRECTION v2.1.1 : Filtre les lignes de commentaire (#) AVANT DictReader
    CORRECTION v2.1.2 : Indexe par colonne 'standard' (terme normalisé)
    
    Architecture :
    - Clé du mapping = colonne 'standard' (terme normalisé sans accents)
    - Les pathologies de la base sont normalisées avant lookup
    - Résultat : traductions pour les 11 langues natives
    """
    if verbose:
        print(f"[DEBUG] suche.py: Chargement de {os.path.abspath(pathoori_path)}")
    
    if not os.path.exists(pathoori_path):
        if verbose:
            print(f"[DEBUG] suche.py: ERREUR - Fichier introuvable: {pathoori_path}")
        return {}
    
    mapping = {}
    
    try:
        with open(pathoori_path, 'r', encoding='utf-8-sig') as f:
            # Filtrer les lignes de commentaire
            lignes = [line for line in f if not line.strip().startswith('#')]
            
            if not lignes:
                if verbose:
                    print(f"[DEBUG] suche.py: Fichier vide ou que des commentaires")
                return {}
            
            import io
            lignes_io = io.StringIO(''.join(lignes))
            
            reader = csv.DictReader(lignes_io, delimiter=';')
            
            for ligne in reader:
                # ╔═══════════════════════════════════════════════════════════════
                # ║ CORRECTION v2.1.2 : Utiliser 'standard' comme clé de mapping
                # ║ C'est le terme normalisé (minuscules, sans accents)
                # ╚═══════════════════════════════════════════════════════════════
                standard = ligne.get('standard', '').strip().lower()
                if not standard:
                    continue
                
                original = ligne.get('original', '').strip()
                fr_value = ligne.get('fr', '').strip()
                
                # Données de traduction
                trad_data = {
                    'original': original,
                    'standard': standard,
                    'fr': fr_value,
                    'en': ligne.get('en', '').strip(),
                    'de': ligne.get('de', '').strip(),
                    'es': ligne.get('es', '').strip(),
                    'it': ligne.get('it', '').strip(),
                    'pt': ligne.get('pt', '').strip(),
                    'pl': ligne.get('pl', '').strip(),
                    'ro': ligne.get('ro', '').strip(),
                    'th': ligne.get('th', '').strip(),
                    'ar': ligne.get('ar', '').strip(),
                    'cn': ligne.get('cn', '').strip(),
                    'ja': ligne.get('ja', '').strip()
                }
                
                # ╔═══════════════════════════════════════════════════════════════
                # ║ CORRECTION v2.1.3 : Indexer par le standard ET par tous les
                # ║ synonymes standardisés pour éviter les appels DeepL
                # ╚═══════════════════════════════════════════════════════════════
                
                # 1. Indexer par le standard lui-même
                mapping[standard] = trad_data
                
                # 2. Indexer par chaque synonyme (standardisé)
                synonymes_str = ligne.get('synonymes', '').strip()
                if synonymes_str:
                    for syn in synonymes_str.split(','):
                        syn_clean = syn.strip()
                        if syn_clean:
                            # Standardiser le synonyme (minuscules, sans accents)
                            syn_std = standardise(syn_clean) if STANDARDISE_DISPONIBLE else syn_clean.lower()
                            if syn_std and syn_std not in mapping:
                                mapping[syn_std] = trad_data
        
        nb_pathologies = len([k for k, v in mapping.items() if k == v.get('standard')])
        if verbose:
            print(f"[DEBUG] suche.py: {nb_pathologies} pathologies, {len(mapping)} clés de lookup depuis pathoori.csv")
        
        return mapping
        
    except Exception as e:
        if verbose:
            print(f"[DEBUG] suche.py: ERREUR chargement pathoori.csv: {e}")
        return {}


def charger_messages_multilingues(messages_path: str, verbose: bool = False) -> Dict[str, dict]:
    """
    Charge messages.csv avec les traductions des messages UI.
    
    CORRECTION v2.1.1 : Filtre les lignes de commentaire (#) AVANT DictReader.
    """
    if verbose:
        print(f"[DEBUG] suche.py: Chargement de {os.path.abspath(messages_path)}")
    
    if not os.path.exists(messages_path):
        if verbose:
            print(f"[DEBUG] suche.py: ERREUR - Fichier introuvable: {messages_path}")
        return {}
    
    messages = {}
    
    try:
        with open(messages_path, 'r', encoding='utf-8-sig') as f:
            # ╔═══════════════════════════════════════════════════════════════
            # ║ CORRECTION v2.1.1 : Filtrer les lignes de commentaire
            # ╚═══════════════════════════════════════════════════════════════
            lignes = [line for line in f if not line.strip().startswith('#')]
            
            if not lignes:
                if verbose:
                    print(f"[DEBUG] suche.py: Fichier messages vide ou que des commentaires")
                return {}
            
            import io
            lignes_io = io.StringIO(''.join(lignes))
            
            reader = csv.DictReader(lignes_io, delimiter=';')
            
            for ligne in reader:
                usage = ligne.get('usage', '').strip()
                if not usage:
                    continue
                
                messages[usage] = {
                    'fr': ligne.get('fr', '').strip(),
                    'en': ligne.get('en', '').strip(),
                    'de': ligne.get('de', '').strip(),
                    'es': ligne.get('es', '').strip(),
                    'it': ligne.get('it', '').strip(),
                    'pt': ligne.get('pt', '').strip(),
                    'pl': ligne.get('pl', '').strip(),
                    'ro': ligne.get('ro', '').strip(),
                    'th': ligne.get('th', '').strip(),
                    'ar': ligne.get('ar', '').strip(),
                    'cn': ligne.get('cn', '').strip(),
                    'ja': ligne.get('ja', '').strip()
                }
        
        if verbose:
            print(f"[DEBUG] suche.py: {len(messages)} messages chargés depuis messages.csv")
        
        return messages
        
    except Exception as e:
        if verbose:
            print(f"[DEBUG] suche.py: ERREUR chargement messages.csv: {e}")
        return {}


# ════════════════════════════════════════════════════════════════
# TRADUCTION DES PATHOLOGIES
# ════════════════════════════════════════════════════════════════

# Import de standardise pour normaliser les pathologies
try:
    from standardise import standardise
    STANDARDISE_DISPONIBLE = True
except ImportError:
    STANDARDISE_DISPONIBLE = False
    import unicodedata
    import re
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


def traduire_pathologie(patho_fr: str, mapping_patho: dict, lang: str, 
                        api_key: str = None, verbose: bool = False) -> str:
    """
    Traduit une pathologie française vers la langue cible.
    
    CORRECTION v2.3.0 : Si api_key=None explicitement, pas de fallback API
    CORRECTION v2.1.2 : Utilise standardise() pour normaliser la pathologie
    avant de chercher dans le mapping (clé = standard).
    
    Args:
        patho_fr: Pathologie en français
        mapping_patho: Dictionnaire de traductions (clé = standard)
        lang: Langue cible
        api_key: Clé API DeepL. Si None, lookup glossaire uniquement (pas d'API)
        verbose: Mode debug
    """
    if lang == 'fr':
        return patho_fr
    
    # ╔═══════════════════════════════════════════════════════════════
    # ║ CORRECTION v2.1.2 : Normaliser avec standardise()
    # ║ Le mapping utilise 'standard' comme clé (sans accents)
    # ╚═══════════════════════════════════════════════════════════════
    patho_std = standardise(patho_fr)
    
    if patho_std in mapping_patho:
        trad = mapping_patho[patho_std].get(lang, '')
        if trad:
            # ╔═══════════════════════════════════════════════════════════════
            # ║ CORRECTION v2.3.1 : Ne prendre que le PREMIER terme
            # ║ Certaines langues (ja) ont tous les synonymes séparés par virgule
            # ║ Ex: "歯軋り, 夜間歯ぎしり, ..." → "歯軋り"
            # ╚═══════════════════════════════════════════════════════════════
            if ',' in trad:
                trad = trad.split(',')[0].strip()
            if verbose:
                print(f"[DEBUG] suche.py: Pathologie '{patho_fr}' → '{patho_std}' → '{trad}' (pathoori)")
            return trad
    
    # ╔═══════════════════════════════════════════════════════════════
    # ║ CORRECTION v2.3.0 : Pas de fallback API si api_key=None
    # ║ Cela permet un lookup glossaire pur (rapide, sans latence)
    # ╚═══════════════════════════════════════════════════════════════
    if api_key is None:
        # Pas d'API demandée, retourner le terme français
        if verbose:
            print(f"[DEBUG] suche.py: Pathologie '{patho_fr}' non trouvée dans glossaire (pas d'API)")
        return patho_fr
    
    # Fallback : traduction via DeepL/MyMemory si clé API fournie
    if TRADUIRE_DISPONIBLE and api_key:
        trad, fournisseur = traduire(patho_fr, 'fr', lang, api_key, verbose)
        if fournisseur != 'none':
            if verbose:
                print(f"[DEBUG] suche.py: Pathologie '{patho_fr}' traduite via {fournisseur}")
            return trad
    
    return patho_fr


def traduire_pathologies_patient(patho_str: str, mapping_patho: dict, lang: str,
                                  api_key: str = None, verbose: bool = False) -> str:
    """
    Traduit la liste de pathologies d'un patient.
    """
    if not patho_str or lang == 'fr':
        return patho_str
    
    pathologies_list = [p.strip() for p in patho_str.split(',') if p.strip()]
    pathologies_trad = []
    
    for patho_fr in pathologies_list:
        trad = traduire_pathologie(patho_fr, mapping_patho, lang, api_key, verbose)
        pathologies_trad.append(trad)
    
    return ', '.join(pathologies_trad)


def traduire_description_filtres(description_fr: str, mapping_patho: dict, lang: str,
                                  api_key: str = None, verbose: bool = False) -> str:
    """
    Traduit la description des filtres vers la langue cible.
    
    La description contient des pathologies séparées par ' + ' ou ', '
    Exemple: "bruxisme + béance face" → "歯軋り + 開咬"
    
    NOUVEAU v2.3.0 : Traduction des filtres pour réponse multilingue
    """
    if not description_fr or lang == 'fr':
        return description_fr
    
    # Séparer par ' + ' d'abord (séparateur principal)
    parties = description_fr.split(' + ')
    parties_traduites = []
    
    for partie in parties:
        # Chaque partie peut contenir des éléments séparés par ', '
        sous_parties = [p.strip() for p in partie.split(', ') if p.strip()]
        sous_parties_trad = []
        
        for terme in sous_parties:
            # Essayer de traduire comme pathologie
            terme_trad = traduire_pathologie(terme, mapping_patho, lang, api_key, verbose=False)
            sous_parties_trad.append(terme_trad)
        
        parties_traduites.append(', '.join(sous_parties_trad))
    
    resultat = ' + '.join(parties_traduites)
    
    if verbose and resultat != description_fr:
        print(f"[DEBUG] suche.py: Filtres '{description_fr}' → '{resultat}'")
    
    return resultat


# ════════════════════════════════════════════════════════════════
# TRADUCTION DES MESSAGES
# ════════════════════════════════════════════════════════════════

def get_message(messages: dict, usage: str, lang: str, nb: int = 0, 
                filtre: str = '', api_key: str = None, verbose: bool = False) -> str:
    """
    Récupère un message traduit avec substitutions.
    """
    if usage not in messages:
        return f"{nb} patients trouvés"
    
    msg_dict = messages[usage]
    msg = msg_dict.get(lang, '')
    
    if not msg and lang not in LANGUES_NATIVES:
        msg_fr = msg_dict.get('fr', '')
        if msg_fr and TRADUIRE_DISPONIBLE:
            msg, fournisseur = traduire(msg_fr, 'fr', lang, api_key, verbose)
            if verbose and fournisseur != 'none':
                print(f"[DEBUG] suche.py: Message '{usage}' traduit via {fournisseur}")
    
    if not msg:
        msg = msg_dict.get('fr', f"{nb} patients trouvés")
    
    msg = msg.replace('xx', str(nb))
    msg = msg.replace('{ff}', filtre)
    
    return msg


# ════════════════════════════════════════════════════════════════
# FONCTION PRINCIPALE : sucher()
# ════════════════════════════════════════════════════════════════

def sucher(question: str, base_path: str, lang: Optional[str] = None, 
           mode: str = 'sc', verbose: bool = False, 
           mapping_patho: Optional[dict] = None,
           messages: Optional[dict] = None,
           response_lang: Optional[str] = None,
           limit: int = 100, offset: int = 0,
           api_key: str = None) -> dict:
    """
    Point d'entrée multilingue pour rechercher des patients.
    
    Args:
        question: Question de recherche (dans n'importe quelle langue)
        base_path: Chemin vers la base SQLite
        lang: Langue de la question ('auto', 'fr', 'en', etc.) ou None pour auto-détection
        mode: Mode de recherche ('sc', 'sp', 'se')
        verbose: Afficher les logs de debug
        mapping_patho: Dict pathologies multilingues (chargé si None)
        messages: Dict messages multilingues (chargé si None)
        response_lang: 'same' = même langue, 'fr' = forcer français
        limit: Nombre max de résultats
        offset: Offset pour pagination
        api_key: Clé API DeepL (priorité sur variable env)
        
    Returns:
        dict: Résultats avec métadonnées multilingues
    """
    start_time = datetime.now()
    base_name = os.path.basename(base_path)
    
    # Clé API : paramètre > variable d'environnement
    deepl_key = api_key or DEEPL_API_KEY_ENV
    
    # Variables pour les logs
    languesaisie = lang if lang else 'Auto'
    langueutilisee = ''
    modulelangue = ''
    question_fr = question
    traduction_fournisseur = 'none'
    
    if verbose:
        print(f"[DEBUG] suche.py: Question: '{question}'")
        print(f"[DEBUG] suche.py: Lang demandée: {lang}, Response: {response_lang}")
        print(f"[DEBUG] suche.py: DeepL API: {'✓' if deepl_key else '✗'}")
    
    # ═══════════════════════════════════════════════════════════════
    # ÉTAPE 1 : DÉTECTION LANGUE
    # ═══════════════════════════════════════════════════════════════
    
    if lang is None or lang.lower() == 'auto':
        if TRADUIRE_DISPONIBLE:
            lang = detecter_langue(question, deepl_key, verbose)
            modulelangue = 'deepl' if deepl_key else 'heuristique'
        else:
            lang = 'fr'
            modulelangue = 'fallback'
    
    lang = lang.lower()
    langueutilisee = lang
    
    if verbose:
        print(f"[DEBUG] suche.py: Langue détectée/utilisée: {lang}")
    
    # ═══════════════════════════════════════════════════════════════
    # ÉTAPE 2 : DÉTERMINER LANGUE DE RÉPONSE
    # ═══════════════════════════════════════════════════════════════
    
    if response_lang == 'fr':
        output_lang = 'fr'
    else:
        output_lang = lang
    
    if verbose:
        print(f"[DEBUG] suche.py: Langue de réponse: {output_lang}")
    
    # ═══════════════════════════════════════════════════════════════
    # ÉTAPE 3 : TRADUIRE QUESTION → FRANÇAIS
    # ═══════════════════════════════════════════════════════════════
    
    if lang == 'fr':
        question_fr = question
        traduction_fournisseur = 'none'
    elif TRADUIRE_DISPONIBLE:
        question_fr, traduction_fournisseur = traduire(question, lang, 'fr', deepl_key, verbose)
        if traduction_fournisseur != 'none':
            modulelangue = traduction_fournisseur
        if verbose:
            print(f"[DEBUG] suche.py: Question traduite: '{question_fr}' (via {traduction_fournisseur})")
    else:
        question_fr = question
        traduction_fournisseur = 'none'
        if verbose:
            print(f"[DEBUG] suche.py: Module traduire non disponible, question non traduite")
    
    # ═══════════════════════════════════════════════════════════════
    # ÉTAPE 4 : CHARGER RÉFÉRENCES SI NON FOURNIES
    # ═══════════════════════════════════════════════════════════════
    
    script_dir = Path(__file__).parent
    refs_dir = script_dir / "refs"
    
    if mapping_patho is None:
        pathoori_path = refs_dir / "pathoori.csv"
        if not pathoori_path.exists():
            pathoori_path = Path("c:/g/refs/pathoori.csv")
        
        if pathoori_path.exists():
            mapping_patho = charger_pathologies_multilingues(str(pathoori_path), verbose)
        else:
            mapping_patho = {}
            if verbose:
                print(f"[DEBUG] suche.py: pathoori.csv introuvable")
    
    if messages is None:
        messages_path = refs_dir / "messages.csv"
        if not messages_path.exists():
            messages_path = Path("c:/g/refs/messages.csv")
        
        if messages_path.exists():
            messages = charger_messages_multilingues(str(messages_path), verbose)
        else:
            messages = {}
            if verbose:
                print(f"[DEBUG] suche.py: messages.csv introuvable")
    
    # ═══════════════════════════════════════════════════════════════
    # ÉTAPE 5 : APPELER CHERCHE.PY (EN FRANÇAIS)
    # ═══════════════════════════════════════════════════════════════
    
    try:
        from cherche import cherche
        
        resultats = cherche(
            question=question_fr,
            base_path=base_path,
            mode=mode,
            limit=limit,
            offset=offset,
            verbose=verbose
        )
        
    except ImportError as e:
        if verbose:
            print(f"[DEBUG] suche.py: ERREUR import cherche.py: {e}")
        elapsed_ms = int((datetime.now() - start_time).total_seconds() * 1000)
        erreur = f"Module cherche.py non disponible: {e}"
        
        _log_recherche(
            question_originale=question,
            question_fr=question_fr,
            base=base_name,
            mode=mode,
            nb_patients=0,
            temps_ms=elapsed_ms,
            pathologies=[],
            ages=[],
            residu='',
            filtres={},
            sql='',
            languesaisie=languesaisie,
            langueutilisee=langueutilisee,
            modulelangue=modulelangue,
            erreur=erreur
        )
        
        return {
            'erreur': erreur,
            'nb_patients': 0,
            'patients': [],
            'lang': lang,
            'response_lang': output_lang
        }
    except Exception as e:
        if verbose:
            print(f"[DEBUG] suche.py: ERREUR cherche(): {e}")
        elapsed_ms = int((datetime.now() - start_time).total_seconds() * 1000)
        erreur = str(e)
        
        _log_recherche(
            question_originale=question,
            question_fr=question_fr,
            base=base_name,
            mode=mode,
            nb_patients=0,
            temps_ms=elapsed_ms,
            pathologies=[],
            ages=[],
            residu='',
            filtres={},
            sql='',
            languesaisie=languesaisie,
            langueutilisee=langueutilisee,
            modulelangue=modulelangue,
            erreur=erreur
        )
        
        return {
            'erreur': erreur,
            'nb_patients': 0,
            'patients': [],
            'lang': lang,
            'response_lang': output_lang
        }
    
    # ═══════════════════════════════════════════════════════════════
    # ÉTAPE 6 : TRADUIRE PATHOLOGIES DES PATIENTS (v2.3.0)
    # ═══════════════════════════════════════════════════════════════
    # 
    # RÉACTIVÉ v2.3.0 : Traduction via lookup glossaire (pas d'API = rapide)
    # Les pathologies sont traduites vers output_lang si != 'fr'
    #
    if output_lang != 'fr' and resultats.get('patients') and mapping_patho:
        t0_trad = datetime.now()
        nb_patients_traduits = 0
        
        for patient in resultats['patients']:
            # Traduire 'pathologies' (version normalisée)
            if patient.get('pathologies'):
                patient['pathologies'] = traduire_pathologies_patient(
                    patient['pathologies'], mapping_patho, output_lang, 
                    api_key=None,  # Pas d'API, lookup seulement
                    verbose=False
                )
            # Traduire 'oripathologies' (version affichage)
            if patient.get('oripathologies'):
                patient['oripathologies'] = traduire_pathologies_patient(
                    patient['oripathologies'], mapping_patho, output_lang,
                    api_key=None,  # Pas d'API, lookup seulement
                    verbose=False
                )
            nb_patients_traduits += 1
        
        elapsed_trad = int((datetime.now() - t0_trad).total_seconds() * 1000)
        if verbose:
            print(f"[DEBUG] suche.py: {nb_patients_traduits} patients traduits en {elapsed_trad}ms (lookup glossaire)")
    elif verbose:
        if output_lang == 'fr':
            print(f"[DEBUG] suche.py: Pathologies en français (pas de traduction)")
        else:
            print(f"[DEBUG] suche.py: Pas de mapping_patho, pathologies non traduites")
    
    # ═══════════════════════════════════════════════════════════════
    # ÉTAPE 7 : GÉNÉRER MESSAGE DANS LA LANGUE DE RÉPONSE
    # ═══════════════════════════════════════════════════════════════
    
    nb_patients = resultats.get('nb_patients', 0)
    description_filtres = resultats.get('description_filtres', '')
    
    # ╔═══════════════════════════════════════════════════════════════
    # ║ NOUVEAU v2.3.0 : Traduire description_filtres vers output_lang
    # ║ Exemple: "bruxisme" → "歯軋り" si output_lang = 'ja'
    # ╚═══════════════════════════════════════════════════════════════
    if output_lang != 'fr' and description_filtres:
        description_filtres_traduite = traduire_description_filtres(
            description_filtres, mapping_patho, output_lang, deepl_key, verbose
        )
        if verbose:
            print(f"[DEBUG] suche.py: Filtres traduits: '{description_filtres}' → '{description_filtres_traduite}'")
    else:
        description_filtres_traduite = description_filtres
    
    if nb_patients == 0:
        usage = 'final_none'
    elif nb_patients == 1:
        usage = 'final_exact'
    else:
        usage = 'final_multiple'
    
    message_traduit = get_message(
        messages, usage, output_lang, nb_patients, 
        description_filtres_traduite, deepl_key, verbose
    )
    
    resultats['message'] = message_traduit
    
    # ═══════════════════════════════════════════════════════════════
    # ÉTAPE 8 : AJOUTER MÉTADONNÉES LINGUISTIQUES
    # ═══════════════════════════════════════════════════════════════
    
    elapsed_ms = int((datetime.now() - start_time).total_seconds() * 1000)
    
    resultats['lang'] = lang
    resultats['lang_detectee'] = lang
    resultats['response_lang'] = output_lang
    resultats['question_originale'] = question
    resultats['question_traduite'] = question_fr if lang != 'fr' else None
    resultats['traduction_provider'] = traduction_fournisseur if lang != 'fr' else None
    resultats['temps_ms'] = elapsed_ms
    
    # ═══════════════════════════════════════════════════════════════
    # ÉTAPE 9 : LOGGER LA RECHERCHE
    # ═══════════════════════════════════════════════════════════════
    
    filtres = resultats.get('filtres', {})
    sql = resultats.get('sql', '')
    
    pathologies_labels = []
    ages_labels = []
    residu = ''
    
    if filtres:
        # ╔═══════════════════════════════════════════════════════════════
        # ║ CORRECTION v2.1.1 : patho peut être un dict OU une string
        # ╚═══════════════════════════════════════════════════════════════
        for patho in filtres.get('pathologies', []):
            if isinstance(patho, dict):
                if patho.get('label'):
                    pathologies_labels.append(patho['label'])
            elif isinstance(patho, str) and patho:
                pathologies_labels.append(patho)
        
        for critere in filtres.get('criteres', []):
            if isinstance(critere, dict) and critere.get('type') == 'age':
                label = critere.get('label', '')
                if label:
                    ages_labels.append(label)
    
    _log_recherche(
        question_originale=question,
        question_fr=question_fr,
        base=base_name,
        mode=mode,
        nb_patients=nb_patients,
        temps_ms=elapsed_ms,
        pathologies=pathologies_labels,
        ages=ages_labels,
        residu=residu,
        filtres=filtres,
        sql=sql,
        languesaisie=languesaisie,
        langueutilisee=langueutilisee,
        modulelangue=modulelangue,
        erreur=resultats.get('erreur', '')
    )
    
    # ═══════════════════════════════════════════════════════════════
    # AUTO-RETRY : Si 0 résultat avec langue imposée → relancer en Auto
    # ═══════════════════════════════════════════════════════════════
    
    if nb_patients == 0 and languesaisie.lower() != 'auto':
        if verbose:
            print(f"[DEBUG] suche.py: 0 résultat avec langue={languesaisie}, retry en Auto...")
        
        # Noms des langues pour le message
        NOMS_LANGUES = {
            'fr': 'Français', 'en': 'English', 'de': 'Deutsch',
            'es': 'Español', 'it': 'Italiano', 'pt': 'Português',
            'pl': 'Polski', 'ro': 'Română', 'th': 'ไทย',
            'ar': 'العربية', 'cn': '中文', 'ja': '日本語'
        }
        nom_langue = NOMS_LANGUES.get(languesaisie.lower(), languesaisie)
        
        # Relancer la recherche en mode Auto
        resultats_retry = sucher(
            question=question,
            base_path=base_path,
            lang='auto',  # ← Forcer Auto
            mode=mode,
            verbose=verbose,
            mapping_patho=mapping_patho,
            messages=messages,
            response_lang=response_lang,
            limit=limit,
            offset=offset,
            api_key=api_key
        )
        
        # Ajouter les infos du retry
        resultats_retry['retry_info'] = {
            'langue_initiale': languesaisie,
            'langue_initiale_nom': nom_langue,
            'langue_detectee': resultats_retry.get('lang_detectee', 'auto'),
            'message': f"Aucun résultat avec {nom_langue}. Recherche relancée en Auto."
        }
        
        if verbose:
            print(f"[DEBUG] suche.py: Retry Auto → {resultats_retry.get('nb_patients', 0)} patient(s)")
        
        return resultats_retry
    
    if verbose:
        print(f"[DEBUG] suche.py: Terminé en {elapsed_ms}ms")
    
    return resultats


# Alias pour compatibilité
suche = sucher


# ════════════════════════════════════════════════════════════════
# TRAITEMENT BATCH
# ════════════════════════════════════════════════════════════════

def _traiter_fichier_batch(db_path: str, input_csv: str, verbose: bool = False,
                           api_key: str = None) -> int:
    """
    Traite un fichier CSV de tests multilingues et génère le fichier de sortie.
    
    Format CSV attendu:
    - question;trouvés           → langue = Auto pour toutes
    - question;langue;trouvés    → langue spécifiée par ligne
    
    Args:
        db_path: Chemin vers la base de données
        input_csv: Chemin du fichier d'entrée
        verbose: Affiche les informations de debug
        api_key: Clé API DeepL optionnelle
        
    Returns:
        Nombre de lignes traitées
    """
    # Résoudre le chemin du fichier d'entrée
    if not os.path.isabs(input_csv):
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
    
    # Construire le nom de sortie
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
    print("Chargement des références multilingues...")
    script_dir = Path(__file__).parent
    refs_dir = script_dir / "refs"
    
    pathoori_path = refs_dir / "pathoori.csv"
    if not pathoori_path.exists():
        pathoori_path = Path("c:/g/refs/pathoori.csv")
    mapping_patho = charger_pathologies_multilingues(str(pathoori_path), verbose) if pathoori_path.exists() else {}
    
    messages_path = refs_dir / "messages.csv"
    if not messages_path.exists():
        messages_path = Path("c:/g/refs/messages.csv")
    messages = charger_messages_multilingues(str(messages_path), verbose) if messages_path.exists() else {}
    
    print()
    
    # Lire le fichier d'entrée et détecter le format
    lignes_data = []
    has_langue_column = False
    encodages = ["utf-8-sig", "utf-8", "windows-1252", "iso-8859-1"]
    
    for encodage in encodages:
        try:
            with open(input_path, "r", encoding=encodage, newline="") as f:
                reader = csv.reader(f, delimiter=";")
                for row in reader:
                    # Ignorer les commentaires
                    if row and (row[0] or "").startswith("#"):
                        continue
                    
                    # Ignorer les lignes vides
                    if not row:
                        continue
                    
                    # Détecter l'en-tête pour savoir si colonne langue existe
                    if (row[0] or "").lower() == "question":
                        # Vérifier si colonne 'langue' existe
                        if len(row) >= 2 and (row[1] or "").lower() == "langue":
                            has_langue_column = True
                        continue
                    
                    question = (row[0] or "").strip()
                    if question:
                        if has_langue_column and len(row) >= 2:
                            langue = (row[1] or "").strip() or "Auto"
                        else:
                            langue = "Auto"
                        lignes_data.append({'question': question, 'langue': langue})
            break
        except (UnicodeDecodeError, UnicodeError):
            continue
        except Exception as e:
            print(f"ERREUR lecture {os.path.abspath(input_path)}: {e}")
            return 0
    
    print(f"{len(lignes_data)} question(s) à traiter")
    print(f"Colonne langue : {'Oui' if has_langue_column else 'Non (Auto pour toutes)'}")
    print("-" * 70)
    
    # Traiter chaque question
    resultats = []
    
    for i, data in enumerate(lignes_data, 1):
        question = data['question']
        langue = data['langue']
        
        # Exécuter la recherche
        resultat = sucher(
            question=question,
            base_path=db_path,
            lang=langue if langue.lower() != 'auto' else None,
            mode='sc',
            limit=100,
            offset=0,
            verbose=verbose,
            mapping_patho=mapping_patho,
            messages=messages,
            api_key=api_key
        )
        
        nb_patients = resultat.get('nb_patients', 0)
        lang_detectee = resultat.get('lang', '?')
        temps_ms = resultat.get('temps_ms', 0)
        description = resultat.get('description_filtres', '')
        
        resultats.append({
            'question': question,
            'langue_demandee': langue,
            'langue_detectee': lang_detectee,
            'trouvés': nb_patients,
            'filtres': description,
            'temps_ms': temps_ms
        })
        
        # Affichage console
        lang_info = f"[{lang_detectee}]" if langue.lower() == 'auto' else f"[{langue}]"
        if nb_patients > 0:
            print(f"✓ [{i}/{len(lignes_data)}] {lang_info} {nb_patients:4d} patient(s) - {question[:50]}...")
        else:
            print(f"  [{i}/{len(lignes_data)}] {lang_info}    0 patient   - {question[:50]}...")
    
    print("-" * 70)
    
    # Écrire le fichier de sortie
    try:
        with open(output_path, "w", encoding="utf-8-sig", newline="") as f:
            writer = csv.writer(f, delimiter=";")
            
            # Cartouche
            timestamp = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
            f.write(f"# {output_basename} V1.0.0 - {timestamp}\n")
            
            # En-tête
            writer.writerow(["question", "langue_demandee", "langue_detectee", "trouvés", "filtres", "temps_ms"])
            
            # Données
            for res in resultats:
                writer.writerow([
                    res['question'], 
                    res['langue_demandee'],
                    res['langue_detectee'],
                    res['trouvés'], 
                    res['filtres'], 
                    res['temps_ms']
                ])
        
        print(f"✓ Fichier de sortie : {os.path.abspath(output_path)}")
        
        # Statistiques
        total = len(resultats)
        avec_patients = sum(1 for res in resultats if res['trouvés'] > 0)
        temps_total = sum(res['temps_ms'] for res in resultats)
        print(f"  {avec_patients}/{total} questions avec patient(s)")
        print(f"  Temps total : {temps_total}ms (moyenne {temps_total//total if total > 0 else 0}ms/question)")
        
    except Exception as e:
        print(f"ERREUR écriture {os.path.abspath(output_path)}: {e}")
        return 0
    
    return len(resultats)


# ════════════════════════════════════════════════════════════════
# POINT D'ENTRÉE CLI
# ════════════════════════════════════════════════════════════════

def main():
    """Interface en ligne de commande."""
    print(f"{__pgm__} V{__version__} - {__date__}")
    print()
    
    if len(sys.argv) < 3:
        print("Usage:")
        print(f"  python {__pgm__} <base.db> \"question\" [options]")
        print(f"  python {__pgm__} <base.db> <fichier.csv> [--verbose]")
        print()
        print("Options:")
        print("  --lang=XX       Langue de la question (auto, fr, en, de, es, it, pt, pl, ro, th, ar, cn)")
        print("  --response=XX   Langue de la réponse: same (défaut) ou fr")
        print("  --mode=XX       Mode de recherche (sc, sp, se)")
        print("  --limit=N       Nombre max de résultats (défaut: 100)")
        print("  --api-key=XXX   Clé API DeepL")
        print("  -v, --verbose   Mode debug")
        print()
        print("Mode batch (fichier CSV):")
        print("  Format: question;trouvés           (langue=Auto)")
        print("  Format: question;langue;trouvés    (langue spécifiée)")
        print()
        print("Exemples:")
        print(f"  python {__pgm__} base55.db \"women under 39\" --lang=en")
        print(f"  python {__pgm__} base55.db \"Frauen mit Bruxismus\" --lang=de")
        print(f"  python {__pgm__} base25000.db testssuchein.csv")
        print()
        print(f"Langues natives: {', '.join(LANGUES_NATIVES)}")
        print(f"DeepL API: {'✓ Configurée' if DEEPL_API_KEY_ENV else '✗ Non configurée'}")
        print(f"Module traduire: {'✓ Disponible' if TRADUIRE_DISPONIBLE else '✗ Non disponible'}")
        print(f"Logs: {LOG_FILE}")
        return 1
    
    base_path = sys.argv[1]
    question_or_file = sys.argv[2]
    
    # Parser les options
    lang = None
    response_lang = 'same'
    mode = 'sc'
    limit = 100
    api_key = None
    verbose = '-v' in sys.argv or '--verbose' in sys.argv
    
    for arg in sys.argv:
        if arg.startswith('--lang='):
            lang = arg.split('=')[1].lower()
        elif arg.startswith('--response='):
            response_lang = arg.split('=')[1].lower()
        elif arg.startswith('--mode='):
            mode = arg.split('=')[1].lower()
        elif arg.startswith('--limit='):
            limit = int(arg.split('=')[1])
        elif arg.startswith('--api-key='):
            api_key = arg.split('=')[1]
    
    # Vérifier que la base existe
    if not os.path.exists(base_path):
        # Essayer dans le répertoire bases
        base_in_bases = os.path.join(RACINE, "bases", base_path)
        if os.path.exists(base_in_bases):
            base_path = base_in_bases
        else:
            print(f"ERREUR : Base {os.path.abspath(base_path)} introuvable")
            return 1
    
    print(f"Base: {os.path.abspath(base_path)}")
    
    # ═══════════════════════════════════════════════════════════════
    # DÉTECTION DU MODE : batch si .csv, sinon unitaire
    # ═══════════════════════════════════════════════════════════════
    
    if question_or_file.endswith('.csv'):
        # Mode BATCH
        print(f"Mode: BATCH MULTILINGUE")
        print()
        
        nb_lignes = _traiter_fichier_batch(base_path, question_or_file, verbose=verbose, api_key=api_key)
        return 0 if nb_lignes > 0 else 1
    
    else:
        # Mode UNITAIRE
        question = question_or_file
        
        print(f"Question: {question}")
        print(f"Langue demandée: {lang or 'Auto'}")
        print()
        
        # Exécuter la recherche
        resultats = sucher(
            question=question,
            base_path=base_path,
            lang=lang,
            mode=mode,
            verbose=verbose,
            response_lang=response_lang,
            limit=limit,
            api_key=api_key
        )
        
        # Afficher les résultats
        print("═" * 70)
        print(f"Question originale : {resultats.get('question_originale', question)}")
        if resultats.get('question_traduite'):
            print(f"Question traduite  : {resultats['question_traduite']}")
            print(f"Traducteur         : {resultats.get('traduction_provider', '?')}")
        print(f"Langue question    : {resultats.get('lang', '?')}")
        print(f"Langue réponse     : {resultats.get('response_lang', '?')}")
        print("═" * 70)
        print(f"Message: {resultats.get('message', '')}")
        print()
        
        if resultats.get('erreur'):
            print(f"ERREUR: {resultats['erreur']}")
            return 1
        
        if resultats.get('patients'):
            print(f"Patients ({len(resultats['patients'])} sur {resultats.get('nb_patients', 0)}):")
            for i, p in enumerate(resultats['patients'][:10], 1):
                sexe = p.get('sexe', '?')
                age = int(p.get('age', 0))
                prenom = p.get('oriprenom', '')
                nom = p.get('orinom', '')
                pathos = p.get('oripathologies', '')
                print(f"  {i}. {prenom} {nom}, {sexe}, {age} ans - {pathos}")
            
            if len(resultats['patients']) > 10:
                print(f"  ... et {len(resultats['patients']) - 10} autres")
        
        print()
        print(f"⏱️  Temps: {resultats.get('temps_ms', 0)}ms")
        print(f"📝 Log: {LOG_FILE}")
        
        return 0


if __name__ == "__main__":
    sys.exit(main())
