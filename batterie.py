# batterie.py V1.0.2 - 12/01/2026 14:31:55
__pgm__ = "batterie.py"
__version__ = "1.0.2"
__date__ = "12/01/2026 14:31:55"

"""
Programme de tests en batterie pour les modules de détection KITVIEW.

Ce programme lit un fichier CSV contenant :
- Une colonne Q avec des questions de test
- Des colonnes avec des templates CLI (ex: "dettags.py Q", "detall.py Q")

Pour chaque question × template, il :
1. Exécute la commande en remplaçant Q par la question
2. Parse le JSON de sortie
3. Génère une synthèse lisible
4. Écrit le tout dans un fichier résultat

NORMALISATION DES COMMANDES (V1.0.1) :
- Ajoute 'python ' si absent au début
- Ajoute '.py' au nom du programme si absent
- Corrige la typo 'detags' → 'dettags'
- Gère Q en milieu ou fin de commande

FORMATS DE SYNTHÈSE :
- dettags  : "N tags: t1, t2 | N adjs: a1 | residu: xxx"
- detage   : "N crit: label1, label2 | residu: xxx"
- detangles: "N angles: classe II | residu: xxx"
- detall   : "MODE | N tags | N ages | residu: xxx"
- detia    : "IA | N tags | Nms | residu: xxx"
- trouve   : "N patients | mode | Nms"
- search   : "N patients | parcours | lang | Nms"

USAGE CLI :
    python batterie.py                      # Utilise batterie.csv par défaut
    python batterie.py tests/batterie.csv   # Fichier spécifique
    python batterie.py --verbose            # Mode verbose
    python batterie.py --debug              # Affiche les commandes exécutées
    python batterie.py --timeout 60         # Timeout 60s par commande

SORTIE :
    batterie_YYYYMMDD_HHMMSS.csv dans le même répertoire que l'entrée
"""

import os
import sys
import csv
import json
import subprocess
import argparse
import re
import io
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple

# Configuration
TIMEOUT_DEFAUT = 30  # secondes par commande
MAX_RESIDU_LEN = 30  # longueur max du résidu affiché


def extraire_json_sortie(output: str) -> Optional[dict]:
    """
    Extrait le JSON de la sortie d'un programme de détection.
    
    Les programmes produisent une sortie avec un bloc JSON après
    la ligne "═══...RÉSULTAT (JSON)═══...".
    
    Args:
        output: Sortie complète du programme (stdout)
        
    Returns:
        dict parsé ou None si extraction impossible
    """
    # Chercher le bloc JSON après "RÉSULTAT (JSON)"
    lignes = output.split('\n')
    json_debut = -1
    
    for i, ligne in enumerate(lignes):
        if 'RÉSULTAT' in ligne and 'JSON' in ligne:
            json_debut = i + 1
            break
    
    if json_debut < 0:
        # Essayer de trouver un JSON brut (commence par {)
        for i, ligne in enumerate(lignes):
            if ligne.strip().startswith('{'):
                json_debut = i
                break
    
    if json_debut < 0:
        return None
    
    # Collecter les lignes JSON
    json_lignes = []
    niveau_accolades = 0
    dans_json = False
    
    for ligne in lignes[json_debut:]:
        stripped = ligne.strip()
        
        if stripped.startswith('{'):
            dans_json = True
        
        if dans_json:
            json_lignes.append(ligne)
            niveau_accolades += stripped.count('{') - stripped.count('}')
            
            if niveau_accolades <= 0 and dans_json:
                break
    
    if not json_lignes:
        return None
    
    try:
        json_str = '\n'.join(json_lignes)
        return json.loads(json_str)
    except json.JSONDecodeError:
        return None


def tronquer_residu(residu: str, max_len: int = MAX_RESIDU_LEN) -> str:
    """Tronque le résidu s'il est trop long."""
    if not residu:
        return ""
    residu = residu.strip()
    if len(residu) <= max_len:
        return residu
    return residu[:max_len-3] + "..."


def synthetiser_dettags(data: dict) -> str:
    """Génère la synthèse pour dettags.py."""
    if not data:
        return "❌ pas de JSON"
    
    criteres = data.get('criteres', [])
    residu = data.get('residu', '')
    
    tags = []
    adjs = []
    
    for c in criteres:
        if c.get('type') == 'tag' or 'canonique' in c:
            tags.append(c.get('canonique', c.get('label', '?')))
            for adj in c.get('adjectifs', []):
                adj_val = adj.get('canonique', adj.get('forme_accordee', '?'))
                if adj_val:
                    adjs.append(adj_val)
    
    parties = []
    if tags:
        parties.append(f"{len(tags)} tag{'s' if len(tags)>1 else ''}: {', '.join(tags)}")
    else:
        parties.append("0 tag")
    
    if adjs:
        parties.append(f"{len(adjs)} adj{'s' if len(adjs)>1 else ''}: {', '.join(adjs)}")
    
    if residu:
        parties.append(f"residu: {tronquer_residu(residu)}")
    
    return " | ".join(parties)


