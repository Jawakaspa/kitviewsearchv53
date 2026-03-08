# generepats.py V1.0.8 - 24/12/2025 17:39:09
__pgm__ = "generepats.py"
__version__ = "1.0.8"
__date__ = "24/12/2025 17:39:09"

"""
Génère des fichiers CSV de patients orthodontiques fictifs pour tester Kitview.
Usage: python generepats.py <nombre> [--silent]

Structure simplifiée : 9 colonnes de sortie uniquement.
"""

import sys
import os
import csv
import random
import time
from datetime import datetime, timedelta
from pathlib import Path
from collections import defaultdict

# Vérification Faker
try:
    from faker import Faker
except ImportError:
    print("ERREUR: La bibliothèque 'faker' n'est pas installée.")
    print("Installez-la avec: pip install faker")
    sys.exit(2)

# Tentative d'import tqdm
try:
    from tqdm import tqdm
    TQDM_AVAILABLE = True
except ImportError:
    TQDM_AVAILABLE = False

# ============================================================================
# CONSTANTES ET CONFIGURATION
# ============================================================================

SCRIPT_DIR = Path(__file__).parent.resolve()
REFS_DIR = SCRIPT_DIR / "refs"
DATA_DIR = SCRIPT_DIR / "data"
LOGS_DIR = SCRIPT_DIR / "logs"
STATS_DIR = SCRIPT_DIR / "stats"

# Fichiers de référence
PORTRAITS_FILE = REFS_DIR / "portraits.csv"
TAGS_FILE = REFS_DIR / "tags.csv"
ADJS_FILE = REFS_DIR / "adjectifs.csv"
SEXEORIGINE_FILE = REFS_DIR / "sexeorigine.csv"
COMMUN_FILE = REFS_DIR / "commun.csv"

# Seeds pour reproductibilité
SEED_GENERAL = 42
SEED_SEXE = 43
SEED_AGE = 44
SEED_TAGS = 45
SEED_ADJS = 46

# Distribution du nombre de tags
TAGS_DISTRIBUTION = [(1, 0.40), (2, 0.25), (3, 0.20), (4, 0.15)]

# Distribution des adjectifs
ADJS_DISTRIBUTION = [(0, 0.30), (1, 0.20), (2, 0.20), (3, 0.20), (4, 0.10)]

# Distribution spéciale des tags
TAG_BEANCE_WEIGHT = 0.20
TAG_BRUXISME_WEIGHT = 0.10
TAG_OTHER_WEIGHT = 0.70

# Colonnes de sortie (9 colonnes uniquement)
OUTPUT_COLUMNS = [
    "id", "canontags", "canonadjs", "sexe", "age", "datenaissance", "prenom", "nom", "idportrait"
]

# ============================================================================
# FONCTIONS UTILITAIRES
# ============================================================================

def load_csv_with_encoding(filepath: Path, silent: bool = False) -> list[dict]:
    """Charge un fichier CSV avec détection d'encodage, en ignorant les commentaires."""
    encodings = ['utf-8-sig', 'utf-8', 'windows-1252', 'iso-8859-1']
    
    for encoding in encodings:
        try:
            with open(filepath, 'r', encoding=encoding, newline='') as f:
                # Lire toutes les lignes et filtrer les commentaires
                lines = []
                for line in f:
                    stripped = line.strip()
                    if stripped and not stripped.startswith('#'):
                        lines.append(line)
                
                if not lines:
                    return []
                
                # Reconstruire le contenu sans commentaires
                content = ''.join(lines)
                reader = csv.DictReader(content.splitlines(), delimiter=';')
                data = list(reader)
                
                if encoding != 'utf-8-sig' and not silent:
                    print(f"  ⚠️  WARNING: {filepath.name} n'est pas en UTF-8-SIG (détecté: {encoding})")
                
                return data
        except (UnicodeDecodeError, UnicodeError):
            continue
    
    print(f"ERREUR: Impossible de lire {filepath} avec les encodages supportés")
    sys.exit(1)


