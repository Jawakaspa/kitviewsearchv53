# questions.py V1.0.2 - 17/12/2025 15:14:32
__pgm__ = "questions.py"
__version__ = "1.0.2"
__date__ = "17/12/2025 15:14:32"

"""
Générateur de questions de test pour le système de recherche orthodontique.
Génère un fichier de questions (qfichier.csv) et un fichier patients modifié (mfichier.csv)
pour garantir que chaque question matche 2-10% des patients.

v2.0.0 : Migration vers tagsadjs.csv + incompatibilités depuis commun.csv
"""

import csv
import sys
import os
import random
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional
from tqdm import tqdm

# ═══════════════════════════════════════════════════════════════════════════════
# CONFIGURATION
# ═══════════════════════════════════════════════════════════════════════════════

ENCODING = "utf-8-sig"
SEP = ";"
MULTI_SEP = ","
ADJ_SEP = "|"

# Répertoires
SCRIPT_DIR = Path(__file__).parent.resolve()
REFS_DIR = SCRIPT_DIR / "refs"

# Fichiers de référence (dans refs/)
TAGSADJS_FILE = REFS_DIR / "tagsadjs.csv"
AGES_FILE = REFS_DIR / "ages.csv"
COMMUN_FILE = REFS_DIR / "commun.csv"

# Pourcentage min/max de patients matchant chaque question
MIN_MATCH_PERCENT = 2
MAX_MATCH_PERCENT = 10

# Nombre de questions par niveau de critères
QUESTIONS_PER_LEVEL = 25

# Plage d'âge pour les patterns avec {n}
AGE_MIN = 5
AGE_MAX = 30


# ═══════════════════════════════════════════════════════════════════════════════
# FONCTIONS UTILITAIRES
# ═══════════════════════════════════════════════════════════════════════════════

def load_csv_with_encoding(filepath: Path) -> list[dict]:
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
                reader = csv.DictReader(content.splitlines(), delimiter=SEP)
                data = list(reader)
                
                if encoding != 'utf-8-sig':
                    print(f"  ⚠️  WARNING: {filepath.name} n'est pas en UTF-8-SIG (détecté: {encoding})")
                
                return data
        except (UnicodeDecodeError, UnicodeError):
            continue
    
    print(f"ERREUR: Impossible de lire {filepath} avec les encodages supportés")
    sys.exit(1)


# ═══════════════════════════════════════════════════════════════════════════════
# STRUCTURES DE DONNÉES
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class AdjInfo:
    """Information sur un adjectif."""
    canon: str  # Forme canonique (ex: "antérieur")
    synonyms: list[str] = field(default_factory=list)  # Synonymes
    forms: dict = field(default_factory=dict)  # Formes accordées: {m, f, mp, fp}
    
    def get_form(self, genre: str) -> str:
        """Retourne la forme accordée selon le genre."""
        return self.forms.get(genre, self.canon)
    
    def get_all_forms(self) -> list[str]:
        """Retourne toutes les formes (pour synonymes)."""
        all_forms = [self.canon] + self.synonyms
        for form in self.forms.values():
            if form and form not in all_forms:
                all_forms.append(form)
        return all_forms


@dataclass
class TagInfo:
    """Information sur un tag (pathologie)."""
    canon: str  # Forme canonique
    synonyms: list[str] = field(default_factory=list)  # Synonymes
    genre: str = "m"  # Genre du tag (m, f, mp, fp)
    adj_canons: list[str] = field(default_factory=list)  # Adjectifs canoniques associés
    adj_groups: list[list[str]] = field(default_factory=list)  # Groupes [forme_accordée, synonymes...]
    
    def get_canonical_adjs(self) -> list[str]:
        """Retourne les adjectifs canoniques accordés (premier de chaque groupe)."""
        return [group[0] for group in self.adj_groups if group]
    
    def get_random_synonym(self) -> str:
        """Retourne un synonyme aléatoire (incluant la forme canonique)."""
        all_forms = [self.canon] + self.synonyms
        return random.choice(all_forms)
    
    def get_random_adj_synonym(self, accorded_adj: str) -> str:
        """Retourne un synonyme aléatoire pour un adjectif accordé donné."""
        for group in self.adj_groups:
            if group and group[0].lower() == accorded_adj.lower():
                return random.choice(group)
        return accorded_adj