def synthetiser_detage(data: dict) -> str:
    """Génère la synthèse pour detage.py."""
    if not data:
        return "❌ pas de JSON"
    
    criteres = data.get('criteres', [])
    residu = data.get('residu', '')
    
    labels = [c.get('label', '?') for c in criteres]
    
    parties = []
    if labels:
        parties.append(f"{len(labels)} crit: {', '.join(labels)}")
    else:
        parties.append("0 crit")
    
    if residu:
        parties.append(f"residu: {tronquer_residu(residu)}")
    
    return " | ".join(parties)


def synthetiser_detangles(data: dict) -> str:
    """Génère la synthèse pour detangles.py."""
    if not data:
        return "❌ pas de JSON"
    
    criteres = data.get('criteres', [])
    residu = data.get('residu', '')
    
    angles = [c.get('canonique', c.get('label', '?')) for c in criteres]
    
    parties = []
    if angles:
        parties.append(f"{len(angles)} angle{'s' if len(angles)>1 else ''}: {', '.join(angles)}")
    else:
        parties.append("0 angle")
    
    if residu:
        parties.append(f"residu: {tronquer_residu(residu)}")
    
    return " | ".join(parties)


def synthetiser_detall(data: dict) -> str:
    """Génère la synthèse pour detall.py (orchestrateur)."""
    if not data:
        return "❌ pas de JSON"
    
    listcount = data.get('listcount', 'LIST')
    criteres = data.get('criteres', [])
    residu = data.get('residu', '')
    
    tags = []
    ages = []
    
    for c in criteres:
        c_type = c.get('type', '')
        if c_type == 'tag':
            tags.append(c.get('canonique', c.get('label', '?')))
        elif c_type in ('age', 'sexe'):
            ages.append(c.get('label', '?'))
    
    parties = [listcount]
    
    if tags:
        parties.append(f"{len(tags)} tag{'s' if len(tags)>1 else ''}: {', '.join(tags[:3])}")
    else:
        parties.append("0 tag")
    
    if ages:
        parties.append(f"{len(ages)} age{'s' if len(ages)>1 else ''}: {', '.join(ages[:2])}")
    
    if residu:
        parties.append(f"residu: {tronquer_residu(residu, 20)}")
    
    return " | ".join(parties)


def synthetiser_detia(data: dict) -> str:
    """Génère la synthèse pour detia.py (détection IA)."""
    if not data:
        return "❌ pas de JSON"
    
    auteur = data.get('auteur', 'IA')
    criteres = data.get('criteres', [])
    latency = data.get('ia_latency_ms', 0)
    residu = data.get('residu', '')
    
    tags = []
    for c in criteres:
        if c.get('type') == 'tag':
            tags.append(c.get('canonique', c.get('label', '?')))
    
    # Extraire le nom court du modèle
    if '/' in auteur:
        modele = auteur.split('/')[-1]
    else:
        modele = auteur
    
    parties = [f"IA:{modele}"]
    
    if tags:
        parties.append(f"{len(tags)} tag{'s' if len(tags)>1 else ''}: {', '.join(tags[:3])}")
    else:
        parties.append("0 tag")
    
    if latency:
        parties.append(f"{latency:.0f}ms")
    
    if residu:
        parties.append(f"residu: {tronquer_residu(residu, 15)}")
    
    return " | ".join(parties)


def synthetiser_trouve(data: dict) -> str:
    """Génère la synthèse pour trouve.py (recherche base)."""
    if not data:
        return "❌ pas de JSON"
    
    nb = data.get('nb', 0)
    mode = data.get('mode', 'standard')
    temps = data.get('temps_total_ms', 0)
    erreur = data.get('erreur', data.get('erreur_sql', ''))
    
    if erreur:
        return f"❌ {erreur[:40]}"
    
    # Vérifier le garde-fou
    if data.get('gardefou'):
        return f"🛡️ garde-fou: {data.get('gardefou_raison', '?')[:30]}"
    
    parties = [f"{nb} patient{'s' if nb != 1 else ''}"]
    parties.append(mode)
    
    if temps:
        parties.append(f"{temps:.0f}ms")
    
    return " | ".join(parties)


