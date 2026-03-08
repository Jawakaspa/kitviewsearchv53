# analyse.py V1.0.9 - 07/01/2026 21:05:10
__pgm__ = "analyse.py"
__version__ = "1.0.9"
__date__ = "07/01/2026 21:05:10"

"""
Module d'analyse des logs de recherche Kitview Search.

CHANGEMENTS V1.0.10 (07/01/2026) :
- Concaténation fakerecherche.csv + logrecherche.csv
- fakerecherche.csv dans /refs/ = données de démo (déployées via Git)
- logrecherche.csv dans /logs/ = vrais logs (volatile sur Render)
- Colonne '_source' ajoutée ('fake' ou 'real') pour distinguer

CHANGEMENTS V1.0.8 (07/01/2026) :
- Ajout _charger_mots_vides() pour filtrer motsvides.csv
- Filtrage des résidus (de, la, les, qui, patients, etc.)
- Texte changé : "synonymes" → "patterns"

Ce module fournit des fonctions d'analyse des logs de recherche stockés
dans les fichiers CSV. Il est utilisable en CLI pour les tests 
et importable par server.py pour les endpoints API.

CHANGEMENTS V1.0.6 (05/01/2026) :
- Ajout temps_ms et pathologies dans DEFAULT_DISPLAY_COLUMNS
- Permet aux graphiques d'analyse d'afficher ces données

CHANGEMENTS V1.0.4 (05/01/2026) :
- Ajout colonne 'moteur' dans LOG_COLUMNS
- Support des nouveaux modes : standard, ia, standarddeepl, iadeepl, standardia
- Ajout statistiques par moteur IA

FONCTIONNALITÉS :
    - Stats globales (nb recherches, taux satisfaction, top pathologies...)
    - Liste paginée avec filtres multiples
    - Détail d'une recherche par session_id
    - Recherches similaires (même session, même IP, similarité IA)
    - Recherche fulltext dans les commentaires (insensible casse/accents)
    - Analyse IA des logs (points d'amélioration)
    - Export CSV filtré

COLONNES LOGRECHERCHE.CSV V1.2.0 :
    module;timestamp;temps_ms;languesaisie;langueutilisee;modulelangue;
    questionoriginale;question;filtres;sql;tri;base;mode;moteur;nb_patients;
    pathologies;ages;residu;erreur;session_id;ip_utilisateur;
    rating;type_probleme;commentaire

MODES DE RECHERCHE :
    - standard : détection locale (detall.py) + traduction glossaire
    - ia : détection IA (detia.py) + traduction glossaire  
    - standarddeepl : détection locale + traduction DeepL
    - iadeepl : détection IA + traduction DeepL
    - standardia : détection locale puis IA si échec

Usage CLI :
    python analyse.py stats                              # Stats globales
    python analyse.py list [--limit=20] [--offset=0]     # Liste paginée
    python analyse.py list --rating=👎 --mode=ia         # Liste filtrée
    python analyse.py detail <session_id>                # Détail
    python analyse.py similaires <session_id> --by=session  # Par session
    python analyse.py similaires <session_id> --by=ip       # Par IP
    python analyse.py similaires <session_id> --by=ia       # Par similarité IA
    python analyse.py search-comment <texte>             # Recherche dans commentaires
    python analyse.py ia-summary                         # Analyse IA
    python analyse.py export [filtres...]                # Export CSV

Usage en import :
    from analyse import (
        get_stats, get_recherches, get_recherche_detail,
        get_recherches_similaires, search_in_commentaires,
        get_ia_summary, export_csv
    )
"""

import sys
import os
import csv
import json
import hashlib
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Tuple
from collections import Counter

# =============================================================================
# CONFIGURATION
# =============================================================================

SCRIPT_DIR = Path(__file__).parent.resolve()
LOGS_DIR = SCRIPT_DIR / "logs"
LOG_FILE = LOGS_DIR / "logrecherche.csv"
REFS_DIR = SCRIPT_DIR / "refs"
FAKE_LOG_FILE = REFS_DIR / "fakerecherche.csv"  # Données de démo (déployées via Git)

# Colonnes du fichier de log V1.2.0 (avec moteur)
LOG_COLUMNS = [
    'module', 'timestamp', 'temps_ms', 'languesaisie', 'langueutilisee',
    'modulelangue', 'questionoriginale', 'question', 'filtres', 'sql', 'tri',
    'base', 'mode', 'moteur', 'nb_patients', 'pathologies', 'ages', 'residu', 'erreur',
    'session_id', 'ip_utilisateur', 'rating', 'type_probleme', 'commentaire'
]

# Colonnes affichées par défaut dans la liste
DEFAULT_DISPLAY_COLUMNS = [
    'timestamp', 'questionoriginale', 'mode', 'moteur', 'nb_patients', 'rating', 'type_probleme', 'temps_ms', 'pathologies'
]

