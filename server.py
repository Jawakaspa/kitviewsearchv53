#*TO*#
__pgm__ = "server.py"
__version__ = "1.3.1"
__date__ = "07/03/2026 12:00"

# ╔════════════════════════════════════════════════════════════════
# ║ server.py v1.2.1 - API FastAPI Recherche Patients
# ║ 
# ║ CHANGEMENTS v1.2.1 (19/02/2026):
# ║   - AJOUT : Endpoint GET /patient pour lecture individuelle
# ║   - AJOUT : Endpoint POST /patient/resolve-tags (résolution dettags)
# ║   - AJOUT : Endpoint PUT /patient/update (mise à jour + recalcul index)
# ║   - AJOUT : Models ResolveTagsRequest, PatientUpdateRequest
# ║   - Fonction _generate_pathologies_combinations() pour indexation
# ║   - Support page majpats.html (modification patient)
# ║
# ║ CHANGEMENTS v1.2.0 (17/02/2026):
# ║   - AJOUT : Module photofit_upload.py pour recherche par image
# ║   - AJOUT : Endpoint POST /photofit/search-by-image
# ║   - AJOUT : Endpoint POST /photofit/save-prospect
# ║   - AJOUT : Endpoint GET /photofit/prospects
# ║   - AJOUT : Mount statique /photofit/prospects/photos/ (bases/prospects/)
# ║   - AJOUT : Init prospects.db + répertoire photos dans lifespan
# ║   - Architecture Option A : base prospects séparée (jamais toucher baseN.db)
# ║
# ║ CHANGEMENTS v1.1.9 (11/02/2026):
# ║   - AJOUT : Fonction _appeler_anthropic() pour appels API Claude
# ║   - AJOUT : Endpoint POST /ia/help-chatbot pour chatbot des modes d'emploi
# ║   - Utilise ANTHROPIC_API_KEY en priorité, fallback OPENAI_API_KEY
# ║   - Contexte de page envoyé au LLM pour réponses contextuelles
# ║
# ║ CHANGEMENTS v1.1.8 (30/01/2026):
# ║   - FIX : Endpoint /params utilise communb.csv au lieu de commun.csv
# ║   - FIX : Lecture du nouveau format section;parametre;valeur;description
# ║
# ║ CHANGEMENTS v1.1.7 (29/01/2026):
# ║   - AJOUT : Endpoint POST /search/page pour pagination optimisée
# ║   - Cache SEARCH_CACHE stocke les critères détectés par session_id
# ║   - /search/page réutilise les critères (pas de re-détection)
# ║   - Latence pagination réduite de ~1500ms à ~50ms
# ║   - TTL cache : 30 minutes, max 1000 sessions
# ║   - AJOUT : Endpoint GET /search/cache/stats pour debug
# ║
# ║ CHANGEMENTS v1.1.6 (14/01/2026):
# ║   - AJOUT : Endpoint GET /exemples pour charger exemples depuis refs/exemples.csv
# ║   - Format : une question par ligne, lignes commençant par # ignorées
# ║
# ║ CHANGEMENTS v1.1.5 (12/01/2026):
# ║   - FIX : POST /ia/ask accepte paramètre 'lang' pour réponse multilingue
# ║   - FIX : Prompt IA modifié pour répondre dans la langue de l'utilisateur
# ║   - AJOUT : Mapping LANGUES_NOMS pour noms complets des langues
# ║
# ║ CHANGEMENTS v1.1.3 (06/01/2026):
# ║   - CACHE VERSIONNÉ : Traductions stockées dans /ihm avec versioning
# ║   - Meta tag <meta name="help-version"> pour versioning du source
# ║   - Fichier help_versions.json pour gérer le cache
# ║   - Ne retraduit que si la version source a changé
# ║   - AJOUT : Endpoint /api/help/versions pour état du cache
# ║
# ║ CHANGEMENTS v1.1.2 (06/01/2026):
# ║   - AJOUT : Endpoint /help pour servir modedemploi.html
# ║   - AJOUT : Endpoint /help/{lang} pour versions traduites
# ║   - AJOUT : Endpoint /api/help/translate/{lang} pour traduction lazy
# ║   - Traduction automatique via DeepL avec cache des fichiers
# ║   - Support 10 langues : en, de, es, it, pt, pl, ro, th, ar, cn
# ║
# ║ CHANGEMENTS v1.1.1 (05/01/2026):
# ║   - LOGS : Ajout indication disponibilité DeepL à l'entrée
# ║   - LOGS : Affichage traduction glossaire pour langues != fr
# ║     Format: Glossaire: '歯軋り' → 'bruxisme'
# ║
# ║ CHANGEMENTS v1.1.0 (05/01/2026):
# ║   - RENOMMAGE : "rapide" → "standard" dans les validations
# ║   - LOGS ENRICHIS : Affichage du parcours_detection
# ║   - Format logs : 🔎 standard:N → 🤖 ia:N → 🌐 deepl → etc.
# ║
# ║ CHANGEMENTS v1.0.24 (31/12/2025):
# ║   - Intégration du module analyse.py pour dashboard analytics
# ║   - 8 nouveaux endpoints /analyse/* pour l'analyse des logs
# ║   - Authentification par mot de passe pour l'accès aux analytics
# ║
# ║ CHANGEMENTS v2.2.0 (29/12/2025):
# ║   - POST /ia/cohorte pour analyse de cohorte par IA
# ║   - Calcul statistiques côté serveur (âge moyen, répartition, top pathologies)
# ║   - Prompt système spécifique pour analyse de cohorte
# ║
# ║ CHANGEMENTS v2.1.0 (28/12/2025):
# ║   - GET /ia retourne TOUS les moteurs (actifs ET inactifs) avec tous les champs
# ║   - PUT /ia/{moteur} pour activer/désactiver un moteur
# ║   - POST /ia/ask pour interroger un LLM avec contexte patient
# ║   - GET /i18n pour récupérer les textes UI traduits depuis glossaire.csv
# ║
# ║ CHANGEMENTS v2.0.0 (28/12/2025):
# ║   - Support de la résolution sémantique via glossaire.csv (search.py v2.0.0)
# ║   - Dictionnaires langue→français chargés en lazy loading dans search.py
# ║   - Affichage question_resolue et mots_non_resolus dans logs et réponse
# ║
# ║ ARCHITECTURE :
# ║   - Modes : standard, ia
# ║   - Auteur retourné : cx, eden/..., cxgti
# ║
# ║ AJOUT v4.1.0:
# ║   - Endpoint /params pour récupérer les langues actives
# ║
# ║ AJOUT v1.1.0:
# ║   - Chargement portraits.csv au démarrage (mapping idportrait → URL)
# ║   - Enrichissement automatique des portraits dans /search
# ║
# ║ AJOUT v1.2.0:
# ║   - Chargement commentaires.csv au démarrage (mapping oripathologie → commentaire)
# ║   - Enrichissement des patients avec les commentaires des pathologies
# ║
# ║ CORRECTION v1.2.1:
# ║   - ia.csv : chargement de la colonne 'notes' pour affichage dans sélecteur
# ║   - ia.csv : détection actif avec 'O' (majuscule)
# ║
# ║ AJOUT v1.3.0:
# ║   - Endpoint POST /api/rating pour les feedbacks utilisateur
# ║   - Endpoint GET /api/export-logs pour télécharger le CSV des logs
# ║   - Passage du session_id à search() pour le logging enrichi
# ║
# ║ AJOUT v1.4.0:
# ║   - Envoi automatique d'email lors d'un feedback utilisateur
# ║   - Configuration SMTP via variables d'environnement
# ║   - Notification à thierry.oberle@kitview.com
# ║
# ║ Endpoints:
# ║   GET  /              - Page d'accueil (index.html)
# ║   GET  /api           - Info API (JSON)
# ║   GET  /health        - État du serveur
# ║   GET  /version       - Version de l'API
# ║   GET  /bases         - Liste des bases disponibles
# ║   GET  /count         - Nombre de patients dans une base
# ║   GET  /illustrations - URLs des illustrations bandeaux (par type)
# ║   GET  /api/illustrations - Liste complète illustrations (JSON)
# ║   POST /api/illustrations - Ajouter une illustration
# ║   PUT  /api/illustrations/{id} - Modifier une illustration
# ║   DELETE /api/illustrations/{id} - Supprimer une illustration
# ║   GET  /illustrations.html - Page de gestion des illustrations
# ║   GET  /params        - Paramètres (langues actives depuis communb.csv)
# ║   GET  /ia            - Liste de TOUS les moteurs IA (actifs et inactifs)
# ║   PUT  /ia/{moteur}   - Activer/désactiver un moteur IA
# ║   POST /ia/ask        - Interroger un LLM avec contexte patient
# ║   POST /ia/cohorte    - Analyser une cohorte de patients par IA
# ║   POST /ia/help-chatbot - Chatbot IA pour les modes d'emploi (Claude/OpenAI)
# ║   GET  /i18n          - Textes UI traduits depuis glossaire.csv
# ║   POST /search        - Recherche patients (multilingue)
# ║   POST /api/rating    - Enregistrer un feedback utilisateur + email
# ║   GET  /api/export-logs - Télécharger le CSV des logs
# ║   GET  /help          - Page mode d'emploi (modedemploi.html)
# ║   GET  /help/{lang}   - Mode d'emploi traduit
# ║   GET  /api/help/translate/{lang} - Générer traduction lazy
# ║   GET  /api/help/versions - État du cache des traductions
# ║   GET  /analyse        - Page d'analyse (analyse12.html)
# ║   GET  /analyse/stats  - Statistiques globales des logs
# ║   GET  /analyse/recherches - Liste paginée des recherches
# ║   GET  /analyse/recherche/{session_id} - Détail d'une recherche
# ║   GET  /analyse/similaires/{session_id} - Recherches similaires
# ║   GET  /analyse/search-comment - Recherche fulltext dans commentaires
# ║   GET  /analyse/ia-summary - Analyse IA des logs
# ║   GET  /analyse/export - Export CSV filtré
# ║   GET  /exemples       - Liste des exemples de recherche (refs/exemples.csv)
# ║   POST /search/page    - Pagination optimisée (réutilise cache)
# ║   GET  /search/cache/stats - Statistiques du cache de recherche
# ║   POST /photofit/search-by-image - Recherche par image uploadée
# ║   POST /photofit/save-prospect   - Sauvegarder un prospect
# ║   GET  /photofit/prospects       - Lister les prospects
# ╚════════════════════════════════════════════════════════════════

from fastapi import FastAPI, HTTPException, Request, File, UploadFile, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, StreamingResponse, RedirectResponse, Response
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
from contextlib import asynccontextmanager
import uvicorn
import logging
import os
from datetime import datetime
from pathlib import Path
import sqlite3
import sys
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import threading
import requests
import time
import json
import tempfile
import re

# ═══════════════════════════════════════════════════════════════
# AJOUT DU RÉPERTOIRE AU PATH
# ═══════════════════════════════════════════════════════════════

SCRIPT_DIR = Path(__file__).parent.resolve()
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

# ═══════════════════════════════════════════════════════════════
# IMPORT DU MODULE SEARCH
# ═══════════════════════════════════════════════════════════════

try:
    from search import search as search_func, update_rating as update_rating_func
    SEARCH_DISPONIBLE = True
except ImportError as e:
    SEARCH_DISPONIBLE = False
    logging.error(f"Module search.py non importable: {e}")

# Import du module traduire (pour info)
try:
    from traduire import LANGUES_NATIVES
    TRADUIRE_DISPONIBLE = True
except ImportError:
    TRADUIRE_DISPONIBLE = False
    LANGUES_NATIVES = ['fr', 'en', 'de', 'es', 'it', 'pt', 'pl', 'ro', 'th', 'ar', 'cn', 'ja']

# ═══════════════════════════════════════════════════════════════
# IMPORT DU MODULE ANALYSE
# ═══════════════════════════════════════════════════════════════

try:
    from analyse import (
        get_stats as analyse_get_stats,
        get_recherches as analyse_get_recherches,
        get_recherche_detail as analyse_get_detail,
        get_recherches_similaires as analyse_get_similaires,
        get_ia_summary as analyse_get_ia_summary,
        export_csv as analyse_export_csv,
        search_in_commentaires as analyse_search_commentaires
    )
    ANALYSE_DISPONIBLE = True
except ImportError as e:
    ANALYSE_DISPONIBLE = False
    logging.warning(f"Module analyse.py non importable: {e}")

# ═══════════════════════════════════════════════════════════════
# IMPORT DU MODULE PHOTOFIT UPLOAD
# ═══════════════════════════════════════════════════════════════

try:
    from photofit_upload import (
        extraire_features as photofit_extraire_features,
        rechercher_par_image as photofit_rechercher,
        enrichir_avec_patients as photofit_enrichir,
        sauver_prospect as photofit_sauver_prospect,
        supprimer_prospect as photofit_supprimer_prospect,
        lister_prospects as photofit_lister_prospects,
        get_stats_prospects as photofit_stats_prospects,
        get_prospect_by_id as photofit_get_prospect_by_id,
        creer_base_prospects,
        lire_config as photofit_lire_config,
    )
    PHOTOFIT_UPLOAD_DISPONIBLE = True
except ImportError as e:
    PHOTOFIT_UPLOAD_DISPONIBLE = False
    logging.warning(f"Module photofit_upload.py non importable: {e}")


# ═══════════════════════════════════════════════════════════════
# CONFIGURATION LOGGING
# ═══════════════════════════════════════════════════════════════

logger = logging.getLogger("server")
logger.setLevel(logging.INFO)

console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s', 
                              datefmt='%d/%m/%Y %H:%M:%S')
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)


# ═══════════════════════════════════════════════════════════════
# CONFIGURATION GLOBALE (avant lifespan)
# ═══════════════════════════════════════════════════════════════

BASES_DIR = None
REFS_DIR = None
CACHE = {}

# Clé API DeepL depuis variable d'environnement
DEEPL_API_KEY = os.environ.get('DEEPL_API_KEY', '')

# Cache des illustrations
ILLUSTRATIONS_CACHE = {
    'medical': [],
    'search': [],
    'zero': []
}

# Cache COMPLET des illustrations (tous les champs)
ILLUSTRATIONS_FULL_CACHE = []

# Cache des portraits (idportrait → URL)
PORTRAITS_CACHE = {}

# Cache des moteurs IA
IA_CACHE = []

# Cache COMPLET des moteurs IA (actifs ET inactifs avec tous les champs)
IA_FULL_CACHE = []

# Cache des textes UI internationalisés (type=ui depuis glossaire.csv)
I18N_CACHE = {}

# Cache des commentaires (oripathologie → {commentaire, auteur})
COMMENTAIRES_CACHE = {}

# Chemin du fichier de log des recherches
LOG_RECHERCHE_PATH = None

# ═══════════════════════════════════════════════════════════════
# CACHE POUR PAGINATION OPTIMISÉE (V1.1.7)
# Stocke les critères détectés par session_id pour éviter la re-détection
# ═══════════════════════════════════════════════════════════════

# Cache des recherches pour pagination optimisée (session_id → données)
# Structure : {session_id: {"question": str, "base": str, "criteres": list, 
#              "nb_total": int, "timestamp": datetime, "lang": str, ...}}
SEARCH_CACHE = {}
SEARCH_CACHE_MAX_SIZE = 1000  # Nombre max de sessions en cache
SEARCH_CACHE_TTL_MINUTES = 30  # Durée de vie en minutes

# Répertoire des photos de prospects (initialisé dans lifespan)
PROSPECTS_PHOTOS_DIR = None


def _cleanup_search_cache():
    """Nettoie les entrées expirées du cache de recherche."""
    global SEARCH_CACHE
    now = datetime.now()
    expired = []
    for session_id, data in SEARCH_CACHE.items():
        timestamp = data.get('timestamp')
        if timestamp:
            age_minutes = (now - timestamp).total_seconds() / 60
            if age_minutes > SEARCH_CACHE_TTL_MINUTES:
                expired.append(session_id)
    
    for session_id in expired:
        del SEARCH_CACHE[session_id]
    
    # Si toujours trop gros, supprimer les plus anciens
    if len(SEARCH_CACHE) > SEARCH_CACHE_MAX_SIZE:
        sorted_sessions = sorted(
            SEARCH_CACHE.items(), 
            key=lambda x: x[1].get('timestamp', datetime.min)
        )
        to_remove = len(SEARCH_CACHE) - SEARCH_CACHE_MAX_SIZE
        for session_id, _ in sorted_sessions[:to_remove]:
            del SEARCH_CACHE[session_id]
    
    return len(expired)

# ═══════════════════════════════════════════════════════════════
# CONFIGURATION EMAIL POUR NOTIFICATIONS RATING
# ═══════════════════════════════════════════════════════════════

EMAIL_CONFIG = {
    'enabled': True,
    'recipient': 'thierry.oberle@kitview.com',
    'smtp_server': os.environ.get('SMTP_SERVER', 'smtp.gmail.com'),
    'smtp_port': int(os.environ.get('SMTP_PORT', '587')),
    'smtp_user': os.environ.get('SMTP_USER', ''),
    'smtp_password': os.environ.get('SMTP_PASSWORD', ''),
    'sender': os.environ.get('SMTP_SENDER', 'noreply@kitview.com')
}