def create_directories():
    """Crée les répertoires nécessaires."""
    for dir_path in [DATA_DIR, LOGS_DIR, STATS_DIR]:
        dir_path.mkdir(parents=True, exist_ok=True)


def weighted_choice(rand: random.Random, items: list, weights: list):
    """Sélection pondérée."""
    total = sum(weights)
    r = rand.random() * total
    cumulative = 0
    for item, weight in zip(items, weights):
        cumulative += weight
        if r <= cumulative:
            return item
    return items[-1]


def distribution_choice(rand: random.Random, distribution: list[tuple[int, float]]) -> int:
    """Choix basé sur une distribution (valeur, probabilité)."""
    values, probs = zip(*distribution)
    return weighted_choice(rand, values, probs)


def normalize_for_comparison(text: str) -> str:
    """Normalise un texte pour la comparaison (minuscules, espaces supprimés)."""
    return text.lower().strip()


# ============================================================================
# GESTION DES INCOMPATIBILITÉS
# ============================================================================

class IncompatibilityManager:
    """Gère les groupes d'adjectifs incompatibles."""
    
    def __init__(self):
        self.groups = []  # Liste de sets d'adjectifs incompatibles (en minuscules)
        self.adj_to_group = {}  # Mapping adjectif (minuscule) -> index du groupe
    
    def load_from_commun(self, commun_data: list[dict], silent: bool = False):
        """Charge les incompatibilités depuis commun.csv."""
        for row in commun_data:
            incomp_str = row.get('incompatibles', '').strip()
            if incomp_str:
                # Les adjectifs incompatibles sont séparés par des virgules
                # IMPORTANT: normaliser en minuscules et supprimer les espaces
                adjs = [a.strip().lower() for a in incomp_str.split(',') if a.strip()]
                if len(adjs) > 1:
                    group_idx = len(self.groups)
                    group_set = set(adjs)
                    self.groups.append(group_set)
                    
                    for adj in adjs:
                        # Un adjectif peut appartenir à un seul groupe (le premier trouvé)
                        if adj not in self.adj_to_group:
                            self.adj_to_group[adj] = group_idx
        
        if not silent:
            print(f"    → {len(self.groups)} groupes d'incompatibilités chargés")
            # Debug: afficher les groupes
            for i, group in enumerate(self.groups):
                sample = sorted(list(group))[:5]
                if len(group) > 5:
                    sample_str = ', '.join(sample) + f"... (+{len(group)-5})"
                else:
                    sample_str = ', '.join(sample)
                print(f"      Groupe {i}: [{sample_str}]")
    
    def filter_compatible(self, available_adjs: list[str], selected_adjs: list[str]) -> list[str]:
        """Filtre les adjectifs disponibles pour exclure ceux incompatibles avec les sélectionnés.
        
        IMPORTANT: La comparaison se fait en minuscules pour être insensible à la casse.
        """
        if not selected_adjs or not self.groups:
            return available_adjs
        
        # Trouver les groupes déjà utilisés par les adjectifs sélectionnés
        blocked_groups = set()
        for adj in selected_adjs:
            adj_lower = adj.lower()
            if adj_lower in self.adj_to_group:
                blocked_groups.add(self.adj_to_group[adj_lower])
        
        # Filtrer les adjectifs qui appartiennent à ces groupes bloqués
        result = []
        for adj in available_adjs:
            adj_lower = adj.lower()
            if adj_lower in self.adj_to_group:
                if self.adj_to_group[adj_lower] in blocked_groups:
                    continue  # Exclure cet adjectif car incompatible
            result.append(adj)
        
        return result
    
    def are_compatible(self, adj1: str, adj2: str) -> bool:
        """Vérifie si deux adjectifs sont compatibles."""
        adj1_lower = adj1.lower()
        adj2_lower = adj2.lower()
        
        # Si l'un des deux est dans un groupe d'incompatibilité
        if adj1_lower in self.adj_to_group:
            group_idx = self.adj_to_group[adj1_lower]
            if adj2_lower in self.groups[group_idx]:
                return False
        
        return True