@dataclass
class AgePattern:
    """Pattern d'âge/sexe."""
    expressions: list[str]  # Expressions possibles
    operator: str  # Opérateur SQL (>=, <, BETWEEN, etc.)
    value_sql: str  # Valeur SQL
    sexe: Optional[str]  # M, F ou None
    label: str  # Libellé pour affichage
    has_variable: bool = False  # Contient {n} ?
    
    def get_random_expression(self, n_value: Optional[int] = None) -> str:
        """Retourne une expression aléatoire, avec remplacement de {n} si nécessaire."""
        expr = random.choice(self.expressions)
        if self.has_variable and n_value is not None:
            expr = expr.replace("{n}", str(n_value))
        return expr
    
    def get_label(self, n_value: Optional[int] = None) -> str:
        """Retourne le label avec remplacement de {n} si nécessaire."""
        label = self.label
        if self.has_variable and n_value is not None:
            label = label.replace("{n}", str(n_value))
        return label
    
    def matches_age(self, age: float, n_value: Optional[int] = None) -> bool:
        """Vérifie si un âge correspond au pattern."""
        if self.operator == ">=":
            val = int(self.value_sql) if not self.has_variable else n_value
            return age >= val
        elif self.operator == ">":
            val = int(self.value_sql.replace("{1}", str(n_value))) if self.has_variable else int(self.value_sql)
            return age > val
        elif self.operator == "<":
            val = int(self.value_sql.replace("{1}", str(n_value))) if self.has_variable else int(self.value_sql)
            return age < val
        elif self.operator == "<=":
            val = int(self.value_sql.replace("{1}", str(n_value))) if self.has_variable else int(self.value_sql)
            return age <= val
        elif self.operator == "BETWEEN":
            # Parse BETWEEN x AND y
            val_sql = self.value_sql
            if self.has_variable and n_value is not None:
                val_sql = val_sql.replace("{1}", str(n_value))
                val_sql = val_sql.replace("{2}", str(n_value + 5))  # Pour les ranges {n} à {n}
            
            if "BETWEEN" in val_sql:
                parts = val_sql.replace("BETWEEN", "").strip().split("AND")
                if len(parts) == 2:
                    try:
                        low = eval(parts[0].strip())
                        high = eval(parts[1].strip())
                        return low <= age <= high
                    except:
                        return False
            return False
        elif self.operator == "":
            # Pas de condition d'âge, juste sexe
            return True
        return False


@dataclass
class Patient:
    """Données d'un patient."""
    id: int
    canontags: list[str]
    canonadjs: list[list[str]]  # Pour chaque tag, liste des adjectifs
    sexe: str
    age: float
    datenaissance: str
    prenom: str
    nom: str
    portrait: str
    
    def has_tag(self, tag: str) -> bool:
        """Vérifie si le patient a un tag donné."""
        return tag.lower() in [t.lower() for t in self.canontags]
    
    def has_tag_with_adjs(self, tag: str, required_adjs: list[str]) -> bool:
        """Vérifie si le patient a un tag avec les adjectifs requis."""
        for i, t in enumerate(self.canontags):
            if t.lower() == tag.lower():
                if not required_adjs:
                    return True
                patient_adjs = self.canonadjs[i] if i < len(self.canonadjs) else []
                patient_adjs_lower = [a.lower() for a in patient_adjs]
                return all(adj.lower() in patient_adjs_lower for adj in required_adjs)
        return False


@dataclass
class Criterion:
    """Un critère de question."""
    type: str  # "tag", "age", "sexe"
    
    # Pour les tags
    tag_canon: Optional[str] = None
    adjs_canon: list[str] = field(default_factory=list)
    tag_syn: Optional[str] = None
    adjs_syn: list[str] = field(default_factory=list)
    
    # Pour âge/sexe
    pattern: Optional[AgePattern] = None
    n_value: Optional[int] = None
    expression_syn: Optional[str] = None
    
    def get_canon_str(self) -> str:
        """Retourne la représentation canonique."""
        if self.type == "tag":
            parts = [self.tag_canon] + self.adjs_canon
            return " ".join(parts)
        elif self.type in ("age", "sexe"):
            return self.pattern.get_label(self.n_value) if self.pattern else ""
        return ""
    
    def get_syn_str(self) -> str:
        """Retourne la représentation avec synonymes."""
        if self.type == "tag":
            parts = [self.tag_syn or self.tag_canon] + self.adjs_syn
            return " ".join(parts)
        elif self.type in ("age", "sexe"):
            return self.expression_syn or self.get_canon_str()
        return ""