def send_rating_email_async(session_id: str, rating: str, type_probleme: str, 
                            commentaire: str, search_info: dict):
    """
    Envoie un email de notification de rating de manière asynchrone.
    
    Args:
        session_id: UUID de la session
        rating: 👍 ou 👎
        type_probleme: Type de problème si pouce bas
        commentaire: Commentaire de l'utilisateur
        search_info: Infos sur la recherche (question, nb_patients, etc.)
    """
    def _send():
        if not EMAIL_CONFIG['enabled']:
            return
        
        if not EMAIL_CONFIG['smtp_user'] or not EMAIL_CONFIG['smtp_password']:
            logger.warning("Email désactivé : credentials SMTP non configurés")
            return
        
        try:
            # Construire le message
            subject = f"[Kitview Search] Feedback {rating}"
            if type_probleme:
                subject += f" - {type_probleme}"
            
            # Corps du message en HTML
            html_body = f"""
            <html>
            <body style="font-family: Arial, sans-serif; padding: 20px;">
                <h2 style="color: {'#27ae60' if rating == '👍' else '#e74c3c'};">
                    Feedback utilisateur : {rating}
                </h2>
                
                <table style="border-collapse: collapse; margin: 20px 0;">
                    <tr>
                        <td style="padding: 8px; border: 1px solid #ddd; background: #f5f5f5;"><strong>Session ID</strong></td>
                        <td style="padding: 8px; border: 1px solid #ddd;">{session_id}</td>
                    </tr>
                    <tr>
                        <td style="padding: 8px; border: 1px solid #ddd; background: #f5f5f5;"><strong>Rating</strong></td>
                        <td style="padding: 8px; border: 1px solid #ddd; font-size: 24px;">{rating}</td>
                    </tr>
                    {'<tr><td style="padding: 8px; border: 1px solid #ddd; background: #f5f5f5;"><strong>Type problème</strong></td><td style="padding: 8px; border: 1px solid #ddd;">' + type_probleme + '</td></tr>' if type_probleme else ''}
                    {'<tr><td style="padding: 8px; border: 1px solid #ddd; background: #f5f5f5;"><strong>Commentaire</strong></td><td style="padding: 8px; border: 1px solid #ddd;">' + commentaire + '</td></tr>' if commentaire else ''}
                </table>
                
                <h3>Informations de recherche</h3>
                <table style="border-collapse: collapse; margin: 20px 0;">
                    <tr>
                        <td style="padding: 8px; border: 1px solid #ddd; background: #f5f5f5;"><strong>Question</strong></td>
                        <td style="padding: 8px; border: 1px solid #ddd;">{search_info.get('question', 'N/A')}</td>
                    </tr>
                    <tr>
                        <td style="padding: 8px; border: 1px solid #ddd; background: #f5f5f5;"><strong>Base</strong></td>
                        <td style="padding: 8px; border: 1px solid #ddd;">{search_info.get('base', 'N/A')}</td>
                    </tr>
                    <tr>
                        <td style="padding: 8px; border: 1px solid #ddd; background: #f5f5f5;"><strong>Nb patients</strong></td>
                        <td style="padding: 8px; border: 1px solid #ddd;">{search_info.get('nb_patients', 'N/A')}</td>
                    </tr>
                    <tr>
                        <td style="padding: 8px; border: 1px solid #ddd; background: #f5f5f5;"><strong>Mode</strong></td>
                        <td style="padding: 8px; border: 1px solid #ddd;">{search_info.get('mode', 'N/A')}</td>
                    </tr>
                    <tr>
                        <td style="padding: 8px; border: 1px solid #ddd; background: #f5f5f5;"><strong>Temps</strong></td>
                        <td style="padding: 8px; border: 1px solid #ddd;">{search_info.get('temps_ms', 'N/A')} ms</td>
                    </tr>
                    <tr>
                        <td style="padding: 8px; border: 1px solid #ddd; background: #f5f5f5;"><strong>Date/Heure</strong></td>
                        <td style="padding: 8px; border: 1px solid #ddd;">{datetime.now().strftime('%d/%m/%Y %H:%M:%S')}</td>
                    </tr>
                </table>
                
                <p style="color: #888; font-size: 12px;">
                    Email envoyé automatiquement par Kitview Search
                </p>
            </body>
            </html>
            """
            
            # Créer le message
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = EMAIL_CONFIG['sender']
            msg['To'] = EMAIL_CONFIG['recipient']
            
            # Version texte simple
            text_body = f"""
Feedback utilisateur : {rating}

Session ID: {session_id}
Type problème: {type_probleme or 'N/A'}
Commentaire: {commentaire or 'N/A'}

Recherche:
- Question: {search_info.get('question', 'N/A')}
- Base: {search_info.get('base', 'N/A')}
- Nb patients: {search_info.get('nb_patients', 'N/A')}
- Mode: {search_info.get('mode', 'N/A')}
- Temps: {search_info.get('temps_ms', 'N/A')} ms
- Date: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}
            """
            
            msg.attach(MIMEText(text_body, 'plain'))
            msg.attach(MIMEText(html_body, 'html'))
            
            # Envoyer l'email
            with smtplib.SMTP(EMAIL_CONFIG['smtp_server'], EMAIL_CONFIG['smtp_port']) as server:
                server.starttls()
                server.login(EMAIL_CONFIG['smtp_user'], EMAIL_CONFIG['smtp_password'])
                server.send_message(msg)
            
            logger.info(f"Email de rating envoyé à {EMAIL_CONFIG['recipient']}")
            
        except Exception as e:
            logger.error(f"Erreur envoi email rating: {e}")
    
    # Lancer dans un thread séparé pour ne pas bloquer la réponse API
    thread = threading.Thread(target=_send)
    thread.daemon = True
    thread.start()


# ═══════════════════════════════════════════════════════════════
# LIFESPAN (remplace @app.on_event("startup"))
# ═══════════════════════════════════════════════════════════════

@asynccontextmanager
async def lifespan(app):
    """Configure les chemins et charge les références au démarrage."""
    global BASES_DIR, REFS_DIR, ILLUSTRATIONS_CACHE, PORTRAITS_CACHE, IA_CACHE, IA_FULL_CACHE, I18N_CACHE, COMMENTAIRES_CACHE, LOG_RECHERCHE_PATH, IHM_CACHE_DIR, PROSPECTS_PHOTOS_DIR
    
    logger.info("════════════════════════════════════════════════════════════")
    logger.info(f"Démarrage du serveur API Recherche Patients")
    logger.info(f"Version : {__version__}")
    logger.info(f"Date : {__date__}")
    logger.info("════════════════════════════════════════════════════════════")
    logger.info("")
    
    # ═══════════════════════════════════════════════════════════════
    # ÉTAPE 1 : CONFIGURATION DES CHEMINS
    # ═══════════════════════════════════════════════════════════════
    
    logger.info("ÉTAPE 1 : Configuration des chemins")
    logger.info(f"  Répertoire du script : {SCRIPT_DIR}")
    
    BASES_DIR = SCRIPT_DIR / "bases"
    REFS_DIR = SCRIPT_DIR / "refs"
    
    # CORRECTION V1.0.23 : Le fichier de log est dans le sous-répertoire logs/
    LOG_RECHERCHE_PATH = SCRIPT_DIR / "logs" / "logrecherche.csv"
    
    logger.info(f"  Répertoire des bases : {BASES_DIR}")
    logger.info(f"  Répertoire des refs  : {REFS_DIR}")
    logger.info(f"  Fichier log recherches : {LOG_RECHERCHE_PATH}")
    
    # S'assurer que le répertoire logs existe
    logs_dir = SCRIPT_DIR / "logs"
    if not logs_dir.exists():
        try:
            logs_dir.mkdir(parents=True, exist_ok=True)
            logger.info(f"  ✓ Répertoire logs/ créé")
        except Exception as e:
            logger.error(f"  ❌ Impossible de créer le répertoire logs/: {e}")
    else:
        logger.info(f"  ✓ Répertoire logs/ trouvé")
    
    # S'assurer que le répertoire ihm existe (cache des traductions)
    IHM_CACHE_DIR = SCRIPT_DIR / "ihm"
    if not IHM_CACHE_DIR.exists():
        try:
            IHM_CACHE_DIR.mkdir(parents=True, exist_ok=True)
            logger.info(f"  ✓ Répertoire ihm/ créé (cache traductions)")
        except Exception as e:
            logger.error(f"  ❌ Impossible de créer le répertoire ihm/: {e}")
            IHM_CACHE_DIR = None
    else:
        # Afficher l'état du cache
        versions_path = IHM_CACHE_DIR / "help_versions.json"
        if versions_path.exists():
            try:
                with open(versions_path, 'r', encoding='utf-8') as f:
                    cache = json.load(f)
                nb_trad = len(cache.get("translations", {}))
                logger.info(f"  ✓ Répertoire ihm/ trouvé ({nb_trad} traduction(s) en cache)")
            except:
                logger.info(f"  ✓ Répertoire ihm/ trouvé")
        else:
            logger.info(f"  ✓ Répertoire ihm/ trouvé (cache vide)")
    
    if not BASES_DIR.exists():
        logger.warning(f"  ⚠️  Dossier bases/ introuvable !")
    else:
        logger.info(f"  ✓ Dossier bases/ trouvé")
    
    logger.info("")
    
    # ═══════════════════════════════════════════════════════════════
    # ÉTAPE 2 : CHARGEMENT DES RÉFÉRENCES
    # ═══════════════════════════════════════════════════════════════
    
    logger.info("ÉTAPE 2 : Chargement des fichiers de référence")
    
    if not REFS_DIR.exists():
        logger.warning(f"  ⚠️  Dossier refs/ introuvable !")
    else:
        logger.info(f"  ✓ Dossier refs/ trouvé")
    
    # Chargement illustrations.csv (COMPLET avec cache full)
    illustrations_path = REFS_DIR / "illustrations.csv"
    if illustrations_path.exists():
        try:
            import csv
            import io
            with open(illustrations_path, 'r', encoding='utf-8-sig') as f:
                lines = [line for line in f if not line.strip().startswith('#')]
            
            reader = csv.DictReader(io.StringIO(''.join(lines)), delimiter=';')
            ILLUSTRATIONS_FULL_CACHE.clear()
            
            for row in reader:
                img_id = row.get('Id', '').strip()
                img_type = row.get('Type', '').strip().lower()
                img_comment = row.get('commentaire', '').strip()
                img_url = row.get('image', '').strip()
                
                # Cache complet pour l'API CRUD
                ILLUSTRATIONS_FULL_CACHE.append({
                    'Id': img_id,
                    'Type': row.get('Type', '').strip(),  # Conserver la casse originale
                    'commentaire': img_comment,
                    'image': img_url
                })
                
                # Cache par type pour les bandeaux (existant)
                # Inclure aussi rmedical et rsearch
                type_mapping = {
                    'medical': 'medical',
                    'rmedical': 'medical',
                    'search': 'search',
                    'rsearch': 'search',
                    'zero': 'zero'
                }
                cache_type = type_mapping.get(img_type)
                if cache_type and img_url:
                    ILLUSTRATIONS_CACHE[cache_type].append(img_url)
            
            nb_total = len(ILLUSTRATIONS_FULL_CACHE)
            nb_medical = len(ILLUSTRATIONS_CACHE['medical'])
            nb_search = len(ILLUSTRATIONS_CACHE['search'])
            nb_zero = len(ILLUSTRATIONS_CACHE['zero'])
            logger.info(f"  ✓ illustrations.csv chargé : {nb_total} total, {nb_medical} medical, {nb_search} search, {nb_zero} zero")
        except Exception as e:
            logger.error(f"  ❌ Erreur chargement illustrations.csv : {e}")
    else:
        logger.warning(f"  ⚠️  illustrations.csv introuvable")
    
    # Chargement portraits.csv (mapping idportrait → URL)
    portraits_path = REFS_DIR / "portraits.csv"
    if portraits_path.exists():
        try:
            import csv
            import io
            with open(portraits_path, 'r', encoding='utf-8-sig') as f:
                lines = [line for line in f if not line.strip().startswith('#')]
            
            reader = csv.DictReader(io.StringIO(''.join(lines)), delimiter=';')
            for row in reader:
                id_portrait = row.get('idportrait', '').strip()
                url_portrait = row.get('portrait', '').strip()
                if id_portrait and url_portrait:
                    PORTRAITS_CACHE[id_portrait] = url_portrait
            
            logger.info(f"  ✓ portraits.csv chargé : {len(PORTRAITS_CACHE)} portraits")
        except Exception as e:
            logger.error(f"  ❌ Erreur chargement portraits.csv : {e}")
    else:
        logger.warning(f"  ⚠️  portraits.csv introuvable")
    
    # Chargement ia.csv (moteurs IA disponibles)
    ia_path = REFS_DIR / "ia.csv"
    if ia_path.exists():
        try:
            import csv
            import io
            with open(ia_path, 'r', encoding='utf-8-sig') as f:
                lines = [line for line in f if not line.strip().startswith('#')]
            
            reader = csv.DictReader(io.StringIO(''.join(lines)), delimiter=';')
            for row in reader:
                moteur = row.get('moteur', '').strip()
                if not moteur:
                    continue
                
                actif_str = row.get('actif', '').strip().upper()
                is_actif = actif_str in ('O', 'OUI', '1', 'TRUE', 'YES')
                
                # Stocker TOUS les champs dans IA_FULL_CACHE
                moteur_data = {
                    'moteur': moteur,
                    'via': row.get('via', '').strip(),
                    'actif': 'O' if is_actif else 'N',
                    'complet': row.get('complet', '').strip(),
                    'cout': row.get('cout', '').strip(),
                    'notes': row.get('notes', '').strip(),
                    'image': row.get('image', '').strip()
                }
                IA_FULL_CACHE.append(moteur_data)
                
                # IA_CACHE garde uniquement les actifs (rétrocompatibilité)
                if is_actif:
                    IA_CACHE.append({
                        'moteur': moteur,
                        'image': moteur_data['image'],
                        'notes': moteur_data['notes']
                    })
            
            logger.info(f"  ✓ ia.csv chargé : {len(IA_FULL_CACHE)} moteur(s) total, {len(IA_CACHE)} actif(s)")
        except Exception as e:
            logger.error(f"  ❌ Erreur chargement ia.csv : {e}")
    else:
        logger.warning(f"  ⚠️  ia.csv introuvable")
    
    # Chargement commentaires.csv (mapping oripathologie → commentaires multilingues)
    commentaires_path = REFS_DIR / "commentaires.csv"
    if commentaires_path.exists():
        try:
            import csv
            import io
            with open(commentaires_path, 'r', encoding='utf-8-sig') as f:
                lines = [line for line in f if not line.strip().startswith('#')]
            
            reader = csv.DictReader(io.StringIO(''.join(lines)), delimiter=';')
            langues_comm = ['fr', 'en', 'de', 'es', 'it', 'ja', 'pt', 'pl', 'ro', 'th', 'ar', 'cn']
            
            for row in reader:
                oripathologie = row.get('oripathologie', '').strip().lower()
                # Charger le commentaire français (rétrocompatibilité)
                commentaire_fr = row.get('commentaire', row.get('fr', '')).strip()
                auteur = row.get('auteur', '').strip()
                
                if oripathologie and commentaire_fr:
                    # Stocker toutes les traductions disponibles
                    traductions = {'fr': commentaire_fr}
                    for lang in langues_comm:
                        if lang != 'fr':
                            trad = row.get(lang, '').strip()
                            traductions[lang] = trad if trad else commentaire_fr  # Fallback français
                    
                    COMMENTAIRES_CACHE[oripathologie] = {
                        'commentaire': commentaire_fr,  # Rétrocompatibilité
                        'traductions': traductions,
                        'auteur': auteur
                    }
            
            logger.info(f"  ✓ commentaires.csv chargé : {len(COMMENTAIRES_CACHE)} commentaire(s)")
        except Exception as e:
            logger.error(f"  ❌ Erreur chargement commentaires.csv : {e}")
    else:
        logger.warning(f"  ⚠️  commentaires.csv introuvable")
    
    # Chargement glossaire.csv pour TOUTES les traductions
    # (UI, tags, adjectifs, etc. - tout ce qui a une colonne 'fr')
    glossaire_path = REFS_DIR / "glossaire.csv"
    if glossaire_path.exists():
        try:
            import csv
            import io
            with open(glossaire_path, 'r', encoding='utf-8-sig') as f:
                lines = [line for line in f if not line.strip().startswith('#')]
            
            reader = csv.DictReader(io.StringIO(''.join(lines)), delimiter=';')
            langues = ['fr', 'en', 'de', 'es', 'it', 'ja', 'pt', 'pl', 'ro', 'th', 'ar', 'cn']
            
            # Comptage par type pour le log
            count_by_type = {}
            
            for row in reader:
                # Charger TOUTES les lignes qui ont une clé française
                cle_fr = row.get('fr', '').strip()
                if cle_fr:
                    I18N_CACHE[cle_fr] = {}
                    for lang in langues:
                        valeur = row.get(lang, '').strip()
                        I18N_CACHE[cle_fr][lang] = valeur if valeur else cle_fr
                    # Comptage par type
                    row_type = row.get('type', '').strip().lower() or 'autre'
                    count_by_type[row_type] = count_by_type.get(row_type, 0) + 1
            
            type_info = ', '.join(f"{k}:{v}" for k, v in sorted(count_by_type.items()))
            logger.info(f"  ✓ glossaire.csv chargé : {len(I18N_CACHE)} texte(s) i18n ({type_info})")
        except Exception as e:
            logger.error(f"  ❌ Erreur chargement glossaire.csv (i18n) : {e}")
    else:
        logger.warning(f"  ⚠️  glossaire.csv introuvable (i18n désactivé)")
    
    logger.info("")
    
    # ═══════════════════════════════════════════════════════════════
    # ÉTAPE 2b : INITIALISATION PHOTOFIT UPLOAD & PROSPECTS
    # ═══════════════════════════════════════════════════════════════
    
    logger.info("ÉTAPE 2b : Initialisation Photofit Upload & Prospects")
    
    if PHOTOFIT_UPLOAD_DISPONIBLE:
        try:
            prospects_db = BASES_DIR / "prospects.db"
            creer_base_prospects(prospects_db, verbose=False)
            
            PROSPECTS_PHOTOS_DIR = BASES_DIR / "prospects"
            PROSPECTS_PHOTOS_DIR.mkdir(parents=True, exist_ok=True)
            
            stats = photofit_stats_prospects(prospects_db)
            logger.info(f"  ✓ prospects.db : {stats['total']} prospect(s)")
            logger.info(f"  ✓ Photos prospects : {PROSPECTS_PHOTOS_DIR}")
            
            config_pf = photofit_lire_config(debug=False)
            logger.info(f"  ✓ Config Photofit : max={config_pf['max_results']}, "
                        f"score_min={config_pf['score_min']}, "
                        f"weights=hair:{config_pf['weight_hair']}/face:{config_pf['weight_face']}")
        except Exception as e:
            logger.error(f"  ❌ Erreur init Photofit Upload : {e}")
    else:
        logger.warning("  ⚠️  Module photofit_upload.py non disponible")
    
    logger.info("")
    
    # ═══════════════════════════════════════════════════════════════
    # ÉTAPE 3 : VÉRIFICATION MODULES
    # ═══════════════════════════════════════════════════════════════
    
    logger.info("ÉTAPE 3 : Vérification des modules")
    
    if SEARCH_DISPONIBLE:
        logger.info(f"  ✓ search.py importé → /search disponible")
    else:
        logger.error(f"  ❌ search.py non disponible → /search DÉSACTIVÉ")
    
    if TRADUIRE_DISPONIBLE:
        logger.info(f"  ✓ traduire.py importé → traduction disponible")
    else:
        logger.warning(f"  ⚠️  traduire.py non importé → traduction limitée")
    
    if ANALYSE_DISPONIBLE:
        logger.info(f"  ✓ analyse.py importé → /analyse/* disponible")
    else:
        logger.warning(f"  ⚠️  analyse.py non importé → /analyse/* DÉSACTIVÉ")
    
    if PHOTOFIT_UPLOAD_DISPONIBLE:
        logger.info(f"  ✓ photofit_upload.py importé → /photofit/* disponible")
    else:
        logger.warning(f"  ⚠️  photofit_upload.py non importé → /photofit/* DÉSACTIVÉ")
    
    logger.info("")
    logger.info("════════════════════════════════════════════════════════════")
    logger.info("Serveur prêt à recevoir des requêtes")
    logger.info("════════════════════════════════════════════════════════════")
    logger.info("")
    
    yield
    
    # Arrêt du serveur
    logger.info("Arrêt du serveur")


