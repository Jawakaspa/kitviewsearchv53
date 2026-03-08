# creefakelog.py V1.0.1 - 02/01/2026 19:30:34
__pgm__ = "creefakelog.py"
__version__ = "1.0.1"
__date__ = "02/01/2026 19:30:34"

"""
Générateur de fichier de logs de recherches fictives.

Ce module crée un fichier logrechercheout.csv avec :
- Phase 1 : Toutes les lignes de logrecherche.csv recopiées telles quelles
- Phase 2 : Ces lignes dupliquées avec timestamp 1er-17 déc 2025 + rating simulé
- Phase 3 : Nouvelles lignes générées (18 déc 2025 - 5 jan 2026) avec questions
            tirées de fr100.csv et résultats de recherche simulés

Usage :
    python creefakelog.py N z.csv
    
    N     : Nombre de lignes souhaité (doit être >= 3 × nombre de lignes de logrecherche.csv)
    z.csv : Fichier de questions avec colonnes fr, en, ja

Exemple :
    python creefakelog.py 300 fr100.csv
"""

import sys
import os
import csv
import random
import uuid
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple

# =============================================================================
# CONFIGURATION
# =============================================================================

SCRIPT_DIR = Path(__file__).parent.resolve()
LOGS_DIR = SCRIPT_DIR / "logs"
REFS_DIR = SCRIPT_DIR / "refs"
TESTS_DIR = SCRIPT_DIR / "tests"

# Fichiers d'entrée/sortie
LOG_INPUT = LOGS_DIR / "logrecherche.csv"
LOG_OUTPUT = LOGS_DIR / "logrechercheout.csv"
MOTSVIDES_FILE = REFS_DIR / "motsvides.csv"

# Périodes de timestamps
PERIODE_PHASE2_DEBUT = datetime(2025, 12, 1, 0, 0, 0)
PERIODE_PHASE2_FIN = datetime(2025, 12, 17, 23, 59, 59)
PERIODE_PHASE3_DEBUT = datetime(2025, 12, 18, 0, 0, 0)
PERIODE_PHASE3_FIN = datetime(2026, 1, 5, 23, 59, 59)

# Répartition des langues phase 3 (cumulative)
PROBA_JA = 0.20  # 20% japonais
PROBA_EN = 0.45  # 25% anglais (20% + 25% = 45%)
# Le reste (55%) = français

# Répartition des ratings
PROBA_RATING_POSITIF = 1/3  # 1/3 positif, 2/3 négatif

# Types de problèmes (équirépartis)
TYPES_PROBLEMES = [
    "Bug IHM",
    "Trop de patients",
    "Pas assez de patients",
    "Autre"
]

# Commentaires élogieux
COMMENTAIRES_POSITIFS = [
    "Excellent ! Exactement ce que je cherchais.",
    "Résultats très pertinents, merci !",
    "Parfait, recherche rapide et efficace.",
    "Super outil, très pratique !",
    "Bravo, ça fonctionne parfaitement.",
    "Très satisfait de cette recherche.",
    "Résultats précis et rapides.",
    "Exactement les patients attendus.",
    "Outil performant, je recommande.",
    "Recherche impeccable !",
    "Très bien, continue comme ça !",
    "Génial, gain de temps énorme.",
    "Interface intuitive et résultats corrects.",
    "Nickel chrome !",
    "Top, rien à redire."
]

# Commentaires négatifs par type de problème
COMMENTAIRES_NEGATIFS = {
    "Bug IHM": [
        "L'interface ne répond plus.",
        "Bouton de recherche bloqué.",
        "Affichage cassé sur mobile.",
        "Page blanche après la recherche.",
        "Les filtres ne fonctionnent pas.",
        "Erreur d'affichage des résultats.",
        "Le scroll ne marche pas.",
        "Interface figée.",
        "Problème de chargement.",
        "Bug visuel sur les cartes patients."
    ],
    "Trop de patients": [
        "Beaucoup trop de résultats, impossible de trouver le bon.",
        "La recherche est trop large.",
        "Je voulais moins de patients.",
        "Résultats non filtrés correctement.",
        "Trop de faux positifs.",
        "Liste interminable de patients.",
        "Filtres insuffisants.",
        "Recherche trop permissive.",
        "J'ai eu des milliers de résultats !",
        "Impossible de trier autant de patients."
    ],
    "Pas assez de patients": [
        "Aucun patient trouvé alors qu'il y en a.",
        "Recherche trop restrictive.",
        "Je sais qu'il y a plus de patients.",
        "Résultats incomplets.",
        "Manque des patients évidents.",
        "La recherche ignore certains cas.",
        "Critères trop stricts.",
        "Où sont passés mes patients ?",
        "Base de données incomplète ?",
        "Recherche partielle seulement."
    ],
    "Autre": [
        "Je ne comprends pas les résultats.",
        "Temps de réponse trop long.",
        "Erreur incompréhensible.",
        "Problème non identifié.",
        "Comportement bizarre.",
        "Résultats incohérents.",
        "Je ne sais pas quoi penser.",
        "Quelque chose ne va pas.",
        "Besoin d'aide pour comprendre.",
        "Fonctionnement étrange."
    ]
}

