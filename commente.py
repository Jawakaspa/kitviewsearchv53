# commente.py V1.0.2 - 26/12/2025 18:41:16
__pgm__ = "commente.py"
__version__ = "1.0.2"
__date__ = "26/12/2025 18:41:16"

"""
Programme de génération de commentaires pour les pathologies orthodontiques via IA.

Lit le fichier refs/commentaires.csv et remplit la colonne 'commentaire' 
pour les lignes où elle est vide, en interrogeant une IA.

Usage:
    python commente.py [nomdelia] [-t pattern]
    
    nomdelia : Nom du moteur IA (gpt4o, sonnet, haiku, etc.)
               Si absent, utilise l'IA par défaut (gpt4o)
    -t pattern : Filtre sur le premier mot de l'oripathologie
                 Si absent, traite toutes les lignes sans commentaire

Exemples:
    python commente.py                     # Toutes les lignes, IA par défaut
    python commente.py sonnet              # Toutes les lignes, avec Sonnet
    python commente.py -t béance           # Seulement les "béance ...", IA par défaut
    python commente.py gpt4omini -t bruxisme  # Seulement les "bruxisme ...", avec GPT-4o-mini

Fichiers utilisés:
    - refs/commentaires.csv : Fichier à compléter (lecture/écriture)
    - refs/ia.csv : Configuration des moteurs IA
"""

import os
import sys
import csv
import json
import time
import argparse
import requests
from pathlib import Path
from typing import Optional, Tuple
from tqdm import tqdm


# =============================================================================
# CONFIGURATION
# =============================================================================

DEFAULT_MODEL = "gpt4o"
EDEN_AI_URL = "https://api.edenai.run/v2/text/chat"
OPENAI_API_URL = "https://api.openai.com/v1/chat/completions"

# Mapping des modèles connus
SUPPORTED_MODELS = {
    "anthropic/claude-3-opus-latest": "anthropic/claude-3-opus-latest",
    "anthropic/claude-3-7-sonnet-20250219": "anthropic/claude-3-7-sonnet-20250219",
    "anthropic/claude-3-5-haiku-latest": "anthropic/claude-3-5-haiku-latest",
    "openai/gpt-4o": "openai/gpt-4o",
    "openai/gpt-4o-mini": "openai/gpt-4o-mini",
    "google/gemini-1.5-pro": "google/gemini-1.5-pro",
    "google/gemini-1.5-flash": "google/gemini-1.5-flash",
    "google/gemini-2.5-flash": "google/gemini-2.5-flash",
}


# =============================================================================
# DÉTECTION DE LA RACINE
# =============================================================================

def detecter_racine() -> Path:
    """Détecte la racine du projet."""
    chemin = Path.cwd()
    for _ in range(10):
        if (chemin / "refs").exists() or (chemin / "data").exists():
            return chemin
        if chemin.parent == chemin:
            break
        chemin = chemin.parent
    
    chemin = Path(__file__).resolve().parent
    for _ in range(10):
        if (chemin / "refs").exists() or (chemin / "data").exists():
            return chemin
        if chemin.parent == chemin:
            break
        chemin = chemin.parent
    
    return Path.cwd()


# =============================================================================
# CHARGEMENT DES MODÈLES IA
# =============================================================================

_MODELES_IA_CACHE = None


def charger_modeles_ia(refs_dir: Path = None) -> dict:
    """Charge les modèles IA depuis refs/ia.csv."""
    global _MODELES_IA_CACHE
    if _MODELES_IA_CACHE is not None:
        return _MODELES_IA_CACHE
    
    if refs_dir is None:
        refs_dir = detecter_racine() / "refs"
    
    ia_path = refs_dir / "ia.csv"
    
    default_config = {
        'gpt4o': {'via': 'openai', 'complet': 'gpt-4o', 'actif': True},
        'gpt4omini': {'via': 'openai', 'complet': 'gpt-4o-mini', 'actif': True},
        'sonnet': {'via': 'eden', 'complet': 'anthropic/claude-3-7-sonnet-20250219', 'actif': True},
        'haiku': {'via': 'eden', 'complet': 'anthropic/claude-3-5-haiku-latest', 'actif': True},
    }
    
    if not ia_path.exists():
        print(f"[INFO] ia.csv introuvable, utilisation config par défaut")
        _MODELES_IA_CACHE = default_config
        return default_config
    
    modeles = {}
    
    try:
        with open(ia_path, 'r', encoding='utf-8-sig') as f:
            lignes = [line for line in f if line.strip() and not line.strip().startswith('#')]
        
        if not lignes:
            _MODELES_IA_CACHE = default_config
            return default_config
        
        import io
        lignes_io = io.StringIO(''.join(lignes))
        reader = csv.DictReader(lignes_io, delimiter=';')
        
        for row in reader:
            moteur = row.get('moteur', row.get('court', '')).strip().lower()
            if not moteur:
                continue
            
            actif = row.get('actif', 'O').strip().upper() == 'O'
            
            modeles[moteur] = {
                'via': row.get('via', '').strip().lower(),
                'complet': row.get('complet', '').strip(),
                'actif': actif,
            }
        
        _MODELES_IA_CACHE = modeles if modeles else default_config
        return _MODELES_IA_CACHE
        
    except Exception as e:
        print(f"[ERREUR] Chargement ia.csv: {e}")
        _MODELES_IA_CACHE = default_config
        return default_config