# ═══════════════════════════════════════════════════════════════
# APPLICATION FASTAPI
# ═══════════════════════════════════════════════════════════════

app = FastAPI(
    title="API Recherche Patients",
    description="Recherche multilingue avec détection de critères",
    version=__version__,
    lifespan=lifespan
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ═══════════════════════════════════════════════════════════════
# FICHIERS STATIQUES - Servir le dossier ihm/
# ═══════════════════════════════════════════════════════════════
app.mount("/ihm", StaticFiles(directory="ihm", html=True), name="ihm")

# Servir les photos des prospects (bases/prospects/)
_prospects_photos_dir = SCRIPT_DIR / "bases" / "prospects"
_prospects_photos_dir.mkdir(parents=True, exist_ok=True)
app.mount("/photofit/prospects/photos",
          StaticFiles(directory=str(_prospects_photos_dir)),
          name="prospects_photos")
# ═══════════════════════════════════════════════════════════════
# KVM - MANUEL KITVIEW
# ═══════════════════════════════════════════════════════════════
# Route sous /api/kvm/ pour éviter tout conflit avec le mount /kvm.
# index.html dans kvm/ gère la redirection vers kvms.html.

@app.get("/api/kvm/env-config.js")
async def kvm_env_config():
    """
    Génère dynamiquement le JS d'environnement pour le chatbot KVM.
    Route sous /api/ pour ne pas entrer en conflit avec le mount StaticFiles /kvm.
    Utilise ANTHROPIC_API_KEY et OPENAI_API_KEY déjà configurées sur Render.
    """
    claude_key  = os.environ.get("ANTHROPIC_API_KEY", "")
    chatgpt_key = os.environ.get("OPENAI_API_KEY", "")
    js_content = f"""// env-config.js — généré dynamiquement par server.py (route /api/kvm/env-config.js)
window.ENV_CONFIG = {{
  claudeApiKey:  "{claude_key}",
  chatgptApiKey: "{chatgpt_key}"
}};
"""
    return Response(content=js_content, media_type="application/javascript")


# Mount StaticFiles — html=True sert index.html pour /kvm/ automatiquement
app.mount("/kvm", StaticFiles(directory=str(SCRIPT_DIR / "kvm" / "ihm"), html=True), name="kvm")



# ═══════════════════════════════════════════════════════════════
# MODÈLES PYDANTIC
# ═══════════════════════════════════════════════════════════════

class SearchRequest(BaseModel):
    question: str
    base: str = "base100.db"
    lang: Optional[str] = "auto"
    lang_reponse: Optional[str] = "same"
    mode_detection: str = "standard"
    limit: int = 100
    offset: int = 0
    api_key: Optional[str] = None
    session_id: Optional[str] = None  # UUID généré côté client


class RatingRequest(BaseModel):
    """Modèle pour les feedbacks utilisateur."""
    session_id: str                           # UUID de la session (obligatoire)
    rating: str                               # 👍, 👎 ou vide
    type_probleme: Optional[str] = None       # Bug IHM, Pas trouvé tous, Trop trouvé, Autre
    commentaire: Optional[str] = None         # Texte libre


class PageRequest(BaseModel):
    """Modèle pour la pagination optimisée (réutilise les critères en cache)."""
    session_id: str              # UUID de la session (obligatoire)
    offset: int = 0              # Décalage pour la pagination
    limit: int = 20              # Nombre de patients à retourner


class IllustrationRequest(BaseModel):
    """Modèle pour les illustrations CRUD."""
    Id: int
    Type: str
    commentaire: str
    image: str


# ═══════════════════════════════════════════════════════════════
# ENDPOINTS PRINCIPAUX
# ═══════════════════════════════════════════════════════════════

@app.get("/")
async def root():
    """Page d'accueil - redirige vers l'IHM."""
    return RedirectResponse(url="/ihm/index.html")


@app.get("/api")
async def api_info():
    """Informations sur l'API."""
    return {
        "name": "API Recherche Patients",
        "version": __version__,
        "date": __date__,
        "endpoints": {
            "/": "Page d'accueil",
            "/api": "Informations API",
            "/health": "État du serveur",
            "/version": "Version de l'API",
            "/bases": "Liste des bases disponibles",
            "/count": "Nombre de patients",
            "/illustrations": "URLs des illustrations (GET par type)",
            "/api/illustrations": "Liste/ajouter illustrations (GET/POST)",
            "/api/illustrations/{id}": "Modifier/supprimer illustration (PUT/DELETE)",
            "/illustrations.html": "Page de gestion des illustrations",
            "/params": "Paramètres (langues actives)",
            "/ia": "Moteurs IA disponibles",
            "/search": "Recherche patients (POST)",
            "/api/rating": "Enregistrer un feedback (POST)",
            "/api/export-logs": "Télécharger les logs (GET)",
            "/help": "Mode d'emploi",
            "/help/{lang}": "Mode d'emploi traduit",
            "/api/help/translate/{lang}": "Générer traduction mode d'emploi",
            "/api/help/versions": "État du cache des traductions",
            "/analyse": "Dashboard d'analyse",
            "/analyse/stats": "Statistiques globales (GET)",
            "/analyse/recherches": "Liste paginée (GET)",
            "/analyse/recherche/{id}": "Détail recherche (GET)",
            "/analyse/similaires/{id}": "Recherches similaires (GET)",
            "/analyse/search-comment": "Recherche dans commentaires (GET)",
            "/analyse/ia-summary": "Analyse IA (GET)",
            "/analyse/export": "Export CSV (GET)"
        },
        "photofit": {
            "/photofit/search-by-image": "Recherche par image uploadée (POST)",
            "/photofit/search-by-prospect-id": "Recherche par prospect existant (POST)",
            "/photofit/save-prospect": "Sauvegarder un prospect (POST)",
            "/photofit/prospects": "Lister les prospects (GET)",
            "/photofit/prospects/{id}": "Supprimer un prospect (DELETE)",
            "/photofit/prospects/photos/{filename}": "Photo prospect (statique)"
        }
    }


@app.get("/health")
async def health():
    """Vérifie l'état du serveur."""
    return {
        "status": "ok",
        "timestamp": datetime.now().isoformat(),
        "search_disponible": SEARCH_DISPONIBLE,
        "traduire_disponible": TRADUIRE_DISPONIBLE,
        "analyse_disponible": ANALYSE_DISPONIBLE,
        "deepl_configured": bool(DEEPL_API_KEY),
        "commentaires_disponibles": len(COMMENTAIRES_CACHE),
        "photofit_upload_disponible": PHOTOFIT_UPLOAD_DISPONIBLE
    }


@app.get("/version")
async def version():
    """Retourne la version de l'API."""
    return {
        "version": __version__,
        "date": __date__,
        "programme": __pgm__
    }


@app.get("/bases")
async def list_bases():
    """Liste les bases de données disponibles."""
    if BASES_DIR is None or not BASES_DIR.exists():
        logger.warning("GET /bases - Dossier bases/ non configuré")
        raise HTTPException(status_code=500, detail="Dossier bases/ non configuré")
    
    bases = []
    for db_file in sorted(BASES_DIR.glob("*.db")):
        bases.append(db_file.name)
    
    logger.info(f"GET /bases - {len(bases)} base(s) trouvée(s)")
    return {"bases": bases, "count": len(bases)}


@app.get("/count")
async def count_patients(base: str = "base100.db"):
    """Retourne le nombre de patients dans une base."""
    if BASES_DIR is None:
        raise HTTPException(status_code=500, detail="Dossier bases/ non configuré")
    
    db_path = BASES_DIR / base
    if not db_path.exists():
        raise HTTPException(status_code=404, detail=f"Base {base} introuvable")
    
    try:
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM patients")
        count = cursor.fetchone()[0]
        conn.close()
        
        logger.info(f"GET /count - Base {base} : {count} patient(s)")
        return {"base": base, "count": count}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lecture base: {e}")


@app.get("/illustrations")
async def get_illustrations(type: str = "all"):
    """Retourne les URLs des illustrations pour les bandeaux de résultats."""
    logger.info(f"GET /illustrations - Type: {type}")
    
    if type == "all":
        result = ILLUSTRATIONS_CACHE.copy()
        total = sum(len(v) for v in result.values())
        logger.info(f"GET /illustrations - {total} images au total")
        return result
    elif type in ILLUSTRATIONS_CACHE:
        return {type: ILLUSTRATIONS_CACHE[type]}
    else:
        raise HTTPException(status_code=400, detail=f"Type invalide: {type}")


# ═══════════════════════════════════════════════════════════════
# FONCTION HELPER - Recharger le cache des illustrations
# ═══════════════════════════════════════════════════════════════

def _reload_illustrations_cache():
    """Recharge les caches d'illustrations depuis le fichier CSV."""
    global ILLUSTRATIONS_CACHE, ILLUSTRATIONS_FULL_CACHE
    
    ILLUSTRATIONS_CACHE['medical'].clear()
    ILLUSTRATIONS_CACHE['search'].clear()
    ILLUSTRATIONS_CACHE['zero'].clear()
    ILLUSTRATIONS_FULL_CACHE.clear()
    
    illustrations_path = REFS_DIR / "illustrations.csv"
    if not illustrations_path.exists():
        return
    
    try:
        import csv
        import io
        
        with open(illustrations_path, 'r', encoding='utf-8-sig') as f:
            lines = [line for line in f if not line.strip().startswith('#')]
        
        reader = csv.DictReader(io.StringIO(''.join(lines)), delimiter=';')
        
        for row in reader:
            img_id = row.get('Id', '').strip()
            img_type = row.get('Type', '').strip().lower()
            img_comment = row.get('commentaire', '').strip()
            img_url = row.get('image', '').strip()
            
            # Cache complet
            ILLUSTRATIONS_FULL_CACHE.append({
                'Id': img_id,
                'Type': row.get('Type', '').strip(),
                'commentaire': img_comment,
                'image': img_url
            })
            
            # Cache par type
            type_mapping = {
                'medical': 'medical',
                'rmedical': 'medical',
                'search': 'search',
                'rsearch': 'search',
                'zero': 'zero'
            }
            cache_type = type_mapping.get(img_type)
            if cache_type and img_url:
                ILLUSTRATIONS_CACHE[cache_type].append(img_url)
        
        logger.info(f"Cache illustrations rechargé : {len(ILLUSTRATIONS_FULL_CACHE)} entrées")
        
    except Exception as e:
        logger.error(f"Erreur rechargement cache illustrations: {e}")


# ═══════════════════════════════════════════════════════════════
# ENDPOINT GET /api/illustrations - Liste complète avec tous les champs
# ═══════════════════════════════════════════════════════════════

@app.get("/api/illustrations")
async def get_all_illustrations():
    """
    Retourne la liste complète des illustrations avec tous les champs.
    
    Retourne:
    - illustrations: Liste [{Id, Type, commentaire, image}, ...]
    - count: Nombre total d'illustrations
    """
    logger.info(f"GET /api/illustrations - {len(ILLUSTRATIONS_FULL_CACHE)} illustration(s)")
    return {
        "illustrations": ILLUSTRATIONS_FULL_CACHE,
        "count": len(ILLUSTRATIONS_FULL_CACHE)
    }


# ═══════════════════════════════════════════════════════════════
# ENDPOINT POST /api/illustrations - Ajouter une illustration
# ═══════════════════════════════════════════════════════════════

@app.post("/api/illustrations")
async def add_illustration(request: IllustrationRequest):
    """
    Ajoute une nouvelle illustration dans illustrations.csv.
    """
    global ILLUSTRATIONS_CACHE, ILLUSTRATIONS_FULL_CACHE
    
    # Vérifier que l'ID n'existe pas déjà
    for ill in ILLUSTRATIONS_FULL_CACHE:
        if str(ill['Id']) == str(request.Id):
            raise HTTPException(status_code=400, detail=f"L'ID {request.Id} existe déjà")
    
    # Valider le type
    valid_types = ['medical', 'rmedical', 'search', 'rsearch', 'zero']
    if request.Type.lower() not in valid_types:
        raise HTTPException(status_code=400, detail=f"Type invalide. Valeurs acceptées: {', '.join(valid_types)}")
    
    illustrations_path = REFS_DIR / "illustrations.csv"
    if not illustrations_path.exists():
        raise HTTPException(status_code=500, detail="Fichier illustrations.csv introuvable")
    
    try:
        import csv
        import io
        
        with open(illustrations_path, 'r', encoding='utf-8-sig') as f:
            all_lines = f.readlines()
        
        comment_lines = []
        data_lines = []
        for line in all_lines:
            if line.strip().startswith('#'):
                comment_lines.append(line)
            elif line.strip():
                data_lines.append(line)
        
        reader = csv.DictReader(io.StringIO(''.join(data_lines)), delimiter=';')
        fieldnames = reader.fieldnames
        rows = list(reader)
        
        new_row = {
            'Id': str(request.Id),
            'Type': request.Type,
            'commentaire': request.commentaire,
            'image': request.image
        }
        rows.append(new_row)
        rows.sort(key=lambda x: int(x.get('Id', 0)))
        
        with open(illustrations_path, 'w', encoding='utf-8-sig', newline='') as f:
            for comment in comment_lines:
                f.write(comment)
            writer = csv.DictWriter(f, fieldnames=fieldnames, delimiter=';')
            writer.writeheader()
            writer.writerows(rows)
        
        _reload_illustrations_cache()
        
        logger.info(f"POST /api/illustrations - ID={request.Id}, Type={request.Type}")
        return {"status": "ok", "illustration": new_row}
        
    except Exception as e:
        logger.error(f"POST /api/illustrations - Erreur: {e}")
        raise HTTPException(status_code=500, detail=f"Erreur création illustration: {e}")


# ═══════════════════════════════════════════════════════════════
# ENDPOINT PUT /api/illustrations/{id} - Modifier une illustration
# ═══════════════════════════════════════════════════════════════

@app.put("/api/illustrations/{id}")
async def update_illustration(id: int, request: IllustrationRequest):
    """
    Modifie une illustration existante dans illustrations.csv.
    """
    global ILLUSTRATIONS_CACHE, ILLUSTRATIONS_FULL_CACHE
    
    found = False
    for ill in ILLUSTRATIONS_FULL_CACHE:
        if str(ill['Id']) == str(id):
            found = True
            break
    
    if not found:
        raise HTTPException(status_code=404, detail=f"Illustration ID {id} non trouvée")
    
    valid_types = ['medical', 'rmedical', 'search', 'rsearch', 'zero']
    if request.Type.lower() not in valid_types:
        raise HTTPException(status_code=400, detail=f"Type invalide. Valeurs acceptées: {', '.join(valid_types)}")
    
    illustrations_path = REFS_DIR / "illustrations.csv"
    if not illustrations_path.exists():
        raise HTTPException(status_code=500, detail="Fichier illustrations.csv introuvable")
    
    try:
        import csv
        import io
        
        with open(illustrations_path, 'r', encoding='utf-8-sig') as f:
            all_lines = f.readlines()
        
        comment_lines = []
        data_lines = []
        for line in all_lines:
            if line.strip().startswith('#'):
                comment_lines.append(line)
            elif line.strip():
                data_lines.append(line)
        
        reader = csv.DictReader(io.StringIO(''.join(data_lines)), delimiter=';')
        fieldnames = reader.fieldnames
        rows = list(reader)
        
        updated_row = None
        for row in rows:
            if str(row.get('Id', '')) == str(id):
                row['Id'] = str(request.Id)
                row['Type'] = request.Type
                row['commentaire'] = request.commentaire
                row['image'] = request.image
                updated_row = row.copy()
        
        rows.sort(key=lambda x: int(x.get('Id', 0)))
        
        with open(illustrations_path, 'w', encoding='utf-8-sig', newline='') as f:
            for comment in comment_lines:
                f.write(comment)
            writer = csv.DictWriter(f, fieldnames=fieldnames, delimiter=';')
            writer.writeheader()
            writer.writerows(rows)
        
        _reload_illustrations_cache()
        
        logger.info(f"PUT /api/illustrations/{id} - Type={request.Type}")
        return {"status": "ok", "illustration": updated_row}
        
    except Exception as e:
        logger.error(f"PUT /api/illustrations/{id} - Erreur: {e}")
        raise HTTPException(status_code=500, detail=f"Erreur modification illustration: {e}")


# ═══════════════════════════════════════════════════════════════
# ENDPOINT DELETE /api/illustrations/{id} - Supprimer une illustration
# ═══════════════════════════════════════════════════════════════

@app.delete("/api/illustrations/{id}")
async def delete_illustration(id: int):
    """
    Supprime une illustration de illustrations.csv.
    """
    global ILLUSTRATIONS_CACHE, ILLUSTRATIONS_FULL_CACHE
    
    found = False
    for ill in ILLUSTRATIONS_FULL_CACHE:
        if str(ill['Id']) == str(id):
            found = True
            break
    
    if not found:
        raise HTTPException(status_code=404, detail=f"Illustration ID {id} non trouvée")
    
    illustrations_path = REFS_DIR / "illustrations.csv"
    if not illustrations_path.exists():
        raise HTTPException(status_code=500, detail="Fichier illustrations.csv introuvable")
    
    try:
        import csv
        import io
        
        with open(illustrations_path, 'r', encoding='utf-8-sig') as f:
            all_lines = f.readlines()
        
        comment_lines = []
        data_lines = []
        for line in all_lines:
            if line.strip().startswith('#'):
                comment_lines.append(line)
            elif line.strip():
                data_lines.append(line)
        
        reader = csv.DictReader(io.StringIO(''.join(data_lines)), delimiter=';')
        fieldnames = reader.fieldnames
        rows = list(reader)
        
        rows = [row for row in rows if str(row.get('Id', '')) != str(id)]
        
        with open(illustrations_path, 'w', encoding='utf-8-sig', newline='') as f:
            for comment in comment_lines:
                f.write(comment)
            writer = csv.DictWriter(f, fieldnames=fieldnames, delimiter=';')
            writer.writeheader()
            writer.writerows(rows)
        
        _reload_illustrations_cache()
        
        logger.info(f"DELETE /api/illustrations/{id} - Supprimé")
        return {"status": "ok", "deleted_id": id}
        
    except Exception as e:
        logger.error(f"DELETE /api/illustrations/{id} - Erreur: {e}")
        raise HTTPException(status_code=500, detail=f"Erreur suppression illustration: {e}")


# ═══════════════════════════════════════════════════════════════
# ENDPOINT GET /illustrations.html - Servir la page de gestion
# ═══════════════════════════════════════════════════════════════

@app.get("/illustrations.html")
async def serve_illustrations_page():
    """Sert la page HTML de gestion des illustrations."""
    illustrations_html = SCRIPT_DIR / "ihm" / "illustrations.html"
    if illustrations_html.exists():
        return FileResponse(illustrations_html)
    raise HTTPException(status_code=404, detail="Page illustrations.html non trouvée")


# ═══════════════════════════════════════════════════════════════
# ENDPOINT GET /params - Paramètres depuis communb.csv
# ═══════════════════════════════════════════════════════════════

@app.get("/params")
async def get_params(param: str = "languesactives"):
    """
    Retourne des paramètres de configuration depuis communb.csv.
    
    Format communb.csv : section;parametre;valeur;description
    
    Paramètres disponibles:
    - languesactives: Liste des codes de langues actives (section=langues, parametre=langues)
    """
    if REFS_DIR is None:
        raise HTTPException(status_code=500, detail="Dossier refs/ non configuré")
    
    # V1.1.8 : Utiliser communb.csv au lieu de commun.csv
    commun_path = REFS_DIR / "communb.csv"
    if not commun_path.exists():
        raise HTTPException(status_code=404, detail="Fichier communb.csv introuvable")
    
    try:
        import csv
        import io
        
        with open(commun_path, 'r', encoding='utf-8-sig') as f:
            lines = [line for line in f if not line.strip().startswith('#')]
        
        reader = csv.DictReader(io.StringIO(''.join(lines)), delimiter=';')
        
        if param == "languesactives":
            # V1.1.8 : Format communb.csv = section;parametre;valeur;description
            # Chercher section=langues, parametre=langues
            langues = []
            for row in reader:
                section = row.get('section', '').strip()
                parametre = row.get('parametre', '').strip()
                valeur = row.get('valeur', '').strip()
                
                if section == 'langues' and parametre == 'langues' and valeur:
                    # La valeur contient les langues séparées par des virgules
                    langues = [lang.strip() for lang in valeur.split(',') if lang.strip()]
                    break
            
            logger.info(f"GET /params?param=languesactives - {len(langues)} langue(s): {langues}")
            return {"languesactives": langues}
        else:
            raise HTTPException(status_code=400, detail=f"Paramètre inconnu: {param}")
            
    except Exception as e:
        logger.error(f"GET /params - Erreur: {e}")
        raise HTTPException(status_code=500, detail=f"Erreur lecture communb.csv: {e}")


# ═══════════════════════════════════════════════════════════════
# ENDPOINT GET /ia - Moteurs IA (TOUS avec tous les champs)
# ═══════════════════════════════════════════════════════════════

@app.get("/ia")
async def get_ia():
    """
    Retourne la liste de TOUS les moteurs IA depuis ia.csv (actifs ET inactifs).
    
    Retourne:
    - moteurs: Liste complète [{moteur, via, actif, complet, cout, notes, image}, ...]
    - count: Nombre total de moteurs
    - count_actifs: Nombre de moteurs actifs
    """
    count_actifs = sum(1 for m in IA_FULL_CACHE if m.get('actif') == 'O')
    logger.info(f"GET /ia - {len(IA_FULL_CACHE)} moteur(s) total, {count_actifs} actif(s)")
    return {
        "moteurs": IA_FULL_CACHE,
        "count": len(IA_FULL_CACHE),
        "count_actifs": count_actifs
    }


# ═══════════════════════════════════════════════════════════════
# ENDPOINT PUT /ia/{moteur} - Activer/désactiver un moteur
# ═══════════════════════════════════════════════════════════════

class IaUpdateRequest(BaseModel):
    actif: str  # 'O' ou 'N'

@app.put("/ia/{moteur}")
async def update_ia_moteur(moteur: str, request: IaUpdateRequest):
    """
    Active ou désactive un moteur IA dans ia.csv.
    
    Args:
    - moteur: Nom court du moteur (ex: gpt4o, sonnet, haiku)
    - actif: 'O' pour activer, 'N' pour désactiver
    
    Retourne:
    - status: 'ok' si succès
    - moteur: Nom du moteur modifié
    - actif: Nouvelle valeur
    """
    global IA_CACHE, IA_FULL_CACHE
    
    # Valider la valeur de actif
    new_actif = request.actif.upper()
    if new_actif not in ('O', 'N'):
        raise HTTPException(status_code=400, detail="actif doit être 'O' ou 'N'")
    
    # Vérifier que le moteur existe
    moteur_lower = moteur.lower()
    found = False
    for m in IA_FULL_CACHE:
        if m['moteur'].lower() == moteur_lower:
            found = True
            break
    
    if not found:
        raise HTTPException(status_code=404, detail=f"Moteur '{moteur}' non trouvé")
    
    # Réécrire ia.csv
    ia_path = REFS_DIR / "ia.csv"
    if not ia_path.exists():
        raise HTTPException(status_code=500, detail="Fichier ia.csv introuvable")
    
    try:
        import csv
        import io
        
        # Lire tout le fichier (commentaires inclus)
        with open(ia_path, 'r', encoding='utf-8-sig') as f:
            all_lines = f.readlines()
        
        # Séparer commentaires et données
        comment_lines = []
        data_lines = []
        for line in all_lines:
            if line.strip().startswith('#'):
                comment_lines.append(line)
            elif line.strip():
                data_lines.append(line)
        
        # Parser les données
        reader = csv.DictReader(io.StringIO(''.join(data_lines)), delimiter=';')
        fieldnames = reader.fieldnames
        rows = list(reader)
        
        # Modifier le moteur ciblé
        for row in rows:
            if row.get('moteur', '').lower() == moteur_lower:
                row['actif'] = new_actif
        
        # Réécrire le fichier
        with open(ia_path, 'w', encoding='utf-8-sig', newline='') as f:
            # Écrire les commentaires
            for comment in comment_lines:
                f.write(comment)
            
            # Écrire l'entête et les données
            writer = csv.DictWriter(f, fieldnames=fieldnames, delimiter=';')
            writer.writeheader()
            writer.writerows(rows)
        
        # Mettre à jour les caches en mémoire
        IA_CACHE.clear()
        IA_FULL_CACHE.clear()
        
        for row in rows:
            m = row.get('moteur', '').strip()
            if not m:
                continue
            
            is_actif = row.get('actif', '').upper() == 'O'
            moteur_data = {
                'moteur': m,
                'via': row.get('via', '').strip(),
                'actif': 'O' if is_actif else 'N',
                'complet': row.get('complet', '').strip(),
                'cout': row.get('cout', '').strip(),
                'notes': row.get('notes', '').strip(),
                'image': row.get('image', '').strip()
            }
            IA_FULL_CACHE.append(moteur_data)
            
            if is_actif:
                IA_CACHE.append({
                    'moteur': m,
                    'image': moteur_data['image'],
                    'notes': moteur_data['notes']
                })
        
        logger.info(f"PUT /ia/{moteur} - actif={new_actif}")
        return {"status": "ok", "moteur": moteur, "actif": new_actif}
        
    except Exception as e:
        logger.error(f"PUT /ia/{moteur} - Erreur: {e}")
        raise HTTPException(status_code=500, detail=f"Erreur modification ia.csv: {e}")


# ═══════════════════════════════════════════════════════════════
# ENDPOINT POST /ia/ask - Interroger un LLM
# ═══════════════════════════════════════════════════════════════

class IaAskRequest(BaseModel):
    moteur: Optional[str] = "gpt4o"
    patient: Dict[str, Any]
    question: str
    lang: Optional[str] = "fr"  # Langue pour la réponse IA

@app.post("/ia/ask")
async def ask_ia(request: IaAskRequest):
    """
    Interroge un LLM avec le contexte d'un patient.
    
    Args:
    - moteur: Nom court du moteur IA (défaut: gpt4o)
    - patient: Données du patient (nom, prenom, age, sexe, oripathologies, commentaires)
    - question: Question de l'utilisateur
    - lang: Langue pour la réponse (défaut: fr)
    
    Retourne:
    - reponse: Texte généré par le LLM
    - moteur: Moteur utilisé
    - temps_ms: Temps de réponse en millisecondes
    """
    moteur_name = request.moteur or "gpt4o"
    lang_code = request.lang or "fr"
    
    # Mapping code langue → nom complet pour le prompt
    LANGUES_NOMS = {
        'fr': 'français',
        'en': 'English',
        'de': 'Deutsch',
        'es': 'español',
        'it': 'italiano',
        'pt': 'português',
        'pl': 'polski',
        'ro': 'română',
        'th': 'ภาษาไทย',
        'ar': 'العربية',
        'cn': '中文',
        'ja': '日本語'
    }
    langue_nom = LANGUES_NOMS.get(lang_code, 'français')
    
    # Trouver la config du moteur
    moteur_config = None
    for m in IA_FULL_CACHE:
        if m['moteur'].lower() == moteur_name.lower():
            moteur_config = m
            break
    
    if not moteur_config:
        # Fallback sur gpt4o
        for m in IA_FULL_CACHE:
            if m['moteur'].lower() == 'gpt4o':
                moteur_config = m
                break
    
    if not moteur_config:
        raise HTTPException(status_code=400, detail="Aucun moteur IA disponible")
    
    via = moteur_config.get('via', 'openai')
    model_complet = moteur_config.get('complet', 'gpt-4o')
    
    # Construire le prompt système (multilingue)
    patient = request.patient
    
    # Instruction de langue en début de prompt
    if lang_code == 'fr':
        prompt_systeme = f"""Tu es un assistant médical spécialisé en orthodontie.
Tu analyses le dossier d'un patient et réponds aux questions du praticien.

PATIENT :
- Nom : {patient.get('nom', 'Inconnu')} {patient.get('prenom', '')}
- Âge : {patient.get('age', 'N/A')} ans
- Sexe : {'Masculin' if patient.get('sexe') == 'M' else 'Féminin' if patient.get('sexe') == 'F' else 'N/A'}
- Pathologies : {patient.get('oripathologies', 'Aucune')}

COMMENTAIRES CLINIQUES :
{_format_commentaires_for_prompt(patient.get('commentaires', []))}

INSTRUCTIONS :
- Réponds de manière concise et professionnelle
- Base-toi sur les données du patient
- Si tu n'as pas assez d'informations, dis-le
- Ne fais pas de diagnostic définitif, suggère des pistes"""
    else:
        # Prompt multilingue : demander à l'IA de répondre dans la langue cible
        prompt_systeme = f"""You are a medical assistant specialized in orthodontics.
You analyze a patient's file and answer the practitioner's questions.

IMPORTANT: You MUST respond in {langue_nom}.

PATIENT:
- Name: {patient.get('nom', 'Unknown')} {patient.get('prenom', '')}
- Age: {patient.get('age', 'N/A')} years old
- Sex: {'Male' if patient.get('sexe') == 'M' else 'Female' if patient.get('sexe') == 'F' else 'N/A'}
- Pathologies: {patient.get('oripathologies', 'None')}

CLINICAL COMMENTS:
{_format_commentaires_for_prompt(patient.get('commentaires', []))}

INSTRUCTIONS:
- Respond concisely and professionally in {langue_nom}
- Base your response on the patient's data
- If you don't have enough information, say so
- Don't make definitive diagnoses, suggest possibilities"""

    prompt_utilisateur = request.question
    
    start_time = time.time()
    
    try:
        if via == 'openai':
            reponse_texte = await _appeler_openai(prompt_systeme, prompt_utilisateur, model_complet)
        else:
            reponse_texte = await _appeler_eden(prompt_systeme, prompt_utilisateur, model_complet)
        
        temps_ms = round((time.time() - start_time) * 1000)
        
        logger.info(f"POST /ia/ask - moteur={moteur_name}, temps={temps_ms}ms")
        return {
            "reponse": reponse_texte,
            "moteur": moteur_name,
            "temps_ms": temps_ms
        }
        
    except Exception as e:
        logger.error(f"POST /ia/ask - Erreur: {e}")
        raise HTTPException(status_code=500, detail=f"Erreur appel IA: {e}")


def _format_commentaires_for_prompt(commentaires: List[Dict]) -> str:
    """Formate les commentaires cliniques pour le prompt."""
    if not commentaires:
        return "Aucun commentaire disponible"
    
    lines = []
    for c in commentaires:
        patho = c.get('pathologie', 'N/A')
        texte = c.get('commentaire', c.get('fr', ''))
        if texte:
            lines.append(f"- {patho}: {texte}")
    
    return '\n'.join(lines) if lines else "Aucun commentaire disponible"


async def _appeler_openai(prompt_systeme: str, prompt_utilisateur: str, model: str) -> str:
    """Appelle l'API OpenAI directement."""
    api_key = os.environ.get('OPENAI_API_KEY')
    if not api_key:
        raise ValueError("Variable OPENAI_API_KEY non définie")
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": prompt_systeme},
            {"role": "user", "content": prompt_utilisateur}
        ],
        "temperature": 0.3,
        "max_tokens": 1000
    }
    
    response = requests.post(
        "https://api.openai.com/v1/chat/completions",
        headers=headers,
        json=payload,
        timeout=60
    )
    
    if response.status_code != 200:
        raise ValueError(f"Erreur API OpenAI: {response.status_code} - {response.text}")
    
    data = response.json()
    return data['choices'][0]['message']['content'].strip()