# Modes de recherche possibles
MODES_RECHERCHE = ["rapide", "ia", "compare", "union"]

# Nombre maximum de questions strictement identiques autorisées
MAX_QUESTIONS_IDENTIQUES = 2

# Modules langue possibles
MODULES_LANGUE = ["glossaire_fr", "glossaire_resolution", "deepl", "fallback"]

# En-tête du fichier de log
LOG_HEADER = [
    'module', 'timestamp', 'temps_ms', 'languesaisie', 'langueutilisee',
    'modulelangue', 'questionoriginale', 'question', 'filtres', 'sql', 'tri',
    'base', 'mode', 'nb_patients', 'pathologies', 'ages', 'residu', 'erreur',
    'session_id', 'ip_utilisateur', 'rating', 'type_probleme', 'commentaire'
]


# =============================================================================
# FONCTIONS UTILITAIRES
# =============================================================================

def lire_csv_avec_commentaires(filepath: Path) -> Tuple[List[str], List[Dict[str, str]]]:
    """
    Lit un fichier CSV en ignorant les lignes de commentaires (#).
    
    Args:
        filepath: Chemin du fichier CSV
        
    Returns:
        Tuple (lignes_commentaires, liste_dictionnaires)
    """
    commentaires = []
    lignes_data = []
    
    with open(filepath, 'r', encoding='utf-8-sig', newline='') as f:
        for ligne in f:
            if ligne.strip().startswith('#'):
                commentaires.append(ligne.rstrip('\n\r'))
            else:
                lignes_data.append(ligne)
    
    # Parser les lignes de données
    if lignes_data:
        reader = csv.DictReader(lignes_data, delimiter=';')
        data = list(reader)
    else:
        data = []
    
    return commentaires, data


def generer_timestamp_aleatoire(debut: datetime, fin: datetime) -> str:
    """
    Génère un timestamp aléatoire entre deux dates au format DD/MM/YYYY HH:MM:SS.
    
    Args:
        debut: Date de début
        fin: Date de fin
        
    Returns:
        Timestamp formaté
    """
    delta = fin - debut
    secondes_totales = int(delta.total_seconds())
    secondes_aleatoires = random.randint(0, secondes_totales)
    date_aleatoire = debut + timedelta(seconds=secondes_aleatoires)
    return date_aleatoire.strftime("%d/%m/%Y %H:%M:%S")


def generer_session_id() -> str:
    """Génère un UUID de session."""
    return str(uuid.uuid4())


def generer_ip() -> str:
    """Génère une adresse IP fictive."""
    if random.random() < 0.7:
        return "127.0.0.1"
    else:
        return f"192.168.1.{random.randint(1, 254)}"


def choisir_rating_et_commentaire(avec_rating: bool = True) -> Tuple[str, str, str]:
    """
    Choisit un rating et un commentaire selon les règles de répartition.
    
    Args:
        avec_rating: Si True, génère un rating. Sinon, retourne des valeurs vides.
        
    Returns:
        Tuple (rating, type_probleme, commentaire)
    """
    if not avec_rating:
        return "", "", ""
    
    if random.random() < PROBA_RATING_POSITIF:
        # Positif (1/3)
        rating = "👍"
        type_probleme = ""
        commentaire = random.choice(COMMENTAIRES_POSITIFS)
    else:
        # Négatif (2/3)
        rating = "👎"
        type_probleme = random.choice(TYPES_PROBLEMES)
        commentaire = random.choice(COMMENTAIRES_NEGATIFS[type_probleme])
    
    return rating, type_probleme, commentaire