@dataclass
class Question:
    """Une question générée."""
    criteria: list[Criterion] = field(default_factory=list)
    text: str = ""
    nb: int = 0
    ids: list[int] = field(default_factory=list)
    extrait: str = ""


# ═══════════════════════════════════════════════════════════════════════════════
# GESTION DES INCOMPATIBILITÉS (depuis commun.csv)
# ═══════════════════════════════════════════════════════════════════════════════

class IncompatibilityManager:
    """Gère les groupes d'adjectifs incompatibles chargés depuis commun.csv."""
    
    def __init__(self):
        self.groups = []  # Liste de sets d'adjectifs incompatibles
        self.adj_to_group = {}  # Mapping adjectif -> index du groupe
    
    def load_from_file(self, filepath: Path):
        """Charge les incompatibilités depuis commun.csv."""
        if not filepath.exists():
            print(f"[WARNING] Fichier commun.csv non trouvé: {filepath.absolute()}")
            print("[WARNING] Pas de gestion des incompatibilités")
            return
        
        data = load_csv_with_encoding(filepath)
        
        for row in data:
            incomp_str = row.get('incompatibles', '').strip()
            if incomp_str:
                # Les adjectifs incompatibles sont séparés par des virgules
                adjs = [a.strip().lower() for a in incomp_str.split(',') if a.strip()]
                if len(adjs) > 1:
                    group_idx = len(self.groups)
                    group_set = set(adjs)
                    self.groups.append(group_set)
                    
                    for adj in adjs:
                        self.adj_to_group[adj] = group_idx
        
        print(f"[DEBUG] {len(self.groups)} groupes d'incompatibilités chargés depuis {filepath.absolute()}")
    
    def are_compatible(self, adj1: str, adj2: str) -> bool:
        """Vérifie si deux adjectifs sont compatibles."""
        adj1_lower = adj1.lower()
        adj2_lower = adj2.lower()
        
        # Si l'un des deux est dans un groupe d'incompatibilité
        if adj1_lower in self.adj_to_group:
            group_idx = self.adj_to_group[adj1_lower]
            if adj2_lower in self.groups[group_idx]:
                return False
        
        if adj2_lower in self.adj_to_group:
            group_idx = self.adj_to_group[adj2_lower]
            if adj1_lower in self.groups[group_idx]:
                return False
        
        return True
    
    def filter_compatible(self, available_adjs: list[str], selected_adjs: list[str]) -> list[str]:
        """Filtre les adjectifs disponibles pour exclure ceux incompatibles avec les sélectionnés."""
        if not selected_adjs:
            return available_adjs
        
        result = []
        for adj in available_adjs:
            if all(self.are_compatible(adj, sel) for sel in selected_adjs):
                result.append(adj)
        
        return result


# Instance globale du gestionnaire d'incompatibilités
incompatibility_manager = IncompatibilityManager()


# ═══════════════════════════════════════════════════════════════════════════════
# CHARGEMENT DES DONNÉES
# ═══════════════════════════════════════════════════════════════════════════════

def load_adjectives(filepath: Path) -> dict[str, AdjInfo]:
    """Charge les adjectifs (type=a) depuis tagsadjs.csv."""
    adjectives = {}
    
    data = load_csv_with_encoding(filepath)
    
    for row in data:
        if row.get("type") != "a":
            continue
        
        canon = row.get("canon", "").strip()
        if not canon:
            continue
        
        # Synonymes
        synonyms_str = row.get("synonymes", "")
        synonyms = [s.strip() for s in synonyms_str.split(MULTI_SEP) if s.strip()]
        
        # Formes accordées
        forms = {
            'm': row.get('m', canon).strip() or canon,
            'f': row.get('f', canon).strip() or canon,
            'mp': row.get('mp', canon).strip() or canon,
            'fp': row.get('fp', canon).strip() or canon
        }
        
        adjectives[canon.lower()] = AdjInfo(
            canon=canon,
            synonyms=synonyms,
            forms=forms
        )
    
    return adjectives