async def _appeler_eden(prompt_systeme: str, prompt_utilisateur: str, model: str) -> str:
    """Appelle l'API Eden AI."""
    api_key = os.environ.get('EDENAI_API_KEY')
    if not api_key:
        raise ValueError("Variable EDENAI_API_KEY non définie")
    
    # Extraire provider et model_name
    if '/' in model:
        provider = model.split('/')[0]
        model_name = model.split('/', 1)[1]
    else:
        provider = model
        model_name = model
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "providers": provider,
        "text": prompt_utilisateur,
        "chatbot_global_action": prompt_systeme,
        "previous_history": [],
        "temperature": 0.3,
        "max_tokens": 1000,
        "settings": {provider: model_name}
    }
    
    response = requests.post(
        "https://api.edenai.run/v2/text/chat",
        headers=headers,
        json=payload,
        timeout=60
    )
    
    if response.status_code != 200:
        raise ValueError(f"Erreur API Eden: {response.status_code} - {response.text}")
    
    data = response.json()
    
    # Chercher le texte généré
    generated_text = data.get(provider, {}).get('generated_text', '')
    if not generated_text:
        for key in data:
            if isinstance(data[key], dict) and 'generated_text' in data[key]:
                generated_text = data[key]['generated_text']
                break
    
    return generated_text.strip()


async def _appeler_anthropic(prompt_systeme: str, prompt_utilisateur: str, model: str = "claude-sonnet-4-20250514") -> str:
    """Appelle l'API Anthropic (Claude) directement."""
    api_key = os.environ.get('ANTHROPIC_API_KEY')
    if not api_key:
        raise ValueError("Variable ANTHROPIC_API_KEY non définie")
    
    headers = {
        "x-api-key": api_key,
        "anthropic-version": "2023-06-01",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": model,
        "max_tokens": 1500,
        "system": prompt_systeme,
        "messages": [
            {"role": "user", "content": prompt_utilisateur}
        ],
        "temperature": 0.3
    }
    
    response = requests.post(
        "https://api.anthropic.com/v1/messages",
        headers=headers,
        json=payload,
        timeout=60
    )
    
    if response.status_code != 200:
        raise ValueError(f"Erreur API Anthropic: {response.status_code} - {response.text}")
    
    data = response.json()
    # Extraire le texte de la réponse
    content = data.get('content', [])
    texts = [block.get('text', '') for block in content if block.get('type') == 'text']
    return '\n'.join(texts).strip()


# ═══════════════════════════════════════════════════════════════
# ENDPOINT POST /ia/help-chatbot - Assistant IA pour les modes d'emploi
# ═══════════════════════════════════════════════════════════════

class HelpChatbotRequest(BaseModel):
    """Requête pour le chatbot d'aide."""
    question: str
    page_context: Optional[str] = ""  # Contenu textuel de la page pour le contexte
    history: Optional[List[Dict[str, str]]] = []  # Historique de conversation
    lang: Optional[str] = "fr"