def synthetiser_search(data: dict) -> str:
    """Génère la synthèse pour search.py (recherche multilingue)."""
    if not data:
        return "❌ pas de JSON"
    
    nb = data.get('nb_patients', data.get('nb', 0))
    mode = data.get('mode_detection', data.get('mode', 'standard'))
    temps = data.get('temps_ms', data.get('temps_total_ms', 0))
    erreur = data.get('erreur', '')
    parcours = data.get('parcours_detection', '')
    lang = data.get('lang', '')
    
    if erreur:
        return f"❌ {erreur[:40]}"
    
    parties = [f"{nb} patient{'s' if nb != 1 else ''}"]
    
    # Afficher le parcours s'il y a eu escalade
    if parcours and '→' in parcours:
        parties.append(parcours)
    else:
        parties.append(mode)
    
    if lang and lang != 'fr':
        parties.append(f"lang:{lang}")
    
    if temps:
        parties.append(f"{temps:.0f}ms")
    
    return " | ".join(parties)


def identifier_programme(template: str) -> str:
    """
    Identifie le programme à partir du template CLI.
    
    Args:
        template: Template comme "dettags.py Q" ou "trouve base.db -v Q"
        
    Returns:
        Nom du programme (dettags, detage, detangles, detall, detia, trouve, search)
    """
    template_lower = template.lower()
    
    # Ordre important : dettags avant detags (pour attraper la typo)
    if 'dettags' in template_lower:
        return 'dettags'
    elif 'detags' in template_lower:
        # Typo courante : detags au lieu de dettags
        return 'dettags'
    elif 'detage' in template_lower:
        return 'detage'
    elif 'detangles' in template_lower:
        return 'detangles'
    elif 'detall' in template_lower:
        return 'detall'
    elif 'detia' in template_lower:
        return 'detia'
    elif 'search' in template_lower:
        return 'search'
    elif 'trouve' in template_lower:
        return 'trouve'
    else:
        return 'inconnu'


def normaliser_commande(template: str, question: str) -> str:
    """
    Normalise un template CLI en commande exécutable.
    
    Corrections appliquées :
    1. Ajoute 'python ' si absent
    2. Ajoute '.py' au nom du programme si absent
    3. Corrige la typo 'detags' → 'dettags'
    4. Remplace Q par la question échappée
    
    Args:
        template: Template CLI (ex: "trouve base.db Q")
        question: Question à insérer
        
    Returns:
        Commande complète prête à exécuter
    """
    commande = template.strip()
    
    # Retirer 'python ' du début pour traiter le nom du programme
    if commande.lower().startswith('python '):
        commande = commande[7:].strip()
    
    # Identifier le premier mot (nom du programme)
    parties = commande.split(None, 1)  # Split sur le premier espace
    if not parties:
        return f'python {template}'
    
    programme = parties[0]
    reste = parties[1] if len(parties) > 1 else ''
    
    # Corriger la typo detags → dettags
    if programme.lower().startswith('detags'):
        programme = 'dettags' + programme[6:]
    
    # Ajouter .py si absent
    if not programme.lower().endswith('.py'):
        programme = programme + '.py'
    
    # Reconstruire la commande
    if reste:
        commande = f"{programme} {reste}"
    else:
        commande = programme
    
    # Échapper la question pour le shell (guillemets doubles)
    question_escaped = question.replace('"', '\\"')
    
    # Remplacer Q par la question
    # Attention : Q peut être au milieu ou à la fin
    commande = commande.replace(' Q ', f' "{question_escaped}" ')
    commande = commande.replace(' Q', f' "{question_escaped}"')
    if commande.endswith('Q'):
        commande = commande[:-1] + f'"{question_escaped}"'
    
    # Ajouter python au début
    commande = f"python {commande}"
    
    return commande


def synthetiser_resultat(programme: str, data: dict) -> str:
    """
    Génère la synthèse adaptée au programme.
    
    Args:
        programme: Nom du programme (dettags, detage, etc.)
        data: JSON parsé de la sortie
        
    Returns:
        Chaîne de synthèse lisible
    """
    syntheseurs = {
        'dettags': synthetiser_dettags,
        'detage': synthetiser_detage,
        'detangles': synthetiser_detangles,
        'detall': synthetiser_detall,
        'detia': synthetiser_detia,
        'trouve': synthetiser_trouve,
        'search': synthetiser_search,
    }
    
    if programme in syntheseurs:
        return syntheseurs[programme](data)
    else:
        # Synthèse générique
        if data:
            nb_criteres = len(data.get('criteres', []))
            return f"{nb_criteres} critère(s)"
        return "❌ inconnu"