# ============================================================================
# CHARGEMENT DES DONNÉES
# ============================================================================

class DataLoader:
    """Charge et prépare les données de référence."""
    
    def __init__(self, silent: bool = False):
        self.silent = silent
        self.portraits_f = []
        self.portraits_m = []
        self.sexeorigine_data = []
        self.canonical_tags = []
        self.tag_info = {}  # canon -> {genre, adjs_canon}
        self.adj_forms = {}  # adj_canon (MINUSCULE) -> {m, f, mp, fp}
        self.beance_index = -1
        self.bruxisme_index = -1
        self.incompatibility_manager = IncompatibilityManager()
        self.origine_by_sexe = {'M': [], 'F': []}
        
    def log(self, msg: str):
        if not self.silent:
            print(msg)
    
    def load_all(self):
        """Charge tous les fichiers de référence."""
        self._load_commun()
        self._load_portraits()
        self._load_adjs()
        self._load_tags()
        self._load_sexeorigine()
        
    def _load_commun(self):
        """Charge commun.csv pour les incompatibilités."""
        if not COMMUN_FILE.exists():
            self.log(f"  ⚠️  WARNING: {COMMUN_FILE.name} non trouvé, pas de gestion des incompatibilités")
            return
        
        data = load_csv_with_encoding(COMMUN_FILE, self.silent)
        self.log(f"  ✓ {COMMUN_FILE.absolute()}")
        self.incompatibility_manager.load_from_commun(data, self.silent)
    
    def _load_portraits(self):
        """Charge les portraits par sexe avec leur id."""
        if not PORTRAITS_FILE.exists():
            print(f"ERREUR: Fichier manquant: {PORTRAITS_FILE.absolute()}")
            sys.exit(1)
        
        data = load_csv_with_encoding(PORTRAITS_FILE, self.silent)
        for row in data:
            sexe = row.get('sexe', '').strip().upper()
            idportrait = row.get('idportrait', '').strip()
            if sexe == 'F':
                self.portraits_f.append(idportrait)
            elif sexe == 'M':
                self.portraits_m.append(idportrait)
        
        self.log(f"  ✓ {PORTRAITS_FILE.absolute()}")
        self.log(f"    → {len(self.portraits_f)} portraits F, {len(self.portraits_m)} portraits M")
    
    def _load_adjs(self):
        """Charge les adjectifs depuis adjectifs.csv (V2.1+).
        
        Colonnes : a;f;mp;fp;pas
        - a = forme canonique (= masculin singulier)
        - f = féminin singulier
        - mp = masculin pluriel
        - fp = féminin pluriel
        """
        if not ADJS_FILE.exists():
            print(f"ERREUR: Fichier manquant: {ADJS_FILE.absolute()}")
            sys.exit(1)
        
        data = load_csv_with_encoding(ADJS_FILE, self.silent)
        
        nb_adjectifs = 0
        for row in data:
            canon = row.get('a', '').strip()
            if not canon:
                continue
            
            canon_lower = canon.lower()
            self.adj_forms[canon_lower] = {
                'm': canon,
                'f': row.get('f', canon).strip() or canon,
                'mp': row.get('mp', canon).strip() or canon,
                'fp': row.get('fp', canon).strip() or canon
            }
            nb_adjectifs += 1
        
        self.log(f"  ✓ {ADJS_FILE.absolute()}")
        self.log(f"    → {nb_adjectifs} adjectifs avec formes accordées")
    
    def _load_tags(self):
        """Charge tous les tags depuis tags.csv (V2.1+).
        
        Colonnes : t;gn;as;pts;cat
        Tous les tags sont retenus (toutes catégories).
        """
        if not TAGS_FILE.exists():
            print(f"ERREUR: Fichier manquant: {TAGS_FILE.absolute()}")
            sys.exit(1)
        
        data = load_csv_with_encoding(TAGS_FILE, self.silent)
        
        nb_tags = 0
        cats_stats = defaultdict(int)
        
        for row in data:
            canon = row.get('t', '').strip()
            if not canon:
                continue
            
            # Genre du tag
            genre = row.get('gn', '').strip().lower()
            if not genre:
                genre = 'm'
            
            # Catégorie (pour stats)
            cat = row.get('cat', '').strip().lower()
            if cat:
                cats_stats[cat] += 1
            
            # Adjectifs canoniques associés (colonne as)
            adjs_str = row.get('as', '').strip()
            adjs_canon = []
            if adjs_str:
                adjs_canon = [a.strip() for a in adjs_str.split(',') if a.strip()]
            
            self.canonical_tags.append(canon)
            self.tag_info[canon] = {
                'genre': genre,
                'adjs_canon': adjs_canon
            }
            nb_tags += 1
            
            # Identifier béance et bruxisme
            canon_lower = canon.lower()
            if 'béance' in canon_lower or 'beance' in canon_lower:
                self.beance_index = len(self.canonical_tags) - 1
            elif 'bruxisme' in canon_lower:
                self.bruxisme_index = len(self.canonical_tags) - 1
        
        self.log(f"  ✓ {TAGS_FILE.absolute()}")
        self.log(f"    → {nb_tags} tags chargés (toutes catégories)")
        if cats_stats:
            cats_str = ', '.join(f"{k}={v}" for k, v in sorted(cats_stats.items()))
            self.log(f"    → Catégories : {cats_str}")
        self.log(f"    → {sum(1 for t in self.tag_info.values() if t['adjs_canon'])} tags avec adjectifs autorisés")
        
        if self.beance_index >= 0:
            self.log(f"    → Béance trouvé à l'index {self.beance_index}: {self.canonical_tags[self.beance_index]}")
        if self.bruxisme_index >= 0:
            self.log(f"    → Bruxisme trouvé à l'index {self.bruxisme_index}: {self.canonical_tags[self.bruxisme_index]}")
    
    def get_accorded_adj(self, adj_canon: str, genre: str) -> str:
        """Retourne la forme accordée d'un adjectif selon le genre.
        
        Args:
            adj_canon: L'adjectif en forme canonique (ex: "antérieur")
            genre: Le genre du tag (m, f, mp, fp)
            
        Returns:
            La forme accordée (ex: "antérieure" pour genre="f")
        """
        # Chercher avec clé en MINUSCULES
        adj_lower = adj_canon.lower()
        if adj_lower in self.adj_forms:
            forms = self.adj_forms[adj_lower]
            # Genre valide : m, f, mp, fp
            if genre in forms:
                return forms[genre]
        # Si non trouvé, retourner la forme canonique
        return adj_canon
    
    def _load_sexeorigine(self):
        """Charge les données d'origine des noms/prénoms."""
        if not SEXEORIGINE_FILE.exists():
            print(f"ERREUR: Fichier manquant: {SEXEORIGINE_FILE.absolute()}")
            sys.exit(1)
        
        data = load_csv_with_encoding(SEXEORIGINE_FILE, self.silent)
        self.sexeorigine_data = data
        
        # Organiser par sexe et origine
        for row in data:
            sexe = row.get('sexe', '').strip().upper()
            if sexe in self.origine_by_sexe:
                self.origine_by_sexe[sexe].append(row)
        
        self.log(f"  ✓ {SEXEORIGINE_FILE.absolute()}")
        self.log(f"    → {len(self.origine_by_sexe['M'])} entrées M, {len(self.origine_by_sexe['F'])} entrées F")