def load_tags(filepath: Path, adjectives: dict[str, AdjInfo]) -> dict[str, TagInfo]:
    """Charge les tags (type=p) depuis tagsadjs.csv."""
    tags = {}
    
    data = load_csv_with_encoding(filepath)
    
    for row in data:
        if row.get("type") != "p":
            continue
            
        canon = row.get("canon", "").strip()
        if not canon:
            continue
        
        # Genre du tag
        genre = row.get("Xgn", "m").strip().lower() or "m"
        
        # Synonymes du tag
        synonyms_str = row.get("synonymes", "")
        synonyms = [s.strip() for s in synonyms_str.split(MULTI_SEP) if s.strip()]
        
        # Adjectifs canoniques associés
        adjs_str = row.get("adjs", "")
        adj_canons = [a.strip() for a in adjs_str.split(MULTI_SEP) if a.strip()]
        
        # Construire les groupes d'adjectifs [forme_accordée, synonymes...]
        adj_groups = []
        for adj_canon in adj_canons:
            adj_info = adjectives.get(adj_canon.lower())
            if adj_info:
                # Forme accordée selon le genre du tag
                accorded_form = adj_info.get_form(genre)
                # Groupe = [forme accordée, synonymes de l'adjectif]
                group = [accorded_form] + adj_info.synonyms
                adj_groups.append(group)
            else:
                # Adjectif non trouvé, utiliser tel quel
                adj_groups.append([adj_canon])
        
        tags[canon.lower()] = TagInfo(
            canon=canon,
            synonyms=synonyms,
            genre=genre,
            adj_canons=adj_canons,
            adj_groups=adj_groups
        )
    
    return tags


def load_age_patterns(filepath: Path) -> list[AgePattern]:
    """Charge les patterns d'âge depuis ages.csv."""
    patterns = []
    
    data = load_csv_with_encoding(filepath)
    
    for row in data:
        expressions_str = row.get("expression", "")
        if not expressions_str.strip():
            continue
        
        expressions = [e.strip() for e in expressions_str.split(ADJ_SEP) if e.strip()]
        operator = row.get("operateur", "").strip()
        value_sql = row.get("valeur_sql", "").strip()
        sexe = row.get("sexe", "").strip() or None
        label = row.get("label", "").strip()
        
        has_variable = "{n}" in expressions_str or "{1}" in value_sql
        
        patterns.append(AgePattern(
            expressions=expressions,
            operator=operator,
            value_sql=value_sql,
            sexe=sexe,
            label=label,
            has_variable=has_variable
        ))
    
    return patterns


def load_patients(filepath: Path) -> list[Patient]:
    """Charge les patients depuis le fichier CSV."""
    patients = []
    
    data = load_csv_with_encoding(filepath)
    
    for row in data:
        id_val = int(row.get("id", 0))
        
        # Tags
        canontags_str = row.get("canontags", "")
        canontags = [t.strip() for t in canontags_str.split(MULTI_SEP) if t.strip()]
        
        # Adjectifs (alignés avec les tags)
        canonadjs_str = row.get("canonadjs", "")
        canonadjs_parts = canonadjs_str.split(MULTI_SEP) if canonadjs_str else []
        canonadjs = []
        for part in canonadjs_parts:
            if part.strip():
                adjs = [a.strip() for a in part.split(ADJ_SEP) if a.strip()]
                canonadjs.append(adjs)
            else:
                canonadjs.append([])
        
        patients.append(Patient(
            id=id_val,
            canontags=canontags,
            canonadjs=canonadjs,
            sexe=row.get("sexe", "").strip(),
            age=float(row.get("age", 0)),
            datenaissance=row.get("datenaissance", ""),
            prenom=row.get("prenom", ""),
            nom=row.get("nom", ""),
            portrait=row.get("portrait", "")
        ))
    
    return patients


# ═══════════════════════════════════════════════════════════════════════════════
# GÉNÉRATION DES QUESTIONS
# ═══════════════════════════════════════════════════════════════════════════════

def select_compatible_adjs(tag_info: TagInfo, n_adjs: int) -> list[str]:
    """Sélectionne n adjectifs canoniques accordés compatibles entre eux."""
    if n_adjs == 0 or not tag_info.adj_groups:
        return []
    
    canonical_adjs = tag_info.get_canonical_adjs()
    if not canonical_adjs:
        return []
    
    selected = []
    available = canonical_adjs.copy()
    
    for _ in range(min(n_adjs, len(available))):
        # Filtrer les adjectifs incompatibles avec ceux déjà sélectionnés
        compatible = incompatibility_manager.filter_compatible(available, selected)
        
        if not compatible:
            break
        
        chosen = random.choice(compatible)
        selected.append(chosen)
        available.remove(chosen)
    
    return selected