def choisir_langue_question() -> str:
    """
    Choisit la langue de la question selon la répartition :
    - 20% japonais
    - 25% anglais  
    - 55% français
    
    Returns:
        Code langue ('fr', 'en', 'ja')
    """
    r = random.random()
    if r < PROBA_JA:
        return 'ja'
    elif r < PROBA_EN:
        return 'en'
    else:
        return 'fr'


def simuler_resultats_recherche(question: str, langue: str) -> Dict[str, Any]:
    """
    Simule les résultats d'une recherche.
    
    Args:
        question: Question de recherche
        langue: Langue de la question
        
    Returns:
        Dictionnaire avec les champs simulés
    """
    # Temps de réponse simulé (entre 10ms et 500ms pour rapide, plus pour IA)
    mode = random.choice(MODES_RECHERCHE)
    if mode == "rapide":
        temps_ms = random.randint(10, 150)
    elif mode == "ia":
        temps_ms = random.randint(1500, 5000)
    else:
        temps_ms = random.randint(500, 2000)
    
    # Nombre de patients (0 à 500, avec tendance vers les petits nombres)
    nb_patients = int(random.expovariate(0.02))  # Distribution exponentielle
    nb_patients = min(nb_patients, 25000)  # Plafonner
    
    # Module langue
    if langue == 'fr':
        modulelangue = "glossaire_fr"
    elif langue in ('ja', 'en'):
        modulelangue = random.choice(["glossaire_resolution", "deepl"])
    else:
        modulelangue = "fallback"
    
    # Filtres simulés (format JSON simplifié)
    if nb_patients > 0 and random.random() > 0.3:
        filtres = '{"criteres": [{"type": "tag", "detecte": "simule", "canonique": "Simule"}]}'
    else:
        filtres = '{"criteres": []}'
    
    # Pathologies simulées (parfois vide)
    pathologies = ""
    if random.random() > 0.4:
        pathos = ["Bruxisme", "Béance", "Classe II", "Supraclusion", "Infraclusion"]
        pathologies = random.choice(pathos)
    
    # Résidu (parfois la question si pas de détection)
    residu = ""
    if random.random() > 0.7:
        residu = question.lower()[:30]
    
    return {
        'temps_ms': temps_ms,
        'mode': mode,
        'modulelangue': modulelangue,
        'nb_patients': nb_patients,
        'filtres': filtres,
        'pathologies': pathologies,
        'residu': residu
    }


def charger_motsvides(filepath: Path) -> List[str]:
    """
    Charge la liste des mots vides depuis un fichier CSV.
    
    Args:
        filepath: Chemin du fichier motsvides.csv
        
    Returns:
        Liste des mots vides
    """
    if not filepath.exists():
        print(f"  ⚠️  Fichier {filepath} non trouvé, utilisation de mots vides par défaut")
        return ["aussi", "donc", "alors", "peut-être", "vraiment", "bien", "très"]
    
    _, lignes = lire_csv_avec_commentaires(filepath)
    
    # Extraire les mots de la colonne 'fr'
    mots = [ligne.get('fr', '').strip() for ligne in lignes if ligne.get('fr', '').strip()]
    
    # Filtrer les mots trop courts ou les caractères spéciaux
    mots = [m for m in mots if len(m) > 1 and m not in ('{', '}', '?', '!')]
    
    print(f"  → {len(mots)} mots vides chargés depuis {filepath}")
    return mots


def diversifier_question(question: str, mots_vides: List[str]) -> str:
    """
    Diversifie une question en ajoutant un mot vide aléatoire.
    
    Le mot est ajouté :
    - Avant le '?' final si présent
    - À la fin sinon
    
    Args:
        question: Question originale
        mots_vides: Liste des mots vides disponibles
        
    Returns:
        Question modifiée avec un mot vide ajouté
    """
    if not mots_vides:
        return question
    
    mot_aleatoire = random.choice(mots_vides)
    
    # Vérifier si la question se termine par un ?
    question = question.strip()
    if question.endswith('?'):
        # Insérer le mot avant le ?
        return f"{question[:-1]} {mot_aleatoire} ?"
    else:
        # Ajouter le mot à la fin
        return f"{question} {mot_aleatoire}"


# =============================================================================
# FONCTIONS PRINCIPALES
# =============================================================================

def charger_questions(filepath: Path) -> List[Dict[str, str]]:
    """
    Charge le fichier de questions.
    
    Args:
        filepath: Chemin du fichier CSV de questions
        
    Returns:
        Liste des questions avec colonnes fr, en, ja
    """
    _, questions = lire_csv_avec_commentaires(filepath)
    print(f"  → {len(questions)} questions chargées depuis {filepath}")
    return questions