# ============================================================================
# GÉNÉRATEUR DE PATIENTS
# ============================================================================

class PatientGenerator:
    """Génère des patients fictifs."""
    
    def __init__(self, data_loader: DataLoader, silent: bool = False):
        self.data = data_loader
        self.silent = silent
        
        # Générateurs aléatoires avec seeds fixes
        self.rand_general = random.Random(SEED_GENERAL)
        self.rand_sexe = random.Random(SEED_SEXE)
        self.rand_age = random.Random(SEED_AGE)
        self.rand_tags = random.Random(SEED_TAGS)
        self.rand_adjs = random.Random(SEED_ADJS)
        
        # Faker
        Faker.seed(SEED_GENERAL)
        self.faker = Faker('fr_FR')
        
        # Date de référence (aujourd'hui)
        self.today = datetime.now()
        
        # Statistiques
        self.stats_tags = defaultdict(int)
        self.stats_tag_adj = defaultdict(int)
        self.stats_age = defaultdict(int)
        
    def generate(self, patient_id: int) -> dict:
        """Génère un patient avec 9 colonnes."""
        patient = {col: "" for col in OUTPUT_COLUMNS}
        patient['id'] = str(patient_id)
        
        # Sexe (50/50)
        sexe = 'F' if self.rand_sexe.random() < 0.5 else 'M'
        patient['sexe'] = sexe
        
        # Âge (gaussienne, moyenne 15, écart-type 6, borné 5-50)
        age = self.rand_age.gauss(15, 6)
        age = max(5, min(50, age))
        patient['age'] = f"{age:.3f}"
        self.stats_age[int(age)] += 1
        
        # Date de naissance
        days_old = age * 365.25
        birth_date = self.today - timedelta(days=days_old)
        patient['datenaissance'] = birth_date.strftime('%Y-%m-%d')
        
        # Portrait (idportrait uniquement)
        portraits = self.data.portraits_f if sexe == 'F' else self.data.portraits_m
        if portraits:
            idportrait = self.rand_general.choice(portraits)
            patient['idportrait'] = idportrait
        
        # Tags et adjectifs
        canontags, canonadjs = self._generate_tags_and_adjs()
        patient['canontags'] = canontags
        patient['canonadjs'] = canonadjs
        
        # Nom et prénom
        prenom, nom = self._generate_name(sexe)
        patient['prenom'] = prenom
        patient['nom'] = nom
        
        return patient
    
    def _generate_tags_and_adjs(self) -> tuple[str, str]:
        """Génère les tags et leurs adjectifs avec gestion des incompatibilités et accord en genre."""
        # Nombre de tags
        nb_tags = distribution_choice(self.rand_tags, TAGS_DISTRIBUTION)
        
        # Sélection des tags avec pondération spéciale pour béance et bruxisme
        selected_tags = []
        selected_indices = set()
        
        for _ in range(nb_tags):
            if len(selected_indices) >= len(self.data.canonical_tags):
                break
            
            # Déterminer quel type de tag sélectionner
            r = self.rand_tags.random()
            
            if r < TAG_BEANCE_WEIGHT and self.data.beance_index >= 0 and self.data.beance_index not in selected_indices:
                idx = self.data.beance_index
            elif r < TAG_BEANCE_WEIGHT + TAG_BRUXISME_WEIGHT and self.data.bruxisme_index >= 0 and self.data.bruxisme_index not in selected_indices:
                idx = self.data.bruxisme_index
            else:
                # Tag aléatoire parmi les autres
                available = [i for i in range(len(self.data.canonical_tags)) if i not in selected_indices]
                if not available:
                    break
                idx = self.rand_tags.choice(available)
            
            selected_indices.add(idx)
            selected_tags.append(self.data.canonical_tags[idx])
        
        # Générer les adjectifs pour chaque tag avec incompatibilités et accord
        all_adjs = []
        for tag in selected_tags:
            self.stats_tags[tag] += 1
            
            # Récupérer les infos du tag
            tag_info = self.data.tag_info.get(tag, {})
            available_adjs_canon = tag_info.get('adjs_canon', [])
            genre = tag_info.get('genre', 'm')  # Par défaut masculin
            
            if not available_adjs_canon:
                all_adjs.append([])
                continue
            
            # Nombre d'adjectifs pour ce tag
            nb_adjs = distribution_choice(self.rand_adjs, ADJS_DISTRIBUTION)
            nb_adjs = min(nb_adjs, len(available_adjs_canon))
            
            # Sélectionner les adjectifs en respectant les incompatibilités
            tag_adjs_canon = []  # Adjectifs en forme canonique (pour vérifier incompatibilités)
            tag_adjs_accorded = []  # Adjectifs accordés (pour sortie)
            remaining_adjs = available_adjs_canon.copy()
            
            for _ in range(nb_adjs):
                if not remaining_adjs:
                    break
                
                # Filtrer les adjectifs incompatibles avec ceux déjà sélectionnés
                # IMPORTANT: passer les formes canoniques pour la comparaison
                compatible_adjs = self.data.incompatibility_manager.filter_compatible(
                    remaining_adjs, tag_adjs_canon
                )
                
                if not compatible_adjs:
                    break
                
                # Sélectionner un adjectif canonique
                adj_canon = self.rand_adjs.choice(compatible_adjs)
                tag_adjs_canon.append(adj_canon)
                
                # Obtenir la forme accordée selon le genre du tag
                adj_accorded = self.data.get_accorded_adj(adj_canon, genre)
                tag_adjs_accorded.append(adj_accorded)
                
                remaining_adjs.remove(adj_canon)
            
            all_adjs.append(tag_adjs_accorded)
            
            # Stats avec forme accordée
            for adj in tag_adjs_accorded:
                self.stats_tag_adj[f"{tag}|{adj}"] += 1
        
        # Formater canontags et canonadjs
        canontags = ','.join(selected_tags)
        
        # canonadjs: adjectifs séparés par | pour un même tag, virgule entre tags
        canonadjs_parts = []
        for adjs in all_adjs:
            canonadjs_parts.append('|'.join(adjs))
        canonadjs = ','.join(canonadjs_parts)
        
        return canontags, canonadjs
    
    def _generate_name(self, sexe: str) -> tuple[str, str]:
        """Génère un nom et prénom."""
        # 75% Faker, 25% sexeorigine
        if self.rand_general.random() < 0.75:
            # Utiliser Faker
            if sexe == 'F':
                prenom = self.faker.first_name_female()
            else:
                prenom = self.faker.first_name_male()
            nom = self.faker.last_name()
        else:
            # Utiliser sexeorigine avec pondération
            entries = self.data.origine_by_sexe.get(sexe, [])
            if entries:
                # Sélection pondérée pour le nom
                noms = [(e['nom'], int(e.get('poidsnom', 1))) for e in entries if e.get('nom')]
                if noms:
                    items, weights = zip(*noms)
                    nom = weighted_choice(self.rand_general, items, weights)
                else:
                    nom = self.faker.last_name()
                
                # Sélection pondérée pour le prénom (même sexe)
                prenoms = [(e['prenom'], int(e.get('poidsprenom', 1))) for e in entries if e.get('prenom')]
                if prenoms:
                    items, weights = zip(*prenoms)
                    prenom = weighted_choice(self.rand_general, items, weights)
                else:
                    prenom = self.faker.first_name_female() if sexe == 'F' else self.faker.first_name_male()
            else:
                if sexe == 'F':
                    prenom = self.faker.first_name_female()
                else:
                    prenom = self.faker.first_name_male()
                nom = self.faker.last_name()
        
        return prenom, nom