def generate_tag_criterion(tags: dict[str, TagInfo]) -> Criterion:
    """Génère un critère de type tag avec équiprobabilité sur le nombre d'adjectifs."""
    tag_info = random.choice(list(tags.values()))
    
    # Équiprobabilité: 0 à n adjectifs
    n_adj_groups = len(tag_info.adj_groups)
    n_adjs = random.randint(0, n_adj_groups)
    
    adjs_canon = select_compatible_adjs(tag_info, n_adjs)
    
    # Synonymes
    tag_syn = tag_info.get_random_synonym()
    adjs_syn = [tag_info.get_random_adj_synonym(adj) for adj in adjs_canon]
    
    return Criterion(
        type="tag",
        tag_canon=tag_info.canon,
        adjs_canon=adjs_canon,
        tag_syn=tag_syn,
        adjs_syn=adjs_syn
    )


def generate_age_criterion(patterns: list[AgePattern], sexe_only: bool = False, 
                           patients: list[Patient] = None) -> Criterion:
    """Génère un critère d'âge ou de sexe.
    
    Si patients est fourni, vérifie que le pattern matche au moins quelques patients.
    """
    # Filtrer les patterns
    if sexe_only:
        valid_patterns = [p for p in patterns if p.sexe and not p.operator]
    else:
        valid_patterns = [p for p in patterns if p.operator]
    
    if not valid_patterns:
        valid_patterns = patterns
    
    # Mélanger pour éviter les biais
    random.shuffle(valid_patterns)
    
    for pattern in valid_patterns:
        # Valeur pour {n} si nécessaire
        n_value = None
        if pattern.has_variable:
            n_value = random.randint(AGE_MIN, AGE_MAX)
        
        # Vérifier que le pattern matche suffisamment de patients
        if patients:
            matching_count = 0
            for p in patients:
                if pattern.sexe and p.sexe != pattern.sexe:
                    continue
                if pattern.operator and not pattern.matches_age(p.age, n_value):
                    continue
                matching_count += 1
            
            # Si moins de 5% de match, essayer un autre pattern ou une autre valeur n
            if matching_count < len(patients) * 0.05:
                # Essayer avec une autre valeur de n si variable
                if pattern.has_variable:
                    for _ in range(5):  # 5 tentatives
                        n_value = random.randint(AGE_MIN, AGE_MAX)
                        matching_count = sum(1 for p in patients 
                                            if (not pattern.sexe or p.sexe == pattern.sexe) and
                                               pattern.matches_age(p.age, n_value))
                        if matching_count >= len(patients) * 0.05:
                            break
                    else:
                        continue  # Essayer un autre pattern
                else:
                    continue  # Essayer un autre pattern
        
        expression_syn = pattern.get_random_expression(n_value)
        
        crit_type = "sexe" if pattern.sexe and not pattern.operator else "age"
        if pattern.sexe and pattern.operator:
            crit_type = "sexe"  # Pattern comme "femme" qui inclut âge+sexe
        
        return Criterion(
            type=crit_type,
            pattern=pattern,
            n_value=n_value,
            expression_syn=expression_syn
        )
    
    # Fallback: prendre le premier pattern disponible
    pattern = valid_patterns[0] if valid_patterns else patterns[0]
    n_value = random.randint(AGE_MIN, AGE_MAX) if pattern.has_variable else None
    expression_syn = pattern.get_random_expression(n_value)
    
    crit_type = "sexe" if pattern.sexe and not pattern.operator else "age"
    if pattern.sexe and pattern.operator:
        crit_type = "sexe"
    
    return Criterion(
        type=crit_type,
        pattern=pattern,
        n_value=n_value,
        expression_syn=expression_syn
    )


def generate_question_text(criteria: list[Criterion]) -> str:
    """Génère le texte de la question à partir des critères (version synonymes)."""
    parts = []
    
    for crit in criteria:
        parts.append(crit.get_syn_str())
    
    if len(parts) == 1:
        return f"Quels sont les patients avec {parts[0]} ?"
    elif len(parts) == 2:
        return f"Quels sont les patients avec {parts[0]} et {parts[1]} ?"
    else:
        main_parts = ", ".join(parts[:-1])
        return f"Quels sont les patients avec {main_parts} et {parts[-1]} ?"