# Types de problèmes connus
TYPES_PROBLEMES = [
    'Bug IHM', 'Trop de patients', 'Pas assez de patients', 'Autre'
]

# Ratings valides
RATINGS_VALIDES = ['👍', '👎', '', None]

# Cache des mots vides
_MOTS_VIDES_CACHE = None


def _charger_mots_vides() -> set:
    """
    Charge les mots vides depuis motsvides.csv (avec cache).
    
    Returns:
        set: Ensemble des mots vides en minuscules
    """
    global _MOTS_VIDES_CACHE
    
    if _MOTS_VIDES_CACHE is not None:
        return _MOTS_VIDES_CACHE
    
    mots_vides = set()
    chemins = [
        REFS_DIR / "motsvides.csv",
        Path("refs/motsvides.csv"),
        Path("c:/g/refs/motsvides.csv"),
    ]
    
    for chemin in chemins:
        if chemin.exists():
            try:
                with open(chemin, 'r', encoding='utf-8-sig') as f:
                    for ligne in f:
                        ligne = ligne.strip()
                        # Ignorer commentaires et ligne d'en-tête
                        if ligne and not ligne.startswith('#') and ligne != 'fr':
                            mots_vides.add(ligne.lower())
                break
            except Exception:
                pass
    
    _MOTS_VIDES_CACHE = mots_vides
    return mots_vides


# =============================================================================
# FONCTIONS UTILITAIRES
# =============================================================================

def normalize_text(text: str) -> str:
    """
    Normalise un texte pour recherche insensible à la casse et aux accents.
    
    Args:
        text: Texte à normaliser
        
    Returns:
        Texte en minuscules sans accents
    """
    import unicodedata
    
    if not text:
        return ""
    
    # Minuscules
    text = text.lower()
    
    # Supprimer les accents
    text = unicodedata.normalize('NFD', text)
    text = ''.join(c for c in text if unicodedata.category(c) != 'Mn')
    
    return text


def _charger_un_csv(csv_file: Path, source_tag: str = '') -> List[Dict[str, Any]]:
    """
    Charge un fichier CSV de logs.
    
    Args:
        csv_file: Chemin du fichier CSV
        source_tag: Tag pour identifier la source ('fake' ou 'real')
        
    Returns:
        Liste de dictionnaires
    """
    logs = []
    
    if not csv_file.exists():
        return logs
    
    try:
        with open(csv_file, 'r', encoding='utf-8-sig') as f:
            lines = []
            for line in f:
                line = line.replace('\r', '')
                stripped = line.strip()
                if stripped and not stripped.startswith('#'):
                    lines.append(line)
            
            if not lines:
                return logs
            
            import io
            clean_content = ''.join(lines)
            reader = csv.DictReader(io.StringIO(clean_content), delimiter=';')
            
            for row in reader:
                for key in row:
                    if row[key] and isinstance(row[key], str):
                        row[key] = row[key].strip()
                
                try:
                    row['temps_ms'] = int(row.get('temps_ms', 0) or 0)
                except (ValueError, TypeError):
                    row['temps_ms'] = 0
                
                try:
                    row['nb_patients'] = int(row.get('nb_patients', 0) or 0)
                except (ValueError, TypeError):
                    row['nb_patients'] = 0
                
                # Ajouter le tag source
                if source_tag:
                    row['_source'] = source_tag
                
                logs.append(row)
                
    except Exception as e:
        print(f"[ERREUR] Lecture {csv_file.name}: {e}")
    
    return logs


def _charger_logs(log_file: Path = None) -> List[Dict[str, Any]]:
    """
    Charge les logs depuis les fichiers CSV.
    
    Concatène :
    1. fakerecherche.csv (données de démo, dans /refs/)
    2. logrecherche.csv (vrais logs, dans /logs/)
    
    Args:
        log_file: Chemin du fichier de log réel (optionnel)
        
    Returns:
        Liste de dictionnaires représentant chaque ligne
    """
    all_logs = []
    
    # 1. Charger les données de démo (fake) depuis /refs/
    fake_logs = _charger_un_csv(FAKE_LOG_FILE, source_tag='fake')
    all_logs.extend(fake_logs)
    
    # 2. Charger les vrais logs depuis /logs/
    real_file = log_file if log_file else LOG_FILE
    real_logs = _charger_un_csv(real_file, source_tag='real')
    all_logs.extend(real_logs)
    
    return all_logs