def get_model_config(model_name: str) -> dict:
    """Résout un nom de modèle vers sa configuration."""
    modeles = charger_modeles_ia()
    
    if model_name.lower() in modeles:
        config = modeles[model_name.lower()]
        return {'via': config['via'], 'model': config['complet']}
    
    if model_name.startswith('gpt-'):
        return {'via': 'openai', 'model': model_name}
    
    if '/' in model_name:
        return {'via': 'eden', 'model': model_name}
    
    # Défaut
    return {'via': 'openai', 'model': 'gpt-4o'}


def lister_moteurs() -> None:
    """Affiche la liste des moteurs disponibles."""
    modeles = charger_modeles_ia()
    print("Moteurs IA disponibles :")
    print()
    for moteur, config in sorted(modeles.items()):
        if not config.get('via'):
            continue
        status = "✓" if config.get('actif', True) else "✗"
        print(f"  {status} {moteur:15} via {config['via']:8} → {config['complet']}")
    print()


# =============================================================================
# APPELS API
# =============================================================================

def appeler_openai(prompt_systeme: str, prompt_utilisateur: str, model: str) -> Tuple[str, float]:
    """Appelle l'API OpenAI et retourne le texte généré."""
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
        "temperature": 0.7,
        "max_tokens": 200
    }
    
    start_time = time.time()
    
    response = requests.post(
        OPENAI_API_URL,
        headers=headers,
        json=payload,
        timeout=60
    )
    
    latency_ms = (time.time() - start_time) * 1000
    
    if response.status_code != 200:
        raise ValueError(f"Erreur API OpenAI: {response.status_code} - {response.text}")
    
    data = response.json()
    generated_text = data['choices'][0]['message']['content'].strip()
    
    return generated_text, latency_ms


def appeler_eden(prompt_systeme: str, prompt_utilisateur: str, model: str) -> Tuple[str, float]:
    """Appelle l'API Eden AI et retourne le texte généré."""
    api_key = os.environ.get('EDENAI_API_KEY')
    
    if not api_key:
        raise ValueError("Variable EDENAI_API_KEY non définie")
    
    model_id = SUPPORTED_MODELS.get(model, model)
    
    if '/' in model_id:
        provider = model_id.split('/')[0]
        model_name = model_id.split('/', 1)[1]
    else:
        provider = model_id
        model_name = model_id
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "providers": provider,
        "text": prompt_utilisateur,
        "chatbot_global_action": prompt_systeme,
        "previous_history": [],
        "temperature": 0.7,
        "max_tokens": 200,
        "settings": {
            provider: model_name
        }
    }
    
    start_time = time.time()
    
    response = requests.post(
        EDEN_AI_URL,
        headers=headers,
        json=payload,
        timeout=60
    )
    
    latency_ms = (time.time() - start_time) * 1000
    
    if response.status_code != 200:
        raise ValueError(f"Erreur API Eden AI: {response.status_code} - {response.text}")
    
    data = response.json()
    
    # Extraire la réponse du provider
    if provider in data:
        generated_text = data[provider].get('generated_text', '')
    else:
        for key in data:
            if isinstance(data[key], dict) and 'generated_text' in data[key]:
                generated_text = data[key]['generated_text']
                break
        else:
            raise ValueError(f"Réponse inattendue: {data}")
    
    return generated_text.strip(), latency_ms


def appeler_ia(prompt_systeme: str, prompt_utilisateur: str, model_name: str) -> Tuple[str, float]:
    """Appelle l'IA appropriée selon la configuration du modèle."""
    config = get_model_config(model_name)
    via = config['via']
    model = config['model']
    
    if via == 'openai':
        return appeler_openai(prompt_systeme, prompt_utilisateur, model)
    else:
        return appeler_eden(prompt_systeme, prompt_utilisateur, model)