# ============================================================================
# ÉCRITURE DES FICHIERS
# ============================================================================

def write_patients_csv(filepath: Path, patients: list[dict]):
    """Écrit le fichier patients CSV (9 colonnes)."""
    with open(filepath, 'w', encoding='utf-8-sig', newline='') as f:
        # Cartouche
        now = datetime.now().strftime('%d/%m/%Y %H:%M:%S')
        f.write(f"#{filepath.name} v1.0.0 - {now}\n")
        
        writer = csv.DictWriter(f, fieldnames=OUTPUT_COLUMNS, delimiter=';', extrasaction='ignore')
        writer.writeheader()
        writer.writerows(patients)


def write_stats_tags(filepath: Path, stats: dict):
    """Écrit les statistiques tags+adjectifs."""
    with open(filepath, 'w', encoding='utf-8-sig', newline='') as f:
        now = datetime.now().strftime('%d/%m/%Y %H:%M:%S')
        f.write(f"#{filepath.name} v1.0.0 - {now}\n")
        
        writer = csv.writer(f, delimiter=';')
        writer.writerow(['canontag', 'canonadj', 'effectif'])
        
        for key, count in sorted(stats.items(), key=lambda x: -x[1]):
            if '|' in key:
                tag, adj = key.split('|', 1)
            else:
                tag, adj = key, ''
            writer.writerow([tag, adj, count])