def _filtrer_logs(
    logs: List[Dict],
    rating: str = None,
    date_debut: str = None,
    date_fin: str = None,
    q: str = None,
    mode: str = None,
    erreur: bool = None,
    type_probleme: str = None,
    session_id: str = None,
    ip_utilisateur: str = None
) -> List[Dict]:
    """
    Filtre les logs selon les critères fournis.
    
    Args:
        logs: Liste des logs à filtrer
        rating: Filtrer par rating (👍, 👎, null, all)
        date_debut: Date de début (format JJ/MM/AAAA ou AAAA-MM-JJ)
        date_fin: Date de fin
        q: Recherche texte libre dans questionoriginale
        mode: Mode de recherche (rapide, ia, compare, union)
        erreur: True = avec erreur, False = sans erreur
        type_probleme: Type de problème
        session_id: ID de session
        ip_utilisateur: Adresse IP
        
    Returns:
        Liste filtrée
    """
    resultats = logs
    
    # Filtre par rating
    if rating and rating != 'all':
        if rating == 'null':
            resultats = [r for r in resultats if not r.get('rating')]
        else:
            resultats = [r for r in resultats if r.get('rating') == rating]
    
    # Filtre par date
    if date_debut:
        try:
            if '-' in date_debut:
                dt_debut = datetime.strptime(date_debut, '%Y-%m-%d')
            else:
                dt_debut = datetime.strptime(date_debut, '%d/%m/%Y')
            
            resultats_temp = []
            for r in resultats:
                try:
                    ts = r.get('timestamp', '')
                    if ts:
                        dt_log = datetime.strptime(ts.split()[0], '%d/%m/%Y')
                        if dt_log >= dt_debut:
                            resultats_temp.append(r)
                except:
                    pass
            resultats = resultats_temp
        except:
            pass
    
    if date_fin:
        try:
            if '-' in date_fin:
                dt_fin = datetime.strptime(date_fin, '%Y-%m-%d')
            else:
                dt_fin = datetime.strptime(date_fin, '%d/%m/%Y')
            dt_fin = dt_fin.replace(hour=23, minute=59, second=59)
            
            resultats_temp = []
            for r in resultats:
                try:
                    ts = r.get('timestamp', '')
                    if ts:
                        dt_log = datetime.strptime(ts.split()[0], '%d/%m/%Y')
                        if dt_log <= dt_fin:
                            resultats_temp.append(r)
                except:
                    pass
            resultats = resultats_temp
        except:
            pass
    
    # Filtre par texte (question)
    if q:
        q_lower = q.lower()
        resultats = [
            r for r in resultats 
            if q_lower in (r.get('questionoriginale', '') or '').lower()
            or q_lower in (r.get('question', '') or '').lower()
        ]
    
    # Filtre par mode
    if mode:
        resultats = [r for r in resultats if r.get('mode') == mode]
    
    # Filtre par erreur
    if erreur is not None:
        if erreur:
            resultats = [r for r in resultats if r.get('erreur')]
        else:
            resultats = [r for r in resultats if not r.get('erreur')]
    
    # Filtre par type de problème
    if type_probleme:
        resultats = [r for r in resultats if r.get('type_probleme') == type_probleme]
    
    # Filtre par session
    if session_id:
        resultats = [r for r in resultats if r.get('session_id') == session_id]
    
    # Filtre par IP
    if ip_utilisateur:
        resultats = [r for r in resultats if r.get('ip_utilisateur') == ip_utilisateur]
    
    return resultats


def _paginer(logs: List[Dict], offset: int = 0, limit: int = 20) -> Tuple[List[Dict], int]:
    """
    Pagine une liste de logs.
    
    Args:
        logs: Liste complète
        offset: Index de départ
        limit: Nombre d'éléments à retourner
        
    Returns:
        Tuple (liste paginée, total)
    """
    total = len(logs)
    paginated = logs[offset:offset + limit]
    return paginated, total


# =============================================================================
# FONCTIONS PRINCIPALES D'ANALYSE
# =============================================================================