@app.post("/ia/help-chatbot")
async def help_chatbot(request: HelpChatbotRequest):
    """
    Chatbot IA pour les pages de mode d'emploi.
    
    Utilise ANTHROPIC_API_KEY (Claude) en priorité, avec fallback sur OPENAI_API_KEY.
    Le contexte de la page est envoyé pour que l'IA puisse répondre aux questions
    sur le contenu du mode d'emploi.
    
    Args:
    - question: Question de l'utilisateur
    - page_context: Texte extrait de la page HTML pour le contexte
    - history: Historique des échanges [{role: "user"/"assistant", content: "..."}]
    - lang: Code langue pour la réponse (défaut: fr)
    
    Retourne:
    - reponse: Texte généré par l'IA
    - moteur: Nom du moteur utilisé (claude / openai)
    - temps_ms: Temps de réponse en millisecondes
    """
    lang_code = request.lang or "fr"
    langue_nom = LANGUES_NOMS.get(lang_code, 'français')
    
    # Construire le prompt système
    context_section = ""
    if request.page_context:
        # Limiter le contexte à ~4000 caractères pour ne pas exploser les tokens
        ctx = request.page_context[:4000]
        context_section = f"""

CONTENU DE LA PAGE D'AIDE :
{ctx}
"""
    
    prompt_systeme = f"""Tu es l'assistant du logiciel Kitview Search, un outil de recherche de patients orthodontiques.
Tu réponds aux questions des utilisateurs sur le mode d'emploi et les fonctionnalités de l'application.
{context_section}
INSTRUCTIONS :
- Réponds de manière concise et utile en {langue_nom}
- Base-toi sur le contenu de la page d'aide fourni
- Si la réponse n'est pas dans le contenu fourni, dis-le clairement
- Utilise des exemples concrets quand possible
- Formate ta réponse en Markdown léger (gras, listes) si nécessaire"""

    # Construire le prompt utilisateur avec l'historique
    prompt_utilisateur = request.question
    
    start_time = time.time()
    moteur_utilise = "unknown"
    
    try:
        # Priorité 1 : Anthropic (Claude)
        anthropic_key = os.environ.get('ANTHROPIC_API_KEY')
        openai_key = os.environ.get('OPENAI_API_KEY')
        
        if anthropic_key:
            moteur_utilise = "claude"
            reponse_texte = await _appeler_anthropic(prompt_systeme, prompt_utilisateur)
        elif openai_key:
            moteur_utilise = "openai"
            reponse_texte = await _appeler_openai(prompt_systeme, prompt_utilisateur, "gpt-4o")
        else:
            raise ValueError("Aucune clé API configurée (ANTHROPIC_API_KEY ou OPENAI_API_KEY)")
        
        temps_ms = round((time.time() - start_time) * 1000)
        
        logger.info(f"POST /ia/help-chatbot - moteur={moteur_utilise}, lang={lang_code}, temps={temps_ms}ms")
        return {
            "reponse": reponse_texte,
            "moteur": moteur_utilise,
            "temps_ms": temps_ms
        }
        
    except Exception as e:
        logger.error(f"POST /ia/help-chatbot - Erreur: {e}")
        raise HTTPException(status_code=500, detail=f"Erreur chatbot aide: {e}")


# ═══════════════════════════════════════════════════════════════
# ENDPOINT GET /i18n - Textes UI traduits
# ═══════════════════════════════════════════════════════════════

@app.get("/i18n")
async def get_i18n():
    """
    Retourne les textes UI traduits depuis glossaire.csv (type=ui).
    
    Retourne:
    - ui: Dict {cle_fr: {fr: "...", en: "...", ja: "...", ...}}
    - count: Nombre de textes UI
    """
    logger.info(f"GET /i18n - {len(I18N_CACHE)} texte(s) UI")
    return {
        "ui": I18N_CACHE,
        "count": len(I18N_CACHE)
    }


# ═══════════════════════════════════════════════════════════════
# ENDPOINT POST /search
# ═══════════════════════════════════════════════════════════════

def get_client_ip(request: Request) -> str:
    """Récupère l'adresse IP du client (gère les proxies)."""
    # Vérifier X-Forwarded-For pour les proxies
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        # Prendre la première IP (client original)
        return forwarded_for.split(",")[0].strip()
    
    # Vérifier X-Real-IP
    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip.strip()
    
    # Fallback sur l'IP directe
    if request.client:
        return request.client.host
    
    return "unknown"