def generate_questions(tags: dict[str, TagInfo], patterns: list[AgePattern],
                       patients: list[Patient] = None) -> list[Question]:
    """Génère les 100 questions (25 par niveau de critères)."""
    questions = []
    
    for n_criteria in range(1, 5):
        print(f"[DEBUG] Génération des questions à {n_criteria} critère(s)...")
        
        for q_idx in tqdm(range(QUESTIONS_PER_LEVEL), desc=f"{n_criteria} critère(s)"):
            criteria = []
            has_age = False
            has_sexe = False
            
            # Décider de la composition des critères
            # Max 1 âge, max 1 sexe, le reste en tags
            n_tags_needed = n_criteria
            
            # Possibilité d'avoir un critère âge
            if n_criteria >= 1 and random.random() < 0.4:
                crit = generate_age_criterion(patterns, sexe_only=False, patients=patients)
                criteria.append(crit)
                if crit.type == "age":
                    has_age = True
                if crit.pattern and crit.pattern.sexe:
                    has_sexe = True
                n_tags_needed -= 1
            
            # Possibilité d'avoir un critère sexe (si pas déjà inclus via âge)
            if not has_sexe and n_tags_needed > 0 and random.random() < 0.3:
                crit = generate_age_criterion(patterns, sexe_only=True, patients=patients)
                if crit.pattern:
                    criteria.append(crit)
                    has_sexe = True
                    n_tags_needed -= 1
            
            # Le reste en critères tags
            used_tags = set()
            for _ in range(n_tags_needed):
                # Éviter les doublons de tags
                attempts = 0
                while attempts < 10:
                    crit = generate_tag_criterion(tags)
                    if crit.tag_canon.lower() not in used_tags:
                        criteria.append(crit)
                        used_tags.add(crit.tag_canon.lower())
                        break
                    attempts += 1
                else:
                    # Forcer un tag même en doublon si trop de tentatives
                    criteria.append(generate_tag_criterion(tags))
            
            # Mélanger l'ordre des critères
            random.shuffle(criteria)
            
            # Générer le texte
            text = generate_question_text(criteria)
            
            questions.append(Question(criteria=criteria, text=text))
    
    return questions


# ═══════════════════════════════════════════════════════════════════════════════
# MATCHING ET AJUSTEMENT
# ═══════════════════════════════════════════════════════════════════════════════

def patient_matches_criterion(patient: Patient, criterion: Criterion) -> bool:
    """Vérifie si un patient correspond à un critère."""
    if criterion.type == "tag":
        return patient.has_tag_with_adjs(criterion.tag_canon, criterion.adjs_canon)
    
    elif criterion.type in ("age", "sexe"):
        if not criterion.pattern:
            return True
        
        # Vérifier le sexe si spécifié
        if criterion.pattern.sexe and patient.sexe != criterion.pattern.sexe:
            return False
        
        # Vérifier l'âge si opérateur spécifié
        if criterion.pattern.operator:
            return criterion.pattern.matches_age(patient.age, criterion.n_value)
        
        return True
    
    return False


def patient_matches_question(patient: Patient, question: Question) -> bool:
    """Vérifie si un patient correspond à tous les critères d'une question."""
    return all(patient_matches_criterion(patient, crit) for crit in question.criteria)


def count_matches(patients: list[Patient], question: Question) -> tuple[int, list[int]]:
    """Compte les patients matchant une question et retourne leurs IDs."""
    matching_ids = [p.id for p in patients if patient_matches_question(p, question)]
    return len(matching_ids), matching_ids


def add_tag_to_patient(patient: Patient, tag_canon: str, adjs_canon: list[str]):
    """Ajoute un tag avec ses adjectifs à un patient."""
    # Vérifier si le tag existe déjà
    for i, t in enumerate(patient.canontags):
        if t.lower() == tag_canon.lower():
            # Tag existe, ajouter les adjectifs manquants
            while len(patient.canonadjs) <= i:
                patient.canonadjs.append([])
            for adj in adjs_canon:
                if adj.lower() not in [a.lower() for a in patient.canonadjs[i]]:
                    patient.canonadjs[i].append(adj)
            return
    
    # Nouveau tag
    patient.canontags.append(tag_canon)
    patient.canonadjs.append(adjs_canon.copy())


def adjust_patient_for_question(patient: Patient, question: Question):
    """Modifie un patient pour qu'il corresponde à une question.
    
    Note: On ne modifie PAS le sexe ni l'âge car cela créerait des incohérences
    avec le prénom et la date de naissance.
    """
    for criterion in question.criteria:
        if criterion.type == "tag":
            add_tag_to_patient(patient, criterion.tag_canon, criterion.adjs_canon)
        # On ne modifie pas le sexe ni l'âge pour éviter les incohérences