def get_stats(log_file: Path = None) -> Dict[str, Any]:
    """
    Calcule les statistiques globales des logs.
    
    Returns:
        Dictionnaire avec les stats
    """
    logs = _charger_logs(log_file)
    
    if not logs:
        return {
            'total_recherches': 0,
            'periode': {'debut': None, 'fin': None},
            'ratings': {'positif': 0, 'negatif': 0, 'sans': 0},
            'taux_satisfaction': 0,
            'modes': {},
            'top_pathologies': [],
            'top_problemes': [],
            'temps_moyen_ms': 0,
            'erreurs_count': 0,
            'langues': {},
            'bases': {}
        }
    
    # Période
    timestamps = [r.get('timestamp', '') for r in logs if r.get('timestamp')]
    periode_debut = min(timestamps) if timestamps else None
    periode_fin = max(timestamps) if timestamps else None
    
    # Ratings
    ratings = Counter(r.get('rating', '') for r in logs)
    positif = ratings.get('👍', 0)
    negatif = ratings.get('👎', 0)
    sans_rating = sum(v for k, v in ratings.items() if k not in ['👍', '👎'])
    
    # Taux de satisfaction
    total_avec_rating = positif + negatif
    taux_satisfaction = round(positif / total_avec_rating * 100, 1) if total_avec_rating > 0 else 0
    
    # Modes
    modes = Counter(r.get('mode', 'inconnu') for r in logs)
    
    # Top pathologies (depuis la colonne pathologies)
    pathos = []
    for r in logs:
        p = r.get('pathologies', '')
        if p:
            pathos.extend([x.strip() for x in p.split(',') if x.strip()])
    top_pathologies = Counter(pathos).most_common(10)
    
    # Top problèmes
    problemes = [r.get('type_probleme') for r in logs if r.get('type_probleme')]
    top_problemes = Counter(problemes).most_common(5)
    
    # Temps moyen
    temps = [r.get('temps_ms', 0) for r in logs if r.get('temps_ms')]
    temps_moyen = round(sum(temps) / len(temps)) if temps else 0
    
    # Erreurs
    erreurs_count = sum(1 for r in logs if r.get('erreur'))
    
    # Langues
    langues = Counter(r.get('langueutilisee', 'inconnu') for r in logs)
    
    # Bases
    bases = Counter(r.get('base', 'inconnu') for r in logs)
    
    # Termes non reconnus (depuis la colonne residu)
    termes_non_reconnus = []
    for r in logs:
        residu = r.get('residu', '')
        if residu:
            # Extraire les mots du résidu
            mots = [m.strip().lower() for m in residu.replace(',', ' ').split() if m.strip() and len(m.strip()) > 1]
            termes_non_reconnus.extend(mots)
    top_termes = Counter(termes_non_reconnus).most_common(15)
    
    # Moteurs IA (V1.0.4)
    moteurs = Counter(r.get('moteur', '') for r in logs if r.get('moteur'))
    
    return {
        'total_recherches': len(logs),
        'periode': {'debut': periode_debut, 'fin': periode_fin},
        'ratings': {
            'positif': positif,
            'negatif': negatif,
            'sans': sans_rating
        },
        'taux_satisfaction': taux_satisfaction,
        'modes': dict(modes),
        'moteurs': dict(moteurs),
        'top_pathologies': [{'pathologie': p, 'count': c} for p, c in top_pathologies],
        'top_problemes': [{'probleme': p, 'count': c} for p, c in top_problemes],
        'types_problemes': [{'type': p, 'count': c} for p, c in top_problemes],
        'termes_non_reconnus': [{'terme': t, 'count': c} for t, c in top_termes],
        'temps_moyen_ms': temps_moyen,
        'erreurs': erreurs_count,
        'erreurs_count': erreurs_count,
        'langues': dict(langues),
        'bases': dict(bases)
    }


def get_recherches(
    offset: int = 0,
    limit: int = 20,
    rating: str = None,
    date_debut: str = None,
    date_fin: str = None,
    q: str = None,
    mode: str = None,
    erreur: bool = None,
    type_probleme: str = None,
    log_file: Path = None
) -> Dict[str, Any]:
    """
    Récupère la liste paginée des recherches avec filtres.
    
    Returns:
        Dictionnaire avec recherches paginées et métadonnées
    """
    logs = _charger_logs(log_file)
    
    # Trier par timestamp décroissant (plus récent en premier)
    logs.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
    
    # Appliquer les filtres
    logs_filtres = _filtrer_logs(
        logs,
        rating=rating,
        date_debut=date_debut,
        date_fin=date_fin,
        q=q,
        mode=mode,
        erreur=erreur,
        type_probleme=type_probleme
    )
    
    # Paginer
    paginated, total = _paginer(logs_filtres, offset, limit)
    
    # Extraire les colonnes affichées
    resultats = []
    for r in paginated:
        item = {col: r.get(col, '') for col in DEFAULT_DISPLAY_COLUMNS}
        item['session_id'] = r.get('session_id', '')  # Toujours inclure pour le lien
        item['erreur'] = r.get('erreur', '')
        item['commentaire'] = r.get('commentaire', '')
        # FIX v1.0.25 : Inclure base et languesaisie pour le bouton Relancer
        item['base'] = r.get('base', '')
        item['languesaisie'] = r.get('languesaisie', '')
        resultats.append(item)
    
    return {
        'recherches': resultats,
        'total': total,
        'offset': offset,
        'limit': limit,
        'filtres_actifs': {
            'rating': rating,
            'date_debut': date_debut,
            'date_fin': date_fin,
            'q': q,
            'mode': mode,
            'erreur': erreur,
            'type_probleme': type_probleme
        }
    }


def get_recherche_detail(session_id: str, log_file: Path = None) -> Optional[Dict[str, Any]]:
    """
    Récupère le détail complet d'une recherche par son session_id.
    
    Args:
        session_id: Identifiant de session
        
    Returns:
        Dictionnaire complet de la recherche ou None
    """
    logs = _charger_logs(log_file)
    
    for r in logs:
        if r.get('session_id') == session_id:
            return r
    
    return None