def charger_log_existant(filepath: Path) -> Tuple[List[str], List[Dict[str, str]]]:
    """
    Charge le fichier de log existant.
    
    Args:
        filepath: Chemin du fichier logrecherche.csv
        
    Returns:
        Tuple (commentaires, lignes)
    """
    if not filepath.exists():
        print(f"  ⚠️  Fichier {filepath} non trouvé, création d'un log vide")
        return [], []
    
    commentaires, lignes = lire_csv_avec_commentaires(filepath)
    print(f"  → {len(lignes)} lignes existantes chargées (LR = {len(lignes)})")
    return commentaires, lignes


def generer_lignes_phase2(lignes_originales: List[Dict[str, str]]) -> List[Dict[str, str]]:
    """
    Phase 2 : Duplique les lignes avec timestamp 1er-17 déc + rating.
    
    Args:
        lignes_originales: Lignes du log original
        
    Returns:
        Liste des lignes dupliquées avec modifications
    """
    lignes_phase2 = []
    
    for ligne in lignes_originales:
        nouvelle_ligne = ligne.copy()
        
        # Nouveau timestamp
        nouvelle_ligne['timestamp'] = generer_timestamp_aleatoire(
            PERIODE_PHASE2_DEBUT, PERIODE_PHASE2_FIN
        )
        
        # Nouveau session_id et IP
        nouvelle_ligne['session_id'] = generer_session_id()
        nouvelle_ligne['ip_utilisateur'] = generer_ip()
        
        # Rating (toujours présent en phase 2)
        rating, type_prob, comment = choisir_rating_et_commentaire(avec_rating=True)
        nouvelle_ligne['rating'] = rating
        nouvelle_ligne['type_probleme'] = type_prob
        nouvelle_ligne['commentaire'] = comment
        
        lignes_phase2.append(nouvelle_ligne)
    
    print(f"  → Phase 2 : {len(lignes_phase2)} lignes générées (1-17 déc)")
    return lignes_phase2


def generer_lignes_phase3(
    questions: List[Dict[str, str]], 
    nb_lignes: int,
    mots_vides: List[str]
) -> List[Dict[str, str]]:
    """
    Phase 3 : Génère de nouvelles lignes avec questions aléatoires.
    
    Limite les questions strictement identiques à MAX_QUESTIONS_IDENTIQUES (2).
    Si une question est tirée une 3ème fois, un mot vide est ajouté pour la diversifier.
    
    Args:
        questions: Liste des questions disponibles
        nb_lignes: Nombre de lignes à générer
        mots_vides: Liste des mots vides pour diversification
        
    Returns:
        Liste des nouvelles lignes
    """
    lignes_phase3 = []
    
    # Compteur d'occurrences des questions
    occurrences_questions: Dict[str, int] = {}
    nb_diversifiees = 0
    
    # Filtrer les questions valides par langue
    questions_par_langue = {
        'fr': [q for q in questions if q.get('fr', '').strip()],
        'en': [q for q in questions if q.get('en', '').strip()],
        'ja': [q for q in questions if q.get('ja', '').strip()]
    }
    
    print(f"  → Questions disponibles : fr={len(questions_par_langue['fr'])}, "
          f"en={len(questions_par_langue['en'])}, ja={len(questions_par_langue['ja'])}")
    
    for i in range(nb_lignes):
        # Choisir la langue
        langue = choisir_langue_question()
        
        # Vérifier qu'on a des questions dans cette langue, sinon fallback fr
        if not questions_par_langue[langue]:
            langue = 'fr'
        
        if not questions_par_langue[langue]:
            print(f"  ⚠️  Aucune question disponible, ligne {i+1} ignorée")
            continue
        
        # Choisir une question
        question_dict = random.choice(questions_par_langue[langue])
        question = question_dict[langue].strip()
        
        # Vérifier le nombre d'occurrences et diversifier si nécessaire
        if question in occurrences_questions:
            if occurrences_questions[question] >= MAX_QUESTIONS_IDENTIQUES:
                # Diversifier la question en ajoutant un mot vide
                question = diversifier_question(question, mots_vides)
                nb_diversifiees += 1
        
        # Incrémenter le compteur (pour la question originale, pas la diversifiée)
        question_base = question_dict[langue].strip()
        occurrences_questions[question_base] = occurrences_questions.get(question_base, 0) + 1
        
        # Simuler les résultats
        resultats = simuler_resultats_recherche(question, langue)
        
        # Rating (1 fois sur 2)
        avec_rating = random.random() < 0.5
        rating, type_prob, comment = choisir_rating_et_commentaire(avec_rating)
        
        # Construire la ligne
        nouvelle_ligne = {
            'module': 'search.py',
            'timestamp': generer_timestamp_aleatoire(PERIODE_PHASE3_DEBUT, PERIODE_PHASE3_FIN),
            'temps_ms': str(resultats['temps_ms']),
            'languesaisie': 'Auto' if langue == 'fr' else langue,
            'langueutilisee': langue,
            'modulelangue': resultats['modulelangue'],
            'questionoriginale': question,
            'question': question,  # Même valeur pour simulation
            'filtres': resultats['filtres'],
            'sql': '',
            'tri': '',
            'base': 'base25000.db',
            'mode': resultats['mode'],
            'nb_patients': str(resultats['nb_patients']),
            'pathologies': resultats['pathologies'],
            'ages': '',
            'residu': resultats['residu'],
            'erreur': '',
            'session_id': generer_session_id(),
            'ip_utilisateur': generer_ip(),
            'rating': rating,
            'type_probleme': type_prob,
            'commentaire': comment
        }
        
        lignes_phase3.append(nouvelle_ligne)
        
        # Progression
        if (i + 1) % 50 == 0:
            print(f"    [{i+1}/{nb_lignes}] lignes générées...")
    
    print(f"  → Phase 3 : {len(lignes_phase3)} lignes générées (18 déc - 5 jan)")
    if nb_diversifiees > 0:
        print(f"  → {nb_diversifiees} questions diversifiées (> {MAX_QUESTIONS_IDENTIQUES} occurrences)")
    return lignes_phase3