def adjust_data_for_questions(patients: list[Patient], questions: list[Question], 
                               tags: dict[str, TagInfo]) -> list[Patient]:
    """Ajuste les données patients pour que chaque question matche 2-10%."""
    n_patients = len(patients)
    min_matches = max(2, int(n_patients * MIN_MATCH_PERCENT / 100))
    max_matches = int(n_patients * MAX_MATCH_PERCENT / 100)
    
    print(f"\n[DEBUG] Ajustement des données pour {len(questions)} questions...")
    print(f"[DEBUG] Cible: {min_matches}-{max_matches} patients par question ({MIN_MATCH_PERCENT}-{MAX_MATCH_PERCENT}%)")
    
    for q_idx, question in enumerate(tqdm(questions, desc="Ajustement")):
        nb, ids = count_matches(patients, question)
        
        if nb < min_matches:
            # Besoin d'ajouter des matchs
            needed = min_matches - nb
            
            # Stratégie: trouver des patients qui matchent déjà certains critères
            # (surtout âge/sexe qu'on ne peut pas modifier)
            
            # Séparer les critères tag des critères âge/sexe
            tag_criteria = [c for c in question.criteria if c.type == "tag"]
            age_sexe_criteria = [c for c in question.criteria if c.type in ("age", "sexe")]
            
            # Trouver les patients qui matchent déjà les critères âge/sexe
            candidates = []
            for p in patients:
                if p.id in ids:
                    continue  # Déjà un match complet
                
                # Vérifier les critères âge/sexe
                matches_age_sexe = all(
                    patient_matches_criterion(p, c) for c in age_sexe_criteria
                )
                
                if matches_age_sexe:
                    candidates.append(p)
            
            # Si pas assez de candidats, prendre n'importe qui (sauf les matchs existants)
            if len(candidates) < needed:
                non_matching = [p for p in patients if p.id not in ids and p not in candidates]
                candidates.extend(non_matching)
            
            random.shuffle(candidates)
            
            # Ajuster les patients sélectionnés (seulement les tags)
            for patient in candidates[:needed]:
                for crit in tag_criteria:
                    add_tag_to_patient(patient, crit.tag_canon, crit.adjs_canon)
    
    return patients


# ═══════════════════════════════════════════════════════════════════════════════
# CALCUL DES RÉSULTATS
# ═══════════════════════════════════════════════════════════════════════════════

def calculate_results(patients: list[Patient], questions: list[Question]):
    """Calcule nb, ids et extrait pour chaque question."""
    print("\n[DEBUG] Calcul des résultats...")
    
    for question in tqdm(questions, desc="Résultats"):
        nb, ids = count_matches(patients, question)
        question.nb = nb
        question.ids = ids
        
        # Extrait: jusqu'à 10 patients
        matching_patients = [p for p in patients if p.id in ids][:10]
        question.extrait = ", ".join(f"{p.prenom} {p.nom}" for p in matching_patients)


# ═══════════════════════════════════════════════════════════════════════════════
# SAUVEGARDE
# ═══════════════════════════════════════════════════════════════════════════════

def save_questions(questions: list[Question], filepath: Path):
    """Sauvegarde les questions dans un fichier CSV."""
    print(f"\n[DEBUG] Sauvegarde des questions dans {filepath.absolute()}")
    
    with open(filepath, "w", encoding=ENCODING, newline="") as f:
        writer = csv.writer(f, delimiter=SEP)
        
        # En-tête
        writer.writerow([
            "crit1_canon", "crit2_canon", "crit3_canon", "crit4_canon",
            "crit1_syn", "crit2_syn", "crit3_syn", "crit4_syn",
            "question", "nb", "ids", "extrait"
        ])
        
        for question in questions:
            # Critères canoniques (4 colonnes)
            canon_cols = []
            for i in range(4):
                if i < len(question.criteria):
                    canon_cols.append(question.criteria[i].get_canon_str())
                else:
                    canon_cols.append("")
            
            # Critères synonymes (4 colonnes)
            syn_cols = []
            for i in range(4):
                if i < len(question.criteria):
                    syn_cols.append(question.criteria[i].get_syn_str())
                else:
                    syn_cols.append("")
            
            # IDs en chaîne
            ids_str = MULTI_SEP.join(str(id_) for id_ in question.ids)
            
            writer.writerow(canon_cols + syn_cols + [
                question.text,
                question.nb,
                ids_str,
                question.extrait
            ])