def get_recherches_similaires(
    session_id: str,
    by: str = 'session',
    limit: int = 20,
    log_file: Path = None,
    ia_model: str = None
) -> Dict[str, Any]:
    """
    Récupère les recherches similaires selon le critère choisi.
    
    Args:
        session_id: Session de référence
        by: Critère de similarité ('session', 'ip', 'ia')
        limit: Nombre max de résultats
        ia_model: Modèle IA à utiliser (pour by='ia')
        
    Returns:
        Dictionnaire avec recherches similaires
    """
    logs = _charger_logs(log_file)
    
    # Trouver la recherche de référence
    reference = None
    for r in logs:
        if r.get('session_id') == session_id:
            reference = r
            break
    
    if not reference:
        return {
            'reference': None,
            'similaires': [],
            'critere': by,
            'message': f"Session {session_id} introuvable"
        }
    
    similaires = []
    
    if by == 'session':
        # Même session (toutes les recherches de la même session)
        similaires = [
            r for r in logs 
            if r.get('session_id') == session_id
        ]
    
    elif by == 'ip':
        # Même IP
        ip = reference.get('ip_utilisateur')
        if ip:
            similaires = [
                r for r in logs 
                if r.get('ip_utilisateur') == ip
            ]
    
    elif by == 'ia':
        # Similarité par IA (basée sur la question)
        # Pour l'instant, recherche simple par mots-clés
        # TODO: Intégrer l'appel IA réel
        question_ref = (reference.get('questionoriginale') or '').lower()
        mots_ref = set(question_ref.split())
        
        for r in logs:
            if r.get('session_id') == session_id:
                continue
            
            question = (r.get('questionoriginale') or '').lower()
            mots = set(question.split())
            
            # Calculer un score de similarité simple (Jaccard)
            if mots_ref and mots:
                intersection = len(mots_ref & mots)
                union = len(mots_ref | mots)
                score = intersection / union if union > 0 else 0
                
                if score > 0.3:  # Seuil de similarité
                    r_copy = dict(r)
                    r_copy['score_similarite'] = round(score, 2)
                    similaires.append(r_copy)
        
        # Trier par score décroissant
        similaires.sort(key=lambda x: x.get('score_similarite', 0), reverse=True)
    
    # Trier par timestamp
    if by != 'ia':
        similaires.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
    
    return {
        'reference': reference,
        'similaires': similaires[:limit],
        'total': len(similaires),
        'critere': by
    }


def get_ia_summary(log_file: Path = None, ia_model: str = 'gpt4o') -> Dict[str, Any]:
    """
    Génère une analyse IA des logs de recherche.
    
    Cette fonction prépare les données pour l'analyse IA et appelle
    le modèle spécifié pour obtenir des recommandations.
    
    Args:
        log_file: Chemin du fichier de logs
        ia_model: Modèle IA à utiliser
        
    Returns:
        Dictionnaire avec l'analyse IA
    """
    logs = _charger_logs(log_file)
    
    if not logs:
        return {
            'analyse': "Aucun log disponible pour l'analyse.",
            'moteur': ia_model,
            'donnees_analysees': 0
        }
    
    # Préparer les données pour l'analyse
    stats = get_stats(log_file)
    
    # Recherches problématiques (👎 ou erreur)
    problematiques = [
        {
            'question': r.get('questionoriginale', ''),
            'erreur': r.get('erreur', ''),
            'type_probleme': r.get('type_probleme', ''),
            'commentaire': r.get('commentaire', ''),
            'nb_patients': r.get('nb_patients', 0)
        }
        for r in logs
        if r.get('rating') == '👎' or r.get('erreur')
    ][:50]  # Limiter à 50 pour l'analyse
    
    # Mots non résolus fréquents (depuis la colonne residu)
    # Filtrer les mots vides (de, la, les, etc.)
    mots_vides = _charger_mots_vides()
    residus = []
    for r in logs:
        residu = r.get('residu', '')
        if residu:
            for mot in residu.split():
                mot = mot.strip().lower()
                if mot and mot not in mots_vides:
                    residus.append(mot)
    top_residus = Counter(residus).most_common(20)
    
    # Préparer le prompt pour l'IA
    prompt_data = {
        'stats': stats,
        'recherches_problematiques': problematiques,
        'mots_non_resolus_frequents': top_residus,
        'types_erreurs': stats.get('top_problemes', [])
    }
    
    # TODO: Appeler le modèle IA réel
    # Pour l'instant, retourner une analyse statique préparée
    
    analyse_texte = _generer_analyse_statique(prompt_data)
    
    return {
        'analyse': analyse_texte,
        'moteur': ia_model,
        'donnees_analysees': len(logs),
        'donnees_brutes': {
            'stats': stats,
            'top_residus': [{'mot': m, 'count': c} for m, c in top_residus],
            'nb_problematiques': len(problematiques)
        }
    }