# =============================================================================
# GÉNÉRATION DES COMMENTAIRES
# =============================================================================

PROMPT_SYSTEME = """Tu es un assistant spécialisé en orthodontie.
Tu dois fournir un commentaire court et utile pour un praticien orthodontiste.

RÈGLES STRICTES :
1. Le commentaire doit faire entre 40 et 120 caractères
2. Pas de guillemets autour du commentaire
3. Pas de préfixe comme "Commentaire:" ou "Définition:"
4. Utilise un vocabulaire technique approprié
5. Sois concis et informatif
6. Réponds UNIQUEMENT avec le commentaire, rien d'autre"""


def generer_commentaire(oripathologie: str, model_name: str) -> Tuple[str, float]:
    """
    Génère un commentaire pour une pathologie donnée.
    
    Returns:
        Tuple (commentaire, latency_ms)
    """
    prompt_utilisateur = f"""Donne un commentaire orthodontique pour : "{oripathologie}"

Rappel : entre 40 et 120 caractères, vocabulaire technique, utile au praticien."""
    
    commentaire, latency = appeler_ia(PROMPT_SYSTEME, prompt_utilisateur, model_name)
    
    # Nettoyer le commentaire
    commentaire = commentaire.strip()
    
    # Supprimer les guillemets englobants
    if commentaire.startswith('"') and commentaire.endswith('"'):
        commentaire = commentaire[1:-1]
    if commentaire.startswith("'") and commentaire.endswith("'"):
        commentaire = commentaire[1:-1]
    
    # Supprimer les préfixes courants
    prefixes = ['Commentaire:', 'Définition:', 'Description:', 'Note:']
    for prefix in prefixes:
        if commentaire.lower().startswith(prefix.lower()):
            commentaire = commentaire[len(prefix):].strip()
    
    # Tronquer si trop long (avec marge)
    if len(commentaire) > 130:
        commentaire = commentaire[:127] + "..."
    
    return commentaire, latency


# =============================================================================
# TRAITEMENT DU FICHIER
# =============================================================================

def charger_commentaires(chemin: Path) -> Tuple[list[dict], list[str]]:
    """
    Charge le fichier commentaires.csv.
    
    Returns:
        Tuple (rows, lignes_commentaires)
        - rows: Liste des lignes de données
        - lignes_commentaires: Lignes de commentaires à préserver
    """
    rows = []
    lignes_commentaires = []
    
    if not chemin.exists():
        print(f"[ERREUR] Fichier introuvable : {chemin}")
        sys.exit(1)
    
    try:
        with open(chemin, 'r', encoding='utf-8-sig') as f:
            lignes = f.readlines()
        
        # Séparer les commentaires des données
        lignes_donnees = []
        for ligne in lignes:
            if ligne.strip().startswith('#'):
                lignes_commentaires.append(ligne.rstrip('\r\n'))
            else:
                lignes_donnees.append(ligne)
        
        # Parser les données
        import io
        reader = csv.DictReader(io.StringIO(''.join(lignes_donnees)), delimiter=';')
        for row in reader:
            # S'assurer que la colonne auteur existe
            if 'auteur' not in row:
                row['auteur'] = ''
            rows.append(row)
            
    except UnicodeDecodeError:
        print(f"[ERREUR] Le fichier {chemin} n'est pas encodé en UTF-8-BOM")
        sys.exit(1)
    
    return rows, lignes_commentaires


def sauvegarder_commentaires(chemin: Path, rows: list[dict], lignes_commentaires: list[str] = None) -> None:
    """Sauvegarde le fichier commentaires.csv en préservant les commentaires."""
    with open(chemin, 'w', encoding='utf-8-sig', newline='') as f:
        # Écrire les lignes de commentaires en premier
        if lignes_commentaires:
            for ligne in lignes_commentaires:
                f.write(ligne + '\n')
        
        # Écrire les données
        writer = csv.DictWriter(f, fieldnames=['oripathologie', 'commentaire', 'auteur'], delimiter=';')
        writer.writeheader()
        writer.writerows(rows)


def filtrer_lignes_a_traiter(rows: list[dict], pattern: Optional[str]) -> list[int]:
    """
    Retourne les indices des lignes à traiter.
    
    Args:
        rows: Liste des lignes du CSV
        pattern: Filtre sur le premier mot (optionnel)
    
    Returns:
        Liste des indices des lignes à traiter
    """
    indices = []
    
    for i, row in enumerate(rows):
        # Seulement les lignes sans commentaire
        if row.get('commentaire', '').strip():
            continue
        
        oripathologie = row.get('oripathologie', '').strip()
        if not oripathologie:
            continue
        
        # Filtre sur le premier mot si pattern spécifié
        if pattern:
            premier_mot = oripathologie.split()[0].lower() if oripathologie else ''
            if premier_mot != pattern.lower():
                continue
        
        indices.append(i)
    
    return indices