def save_patients(patients: list[Patient], filepath: Path):
    """Sauvegarde les patients modifiés dans un fichier CSV."""
    print(f"\n[DEBUG] Sauvegarde des patients dans {filepath.absolute()}")
    
    with open(filepath, "w", encoding=ENCODING, newline="") as f:
        writer = csv.writer(f, delimiter=SEP)
        
        # En-tête
        writer.writerow([
            "id", "canontags", "canonadjs", "sexe", "age", 
            "datenaissance", "prenom", "nom", "portrait"
        ])
        
        for patient in patients:
            # Tags en chaîne
            canontags_str = MULTI_SEP.join(patient.canontags)
            
            # Adjectifs: chaque groupe séparé par |, groupes séparés par ,
            canonadjs_parts = []
            for adj_list in patient.canonadjs:
                canonadjs_parts.append(ADJ_SEP.join(adj_list))
            canonadjs_str = MULTI_SEP.join(canonadjs_parts)
            
            writer.writerow([
                patient.id,
                canontags_str,
                canonadjs_str,
                patient.sexe,
                patient.age,
                patient.datenaissance,
                patient.prenom,
                patient.nom,
                patient.portrait
            ])


# ═══════════════════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════════════════

def main():
    print(f"{__pgm__} V{__version__} - {__date__}")
    
    # Vérification des arguments
    if len(sys.argv) < 2:
        print("Usage: python questions.py <fichier_patients.csv>")
        print("       Les fichiers tagsadjs.csv, ages.csv et commun.csv doivent être dans refs/")
        sys.exit(1)
    
    patients_file = Path(sys.argv[1])
    
    if not patients_file.exists():
        print(f"[ERREUR] Fichier introuvable: {patients_file.absolute()}")
        sys.exit(1)
    
    # Fichiers de sortie (dans le même répertoire que le fichier patients)
    output_dir = patients_file.parent
    base_name = patients_file.name
    output_questions = output_dir / f"q{base_name}"
    output_patients = output_dir / f"m{base_name}"
    
    print(f"\n[DEBUG] Fichier patients: {patients_file.absolute()}")
    print(f"[DEBUG] Fichier tags: {TAGSADJS_FILE.absolute()}")
    print(f"[DEBUG] Fichier ages: {AGES_FILE.absolute()}")
    print(f"[DEBUG] Fichier commun: {COMMUN_FILE.absolute()}")
    
    # Vérifier les fichiers requis
    for f in [TAGSADJS_FILE, AGES_FILE]:
        if not f.exists():
            print(f"[ERREUR] Fichier requis introuvable: {f.absolute()}")
            sys.exit(1)
    
    # Chargement des incompatibilités
    print("\n[DEBUG] Chargement des incompatibilités...")
    incompatibility_manager.load_from_file(COMMUN_FILE)
    
    # Chargement des données
    print("\n[DEBUG] Chargement des données...")
    
    # D'abord charger les adjectifs
    adjectives = load_adjectives(TAGSADJS_FILE)
    print(f"[DEBUG] {len(adjectives)} adjectifs chargés")
    
    # Puis charger les tags avec référence aux adjectifs
    tags = load_tags(TAGSADJS_FILE, adjectives)
    print(f"[DEBUG] {len(tags)} tags chargés")
    
    patterns = load_age_patterns(AGES_FILE)
    print(f"[DEBUG] {len(patterns)} patterns âge/sexe chargés")
    
    patients = load_patients(patients_file)
    print(f"[DEBUG] {len(patients)} patients chargés")
    
    # Génération des questions
    print("\n[DEBUG] Génération des questions...")
    questions = generate_questions(tags, patterns, patients)
    print(f"[DEBUG] {len(questions)} questions générées")
    
    # Ajustement des données
    patients = adjust_data_for_questions(patients, questions, tags)
    
    # Calcul des résultats
    calculate_results(patients, questions)
    
    # Statistiques
    print("\n[DEBUG] Statistiques:")
    for n_crit in range(1, 5):
        start_idx = (n_crit - 1) * QUESTIONS_PER_LEVEL
        end_idx = start_idx + QUESTIONS_PER_LEVEL
        subset = questions[start_idx:end_idx]
        avg_nb = sum(q.nb for q in subset) / len(subset)
        print(f"  {n_crit} critère(s): moyenne {avg_nb:.1f} patients/question")
    
    # Sauvegarde
    save_questions(questions, output_questions)
    save_patients(patients, output_patients)
    
    print(f"\n✅ Terminé!")
    print(f"   Questions: {output_questions.absolute()}")
    print(f"   Patients modifiés: {output_patients.absolute()}")


if __name__ == "__main__":
    main()