def _generer_analyse_statique(data: Dict) -> str:
    """
    Génère une analyse statique basée sur les données.
    Cette fonction sera remplacée par un appel IA réel.
    """
    stats = data.get('stats', {})
    problematiques = data.get('recherches_problematiques', [])
    residus = data.get('mots_non_resolus_frequents', [])
    
    lignes = []
    lignes.append("## 📊 Analyse des logs de recherche\n")
    
    # Satisfaction
    taux = stats.get('taux_satisfaction', 0)
    if taux >= 80:
        lignes.append(f"✅ **Satisfaction globale** : {taux}% - Excellent !")
    elif taux >= 60:
        lignes.append(f"⚠️ **Satisfaction globale** : {taux}% - Peut être amélioré")
    else:
        lignes.append(f"❌ **Satisfaction globale** : {taux}% - Nécessite attention")
    
    lignes.append("")
    
    # Erreurs
    erreurs = stats.get('erreurs_count', 0)
    total = stats.get('total_recherches', 1)
    taux_erreur = round(erreurs / total * 100, 1) if total > 0 else 0
    lignes.append(f"### 🐛 Erreurs : {erreurs} ({taux_erreur}%)")
    
    # Top problèmes
    top_pb = stats.get('top_problemes', [])
    if top_pb:
        lignes.append("\n### 🔴 Problèmes les plus fréquents :")
        for item in top_pb[:5]:
            lignes.append(f"- {item['probleme']} : {item['count']} occurrences")
    
    # Mots non résolus
    if residus:
        lignes.append("\n### 📝 Termes non reconnus fréquents :")
        lignes.append("Ces termes pourraient nécessiter l'ajout de patterns :")
        for mot, count in residus[:10]:
            lignes.append(f"- \"{mot}\" : {count} fois")
    
    # Recommandations
    lignes.append("\n### 💡 Recommandations :")
    
    if taux < 70:
        lignes.append("1. Analyser les recherches avec 👎 pour identifier les patterns")
    
    if residus:
        lignes.append("2. Enrichir le glossaire avec les termes non reconnus")
    
    if erreurs > 0:
        lignes.append("3. Investiguer les erreurs techniques récurrentes")
    
    return "\n".join(lignes)


def search_in_commentaires(
    query: str,
    limit: int = 100,
    log_file: Path = None
) -> Dict[str, Any]:
    """
    Recherche fulltext dans les commentaires des logs.
    Insensible à la casse et aux accents.
    
    Args:
        query: Texte à rechercher
        limit: Nombre max de résultats (défaut: 100)
        log_file: Chemin du fichier de log (optionnel)
        
    Returns:
        {
            'query': query,
            'results': [...],
            'total': int
        }
    """
    logs = _charger_logs(log_file)
    
    if not logs or not query:
        return {'query': query, 'results': [], 'total': 0}
    
    # Normaliser la requête
    query_normalized = normalize_text(query)
    
    results = []
    for log in logs:
        commentaire = log.get('commentaire', '')
        if not commentaire:
            continue
        
        # Normaliser le commentaire pour comparaison
        commentaire_normalized = normalize_text(commentaire)
        
        if query_normalized in commentaire_normalized:
            results.append({
                'session_id': log.get('session_id', ''),
                'timestamp': log.get('timestamp', ''),
                'question': log.get('questionoriginale', ''),
                'commentaire': commentaire,
                'rating': log.get('rating', ''),
                'type_probleme': log.get('type_probleme', ''),
                'nb_patients': log.get('nb_patients', 0),
                'mode': log.get('mode', '')
            })
            
            if len(results) >= limit:
                break
    
    return {
        'query': query,
        'results': results,
        'total': len(results)
    }


def export_csv(
    output_path: str = None,
    rating: str = None,
    date_debut: str = None,
    date_fin: str = None,
    q: str = None,
    mode: str = None,
    erreur: bool = None,
    type_probleme: str = None,
    log_file: Path = None
) -> Tuple[str, int]:
    """
    Exporte les logs filtrés en CSV.
    
    Args:
        output_path: Chemin du fichier de sortie
        [filtres]: Mêmes filtres que get_recherches
        
    Returns:
        Tuple (chemin du fichier, nombre de lignes exportées)
    """
    logs = _charger_logs(log_file)
    
    # Appliquer les filtres
    logs_filtres = _filtrer_logs(
        logs,
        rating=rating,
        date_debut=date_debut,
        date_fin=date_fin,
        q=q,
        mode=mode,
        erreur=erreur,
        type_probleme=type_probleme
    )
    
    # Définir le chemin de sortie
    if output_path is None:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_path = str(LOGS_DIR / f"export_analyse_{timestamp}.csv")
    
    # Écrire le fichier
    try:
        with open(output_path, 'w', encoding='utf-8-sig', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=LOG_COLUMNS, delimiter=';')
            writer.writeheader()
            writer.writerows(logs_filtres)
        
        return output_path, len(logs_filtres)
    
    except Exception as e:
        return f"ERREUR: {e}", 0


# =============================================================================
# INTERFACE CLI
# =============================================================================