def trier_par_timestamp(lignes: List[Dict[str, str]]) -> List[Dict[str, str]]:
    """
    Trie les lignes par timestamp croissant.
    
    Args:
        lignes: Liste des lignes à trier
        
    Returns:
        Liste triée
    """
    def parse_timestamp(ts: str) -> datetime:
        try:
            return datetime.strptime(ts, "%d/%m/%Y %H:%M:%S")
        except:
            return datetime.min
    
    return sorted(lignes, key=lambda x: parse_timestamp(x.get('timestamp', '')))


def ecrire_log_sortie(
    filepath: Path, 
    lignes: List[Dict[str, str]],
    commentaire_version: str
) -> int:
    """
    Écrit le fichier de log de sortie.
    
    Args:
        filepath: Chemin du fichier de sortie
        lignes: Lignes à écrire
        commentaire_version: Commentaire de version pour l'en-tête
        
    Returns:
        Nombre de lignes écrites
    """
    # S'assurer que le répertoire existe
    filepath.parent.mkdir(parents=True, exist_ok=True)
    
    with open(filepath, 'w', encoding='utf-8-sig', newline='') as f:
        # Écrire le commentaire de version
        f.write(f"{commentaire_version}\n")
        
        # Écrire avec DictWriter
        writer = csv.DictWriter(f, fieldnames=LOG_HEADER, delimiter=';', extrasaction='ignore')
        writer.writeheader()
        
        for ligne in lignes:
            # S'assurer que toutes les colonnes existent
            ligne_complete = {col: ligne.get(col, '') for col in LOG_HEADER}
            writer.writerow(ligne_complete)
    
    return len(lignes)


# =============================================================================
# POINT D'ENTRÉE
# =============================================================================