def executer_commande(commande: str, timeout: int = TIMEOUT_DEFAUT) -> Tuple[str, str, int]:
    """
    Exécute une commande CLI et retourne la sortie.
    
    Args:
        commande: Commande à exécuter
        timeout: Timeout en secondes
        
    Returns:
        Tuple (stdout, stderr, returncode)
    """
    try:
        result = subprocess.run(
            commande,
            shell=True,
            capture_output=True,
            text=True,
            timeout=timeout,
            encoding='utf-8',
            errors='replace'
        )
        return result.stdout, result.stderr, result.returncode
    except subprocess.TimeoutExpired:
        return "", f"Timeout après {timeout}s", -1
    except Exception as e:
        return "", str(e), -1


def charger_batterie_csv(fichier: str) -> Tuple[List[str], List[str], List[List[str]]]:
    """
    Charge le fichier batterie.csv.
    
    Args:
        fichier: Chemin vers le fichier CSV
        
    Returns:
        Tuple (questions, templates, lignes_vides_ignorees)
        - questions: Liste des questions (colonne Q)
        - templates: Liste des templates CLI (entêtes colonnes 1+)
    """
    questions = []
    templates = []
    
    encodages = ["utf-8-sig", "utf-8", "windows-1252", "iso-8859-1"]
    
    for encodage in encodages:
        try:
            with open(fichier, 'r', encoding=encodage, newline='') as f:
                # Filtrer les commentaires
                lignes = [line for line in f if not line.strip().startswith('#')]
            
            if not lignes:
                continue
            
            reader = csv.reader(io.StringIO(''.join(lignes)), delimiter=';')
            rows = list(reader)
            
            if not rows:
                continue
            
            # Première ligne = entêtes
            entetes = rows[0]
            templates = [t.strip() for t in entetes[1:] if t.strip()]
            
            # Lignes suivantes = questions
            for row in rows[1:]:
                if row and row[0].strip():
                    questions.append(row[0].strip())
            
            return questions, templates, []
            
        except (UnicodeDecodeError, UnicodeError):
            continue
    
    return [], [], []


def traiter_batterie(
    fichier_entree: str,
    timeout: int = TIMEOUT_DEFAUT,
    verbose: bool = False,
    debug: bool = False
) -> Tuple[int, str]:
    """
    Traite un fichier batterie et génère le fichier résultat.
    
    Args:
        fichier_entree: Chemin vers batterie.csv
        timeout: Timeout par commande
        verbose: Mode verbose
        debug: Mode debug
        
    Returns:
        Tuple (nb_tests, fichier_sortie)
    """
    # Charger le fichier
    questions, templates, _ = charger_batterie_csv(fichier_entree)
    
    if not questions:
        print(f"[ERREUR] Aucune question trouvée dans {fichier_entree}")
        return 0, ""
    
    if not templates:
        print(f"[ERREUR] Aucun template CLI trouvé dans {fichier_entree}")
        return 0, ""
    
    print(f"Questions : {len(questions)}")
    print(f"Templates : {len(templates)}")
    for t in templates:
        prog = identifier_programme(t)
        print(f"  - {t} → {prog}")
    print()
    
    # Préparer la matrice de résultats
    resultats = []
    nb_tests = 0
    
    # Barre de progression
    total_tests = len(questions) * len(templates)
    
    for i, question in enumerate(questions, 1):
        ligne_resultat = {'question': question}
        
        for template in templates:
            # Construire la commande normalisée
            commande = normaliser_commande(template, question)
            
            if debug:
                print(f"[DEBUG] Template: {template}")
                print(f"[DEBUG] Commande: {commande}")
            
            # Exécuter
            stdout, stderr, returncode = executer_commande(commande, timeout)
            nb_tests += 1
            
            # Parser le JSON
            data = extraire_json_sortie(stdout)
            
            # Identifier le programme
            programme = identifier_programme(template)
            
            # Générer la synthèse
            if returncode != 0 and not data:
                if 'Timeout' in stderr:
                    synthese = f"⏱️ timeout {timeout}s"
                else:
                    synthese = f"❌ erreur (code {returncode})"
                    if debug and stderr:
                        # Afficher l'erreur complète en mode debug
                        print(f"\n[DEBUG] STDERR: {stderr[:200]}")
            else:
                synthese = synthetiser_resultat(programme, data)
            
            # Stocker avec le nom du programme comme clé
            ligne_resultat[programme] = synthese
            
            # Afficher la progression
            pct = 100 * nb_tests / total_tests
            if verbose:
                print(f"  [{nb_tests}/{total_tests}] {question[:30]}... × {programme} → {synthese[:40]}")
            else:
                print(f"\r[{'█' * int(pct/5)}{'░' * (20-int(pct/5))}] {pct:.0f}% - {nb_tests}/{total_tests}", end='', flush=True)
        
        resultats.append(ligne_resultat)
    
    if not verbose:
        print()  # Nouvelle ligne après la barre de progression
    
    # Générer le fichier de sortie
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    chemin_entree = Path(fichier_entree)
    nom_sortie = f"batterie_{timestamp}.csv"
    fichier_sortie = chemin_entree.parent / nom_sortie
    
    # Déterminer les colonnes de sortie
    colonnes = ['Q']
    programmes_uniques = []
    for template in templates:
        prog = identifier_programme(template)
        if prog not in programmes_uniques:
            programmes_uniques.append(prog)
            colonnes.append(prog)
    
    # Écrire le CSV
    with open(fichier_sortie, 'w', encoding='utf-8-sig', newline='') as f:
        writer = csv.writer(f, delimiter=';')
        
        # Commentaire
        writer.writerow([f'# Généré par {__pgm__} V{__version__} le {datetime.now().strftime("%d/%m/%Y %H:%M:%S")}'])
        writer.writerow([f'# Source: {fichier_entree}'])
        writer.writerow([f'# {len(questions)} questions × {len(templates)} tests = {nb_tests} tests'])
        
        # Entête
        writer.writerow(colonnes)
        
        # Données
        for res in resultats:
            row = [res['question']]
            for prog in programmes_uniques:
                row.append(res.get(prog, ''))
            writer.writerow(row)
    
    print(f"\n✓ {nb_tests} tests exécutés → {os.path.abspath(fichier_sortie)}")
    
    return nb_tests, str(fichier_sortie)