def _afficher_stats(stats: Dict):
    """Affiche les statistiques de manière formatée."""
    print("\n" + "═" * 60)
    print("📊 STATISTIQUES GLOBALES")
    print("═" * 60)
    
    print(f"\n📈 Total recherches : {stats['total_recherches']}")
    
    periode = stats.get('periode', {})
    if periode.get('debut'):
        print(f"📅 Période : {periode['debut']} → {periode['fin']}")
    
    ratings = stats.get('ratings', {})
    print(f"\n👍 Positifs : {ratings.get('positif', 0)}")
    print(f"👎 Négatifs : {ratings.get('negatif', 0)}")
    print(f"➖ Sans rating : {ratings.get('sans', 0)}")
    print(f"📊 Taux satisfaction : {stats.get('taux_satisfaction', 0)}%")
    
    print(f"\n⏱️  Temps moyen : {stats.get('temps_moyen_ms', 0)} ms")
    print(f"❌ Erreurs : {stats.get('erreurs_count', 0)}")
    
    modes = stats.get('modes', {})
    if modes:
        print("\n🔧 Modes utilisés :")
        for mode, count in sorted(modes.items(), key=lambda x: -x[1]):
            print(f"   - {mode}: {count}")
    
    top_pathos = stats.get('top_pathologies', [])
    if top_pathos:
        print("\n🏥 Top pathologies :")
        for item in top_pathos[:5]:
            print(f"   - {item['pathologie']}: {item['count']}")
    
    top_pb = stats.get('top_problemes', [])
    if top_pb:
        print("\n⚠️  Top problèmes :")
        for item in top_pb:
            print(f"   - {item['probleme']}: {item['count']}")
    
    print()


def _afficher_liste(data: Dict):
    """Affiche la liste des recherches."""
    recherches = data.get('recherches', [])
    total = data.get('total', 0)
    offset = data.get('offset', 0)
    limit = data.get('limit', 20)
    
    print("\n" + "═" * 100)
    print(f"📋 RECHERCHES ({offset+1}-{offset+len(recherches)} sur {total})")
    print("═" * 100)
    
    # En-tête
    print(f"{'Timestamp':<20} {'Question':<35} {'Mode':<8} {'Nb':<5} {'Rating':<6} {'Problème':<15}")
    print("-" * 100)
    
    for r in recherches:
        ts = r.get('timestamp', '')[:16]
        q = (r.get('questionoriginale', '') or '')[:33]
        mode = r.get('mode', '')[:8]
        nb = str(r.get('nb_patients', ''))[:5]
        rating = r.get('rating', '') or '-'
        pb = (r.get('type_probleme', '') or '')[:15]
        
        print(f"{ts:<20} {q:<35} {mode:<8} {nb:<5} {rating:<6} {pb:<15}")
    
    print("-" * 100)
    print(f"Page {offset//limit + 1} / {(total-1)//limit + 1}")
    print()


def _afficher_detail(recherche: Dict):
    """Affiche le détail d'une recherche."""
    if not recherche:
        print("❌ Recherche non trouvée")
        return
    
    print("\n" + "═" * 60)
    print("🔍 DÉTAIL DE LA RECHERCHE")
    print("═" * 60)
    
    for col in LOG_COLUMNS:
        valeur = recherche.get(col, '')
        if valeur:
            print(f"{col:20} : {valeur}")
    
    print()


def _parser_arguments() -> Dict:
    """Parse les arguments CLI."""
    args = sys.argv[1:]
    
    if not args:
        return {'command': 'help'}
    
    command = args[0]
    options = {
        'command': command,
        'offset': 0,
        'limit': 20,
        'rating': None,
        'date_debut': None,
        'date_fin': None,
        'q': None,
        'mode': None,
        'erreur': None,
        'type_probleme': None,
        'by': 'session',
        'output': None,
        'session_id': None,
        'password': None
    }
    
    i = 1
    while i < len(args):
        arg = args[i]
        
        if arg.startswith('--offset='):
            options['offset'] = int(arg.split('=')[1])
        elif arg.startswith('--limit='):
            options['limit'] = int(arg.split('=')[1])
        elif arg.startswith('--rating='):
            options['rating'] = arg.split('=')[1]
        elif arg.startswith('--date-debut='):
            options['date_debut'] = arg.split('=')[1]
        elif arg.startswith('--date-fin='):
            options['date_fin'] = arg.split('=')[1]
        elif arg.startswith('--q='):
            options['q'] = arg.split('=')[1]
        elif arg.startswith('--mode='):
            options['mode'] = arg.split('=')[1]
        elif arg.startswith('--erreur='):
            options['erreur'] = arg.split('=')[1].lower() == 'true'
        elif arg.startswith('--type-probleme='):
            options['type_probleme'] = arg.split('=')[1]
        elif arg.startswith('--by='):
            options['by'] = arg.split('=')[1]
        elif arg.startswith('--output='):
            options['output'] = arg.split('=')[1]
        elif not arg.startswith('--'):
            # Argument positionnel
            if command in ('detail', 'similaires') and not options['session_id']:
                options['session_id'] = arg
            elif command == 'auth' and not options['password']:
                options['password'] = arg
        
        i += 1
    
    return options