def main():
    """Point d'entrée principal."""
    print(f"╔════════════════════════════════════════════════════════════════")
    print(f"║ {__pgm__} V{__version__} - {__date__}")
    print(f"║ Générateur de fichier de logs de recherches fictives")
    print(f"╚════════════════════════════════════════════════════════════════")
    print()
    
    # Vérification des arguments
    if len(sys.argv) < 3:
        print("Usage:")
        print(f"  python {__pgm__} N fichier_questions.csv")
        print()
        print("Arguments:")
        print("  N                    : Nombre de lignes souhaité (>= 3 × LR)")
        print("  fichier_questions.csv: Fichier de questions (colonnes fr, en, ja)")
        print()
        print("Exemple:")
        print(f"  python {__pgm__} 300 fr100.csv")
        print()
        print(f"Entrée  : {LOG_INPUT}")
        print(f"Sortie  : {LOG_OUTPUT}")
        return 1
    
    # Parser les arguments
    try:
        n_souhaite = int(sys.argv[1])
    except ValueError:
        print(f"ERREUR : N doit être un entier, reçu '{sys.argv[1]}'")
        return 1
    
    fichier_questions = sys.argv[2]
    
    # Résoudre le chemin du fichier de questions
    chemin_questions = Path(fichier_questions)
    if not chemin_questions.is_absolute():
        # Chercher dans plusieurs emplacements
        candidats = [
            SCRIPT_DIR / fichier_questions,
            REFS_DIR / fichier_questions,
            TESTS_DIR / fichier_questions,
            Path(fichier_questions)
        ]
        for candidat in candidats:
            if candidat.exists():
                chemin_questions = candidat
                break
    
    if not chemin_questions.exists():
        print(f"ERREUR : Fichier de questions '{fichier_questions}' introuvable")
        print(f"  Cherché dans : {SCRIPT_DIR}, {REFS_DIR}, {TESTS_DIR}")
        return 1
    
    print(f"Configuration:")
    print(f"  N souhaité        : {n_souhaite}")
    print(f"  Fichier questions : {chemin_questions.resolve()}")
    print(f"  Log entrée        : {LOG_INPUT.resolve()}")
    print(f"  Log sortie        : {LOG_OUTPUT.resolve()}")
    print()
    
    # Phase 0 : Charger les données
    print("Phase 0 : Chargement des données...")
    commentaires, lignes_originales = charger_log_existant(LOG_INPUT)
    questions = charger_questions(chemin_questions)
    mots_vides = charger_motsvides(MOTSVIDES_FILE)
    
    lr = len(lignes_originales)
    n_minimum = 3 * lr
    
    print(f"  → LR (lignes originales) = {lr}")
    print(f"  → N minimum requis = 3 × {lr} = {n_minimum}")
    print()
    
    # Vérification N >= 3 × LR
    if n_souhaite < n_minimum:
        print(f"ERREUR : N ({n_souhaite}) doit être >= 3 × LR ({n_minimum})")
        print(f"  Augmentez N à au moins {n_minimum}")
        return 1
    
    # Phase 1 : Copier les lignes originales telles quelles
    print("Phase 1 : Copie des lignes originales...")
    lignes_phase1 = [ligne.copy() for ligne in lignes_originales]
    print(f"  → Phase 1 : {len(lignes_phase1)} lignes copiées")
    
    # Phase 2 : Dupliquer avec modifications
    print()
    print("Phase 2 : Duplication avec timestamps 1-17 déc et ratings...")
    lignes_phase2 = generer_lignes_phase2(lignes_originales)
    
    # Phase 3 : Générer les nouvelles lignes
    nb_phase3 = n_souhaite - 2 * lr
    print()
    print(f"Phase 3 : Génération de {nb_phase3} nouvelles lignes (18 déc - 5 jan)...")
    lignes_phase3 = generer_lignes_phase3(questions, nb_phase3, mots_vides)
    
    # Fusionner toutes les lignes
    print()
    print("Fusion et tri...")
    toutes_lignes = lignes_phase1 + lignes_phase2 + lignes_phase3
    print(f"  → Total avant tri : {len(toutes_lignes)} lignes")
    
    # Trier par timestamp croissant
    toutes_lignes_triees = trier_par_timestamp(toutes_lignes)
    print(f"  → Tri par timestamp croissant effectué")
    
    # Écrire le fichier de sortie
    print()
    print("Écriture du fichier de sortie...")
    timestamp_now = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    commentaire_version = f"# logrechercheout.csv V1.0.0 - {timestamp_now} - Généré par {__pgm__}"
    
    nb_ecrites = ecrire_log_sortie(LOG_OUTPUT, toutes_lignes_triees, commentaire_version)
    
    print()
    print("═" * 70)
    print(f"✅ Fichier généré : {LOG_OUTPUT.resolve()}")
    print(f"   → {nb_ecrites} lignes écrites")
    print(f"   → Phase 1 : {len(lignes_phase1)} (originales)")
    print(f"   → Phase 2 : {len(lignes_phase2)} (dupliquées 1-17 déc)")
    print(f"   → Phase 3 : {len(lignes_phase3)} (nouvelles 18 déc - 5 jan)")
    print("═" * 70)
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