def trouver_fichier_batterie(nom: str) -> Optional[Path]:
    """Cherche le fichier batterie dans plusieurs répertoires."""
    chemin = Path(nom)
    if chemin.exists():
        return chemin
    
    repertoires = [
        Path('.'),
        Path('tests'),
        Path(__file__).parent / 'tests',
        Path('c:/g/tests'),
        Path('c:/g'),
    ]
    
    nom_seul = Path(nom).name
    
    for rep in repertoires:
        candidat = rep / nom_seul
        if candidat.exists():
            return candidat
    
    # Essayer batterie.csv par défaut
    for rep in repertoires:
        candidat = rep / 'batterie.csv'
        if candidat.exists():
            return candidat
    
    return None


def main():
    """Point d'entrée CLI."""
    print(f"╔════════════════════════════════════════════════════════════════")
    print(f"║ {__pgm__} V{__version__} - {__date__}")
    print(f"║ Tests en batterie des modules de détection KITVIEW")
    print(f"╚════════════════════════════════════════════════════════════════")
    print()
    
    parser = argparse.ArgumentParser(
        description="Exécute des tests en batterie sur les modules de détection"
    )
    parser.add_argument('fichier', nargs='?', default='batterie.csv',
                        help='Fichier CSV de test (défaut: batterie.csv)')
    parser.add_argument('-v', '--verbose', action='store_true',
                        help='Mode verbose (affiche chaque test)')
    parser.add_argument('-d', '--debug', action='store_true',
                        help='Mode debug (affiche les commandes)')
    parser.add_argument('-t', '--timeout', type=int, default=TIMEOUT_DEFAUT,
                        help=f'Timeout par commande en secondes (défaut: {TIMEOUT_DEFAUT})')
    
    args = parser.parse_args()
    
    # Trouver le fichier
    fichier = trouver_fichier_batterie(args.fichier)
    
    if fichier is None:
        print(f"[ERREUR] Fichier introuvable : {args.fichier}")
        print("  Chemins testés :")
        for rep in [Path('.'), Path('tests'), Path('c:/g/tests'), Path('c:/g')]:
            print(f"    - {(rep / args.fichier).absolute()}")
        return 1
    
    print(f"Fichier d'entrée : {fichier.absolute()}")
    print(f"Timeout          : {args.timeout}s par commande")
    print()
    
    # Traiter
    nb_tests, fichier_sortie = traiter_batterie(
        str(fichier),
        timeout=args.timeout,
        verbose=args.verbose,
        debug=args.debug
    )
    
    return 0 if nb_tests > 0 else 1


if __name__ == '__main__':
    sys.exit(main())