def main():
    print(f"{__pgm__} V{__version__} - {__date__}")
    print()
    
    # Parser les arguments
    parser = argparse.ArgumentParser(
        description="Génère des commentaires pour les pathologies orthodontiques via IA",
        usage="%(prog)s [nomdelia] [-t pattern] [-l]"
    )
    parser.add_argument('moteur', nargs='?', default=DEFAULT_MODEL,
                        help=f"Nom du moteur IA (défaut: {DEFAULT_MODEL})")
    parser.add_argument('-t', '--pattern', type=str, default=None,
                        help="Filtre sur le premier mot de l'oripathologie")
    parser.add_argument('-l', '--list', action='store_true',
                        help="Liste les moteurs disponibles")
    parser.add_argument('-v', '--verbose', action='store_true',
                        help="Mode verbeux")
    
    args = parser.parse_args()
    
    # Lister les moteurs si demandé
    if args.list:
        lister_moteurs()
        return 0
    
    # Vérifier que le moteur existe
    modeles = charger_modeles_ia()
    if args.moteur.lower() not in modeles:
        print(f"[ERREUR] Moteur inconnu : {args.moteur}")
        print()
        lister_moteurs()
        return 1
    
    moteur = args.moteur.lower()
    config = get_model_config(moteur)
    
    # Vérifier les clés API
    if config['via'] == 'openai' and not os.environ.get('OPENAI_API_KEY'):
        print("[ERREUR] Variable OPENAI_API_KEY non définie")
        return 1
    elif config['via'] == 'eden' and not os.environ.get('EDENAI_API_KEY'):
        print("[ERREUR] Variable EDENAI_API_KEY non définie")
        return 1
    
    # Chemins
    racine = detecter_racine()
    chemin_commentaires = racine / "refs" / "commentaires.csv"
    
    print(f"[INFO] Racine du projet : {racine}")
    print(f"[INFO] Fichier : {chemin_commentaires}")
    print(f"[INFO] Moteur IA : {moteur} ({config['model']} via {config['via']})")
    if args.pattern:
        print(f"[INFO] Filtre : premier mot = '{args.pattern}'")
    print()
    
    # Charger les données
    rows, lignes_commentaires = charger_commentaires(chemin_commentaires)
    print(f"[INFO] {len(rows)} lignes chargées")
    
    # Identifier les lignes à traiter
    indices = filtrer_lignes_a_traiter(rows, args.pattern)
    
    if not indices:
        print("[INFO] Aucune ligne à traiter (toutes ont déjà un commentaire)")
        return 0
    
    print(f"[INFO] {len(indices)} lignes à commenter")
    print()
    
    # Traiter les lignes
    total_latency = 0
    nb_erreurs = 0
    
    print("Génération des commentaires...")
    print("-" * 70)
    
    for i in tqdm(indices, desc="Progression", unit="ligne"):
        oripathologie = rows[i]['oripathologie']
        
        try:
            commentaire, latency = generer_commentaire(oripathologie, moteur)
            rows[i]['commentaire'] = commentaire
            rows[i]['auteur'] = moteur
            total_latency += latency
            
            if args.verbose:
                tqdm.write(f"  ✓ {oripathologie[:30]:<30} → {commentaire[:50]}...")
            
        except Exception as e:
            nb_erreurs += 1
            tqdm.write(f"  ✗ {oripathologie[:30]:<30} → ERREUR: {e}")
        
        # Sauvegarde intermédiaire toutes les 10 lignes
        if (indices.index(i) + 1) % 10 == 0:
            sauvegarder_commentaires(chemin_commentaires, rows, lignes_commentaires)
    
    # Sauvegarde finale
    sauvegarder_commentaires(chemin_commentaires, rows, lignes_commentaires)
    
    print("-" * 70)
    print()
    print("=" * 70)
    print("RÉSUMÉ")
    print("=" * 70)
    print(f"  Lignes traitées    : {len(indices)}")
    print(f"  Erreurs            : {nb_erreurs}")
    print(f"  Latence totale     : {total_latency:.0f} ms")
    if len(indices) > 0:
        print(f"  Latence moyenne    : {total_latency / len(indices):.0f} ms/ligne")
    print(f"  Fichier mis à jour : {chemin_commentaires}")
    print("=" * 70)
    
    return 0 if nb_erreurs == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