def main():
    """Point d'entrée CLI."""
    print(f"╔════════════════════════════════════════════════════════════════")
    print(f"║ {__pgm__} V{__version__} - {__date__}")
    print(f"║ Analyse des logs de recherche Kitview Search")
    print(f"╚════════════════════════════════════════════════════════════════")
    
    options = _parser_arguments()
    command = options.get('command', 'help')
    
    if command == 'help':
        print("""
Usage:
    python analyse.py <commande> [options]

Commandes:
    stats                   Affiche les statistiques globales
    list                    Liste paginée des recherches
    detail <session_id>     Détail d'une recherche
    similaires <session_id> Recherches similaires
    ia-summary              Analyse IA des logs
    export                  Export CSV filtré
    search-comment <texte> Recherche dans les commentaires

Options pour 'list' et 'export':
    --offset=N              Index de départ (défaut: 0)
    --limit=N               Nombre de résultats (défaut: 20)
    --rating=X              Filtrer par rating (👍, 👎, null, all)
    --date-debut=AAAA-MM-JJ Date de début
    --date-fin=AAAA-MM-JJ   Date de fin
    --q=TEXTE               Recherche dans la question
    --mode=X                Mode (standard, ia, standarddeepl, iadeepl, standardia)
    --erreur=true/false     Avec/sans erreur
    --type-probleme=X       Type de problème

Options pour 'similaires':
    --by=X                  Critère (session, ip, ia)
    --limit=N               Nombre max de résultats

Options pour 'export':
    --output=CHEMIN         Chemin du fichier de sortie

Exemples:
    python analyse.py stats
    python analyse.py list --limit=50 --rating=👎
    python analyse.py detail abc123-session-id
    python analyse.py similaires abc123 --by=ip
    python analyse.py export --rating=👎 --output=negatifs.csv
""")
        return 0
    
    elif command == 'stats':
        stats = get_stats()
        _afficher_stats(stats)
        return 0
    
    elif command == 'list':
        data = get_recherches(
            offset=options['offset'],
            limit=options['limit'],
            rating=options['rating'],
            date_debut=options['date_debut'],
            date_fin=options['date_fin'],
            q=options['q'],
            mode=options['mode'],
            erreur=options['erreur'],
            type_probleme=options['type_probleme']
        )
        _afficher_liste(data)
        return 0
    
    elif command == 'detail':
        session_id = options.get('session_id')
        if not session_id:
            print("❌ Session ID requis")
            return 1
        
        recherche = get_recherche_detail(session_id)
        _afficher_detail(recherche)
        return 0
    
    elif command == 'similaires':
        session_id = options.get('session_id')
        if not session_id:
            print("❌ Session ID requis")
            return 1
        
        data = get_recherches_similaires(
            session_id=session_id,
            by=options['by'],
            limit=options['limit']
        )
        
        print(f"\n🔗 Recherches similaires (critère: {data['critere']})")
        print(f"Total: {data.get('total', 0)}")
        
        if data.get('reference'):
            print(f"\nRéférence: {data['reference'].get('questionoriginale', '')}")
        
        for r in data.get('similaires', []):
            score = r.get('score_similarite', '')
            score_str = f" ({score})" if score else ""
            print(f"  - {r.get('timestamp', '')[:16]} : {r.get('questionoriginale', '')[:40]}{score_str}")
        
        return 0
    
    elif command == 'ia-summary':
        data = get_ia_summary()
        print(data.get('analyse', ''))
        return 0
    
    elif command == 'export':
        chemin, nb = export_csv(
            output_path=options.get('output'),
            rating=options['rating'],
            date_debut=options['date_debut'],
            date_fin=options['date_fin'],
            q=options['q'],
            mode=options['mode'],
            erreur=options['erreur'],
            type_probleme=options['type_probleme']
        )
        
        if nb > 0:
            print(f"✅ Export réussi : {chemin}")
            print(f"   {nb} lignes exportées")
        else:
            print(f"❌ {chemin}")
        
        return 0 if nb > 0 else 1
    
    elif command == 'search-comment':
        query = options.get('query') or options.get('session_id')  # session_id est le 2ème arg
        if not query:
            print("❌ Texte de recherche requis")
            return 1
        
        data = search_in_commentaires(query, limit=options['limit'])
        
        print(f"\n🔍 Recherche dans les commentaires : '{data['query']}'")
        print(f"   {data['total']} résultat(s)")
        
        for r in data.get('results', []):
            print(f"\n  {r.get('timestamp', '')[:16]} | {r.get('rating', '➖')}")
            print(f"  Question: {r.get('question', '')[:50]}")
            print(f"  Commentaire: {r.get('commentaire', '')[:80]}")
        
        return 0
    
    else:
        print(f"❌ Commande inconnue: {command}")
        print("   Utilisez 'python analyse.py help' pour l'aide")
        return 1


if __name__ == "__main__":
    sys.exit(main())