def write_stats_age(filepath: Path, stats: dict, total: int):
    """Écrit les statistiques d'âge."""
    with open(filepath, 'w', encoding='utf-8-sig', newline='') as f:
        now = datetime.now().strftime('%d/%m/%Y %H:%M:%S')
        f.write(f"#{filepath.name} v1.0.0 - {now}\n")
        
        writer = csv.writer(f, delimiter=';')
        writer.writerow(['age', 'effectif', 'pourcentage'])
        
        for age in sorted(stats.keys()):
            count = stats[age]
            pct = (count / total * 100) if total > 0 else 0
            writer.writerow([age, count, f"{pct:.2f}"])


# ============================================================================
# MAIN
# ============================================================================

def main():
    print(f"{__pgm__} V{__version__} - {__date__}")
    print("=" * 60)
    
    # Arguments
    if len(sys.argv) < 2:
        print("Usage: python generepats.py <nombre> [--silent]")
        print("  <nombre>: Nombre de patients à générer (2 à 200000)")
        print("  --silent: Mode silencieux (optionnel)")
        sys.exit(1)
    
    try:
        nb_patients = int(sys.argv[1])
        if nb_patients < 2 or nb_patients > 200000:
            print(f"ERREUR: Le nombre de patients doit être entre 2 et 200000 (reçu: {nb_patients})")
            sys.exit(1)
    except ValueError:
        print(f"ERREUR: '{sys.argv[1]}' n'est pas un nombre valide")
        sys.exit(1)
    
    silent = '--silent' in sys.argv
    
    print(f"\n📊 Génération de {nb_patients:,} patients".replace(',', ' '))
    
    # Chronomètre
    time_start = time.time()
    
    # Créer les répertoires
    create_directories()
    
    # Charger les données
    print("\n📁 Chargement des fichiers de référence...")
    time_load_start = time.time()
    
    loader = DataLoader(silent=silent)
    try:
        loader.load_all()
    except Exception as e:
        print(f"ERREUR lors du chargement: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    
    time_load = time.time() - time_load_start
    
    # Vérifications
    if not loader.canonical_tags:
        print("ERREUR: Aucun tag chargé")
        sys.exit(1)
    
    if not loader.portraits_f and not loader.portraits_m:
        print("ERREUR: Aucun portrait chargé")
        sys.exit(1)
    
    # Générer les patients
    print(f"\n🔄 Génération des patients...")
    time_gen_start = time.time()
    
    generator = PatientGenerator(loader, silent=silent)
    patients = []
    
    if TQDM_AVAILABLE and not silent:
        iterator = tqdm(range(1, nb_patients + 1), desc="Patients", unit="pat", 
                       bar_format='[{bar:20}] {percentage:3.0f}% - Patient {n}/{total}')
    else:
        iterator = range(1, nb_patients + 1)
    
    try:
        for i in iterator:
            patient = generator.generate(i)
            patients.append(patient)
            
            # Affichage progression sans tqdm
            if not TQDM_AVAILABLE and not silent and i % 500 == 0:
                pct = i / nb_patients * 100
                bar_filled = int(pct / 5)
                bar = '█' * bar_filled + '░' * (20 - bar_filled)
                print(f"\r[{bar}] {pct:3.0f}% - Patient {i}/{nb_patients}", end='', flush=True)
        
        if not TQDM_AVAILABLE and not silent:
            print()  # Nouvelle ligne après la barre
            
    except KeyboardInterrupt:
        print("\n\n⚠️  Interruption utilisateur")
        sys.exit(0)
    except Exception as e:
        print(f"\nERREUR lors de la génération: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(3)
    
    time_gen = time.time() - time_gen_start
    
    # Écrire les fichiers
    print(f"\n💾 Écriture des fichiers...")
    time_write_start = time.time()
    
    try:
        # Fichier patients
        patients_file = DATA_DIR / f"pats{nb_patients}.csv"
        write_patients_csv(patients_file, patients)
        print(f"  ✓ {patients_file.absolute()}")
        
        # Stats tags
        stats_tags_file = STATS_DIR / f"stats{nb_patients}_tags.csv"
        # Combiner stats_tags et stats_tag_adj
        combined_stats = {}
        for tag, count in generator.stats_tags.items():
            combined_stats[tag] = count
        for key, count in generator.stats_tag_adj.items():
            combined_stats[key] = count
        write_stats_tags(stats_tags_file, combined_stats)
        print(f"  ✓ {stats_tags_file.absolute()}")
        
        # Stats age
        stats_age_file = STATS_DIR / f"stats{nb_patients}_age.csv"
        write_stats_age(stats_age_file, generator.stats_age, nb_patients)
        print(f"  ✓ {stats_age_file.absolute()}")
        
    except Exception as e:
        print(f"ERREUR lors de l'écriture: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(4)
    
    time_write = time.time() - time_write_start
    time_total = time.time() - time_start
    
    # Récapitulatif
    print("\n" + "=" * 60)
    print("📋 RÉCAPITULATIF")
    print("=" * 60)
    
    print(f"\n✅ {nb_patients:,} patients générés".replace(',', ' '))
    
    # Fichiers créés
    print("\n📁 Fichiers créés:")
    for fpath in [patients_file, stats_tags_file, stats_age_file]:
        size = fpath.stat().st_size
        if size > 1024 * 1024:
            size_str = f"{size / 1024 / 1024:.2f} Mo"
        elif size > 1024:
            size_str = f"{size / 1024:.2f} Ko"
        else:
            size_str = f"{size} octets"
        print(f"  • {fpath.absolute()} ({size_str})")
    
    # Temps d'exécution
    print("\n⏱️  Temps d'exécution:")
    print(f"  • Chargement:  {time_load:.3f}s")
    print(f"  • Génération:  {time_gen:.3f}s")
    print(f"  • Écriture:    {time_write:.3f}s")
    print(f"  • TOTAL:       {time_total:.3f}s")
    if time_gen > 0:
        print(f"  • Vitesse:     {nb_patients / time_gen:.0f} patients/s")
    
    # TOP 10 tags
    print("\n🏷️  TOP 10 tags:")
    sorted_tags = sorted(generator.stats_tags.items(), key=lambda x: -x[1])[:10]
    for i, (tag, count) in enumerate(sorted_tags, 1):
        pct = count / nb_patients * 100
        print(f"  {i:2}. {tag}: {count:,} ({pct:.1f}%)".replace(',', ' '))
    
    # TOP 10 tags+adjectifs
    print("\n🏷️  TOP 10 tags+adjectifs:")
    sorted_tag_adj = sorted(generator.stats_tag_adj.items(), key=lambda x: -x[1])[:10]
    for i, (key, count) in enumerate(sorted_tag_adj, 1):
        tag, adj = key.split('|', 1) if '|' in key else (key, '')
        pct = count / nb_patients * 100
        print(f"  {i:2}. {tag} + {adj}: {count:,} ({pct:.1f}%)".replace(',', ' '))
    
    # Répartition par tranches d'âge
    print("\n📊 Répartition par tranches d'âge:")
    age_ranges = [(5, 10), (11, 15), (16, 20), (21, 30), (31, 50)]
    for start, end in age_ranges:
        count = sum(generator.stats_age.get(a, 0) for a in range(start, end + 1))
        pct = count / nb_patients * 100
        print(f"  • {start}-{end} ans: {count:,} ({pct:.1f}%)".replace(',', ' '))
    
    print("\n✅ Génération terminée avec succès!")
    sys.exit(0)


if __name__ == "__main__":
    main()