@app.post("/search")
async def search_patients(request_data: SearchRequest, request: Request):
    """
    Recherche multilingue de patients via search.py + trouve.py.
    
    Modes de détection:
    - standard: detall.py (regex, synonymes)
    - ia: detia.py (Claude via Eden AI)
    """
    if not SEARCH_DISPONIBLE:
        raise HTTPException(status_code=503, detail="Module search.py non disponible")
    
    # Normalisation du mode_detection
    mode = request_data.mode_detection.lower()
    # Mapper les anciens noms vers les nouveaux (rétrocompatibilité)
    if mode == 'rapide':
        mode = 'standard'
    elif mode not in ['standard', 'ia', 'purstandard', 'puria']:
        # Si c'est un nom de modèle IA, utiliser le mode 'ia'
        mode = 'ia'
    
    # Valider le mode de détection
    modes_valides = ['standard', 'ia', 'purstandard', 'puria']
    if mode not in modes_valides:
        raise HTTPException(
            status_code=400, 
            detail=f"Mode de détection invalide: {mode}. Valeurs acceptées: {modes_valides}"
        )
    
    # Récupérer l'IP du client
    client_ip = get_client_ip(request)
    
    logger.info(f"POST /search - Question: '{request_data.question}' Lang: {request_data.lang or 'auto'}")
    logger.info(f"              Base: {request_data.base}, Mode détection: {mode}")
    logger.info(f"              Session: {request_data.session_id or 'N/A'}, IP: {client_ip}")
    if DEEPL_API_KEY:
        logger.info(f"              DeepL: ✓ disponible")
    else:
        logger.info(f"              DeepL: ✗ clé non configurée (pas d'escalade traduction)")
    
    # Construire le chemin de la base
    db_path = BASES_DIR / request_data.base if BASES_DIR else Path(request_data.base)
    if not db_path.exists():
        raise HTTPException(status_code=404, detail=f"Base {request_data.base} introuvable dans bases/")
    
    try:
        start_time = datetime.now()
        
        # Appeler search.py avec session_id et IP
        resultat = search_func(
            question=request_data.question,
            base_path=str(db_path),
            lang=request_data.lang if request_data.lang != "auto" else None,
            mode_detection=mode,
            verbose=False,
            mapping_patho=CACHE.get('mapping_patho'),
            messages=CACHE.get('messages'),
            response_lang=request_data.lang_reponse,
            limit=request_data.limit,
            offset=request_data.offset,
            api_key=request_data.api_key or DEEPL_API_KEY,
            session_id=request_data.session_id,
            ip_utilisateur=client_ip
        )
        
        # Enrichir les patients
        if 'patients' in resultat:
            ids_manquants = []
            # Récupérer la langue pour les commentaires (utiliser la langue d'interface/réponse)
            lang_ui = resultat.get('response_lang', resultat.get('lang', 'fr'))
            if lang_ui == 'same':
                lang_ui = resultat.get('lang', 'fr')
            if lang_ui == '?' or not lang_ui:
                lang_ui = 'fr'
            
            for patient in resultat['patients']:
                # Enrichir les portraits : remplacer idportrait par l'URL
                if PORTRAITS_CACHE:
                    id_portrait = str(patient.get('idportrait', ''))
                    if id_portrait and id_portrait in PORTRAITS_CACHE:
                        patient['portrait'] = PORTRAITS_CACHE[id_portrait]
                    else:
                        patient['portrait'] = ''
                        if id_portrait:
                            ids_manquants.append(id_portrait)
                
                # Enrichir les commentaires : ajouter les commentaires des pathologies
                if COMMENTAIRES_CACHE:
                    oripathologies = patient.get('oripathologies', '')
                    if oripathologies:
                        # oripathologies est une chaîne séparée par des virgules
                        patho_list = [p.strip().lower() for p in oripathologies.split(',') if p.strip()]
                        commentaires_patient = []
                        for patho in patho_list:
                            if patho in COMMENTAIRES_CACHE:
                                cache_entry = COMMENTAIRES_CACHE[patho]
                                # Utiliser la traduction dans la langue de l'interface si disponible
                                if 'traductions' in cache_entry and lang_ui in cache_entry['traductions']:
                                    commentaire_texte = cache_entry['traductions'][lang_ui]
                                else:
                                    commentaire_texte = cache_entry.get('commentaire', '')
                                
                                commentaires_patient.append({
                                    'pathologie': patho,
                                    'commentaire': commentaire_texte,
                                    'auteur': cache_entry.get('auteur', '')
                                })
                            else:
                                # Pathologie sans commentaire
                                commentaires_patient.append({
                                    'pathologie': patho,
                                    'commentaire': '',
                                    'auteur': ''
                                })
                        patient['commentaires'] = commentaires_patient
                    else:
                        patient['commentaires'] = []
            
            # Log diagnostic portraits
            nb_patients = len(resultat['patients'])
            nb_manquants = len(set(ids_manquants))
            if ids_manquants:
                logger.info(f"  Portraits: {nb_patients - nb_manquants} trouvés, {nb_manquants} manquants (cache: {len(PORTRAITS_CACHE)} entrées)")
        
        elapsed_ms = int((datetime.now() - start_time).total_seconds() * 1000)
        
        # Ajouter métadonnées
        resultat['temps_ms'] = elapsed_ms
        resultat['base'] = request_data.base
        resultat['mode_detection'] = mode
        resultat['session_id'] = request_data.session_id  # Retourner pour le client
        
        nb_patients = resultat.get('nb_patients', 0)
        auteur = resultat.get('auteur', '?')
        lang_detectee = resultat.get('lang', '?')
        lang_reponse = resultat.get('response_lang', 'same')
        question_resolue = resultat.get('question_resolue', '')
        mots_non_resolus = resultat.get('mots_non_resolus', [])
        parcours = resultat.get('parcours_detection', '')
        
        # Log enrichi avec parcours de détection
        logger.info(f"POST /search - {nb_patients} patient(s) en {elapsed_ms}ms")
        if parcours:
            logger.info(f"              Parcours: {parcours}")
        logger.info(f"              Auteur: {auteur}, Langue: {lang_detectee} → {lang_reponse}")
        # Afficher la résolution glossaire si langue != fr
        if question_resolue and lang_detectee != 'fr':
            logger.info(f"              Glossaire: '{request_data.question}' → '{question_resolue}'")
        elif question_resolue:
            logger.info(f"              Résolu: '{question_resolue}'")
        if mots_non_resolus:
            logger.info(f"              Non résolus: {', '.join(mots_non_resolus)}")
        
        # ═══════════════════════════════════════════════════════════════
        # CACHE POUR PAGINATION OPTIMISÉE (V1.1.7)
        # Stocker les critères détectés pour réutilisation par /search/page
        # ═══════════════════════════════════════════════════════════════
        if request_data.session_id:
            # Nettoyer le cache périodiquement
            if len(SEARCH_CACHE) > SEARCH_CACHE_MAX_SIZE * 0.9:
                cleaned = _cleanup_search_cache()
                if cleaned > 0:
                    logger.info(f"              Cache nettoyé: {cleaned} session(s) expirée(s)")
            
            # Stocker les informations nécessaires pour la pagination
            SEARCH_CACHE[request_data.session_id] = {
                'question': request_data.question,
                'base': request_data.base,
                'mode': mode,
                'lang': resultat.get('lang', 'fr'),
                'response_lang': resultat.get('response_lang', 'same'),
                'nb_total': resultat.get('nb_patients', 0),
                'criteres_detectes': resultat.get('criteres_detectes', []),
                'question_resolue': resultat.get('question_resolue', ''),
                'auteur': resultat.get('auteur', ''),
                'timestamp': datetime.now()
            }
            logger.info(f"              Cache: session {request_data.session_id[:8]}... stockée ({len(SEARCH_CACHE)} en cache)")
        
        return resultat
        
    except Exception as e:
        logger.error(f"POST /search - ERREUR: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ═══════════════════════════════════════════════════════════════════════════════
# ENDPOINT POST /search/page - Pagination optimisée (V1.1.7)
# ═══════════════════════════════════════════════════════════════════════════════

@app.post("/search/page")
async def search_page(request_data: PageRequest, request: Request):
    """
    Pagination optimisée : réutilise les critères détectés lors de la recherche initiale.
    
    Cette endpoint est ~30x plus rapide que /search pour la pagination car elle :
    - NE refait PAS la détection (detall/detia)
    - NE refait PAS le parsing de la question
    - Réutilise les critères stockés en cache
    - Génère uniquement le SQL avec le nouvel offset
    
    Requiert que /search ait été appelé avant avec le même session_id.
    """
    session_id = request_data.session_id
    
    # Vérifier que la session existe en cache
    if session_id not in SEARCH_CACHE:
        logger.warning(f"POST /search/page - Session {session_id[:8]}... non trouvée en cache")
        raise HTTPException(
            status_code=404, 
            detail="Session non trouvée. Effectuez d'abord une recherche avec /search."
        )
    
    cached = SEARCH_CACHE[session_id]
    
    logger.info(f"POST /search/page - Session: {session_id[:8]}... offset={request_data.offset}, limit={request_data.limit}")
    
    # Construire le chemin de la base
    db_path = BASES_DIR / cached['base'] if BASES_DIR else Path(cached['base'])
    if not db_path.exists():
        raise HTTPException(status_code=404, detail=f"Base {cached['base']} introuvable")
    
    try:
        start_time = datetime.now()
        
        # Import des modules nécessaires
        from jsonsql import generer_sql
        from lancesql import executer_sql
        
        # Reconstruire le JSON de détection depuis le cache
        json_detection = {
            'criteres': cached['criteres_detectes'],
            'listcount': 'LIST'
        }
        
        # Générer le SQL avec le nouvel offset
        sql_dict = generer_sql(
            json_detection, 
            limit=request_data.limit, 
            offset=request_data.offset,
            verbose=False, 
            debug=False
        )
        
        # Exécuter le SQL
        resultat_sql = executer_sql(
            sql_dict, 
            str(db_path), 
            include_details=True,
            verbose=False, 
            debug=False
        )
        
        # Enrichir les patients (portraits + commentaires)
        patients = resultat_sql.get('patients', [])
        lang_ui = cached.get('response_lang', cached.get('lang', 'fr'))
        if lang_ui == 'same':
            lang_ui = cached.get('lang', 'fr')
        
        for patient in patients:
            # Portraits
            if PORTRAITS_CACHE:
                id_portrait = str(patient.get('idportrait', ''))
                if id_portrait and id_portrait in PORTRAITS_CACHE:
                    patient['portrait'] = PORTRAITS_CACHE[id_portrait]
                else:
                    patient['portrait'] = ''
            
            # Commentaires
            if COMMENTAIRES_CACHE:
                oripathologies = patient.get('oripathologies', '')
                if oripathologies:
                    patho_list = [p.strip().lower() for p in oripathologies.split(',') if p.strip()]
                    commentaires_patient = []
                    for patho in patho_list:
                        if patho in COMMENTAIRES_CACHE:
                            cache_entry = COMMENTAIRES_CACHE[patho]
                            if 'traductions' in cache_entry and lang_ui in cache_entry['traductions']:
                                commentaire_texte = cache_entry['traductions'][lang_ui]
                            else:
                                commentaire_texte = cache_entry.get('commentaire', '')
                            commentaires_patient.append({
                                'pathologie': patho,
                                'commentaire': commentaire_texte,
                                'auteur': cache_entry.get('auteur', '')
                            })
                        else:
                            commentaires_patient.append({
                                'pathologie': patho,
                                'commentaire': '',
                                'auteur': ''
                            })
                    patient['commentaires'] = commentaires_patient
                else:
                    patient['commentaires'] = []
        
        elapsed_ms = int((datetime.now() - start_time).total_seconds() * 1000)
        
        # Construire la réponse
        resultat = {
            'nb_patients': cached['nb_total'],
            'nb_patients_retournes': len(patients),
            'patients': patients,
            'offset': request_data.offset,
            'limit': request_data.limit,
            'session_id': session_id,
            'base': cached['base'],
            'question': cached['question'],
            'temps_ms': elapsed_ms,
            'from_cache': True  # Indicateur que c'est une pagination optimisée
        }
        
        logger.info(f"POST /search/page - {len(patients)} patient(s) en {elapsed_ms}ms (cache hit)")
        
        return resultat
        
    except Exception as e:
        logger.error(f"POST /search/page - ERREUR: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ═══════════════════════════════════════════════════════════════════════════════
# ENDPOINT GET /search/cache/stats - Statistiques du cache (debug)
# ═══════════════════════════════════════════════════════════════════════════════

@app.get("/search/cache/stats")
async def search_cache_stats():
    """Retourne les statistiques du cache de recherche (debug)."""
    now = datetime.now()
    sessions = []
    for session_id, data in SEARCH_CACHE.items():
        age_seconds = (now - data.get('timestamp', now)).total_seconds()
        sessions.append({
            'session_id': session_id[:8] + '...',
            'question': data.get('question', '')[:50],
            'nb_total': data.get('nb_total', 0),
            'age_seconds': int(age_seconds)
        })
    
    # Trier par âge (plus récent en premier)
    sessions.sort(key=lambda x: x['age_seconds'])
    
    return {
        'cache_size': len(SEARCH_CACHE),
        'max_size': SEARCH_CACHE_MAX_SIZE,
        'ttl_minutes': SEARCH_CACHE_TTL_MINUTES,
        'sessions': sessions[:20]  # Limiter l'affichage
    }


# ═══════════════════════════════════════════════════════════════
# ENDPOINT POST /api/rating - Feedback utilisateur
# ═══════════════════════════════════════════════════════════════

def get_search_info_from_log(session_id: str) -> dict:
    """
    Récupère les informations de recherche depuis le fichier de log.
    
    Args:
        session_id: UUID de la session à rechercher
        
    Returns:
        dict avec question, base, nb_patients, mode, temps_ms
    """
    if LOG_RECHERCHE_PATH is None or not LOG_RECHERCHE_PATH.exists():
        return {}
    
    try:
        import csv
        
        with open(LOG_RECHERCHE_PATH, 'r', encoding='utf-8-sig') as f:
            lines = f.readlines()
        
        if len(lines) < 2:
            return {}
        
        # Trouver l'en-tête
        header_idx = -1
        for i, line in enumerate(lines):
            if not line.strip().startswith('#'):
                header_idx = i
                break
        
        if header_idx == -1:
            return {}
        
        header = lines[header_idx].strip().split(';')
        
        # Chercher la ligne avec ce session_id
        for i in range(len(lines) - 1, header_idx, -1):
            if lines[i].strip().startswith('#'):
                continue
            
            cols = lines[i].strip().split(';')
            
            # Trouver l'index de session_id
            try:
                session_col = header.index('session_id')
                if len(cols) > session_col and cols[session_col] == session_id:
                    # Extraire les infos
                    return {
                        'question': cols[header.index('questionoriginale')] if 'questionoriginale' in header else '',
                        'base': cols[header.index('base')] if 'base' in header else '',
                        'nb_patients': cols[header.index('nb_patients')] if 'nb_patients' in header else '',
                        'mode': cols[header.index('mode')] if 'mode' in header else '',
                        'temps_ms': cols[header.index('temps_ms')] if 'temps_ms' in header else ''
                    }
            except (ValueError, IndexError):
                continue
        
        return {}
        
    except Exception as e:
        logger.error(f"Erreur lecture log pour session {session_id}: {e}")
        return {}


@app.post("/api/rating")
async def submit_rating(rating_request: RatingRequest, request: Request):
    """
    Enregistre un feedback utilisateur (pouce haut/bas + commentaire).
    
    Met à jour la ligne correspondante dans logrecherche.csv via session_id.
    Envoie également un email de notification à thierry.oberle@kitview.com.
    """
    if not SEARCH_DISPONIBLE:
        raise HTTPException(status_code=503, detail="Module search.py non disponible")
    
    # Récupérer l'IP du client
    client_ip = get_client_ip(request)
    
    logger.info(f"POST /api/rating - Session: {rating_request.session_id}")
    logger.info(f"                   Rating: {rating_request.rating}")
    if rating_request.type_probleme:
        logger.info(f"                   Type: {rating_request.type_probleme}")
    if rating_request.commentaire:
        logger.info(f"                   Commentaire: {rating_request.commentaire[:50]}...")
    
    # Récupérer les infos de recherche AVANT la mise à jour
    search_info = get_search_info_from_log(rating_request.session_id)
    
    try:
        # Appeler la fonction update_rating de search.py
        succes = update_rating_func(
            session_id=rating_request.session_id,
            rating=rating_request.rating,
            type_probleme=rating_request.type_probleme,
            commentaire=rating_request.commentaire
        )
        
        if succes:
            logger.info(f"POST /api/rating - ✓ Rating enregistré pour session {rating_request.session_id}")
            
            # Envoyer l'email de notification de manière asynchrone
            send_rating_email_async(
                session_id=rating_request.session_id,
                rating=rating_request.rating,
                type_probleme=rating_request.type_probleme,
                commentaire=rating_request.commentaire,
                search_info=search_info
            )
            
            return {
                "status": "ok",
                "message": "Feedback enregistré",
                "session_id": rating_request.session_id,
                "email_sent": EMAIL_CONFIG['enabled'] and bool(EMAIL_CONFIG['smtp_user'])
            }
        else:
            logger.warning(f"POST /api/rating - Session non trouvée: {rating_request.session_id}")
            raise HTTPException(
                status_code=404, 
                detail=f"Session {rating_request.session_id} non trouvée dans les logs"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"POST /api/rating - ERREUR: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ═══════════════════════════════════════════════════════════════
# ENDPOINT GET /api/export-logs - Télécharger les logs
# ═══════════════════════════════════════════════════════════════

@app.get("/api/export-logs")
async def export_logs():
    """
    Retourne le fichier logrecherche.csv complet pour téléchargement.
    """
    if LOG_RECHERCHE_PATH is None or not LOG_RECHERCHE_PATH.exists():
        logger.warning("GET /api/export-logs - Fichier logrecherche.csv introuvable")
        raise HTTPException(status_code=404, detail="Fichier logrecherche.csv introuvable")
    
    logger.info(f"GET /api/export-logs - Téléchargement de {LOG_RECHERCHE_PATH}")
    
    # Retourner le fichier avec un nom explicite
    return FileResponse(
        path=str(LOG_RECHERCHE_PATH),
        filename="logrecherche.csv",
        media_type="text/csv; charset=utf-8-sig"
    )


# ═══════════════════════════════════════════════════════════════
# ENDPOINT POST /ia/cohorte - Analyse de cohorte par IA
# ═══════════════════════════════════════════════════════════════

# Mapping des codes de langue vers les noms complets pour les prompts IA
LANGUES_NOMS = {
    'fr': 'français',
    'en': 'English',
    'de': 'Deutsch',
    'es': 'español',
    'it': 'italiano',
    'ja': '日本語',
    'pt': 'português',
    'pl': 'polski',
    'ro': 'română',
    'th': 'ไทย',
    'ar': 'العربية',
    'cn': '中文'
}

class CohorteRequest(BaseModel):
    """Requête d'analyse de cohorte."""
    moteur: Optional[str] = "gpt4o"
    patients: List[Dict[str, Any]]
    criteres_recherche: str
    nb_total: int
    langue: Optional[str] = "fr"  # Code de langue pour la réponse IA


# ╔════════════════════════════════════════════════════════════════
# ║ MODELS pour les endpoints patient (majpats.html)
# ║ v1.2.1 - 19/02/2026
# ╚════════════════════════════════════════════════════════════════

class ResolveTagsRequest(BaseModel):
    """Requête de résolution de tags via dettags."""
    lines: List[str]

class PatientUpdateRequest(BaseModel):
    """Requête de mise à jour d'un patient."""
    base: str
    id: int
    prenom: str = ""
    nom: str = ""
    sexe: str = "M"
    datenaissance: str = ""
    idportrait: str = ""
    canontags: str = ""
    canonadjs: str = ""
    oripathologies: str = ""


@app.post("/ia/cohorte")
async def analyser_cohorte(request: CohorteRequest):
    """
    Analyse une cohorte de patients via IA.
    
    Args:
    - moteur: Nom court du moteur IA (défaut: gpt4o)
    - patients: Liste des patients (max 50 envoyés au LLM)
    - criteres_recherche: Critères de recherche utilisés
    - nb_total: Nombre total de patients dans la cohorte
    
    Retourne:
    - resume: Texte d'analyse généré par le LLM
    - statistiques: Stats calculées côté serveur (âge moyen, répartition, top pathologies)
    - moteur: Moteur utilisé
    - temps_ms: Temps de réponse en millisecondes
    """
    moteur_name = request.moteur or "gpt4o"
    
    # Trouver la config du moteur
    moteur_config = None
    for m in IA_FULL_CACHE:
        if m['moteur'].lower() == moteur_name.lower():
            moteur_config = m
            break
    
    if not moteur_config:
        # Fallback sur gpt4o
        for m in IA_FULL_CACHE:
            if m['moteur'].lower() == 'gpt4o':
                moteur_config = m
                break
    
    if not moteur_config:
        raise HTTPException(status_code=400, detail="Aucun moteur IA disponible")
    
    via = moteur_config.get('via', 'openai')
    model_complet = moteur_config.get('complet', 'gpt-4o')
    
    # ═══════════════════════════════════════════════════════════════
    # CALCUL DES STATISTIQUES CÔTÉ SERVEUR
    # ═══════════════════════════════════════════════════════════════
    
    patients = request.patients
    nb_total = request.nb_total
    
    # Âge moyen
    ages = [p.get('age') for p in patients if p.get('age') is not None]
    age_moyen = round(sum(ages) / len(ages), 1) if ages else None
    
    # Répartition sexe
    repartition_sexe = {'M': 0, 'F': 0, 'Autre': 0}
    for p in patients:
        sexe = p.get('sexe', '').upper()
        if sexe == 'M':
            repartition_sexe['M'] += 1
        elif sexe == 'F':
            repartition_sexe['F'] += 1
        else:
            repartition_sexe['Autre'] += 1
    
    # Top pathologies
    patho_count = {}
    for p in patients:
        oripathologies = p.get('oripathologies', '') or ''
        if isinstance(oripathologies, str):
            pathos = [x.strip() for x in oripathologies.split(',') if x.strip()]
        else:
            pathos = oripathologies if isinstance(oripathologies, list) else []
        
        for patho in pathos:
            patho_normalized = patho.strip().title()
            patho_count[patho_normalized] = patho_count.get(patho_normalized, 0) + 1
    
    # Trier par fréquence et prendre le top 10
    top_pathologies = sorted(patho_count.items(), key=lambda x: -x[1])[:10]
    pathologies_frequentes = [
        {
            'pathologie': patho,
            'count': count,
            'pct': round(count * 100 / len(patients), 1) if patients else 0
        }
        for patho, count in top_pathologies
    ]
    
    statistiques = {
        'age_moyen': age_moyen,
        'repartition_sexe': repartition_sexe,
        'pathologies_frequentes': pathologies_frequentes,
        'nb_echantillon': len(patients),
        'nb_total': nb_total
    }
    
    # ═══════════════════════════════════════════════════════════════
    # CONSTRUCTION DU PROMPT POUR L'IA
    # ═══════════════════════════════════════════════════════════════
    
    # Limiter à 50 patients maximum pour le prompt
    patients_echantillon = patients[:50]
    
    # Formater la liste des patients pour le prompt
    patients_resume = []
    for i, p in enumerate(patients_echantillon[:20], 1):  # Max 20 détaillés
        age = p.get('age', 'N/A')
        sexe = 'H' if p.get('sexe', '').upper() == 'M' else 'F' if p.get('sexe', '').upper() == 'F' else '?'
        pathologies = p.get('oripathologies', 'N/A')
        patients_resume.append(f"{i}. {sexe}, {age} ans : {pathologies}")
    
    # Formater le top pathologies pour le prompt
    top_patho_str = ', '.join([f"{p['pathologie']} ({p['pct']}%)" for p in pathologies_frequentes[:5]])
    
    # Déterminer la langue de réponse
    langue_code = request.langue or 'fr'
    langue_nom = LANGUES_NOMS.get(langue_code, 'français')
    
    prompt_systeme = f"""Tu es un assistant médical spécialisé en orthodontie.
Tu analyses une cohorte de {nb_total} patients correspondant à la recherche "{request.criteres_recherche}".

DONNÉES DE LA COHORTE :
- Âge moyen : {age_moyen or 'N/A'} ans
- Répartition : {repartition_sexe['M']} hommes, {repartition_sexe['F']} femmes
- Pathologies les plus fréquentes : {top_patho_str}

ÉCHANTILLON DE PATIENTS ({len(patients_resume)} sur {nb_total}) :
{chr(10).join(patients_resume)}

INSTRUCTIONS :
1. Fournis un résumé synthétique de la cohorte (3-5 phrases)
2. Identifie les tendances ou corrélations notables
3. Suggère des points d'attention cliniques
4. Si pertinent, compare avec les normes orthodontiques

IMPORTANT : Réponds UNIQUEMENT en {langue_nom}, de manière professionnelle et concise."""

    prompt_utilisateur = f"Analyse cette cohorte de {nb_total} patients trouvés avec les critères : {request.criteres_recherche}"
    
    start_time = time.time()
    
    try:
        if via == 'openai':
            reponse_texte = await _appeler_openai(prompt_systeme, prompt_utilisateur, model_complet)
        else:
            reponse_texte = await _appeler_eden(prompt_systeme, prompt_utilisateur, model_complet)
        
        temps_ms = round((time.time() - start_time) * 1000)
        
        logger.info(f"POST /ia/cohorte - moteur={moteur_name}, patients={nb_total}, langue={langue_code}, temps={temps_ms}ms")
        return {
            "resume": reponse_texte,
            "statistiques": statistiques,
            "moteur": moteur_name,
            "temps_ms": temps_ms
        }
        
    except Exception as e:
        logger.error(f"POST /ia/cohorte - Erreur: {e}")
        raise HTTPException(status_code=500, detail=f"Erreur analyse cohorte: {e}")


# ═══════════════════════════════════════════════════════════════
# ENDPOINTS MODE D'EMPLOI - Help avec traduction lazy et cache versionné
# ═══════════════════════════════════════════════════════════════

# Cache pour les traductions en cours de génération
HELP_TRANSLATIONS_IN_PROGRESS = set()

# Répertoire de cache des traductions
IHM_CACHE_DIR = None  # Initialisé dans lifespan

# Mapping des codes de langue pour DeepL
DEEPL_LANG_MAPPING = {
    'en': 'EN-GB',
    'de': 'DE',
    'es': 'ES',
    'it': 'IT',
    'pt': 'PT-PT',
    'pl': 'PL',
    'ro': 'RO',
    'th': 'TH',  # Non supporté par DeepL - sera ignoré
    'ar': 'AR',
    'cn': 'ZH'
}


def _get_source_version() -> str:
    """
    Extrait la version du fichier source modedemploi.html.
    Lit la balise <meta name="help-version" content="X.Y.Z">
    """
    source_path = SCRIPT_DIR / "modedemploi.html"
    if not source_path.exists():
        return "0.0.0"
    
    try:
        with open(source_path, 'r', encoding='utf-8') as f:
            # Lire seulement le début du fichier (les meta sont en haut)
            head = f.read(2000)
        
        match = re.search(r'<meta\s+name="help-version"\s+content="([^"]+)"', head)
        if match:
            return match.group(1)
        return "0.0.0"
    except Exception as e:
        logger.warning(f"Impossible de lire la version du mode d'emploi: {e}")
        return "0.0.0"


def _load_versions_cache() -> dict:
    """
    Charge le fichier help_versions.json depuis /ihm.
    """
    if IHM_CACHE_DIR is None:
        return {"source_version": "0.0.0", "translations": {}}
    
    versions_path = IHM_CACHE_DIR / "help_versions.json"
    if not versions_path.exists():
        return {"source_version": "0.0.0", "translations": {}}
    
    try:
        with open(versions_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        logger.warning(f"Erreur lecture help_versions.json: {e}")
        return {"source_version": "0.0.0", "translations": {}}


def _save_versions_cache(cache: dict):
    """
    Sauvegarde le fichier help_versions.json dans /ihm.
    """
    if IHM_CACHE_DIR is None:
        return
    
    versions_path = IHM_CACHE_DIR / "help_versions.json"
    try:
        with open(versions_path, 'w', encoding='utf-8') as f:
            json.dump(cache, f, indent=2, ensure_ascii=False)
    except Exception as e:
        logger.error(f"Erreur sauvegarde help_versions.json: {e}")


def _is_translation_up_to_date(lang: str) -> bool:
    """
    Vérifie si la traduction pour une langue est à jour.
    Compare la version du source avec la version traduite.
    """
    source_version = _get_source_version()
    cache = _load_versions_cache()
    
    if lang not in cache.get("translations", {}):
        return False
    
    cached_version = cache["translations"][lang].get("version", "0.0.0")
    return cached_version == source_version


@app.get("/help")
async def serve_help():
    """Sert la page du mode d'emploi (modedemploi.html)."""
    help_path = SCRIPT_DIR / "modedemploi.html"
    if help_path.exists():
        return FileResponse(help_path)
    raise HTTPException(status_code=404, detail="Page modedemploi.html non trouvée")


@app.get("/help/{lang}")
async def serve_help_translated(lang: str):
    """
    Sert la page du mode d'emploi traduite depuis le cache /ihm.
    
    Args:
        lang: Code de la langue (en, de, es, it, pt, pl, ro, th, ar, cn)
    """
    # Français = page de base
    if lang == 'fr':
        return await serve_help()
    
    # Vérifier si la traduction existe dans /ihm
    if IHM_CACHE_DIR is None:
        raise HTTPException(status_code=500, detail="Répertoire /ihm non configuré")
    
    translated_path = IHM_CACHE_DIR / f"modedemploi_{lang}.html"
    if translated_path.exists():
        return FileResponse(translated_path)
    
    # Sinon 404 - la traduction doit être générée via /api/help/translate/{lang}
    raise HTTPException(
        status_code=404, 
        detail=f"Traduction {lang} non disponible. Utilisez /api/help/translate/{lang} pour la générer."
    )


@app.get("/api/help/translate/{lang}")
async def translate_help(lang: str):
    """
    Traduit le mode d'emploi vers la langue demandée (lazy loading avec cache versionné).
    
    - Si la traduction existe et est à jour → retourne le chemin
    - Si la traduction est obsolète ou inexistante → génère via DeepL
    - Les traductions sont stockées dans /ihm avec versioning
    
    Args:
        lang: Code de la langue cible (en, de, es, it, pt, pl, ro, ar, cn)
    
    Returns:
        - status: 'ok' si traduction disponible, 'generating' si en cours
        - file: Chemin du fichier traduit
        - version: Version du fichier
        - cached: True si servi depuis le cache
    """
    global HELP_TRANSLATIONS_IN_PROGRESS
    
    # Valider la langue
    valid_langs = ['en', 'de', 'es', 'it', 'pt', 'pl', 'ro', 'th', 'ar', 'cn']
    if lang not in valid_langs:
        raise HTTPException(status_code=400, detail=f"Langue non supportée: {lang}. Valides: {valid_langs}")
    
    # Français = pas de traduction nécessaire
    if lang == 'fr':
        return {"status": "ok", "file": "modedemploi.html", "version": _get_source_version(), "cached": False}
    
    # Vérifier le répertoire cache
    if IHM_CACHE_DIR is None:
        raise HTTPException(status_code=500, detail="Répertoire /ihm non configuré")
    
    translated_filename = f"modedemploi_{lang}.html"
    translated_path = IHM_CACHE_DIR / translated_filename
    source_version = _get_source_version()
    
    # Vérifier si la traduction existe ET est à jour
    if translated_path.exists() and _is_translation_up_to_date(lang):
        cache = _load_versions_cache()
        cached_info = cache.get("translations", {}).get(lang, {})
        logger.info(f"GET /api/help/translate/{lang} - Cache OK (v{source_version})")
        return {
            "status": "ok", 
            "file": f"ihm/{translated_filename}", 
            "version": source_version,
            "cached": True,
            "translated_date": cached_info.get("date", "")
        }
    
    # Vérifier si une traduction est en cours
    if lang in HELP_TRANSLATIONS_IN_PROGRESS:
        logger.info(f"GET /api/help/translate/{lang} - Traduction en cours")
        return {"status": "generating", "file": f"ihm/{translated_filename}", "message": "Traduction en cours..."}
    
    # Vérifier que DeepL est configuré
    if not DEEPL_API_KEY:
        logger.warning(f"GET /api/help/translate/{lang} - DeepL non configuré")
        raise HTTPException(
            status_code=503, 
            detail="Service de traduction non configuré (clé DeepL manquante)"
        )
    
    # Vérifier que le fichier source existe
    source_path = SCRIPT_DIR / "modedemploi.html"
    if not source_path.exists():
        raise HTTPException(status_code=404, detail="Fichier source modedemploi.html non trouvé")
    
    # Lancer la traduction en arrière-plan
    HELP_TRANSLATIONS_IN_PROGRESS.add(lang)
    
    def _translate_async():
        try:
            _generate_translation(lang, source_path, translated_path, source_version)
        finally:
            HELP_TRANSLATIONS_IN_PROGRESS.discard(lang)
    
    thread = threading.Thread(target=_translate_async)
    thread.daemon = True
    thread.start()
    
    reason = "nouvelle" if not translated_path.exists() else "mise à jour"
    logger.info(f"GET /api/help/translate/{lang} - Traduction {reason} lancée (v{source_version})")
    return {"status": "generating", "file": f"ihm/{translated_filename}", "message": f"Traduction {reason} en cours..."}


@app.get("/api/help/versions")
async def get_help_versions():
    """
    Retourne l'état du cache des traductions.
    
    Returns:
        - source_version: Version actuelle du fichier source
        - translations: État de chaque traduction (version, date, taille, up_to_date)
    """
    source_version = _get_source_version()
    cache = _load_versions_cache()
    
    # Enrichir avec le statut up_to_date
    result = {
        "source_version": source_version,
        "translations": {}
    }
    
    for lang, info in cache.get("translations", {}).items():
        result["translations"][lang] = {
            **info,
            "up_to_date": info.get("version") == source_version
        }
    
    return result


def _generate_translation(lang: str, source_path: Path, target_path: Path, source_version: str):
    """
    Génère la traduction du mode d'emploi via DeepL et met à jour le cache.
    """
    try:
        logger.info(f"Début traduction mode d'emploi vers {lang} (v{source_version})")
        start_time = time.time()
        
        # Lire le fichier source
        with open(source_path, 'r', encoding='utf-8') as f:
            html_content = f.read()
        
        # Extraire les parties à traduire (contenu textuel visible)
        translated_html = _translate_html_content(html_content, lang)
        
        # Mettre à jour les métadonnées de la page
        translated_html = translated_html.replace(
            '<html lang="fr">',
            f'<html lang="{lang}">'
        )
        
        # Mettre à jour le commentaire de version
        translated_html = re.sub(
            r'\* modedemploi\.html V[\d.]+',
            f'* modedemploi_{lang}.html V{source_version} - Traduit automatiquement',
            translated_html
        )
        
        # Sauvegarder le fichier traduit
        with open(target_path, 'w', encoding='utf-8') as f:
            f.write(translated_html)
        
        # Mettre à jour le cache des versions
        cache = _load_versions_cache()
        cache["source_version"] = source_version
        if "translations" not in cache:
            cache["translations"] = {}
        
        cache["translations"][lang] = {
            "version": source_version,
            "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "size": len(translated_html)
        }
        _save_versions_cache(cache)
        
        elapsed = time.time() - start_time
        logger.info(f"Traduction mode d'emploi vers {lang} terminée en {elapsed:.1f}s ({len(translated_html)} octets)")
        
    except Exception as e:
        logger.error(f"Erreur traduction mode d'emploi vers {lang}: {e}")
        # Supprimer le fichier partiel s'il existe
        if target_path.exists():
            target_path.unlink()


def _translate_html_content(html: str, target_lang: str) -> str:
    """
    Traduit le contenu textuel d'un document HTML via DeepL.
    
    Préserve la structure HTML et ne traduit que le texte visible.
    """
    # DeepL supporte le format HTML nativement
    deepl_lang = DEEPL_LANG_MAPPING.get(target_lang, target_lang.upper())
    
    # Trouver le contenu du body
    body_match = re.search(r'(<body[^>]*>)(.*?)(</body>)', html, re.DOTALL)
    if not body_match:
        logger.warning("Pas de balise <body> trouvée dans le HTML")
        return html
    
    body_start = body_match.group(1)
    body_content = body_match.group(2)
    body_end = body_match.group(3)
    
    # Séparer le contenu en parties traduisibles et non traduisibles
    # Les scripts ne doivent pas être traduits
    parts = re.split(r'(<script[^>]*>.*?</script>)', body_content, flags=re.DOTALL)
    
    translated_parts = []
    for part in parts:
        if part.strip().startswith('<script'):
            # Ne pas traduire les scripts
            translated_parts.append(part)
        elif part.strip():
            # Traduire le contenu HTML
            translated_part = _call_deepl_translate(part, deepl_lang)
            translated_parts.append(translated_part)
        else:
            translated_parts.append(part)
    
    # Reconstruire le HTML
    translated_body = ''.join(translated_parts)
    translated_html = html.replace(body_content, translated_body)
    
    return translated_html


def _call_deepl_translate(text: str, target_lang: str) -> str:
    """
    Appelle l'API DeepL pour traduire du texte/HTML.
    
    Args:
        text: Texte ou HTML à traduire
        target_lang: Code langue DeepL (EN-GB, DE, ES, etc.)
    
    Returns:
        Texte traduit
    """
    if not text.strip():
        return text
    
    # Limiter la taille (DeepL accepte jusqu'à ~128KB par requête)
    if len(text) > 100000:
        # Diviser en morceaux
        chunks = _split_html_safely(text, 50000)
        translated_chunks = [_call_deepl_translate(chunk, target_lang) for chunk in chunks]
        return ''.join(translated_chunks)
    
    try:
        # Déterminer l'URL de l'API DeepL (free ou pro)
        if ':fx' in DEEPL_API_KEY:
            api_url = "https://api-free.deepl.com/v2/translate"
        else:
            api_url = "https://api.deepl.com/v2/translate"
        
        response = requests.post(
            api_url,
            data={
                'auth_key': DEEPL_API_KEY,
                'text': text,
                'source_lang': 'FR',
                'target_lang': target_lang,
                'tag_handling': 'html',
                'preserve_formatting': '1'
            },
            timeout=60
        )
        
        if response.status_code == 200:
            result = response.json()
            if 'translations' in result and result['translations']:
                return result['translations'][0]['text']
            else:
                logger.warning(f"DeepL: réponse inattendue: {result}")
                return text
        else:
            logger.error(f"DeepL API error {response.status_code}: {response.text[:200]}")
            return text
            
    except requests.exceptions.Timeout:
        logger.error("DeepL API timeout")
        return text
    except Exception as e:
        logger.error(f"DeepL API error: {e}")
        return text


def _split_html_safely(html: str, max_size: int) -> list:
    """
    Divise du HTML en morceaux sans couper au milieu des balises.
    """
    chunks = []
    current = ""
    
    # Diviser par paragraphes/sections
    parts = re.split(r'(</(?:p|div|section|h[1-6]|li|tr)>)', html)
    
    for part in parts:
        if len(current) + len(part) > max_size and current:
            chunks.append(current)
            current = part
        else:
            current += part
    
    if current:
        chunks.append(current)
    
    return chunks


# ═══════════════════════════════════════════════════════════════
# ENDPOINTS ANALYSE - Dashboard d'analyse des logs
# ═══════════════════════════════════════════════════════════════

@app.get("/analyse")
async def serve_analyse():
    """Sert la page d'analyse (analyse12.html)."""
    analyse_path = SCRIPT_DIR / "analyse12.html"
    if analyse_path.exists():
        return FileResponse(analyse_path)
    raise HTTPException(status_code=404, detail="Page analyse12.html non trouvée")


@app.get("/analyse/search-comment")
async def analyse_search_comment(q: str, limit: int = 100):
    """
    Recherche fulltext dans les commentaires des logs.
    Insensible à la casse et aux accents.
    
    Paramètres:
    - q: Texte à rechercher
    - limit: Nombre max de résultats (défaut: 100)
    """
    if not ANALYSE_DISPONIBLE:
        raise HTTPException(status_code=503, detail="Module analyse non disponible")
    
    if not q:
        raise HTTPException(status_code=400, detail="Paramètre 'q' requis")
    
    data = analyse_search_commentaires(q, limit=limit)
    logger.info(f"GET /analyse/search-comment?q={q[:20]}... - {data.get('total', 0)} résultat(s)")
    return data


@app.get("/analyse/stats")
async def analyse_stats():
    """
    Retourne les statistiques globales des logs de recherche.
    """
    if not ANALYSE_DISPONIBLE:
        raise HTTPException(status_code=503, detail="Module analyse non disponible")
    
    stats = analyse_get_stats()
    logger.info(f"GET /analyse/stats - {stats.get('total_recherches', 0)} recherches")
    return stats


@app.get("/analyse/recherches")
async def analyse_recherches(
    offset: int = 0,
    limit: int = 20,
    rating: str = None,
    date_debut: str = None,
    date_fin: str = None,
    q: str = None,
    mode: str = None,
    erreur: bool = None,
    type_probleme: str = None
):
    """
    Liste paginée des recherches avec filtres.
    
    Paramètres:
    - offset: Index de départ (défaut: 0)
    - limit: Nombre de résultats (défaut: 20, max: 10000)
    - rating: Filtrer par rating (👍, 👎, null, all)
    - date_debut: Date de début (AAAA-MM-JJ)
    - date_fin: Date de fin (AAAA-MM-JJ)
    - q: Recherche texte dans la question
    - mode: Mode de recherche (standard, ia)
    - erreur: Avec/sans erreur (true/false)
    - type_probleme: Type de problème
    """
    if not ANALYSE_DISPONIBLE:
        raise HTTPException(status_code=503, detail="Module analyse non disponible")
    
    # Valider limit
    if limit > 10000:
        limit = 10000
    
    data = analyse_get_recherches(
        offset=offset,
        limit=limit,
        rating=rating,
        date_debut=date_debut,
        date_fin=date_fin,
        q=q,
        mode=mode,
        erreur=erreur,
        type_probleme=type_probleme
    )
    
    logger.info(f"GET /analyse/recherches - offset={offset}, limit={limit}, total={data.get('total', 0)}")
    return data


@app.get("/analyse/recherche/{session_id}")
async def analyse_recherche_detail(session_id: str):
    """
    Détail complet d'une recherche par son session_id.
    """
    if not ANALYSE_DISPONIBLE:
        raise HTTPException(status_code=503, detail="Module analyse non disponible")
    
    detail = analyse_get_detail(session_id)
    
    if not detail:
        logger.warning(f"GET /analyse/recherche/{session_id} - Non trouvée")
        raise HTTPException(status_code=404, detail="Recherche non trouvée")
    
    logger.info(f"GET /analyse/recherche/{session_id} - OK")
    return detail


@app.get("/analyse/similaires/{session_id}")
async def analyse_similaires(
    session_id: str,
    by: str = "session",
    limit: int = 20
):
    """
    Recherches similaires à une session donnée.
    
    Paramètres:
    - session_id: Session de référence
    - by: Critère de similarité (session, ip, ia)
    - limit: Nombre max de résultats (défaut: 20)
    """
    if not ANALYSE_DISPONIBLE:
        raise HTTPException(status_code=503, detail="Module analyse non disponible")
    
    if by not in ('session', 'ip', 'ia'):
        raise HTTPException(status_code=400, detail="Critère invalide (session, ip, ia)")
    
    data = analyse_get_similaires(
        session_id=session_id,
        by=by,
        limit=limit
    )
    
    logger.info(f"GET /analyse/similaires/{session_id}?by={by} - {data.get('total', 0)} résultat(s)")
    return data


@app.get("/analyse/ia-summary")
async def analyse_ia_summary():
    """
    Analyse IA des logs de recherche.
    
    Génère une analyse automatique avec recommandations.
    """
    if not ANALYSE_DISPONIBLE:
        raise HTTPException(status_code=503, detail="Module analyse non disponible")
    
    # Récupérer le moteur IA actif depuis le cache
    ia_model = 'gpt4o'  # Défaut
    for m in IA_FULL_CACHE:
        if m.get('actif') == 'O' and m.get('moteur') != 'standard':
            ia_model = m.get('moteur', 'gpt4o')
            break
    
    data = analyse_get_ia_summary(ia_model=ia_model)
    logger.info(f"GET /analyse/ia-summary - moteur={ia_model}, {data.get('donnees_analysees', 0)} logs analysés")
    return data


@app.get("/analyse/export")
async def analyse_export(
    rating: str = None,
    date_debut: str = None,
    date_fin: str = None,
    q: str = None,
    mode: str = None,
    erreur: bool = None,
    type_probleme: str = None
):
    """
    Export CSV des logs filtrés.
    
    Retourne un fichier CSV en téléchargement.
    """
    if not ANALYSE_DISPONIBLE:
        raise HTTPException(status_code=503, detail="Module analyse non disponible")
    
    # Créer un fichier temporaire
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, encoding='utf-8-sig') as f:
        temp_path = f.name
    
    chemin, nb = analyse_export_csv(
        output_path=temp_path,
        rating=rating,
        date_debut=date_debut,
        date_fin=date_fin,
        q=q,
        mode=mode,
        erreur=erreur,
        type_probleme=type_probleme
    )
    
    if nb == 0:
        logger.warning("GET /analyse/export - Aucune donnée à exporter")
        raise HTTPException(status_code=404, detail="Aucune donnée à exporter")
    
    # Lire et retourner le fichier
    def iterfile():
        with open(temp_path, 'rb') as f:
            yield from f
        os.unlink(temp_path)
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f"export_analyse_{timestamp}.csv"
    
    logger.info(f"GET /analyse/export - {nb} lignes exportées")
    
    return StreamingResponse(
        iterfile(),
        media_type='text/csv; charset=utf-8-sig',
        headers={
            'Content-Disposition': f'attachment; filename="{filename}"'
        }
    )


# ═══════════════════════════════════════════════════════════════
# ENDPOINTS PHOTOFIT UPLOAD - Recherche par image
# ═══════════════════════════════════════════════════════════════


@app.post("/photofit/search-by-image")
async def photofit_search_by_image(
    img: UploadFile = File(...),
    base: str = Form("base1000.db"),
    score_min: int = Form(None),        # Override communb.csv (ex: 1)
    max_results: int = Form(None),      # Override communb.csv (ex: 3)
):
    """
    Recherche de portraits similaires à partir d'une image uploadée.

    1. Envoie l'image à l'API Photofit pour extraire les embeddings
    2. Recherche dans photofit.db + prospects.db
    3. Enrichit avec les infos patients depuis baseN.db
    4. Retourne les résultats triés par score

    Paramètres (multipart/form-data) :
    - img : Fichier image (jpg, png, webp, bmp)
    - base : Nom de la base patients active (défaut: base1000.db)
    - score_min : Score minimum (override communb.csv, optionnel)
    - max_results : Nombre max de résultats (override communb.csv, optionnel)

    Retourne :
    {
        "resultats": [...],
        "nb_resultats": int,
        "temps_ms": int,
        "hair_embedding": [...],
        "face_embedding": [...],
        "attributes": [...]
    }
    """
    if not PHOTOFIT_UPLOAD_DISPONIBLE:
        raise HTTPException(status_code=503,
                            detail="Module photofit_upload non disponible")

    # Vérifier l'extension
    ext = Path(img.filename).suffix.lower()
    if ext not in {'.jpg', '.jpeg', '.png', '.bmp', '.webp'}:
        raise HTTPException(status_code=400,
                            detail=f"Format non supporté : {ext}. "
                                   f"Acceptés : jpg, png, webp, bmp")

    # Lire le contenu
    image_bytes = await img.read()
    if len(image_bytes) == 0:
        raise HTTPException(status_code=400, detail="Fichier image vide")

    if len(image_bytes) > 10 * 1024 * 1024:  # 10 Mo max
        raise HTTPException(status_code=400,
                            detail="Image trop volumineuse (max 10 Mo)")

    logger.info(f"POST /photofit/search-by-image - {img.filename} "
                f"({len(image_bytes)} bytes), base={base}")

    start_time = datetime.now()

    # Étape 1 : Extraire les features via API Photofit
    features, error = photofit_extraire_features(
        image_bytes, img.filename, verbose=False, debug=False
    )

    if error:
        logger.error(f"  ❌ Erreur API Photofit : {error}")
        raise HTTPException(status_code=502,
                            detail=f"Erreur API Photofit : {error}")

    elapsed_api = int((datetime.now() - start_time).total_seconds() * 1000)
    logger.info(f"  ✓ Features extraites en {elapsed_api}ms "
                f"(hair={len(features['hair_embedding'])}, "
                f"face={len(features.get('face_embedding', []))})")

    # Étape 2 : Rechercher les similaires (avec overrides éventuels)
    config_override = None
    if score_min is not None or max_results is not None:
        config_override = photofit_lire_config(debug=False).copy()
        if score_min is not None:
            config_override['score_min'] = score_min
        if max_results is not None:
            config_override['max_results'] = max_results
        logger.info(f"  → Overrides: score_min={config_override['score_min']}, "
                    f"max_results={config_override['max_results']}")

    resultats = photofit_rechercher(
        hair_embedding=features['hair_embedding'],
        face_embedding=features.get('face_embedding', []),
        config=config_override,
        verbose=False, debug=False
    )

    # Étape 3 : Enrichir avec les infos patients
    db_path = BASES_DIR / base if BASES_DIR else Path(base)
    if not db_path.exists():
        logger.warning(f"  ⚠️  Base {base} introuvable, enrichissement limité")

    resultats = photofit_enrichir(
        resultats=resultats,
        base_path=db_path,
        portraits_cache=PORTRAITS_CACHE,
        debug=False
    )

    elapsed_total = int((datetime.now() - start_time).total_seconds() * 1000)

    nb_photofit = sum(1 for r in resultats if r['source'] == 'photofit')
    nb_prospects = sum(1 for r in resultats if r['source'] == 'prospect')
    logger.info(f"  ✓ {len(resultats)} résultat(s) en {elapsed_total}ms "
                f"({nb_photofit} patients, {nb_prospects} prospects)")

    return {
        "resultats": resultats,
        "nb_resultats": len(resultats),
        "temps_ms": elapsed_total,
        "temps_api_ms": elapsed_api,
        # Renvoyer les embeddings pour un éventuel save-prospect
        "hair_embedding": features['hair_embedding'],
        "face_embedding": features.get('face_embedding', []),
        "attributes": features.get('attributes', []),
    }


@app.post("/photofit/save-prospect")
async def photofit_save_prospect(
    img: UploadFile = File(...),
    prenom: str = Form(...),
    nom: str = Form(...),
    sexe: str = Form(""),
    age: float = Form(None),
    tags: str = Form("prospect"),
    hair_embedding: str = Form(...),     # JSON array stringifié
    face_embedding: str = Form("[]"),    # JSON array stringifié
    attributes: str = Form("[]"),        # JSON array stringifié
):
    """
    Sauvegarde un prospect dans prospects.db avec sa photo.

    Les embeddings sont passés en JSON stringifié pour éviter de
    rappeler l'API Photofit (ils ont déjà été calculés par search-by-image).

    Paramètres (multipart/form-data) :
    - img : Fichier image
    - prenom, nom : Obligatoires
    - sexe, age, tags : Optionnels
    - hair_embedding, face_embedding, attributes : JSON arrays (de search-by-image)
    """
    if not PHOTOFIT_UPLOAD_DISPONIBLE:
        raise HTTPException(status_code=503,
                            detail="Module photofit_upload non disponible")

    # Valider les champs obligatoires
    if not prenom or not prenom.strip():
        raise HTTPException(status_code=400, detail="Prénom obligatoire")
    if not nom or not nom.strip():
        raise HTTPException(status_code=400, detail="Nom obligatoire")

    # Parser les embeddings JSON
    try:
        hair_emb = json.loads(hair_embedding)
        face_emb = json.loads(face_embedding)
        attrs = json.loads(attributes)
    except json.JSONDecodeError as e:
        raise HTTPException(status_code=400,
                            detail=f"Embeddings JSON invalides : {e}")

    if not hair_emb:
        raise HTTPException(status_code=400,
                            detail="hair_embedding requis (appeler search-by-image d'abord)")

    # Lire la photo
    image_bytes = await img.read()
    if len(image_bytes) == 0:
        raise HTTPException(status_code=400, detail="Fichier image vide")

    logger.info(f"POST /photofit/save-prospect - {prenom} {nom}, "
                f"{img.filename} ({len(image_bytes)} bytes)")

    # Construire le dict features
    features = {
        'attributes': attrs,
        'hair_embedding': hair_emb,
        'face_embedding': face_emb,
    }

    # Sauvegarder
    try:
        result = photofit_sauver_prospect(
            prenom=prenom.strip(),
            nom=nom.strip(),
            photo_bytes=image_bytes,
            photo_filename=img.filename,
            features=features,
            sexe=sexe.strip(),
            age=age,
            tags=tags.strip() if tags else "prospect",
            verbose=False, debug=False
        )

        logger.info(f"  ✓ Prospect #{result['id']} sauvegardé : "
                    f"{result['prenom']} {result['nom']}")

        return {
            "success": True,
            "prospect": result,
        }

    except Exception as e:
        logger.error(f"  ❌ Erreur sauvegarde prospect : {e}")
        raise HTTPException(status_code=500,
                            detail=f"Erreur sauvegarde : {str(e)}")


@app.get("/photofit/prospects")
async def photofit_get_prospects():
    """
    Retourne la liste des prospects enregistrés.
    """
    if not PHOTOFIT_UPLOAD_DISPONIBLE:
        raise HTTPException(status_code=503,
                            detail="Module photofit_upload non disponible")

    prospects = photofit_lister_prospects(verbose=False)
    stats = photofit_stats_prospects()

    logger.info(f"GET /photofit/prospects - {len(prospects)} prospect(s)")

    return {
        "prospects": prospects,
        "total": stats.get('total', 0),
    }


@app.delete("/photofit/prospects/{prospect_id}")
async def photofit_delete_prospect_endpoint(prospect_id: int):
    """
    Supprime un prospect par son ID (base + photo sur disque).

    Retourne : {"success": true, "id": int, "photo_deleted": bool}
    """
    if not PHOTOFIT_UPLOAD_DISPONIBLE:
        raise HTTPException(status_code=503,
                            detail="Module photofit_upload non disponible")

    result = photofit_supprimer_prospect(
        prospect_id, verbose=False, debug=False
    )

    if not result['success']:
        raise HTTPException(status_code=404,
                            detail=result.get('error', 'Erreur suppression'))

    logger.info(f"DELETE /photofit/prospects/{prospect_id} - OK "
                f"(photo_deleted={result['photo_deleted']})")

    return result


@app.post("/photofit/search-by-prospect-id")
async def photofit_search_by_prospect_id_endpoint(
    prospect_id: int = Form(...),
    base: str = Form("base1964.db"),
    score_min: int = Form(None),
    max_results: int = Form(None),
):
    """
    Recherche de portraits similaires à partir d'un prospect existant.

    Utilise les embeddings déjà stockés dans prospects.db → pas d'appel API Photofit.

    Paramètres (multipart/form-data) :
    - prospect_id : ID du prospect source
    - base : Nom de la base patients active
    - score_min : Score minimum (override, optionnel)
    - max_results : Nombre max de résultats (override, optionnel)

    Retourne le même format que /photofit/search-by-image + infos du prospect source.
    """
    if not PHOTOFIT_UPLOAD_DISPONIBLE:
        raise HTTPException(status_code=503,
                            detail="Module photofit_upload non disponible")

    # Récupérer le prospect avec ses embeddings
    prospect = photofit_get_prospect_by_id(prospect_id)
    if not prospect:
        raise HTTPException(status_code=404,
                            detail=f"Prospect #{prospect_id} introuvable")

    if not prospect['hair_embedding']:
        raise HTTPException(status_code=400,
                            detail=f"Prospect #{prospect_id} sans embeddings")

    start_time = datetime.now()

    logger.info(f"POST /photofit/search-by-prospect-id - "
                f"prospect #{prospect_id} ({prospect['prenom']} {prospect['nom']}), "
                f"base={base}")

    # Config avec overrides éventuels
    config_override = None
    if score_min is not None or max_results is not None:
        config_override = photofit_lire_config(debug=False).copy()
        if score_min is not None:
            config_override['score_min'] = score_min
        if max_results is not None:
            config_override['max_results'] = max_results

    # Rechercher les similaires (pas d'appel API Photofit)
    resultats = photofit_rechercher(
        hair_embedding=prospect['hair_embedding'],
        face_embedding=prospect['face_embedding'],
        config=config_override,
        verbose=False, debug=False
    )

    # Enrichir avec les infos patients
    db_path = BASES_DIR / base if BASES_DIR else Path(base)
    if not db_path.exists():
        logger.warning(f"  ⚠️  Base {base} introuvable, enrichissement limité")

    resultats = photofit_enrichir(
        resultats=resultats,
        base_path=db_path,
        portraits_cache=PORTRAITS_CACHE,
        debug=False
    )

    elapsed_total = int((datetime.now() - start_time).total_seconds() * 1000)

    nb_photofit = sum(1 for r in resultats if r['source'] == 'photofit')
    nb_prospects = sum(1 for r in resultats if r['source'] == 'prospect')
    logger.info(f"  ✓ {len(resultats)} résultat(s) en {elapsed_total}ms "
                f"({nb_photofit} patients, {nb_prospects} prospects)")

    return {
        "resultats": resultats,
        "nb_resultats": len(resultats),
        "temps_ms": elapsed_total,
        "temps_api_ms": 0,
        "prospect_source": {
            "id": prospect['id'],
            "prenom": prospect['prenom'],
            "nom": prospect['nom'],
            "photo_url": prospect['photo_url'],
        },
        "hair_embedding": prospect['hair_embedding'],
        "face_embedding": prospect['face_embedding'],
        "attributes": prospect['attributes'],
    }


# ═══════════════════════════════════════════════════════════════
# POINT D'ENTRÉE
# ═══════════════════════════════════════════════════════════════

# ═══════════════════════════════════════════════════════════════
# ENDPOINT EXEMPLES DE RECHERCHE
# ═══════════════════════════════════════════════════════════════

@app.get("/exemples")
async def get_exemples():
    """
    Retourne la liste des exemples de recherche depuis refs/exemples.csv.
    
    Format du fichier : une question par ligne, lignes commençant par # ignorées.
    """
    csv_path = REFS_DIR / "exemples.csv"
    exemples = []
    
    try:
        with open(csv_path, 'r', encoding='utf-8-sig') as f:
            for line in f:
                line = line.strip()
                # Ignorer les lignes vides et les commentaires (#)
                if line and not line.startswith('#'):
                    exemples.append(line)
        
        logger.info(f"GET /exemples - {len(exemples)} exemples chargés depuis {csv_path}")
        
    except FileNotFoundError:
        logger.warning(f"GET /exemples - Fichier {csv_path} non trouvé, fallback par défaut")
        exemples = ["patients qui grincent des dents"]
    except Exception as e:
        logger.error(f"GET /exemples - Erreur lecture {csv_path}: {e}")
        exemples = ["patients qui grincent des dents"]
    
    return {"exemples": exemples}


# ╔════════════════════════════════════════════════════════════════════════
# ║ ENDPOINTS MODIFICATION PATIENT (majpats.html) - v1.2.1
# ║ GET  /patient              - Lire un patient par ID
# ║ POST /patient/resolve-tags - Résoudre les tags via dettags
# ║ PUT  /patient/update       - Mettre à jour un patient + recalcul index
# ╚════════════════════════════════════════════════════════════════════════

@app.get("/patient")
async def get_patient(base: str, id: int):
    """
    Retourne toutes les colonnes d'un patient.
    Paramètres URL : ?base=base10.db&id=10002
    """
    if BASES_DIR is None:
        raise HTTPException(status_code=500, detail="Dossier bases/ non configuré")
    
    db_path = BASES_DIR / base
    if not db_path.exists():
        raise HTTPException(status_code=404, detail=f"Base {base} introuvable")
    
    try:
        conn = sqlite3.connect(str(db_path))
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM patients WHERE id = ?", (id,))
        row = cursor.fetchone()
        conn.close()
        
        if not row:
            raise HTTPException(status_code=404, detail=f"Patient {id} introuvable dans {base}")
        
        patient = dict(row)
        logger.info(f"GET /patient - base={base} id={id} → {patient.get('prenom', '')} {patient.get('nom', '')}")
        return patient
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lecture patient: {e}")


@app.post("/patient/resolve-tags")
async def resolve_tags(request_data: ResolveTagsRequest):
    """
    Résout une liste de lignes texte (tag + adjectifs) en formes canoniques
    via le module dettags.
    
    Entrée : { "lines": ["béance antérieure sévère", "macrodontie mandibulaire"] }
    Sortie : { "resolved": [
        { "input": "...", "canontag": "béance", "canonadjs": "antérieur|sévère" },
        ...
    ]}
    """
    try:
        from dettags import charger_tags, detecter_tags
    except ImportError as e:
        raise HTTPException(status_code=500, detail=f"Module dettags non disponible: {e}")
    
    if REFS_DIR is None:
        raise HTTPException(status_code=500, detail="Dossier refs/ non configuré")
    
    tags_path = str(REFS_DIR / "tags.csv")
    adjs_path = str(REFS_DIR / "adjectifs.csv")
    
    if not Path(tags_path).exists():
        raise HTTPException(status_code=500, detail=f"Fichier tags.csv introuvable dans {REFS_DIR}")
    
    tags_data, adjs_data = charger_tags(tags_path, adjs_path, verbose=False, debug=False)
    
    resolved = []
    for line in request_data.lines:
        line = line.strip()
        if not line:
            resolved.append({"input": line, "canontag": "", "canonadjs": ""})
            continue
        
        resultat = detecter_tags(line, tags_data, adjs_data, verbose=False, debug=False)
        
        if resultat['criteres']:
            critere = resultat['criteres'][0]
            canontag = critere.get('canonique', '')
            adjs = critere.get('adjectifs', [])
            canonadjs = '|'.join(a.get('canonique', '') for a in adjs) if adjs else ''
            resolved.append({
                "input": line,
                "canontag": canontag,
                "canonadjs": canonadjs
            })
        else:
            resolved.append({"input": line, "canontag": "", "canonadjs": ""})
    
    logger.info(f"POST /patient/resolve-tags - {len(request_data.lines)} ligne(s), {sum(1 for r in resolved if r['canontag'])} résolue(s)")
    return {"resolved": resolved}


def _generate_pathologies_combinations(canontags_str, canonadjs_str):
    """
    Génère toutes les combinaisons de pathologies pour l'indexation.
    
    Exemple :
        canontags = "béance,macrodontie"
        canonadjs = "droite|sévère,mandibulaire|maxillaire"
    
    Résultat :
        ["beance", "beance droite", "beance droite severe",
         "macrodontie", "macrodontie mandibulaire", "macrodontie mandibulaire maxillaire"]
    """
    import unicodedata
    
    def normalize(text):
        text = text.lower().strip()
        text = unicodedata.normalize('NFD', text)
        text = ''.join(c for c in text if unicodedata.category(c) != 'Mn')
        return text
    
    tags = [t.strip() for t in canontags_str.split(',') if t.strip()]
    adjs_groups = [g.strip() for g in canonadjs_str.split(',')]
    
    while len(adjs_groups) < len(tags):
        adjs_groups.append('')
    
    all_pathologies = []
    
    for i, tag in enumerate(tags):
        tag_norm = normalize(tag)
        if not tag_norm:
            continue
        
        adjs_str = adjs_groups[i] if i < len(adjs_groups) else ''
        adjs = [a.strip() for a in adjs_str.split('|') if a.strip()]
        adjs.sort(key=lambda a: normalize(a))
        
        all_pathologies.append(tag_norm)
        
        current = tag_norm
        for adj in adjs:
            adj_norm = normalize(adj)
            current = current + ' ' + adj_norm
            all_pathologies.append(current)
    
    return all_pathologies


@app.put("/patient/update")
async def update_patient(request_data: PatientUpdateRequest):
    """
    Met à jour un patient et recalcule les index pathologies.
    
    Actions :
    1. UPDATE patients SET ... WHERE id = ?
    2. Recalcul du champ 'pathologies' (combinaisons)
    3. Suppression des anciennes entrées patients_pathologies
    4. Insertion des nouvelles pathologies (création si nécessaire)
    5. Recréation des entrées patients_pathologies
    """
    if BASES_DIR is None:
        raise HTTPException(status_code=500, detail="Dossier bases/ non configuré")
    
    db_path = BASES_DIR / request_data.base
    if not db_path.exists():
        raise HTTPException(status_code=404, detail=f"Base {request_data.base} introuvable")
    
    try:
        conn = sqlite3.connect(str(db_path))
        conn.execute("PRAGMA foreign_keys = ON")
        cursor = conn.cursor()
        
        cursor.execute("SELECT id FROM patients WHERE id = ?", (request_data.id,))
        if not cursor.fetchone():
            conn.close()
            raise HTTPException(status_code=404, detail=f"Patient {request_data.id} introuvable")
        
        # 1. Générer les combinaisons de pathologies
        all_pathos = _generate_pathologies_combinations(
            request_data.canontags,
            request_data.canonadjs
        )
        pathologies_str = ', '.join(all_pathos)
        
        # 2. UPDATE du patient
        cursor.execute("""
            UPDATE patients SET
                prenom = ?,
                nom = ?,
                sexe = ?,
                datenaissance = ?,
                idportrait = ?,
                canontags = ?,
                canonadjs = ?,
                oripathologies = ?,
                pathologies = ?
            WHERE id = ?
        """, (
            request_data.prenom,
            request_data.nom,
            request_data.sexe,
            request_data.datenaissance,
            request_data.idportrait,
            request_data.canontags,
            request_data.canonadjs,
            request_data.oripathologies,
            pathologies_str,
            request_data.id
        ))
        
        # 3. Supprimer les anciennes entrées patients_pathologies
        cursor.execute("DELETE FROM patients_pathologies WHERE patient_id = ?", (request_data.id,))
        
        # 4. Pour chaque pathologie, créer si nécessaire et lier
        nb_pathologies = 0
        for patho in all_pathos:
            if not patho:
                continue
            cursor.execute(
                "INSERT OR IGNORE INTO pathologies (pathologie) VALUES (?)",
                (patho,)
            )
            cursor.execute(
                "SELECT id FROM pathologies WHERE pathologie = ?",
                (patho,)
            )
            patho_row = cursor.fetchone()
            if patho_row:
                patho_id = patho_row[0]
                cursor.execute(
                    "INSERT OR IGNORE INTO patients_pathologies (patient_id, pathologie_id) VALUES (?, ?)",
                    (request_data.id, patho_id)
                )
                nb_pathologies += 1
        
        conn.commit()
        conn.close()
        
        logger.info(
            f"PUT /patient/update - base={request_data.base} id={request_data.id} "
            f"→ {nb_pathologies} pathologies indexées, canontags={request_data.canontags}"
        )
        
        return {
            "status": "ok",
            "id": request_data.id,
            "nb_pathologies": nb_pathologies,
            "pathologies": pathologies_str
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur mise à jour: {e}")


if __name__ == "__main__":
    print(f"{__pgm__} V{__version__} - {__date__}")
    print()
    uvicorn.run(
        "server:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
