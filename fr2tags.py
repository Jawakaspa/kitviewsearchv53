# fr2tags.py V1.0.12 - 12/12/2025 20:52:42
__pgm__ = "fr2tags.py"
__version__ = "1.0.12"
__date__ = "12/12/2025 20:52:42"

# ╔════════════════════════════════════════════════════════════════
# ║ fr2tags.py
# ║ Internationalise tagsfr.csv vers tags.csv
# ║ Traduit les tags et adjectifs français vers toutes les langues
# ║ configurées dans commun.csv
# ║
# ║ V2.0.0 - GLOSSAIRE.CSV COMME SOURCE DE VÉRITÉ :
# ║ Les traductions sont stockées dans glossaire.csv (pas tags.csv)
# ║ Clé = terme français (colonne fr)
# ║ Un terme français donné = toujours la même traduction par langue.
# ║ Avantages :
# ║   - Glossaire réutilisable pour d'autres usages (traduction questions)
# ║   - Robuste : pas de dépendance à la structure de tags.csv
# ║   - Optimisé : un terme traduit une fois n'est jamais retraduit
# ║   - Enrichissement automatique du glossaire
# ║
# ║ Structure glossaire.csv : type;fr;en;de;es;it;pt;pl;ro;th;ar;cn
# ║ Structure tags.csv : canonfr;type;frtags;stdfrtags;fradjs;stdfradjs;...
# ╚════════════════════════════════════════════════════════════════

import csv
import sys
import os
import io
import time
import shutil
import unicodedata
import re
import requests
from datetime import datetime

# Import DeepL (optionnel)
try:
    import deepl
    DEEPL_DISPONIBLE = True
except ImportError:
    DEEPL_DISPONIBLE = False

# Clé API DeepL depuis variable d'environnement
DEEPL_API_KEY = os.environ.get('DEEPL_API_KEY', '')

# Mapping des codes langue internes vers codes DeepL
MAPPING_DEEPL = {
    'fr': 'FR',
    'en': 'EN-GB',
    'de': 'DE',
    'es': 'ES',
    'it': 'IT',
    'pt': 'PT-PT',
    'pl': 'PL',
    'ro': 'RO',
    'th': 'TH',
    'ar': 'AR',
    'cn': 'ZH-HANS'
}


class AuditTraduction:
    """Classe pour tracer l'origine de chaque traduction."""
    
    def __init__(self):
        self.entries = []
        self.date_traitement = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    def ajouter(self, terme_fr, langue, terme_traduit, fournisseur, type_terme="tag"):
        self.entries.append({
            'terme_fr': terme_fr,
            'langue': langue,
            'terme_traduit': terme_traduit,
            'fournisseur': fournisseur,
            'type': type_terme,
            'date': self.date_traitement
        })
    
    def sauvegarder(self, filepath):
        if not self.entries:
            print(f"Fichier audit : aucune entree a sauvegarder")
            return
        
        colonnes = ['terme_fr', 'langue', 'terme_traduit', 'fournisseur', 'type', 'date']
        
        with open(filepath, 'w', encoding='utf-8-sig', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=colonnes, delimiter=';')
            writer.writeheader()
            for entry in self.entries:
                writer.writerow(entry)
        
        print(f"Fichier audit cree : {filepath} ({len(self.entries)} entrees)")


class StatsTraduction:
    """Classe pour gérer les statistiques de traduction."""
    
    def __init__(self):
        self.termes_deja_traduits = 0
        self.termes_nouveaux_traduits = 0
        self.termes_echecs = 0
        self.caracteres_traduits = 0
        self.par_langue = {}
        self.par_fournisseur = {
            'deepl': 0,
            'mymemory': 0,
            'libretranslate': 0,
            'none': 0
        }
    
    def init_langue(self, lang):
        if lang not in self.par_langue:
            self.par_langue[lang] = {
                'deja_traduits': 0,
                'nouveaux_traduits': 0,
                'echecs': 0,
                'caracteres': 0
            }
    
    def ajouter_reutilise(self, lang, nb_termes=1):
        self.init_langue(lang)
        self.termes_deja_traduits += nb_termes
        self.par_langue[lang]['deja_traduits'] += nb_termes
    
    def ajouter_traduit(self, lang, terme, fournisseur):
        self.init_langue(lang)
        self.termes_nouveaux_traduits += 1
        self.caracteres_traduits += len(terme)
        self.par_langue[lang]['nouveaux_traduits'] += 1
        self.par_langue[lang]['caracteres'] += len(terme)
        if fournisseur in self.par_fournisseur:
            self.par_fournisseur[fournisseur] += 1
    
    def ajouter_echec(self, lang):
        self.init_langue(lang)
        self.termes_echecs += 1
        self.par_langue[lang]['echecs'] += 1
        self.par_fournisseur['none'] += 1
    
    @property
    def total_termes(self):
        return self.termes_deja_traduits + self.termes_nouveaux_traduits + self.termes_echecs
    
    @property
    def total_traductions(self):
        return self.termes_deja_traduits + self.termes_nouveaux_traduits
    
    def pct(self, valeur, total):
        if total == 0:
            return 0.0
        return (valeur / total) * 100
    
    def afficher(self):
        total = self.total_termes
        total_trad = self.total_traductions
        
        print()
        print("=" * 70)
        print("STATISTIQUES DE TRADUCTION")
        print("=" * 70)
        
        print()
        print("+" + "-" * 68 + "+")
        print("| TERMES" + " " * 61 + "|")
        print("+" + "-" * 68 + "+")
        print(f"| Termes deja traduits (glossaire)  : {self.termes_deja_traduits:>6} ({self.pct(self.termes_deja_traduits, total):>5.1f}%) |")
        print(f"| Termes nouvellement traduits      : {self.termes_nouveaux_traduits:>6} ({self.pct(self.termes_nouveaux_traduits, total):>5.1f}%) |")
        print(f"| Echecs de traduction              : {self.termes_echecs:>6} ({self.pct(self.termes_echecs, total):>5.1f}%) |")
        print("+" + "-" * 68 + "+")
        print(f"| TOTAL TERMES TRAITES              : {total:>6}          |")
        print("+" + "-" * 68 + "+")
        
        print()
        print("+" + "-" * 68 + "+")
        print("| CARACTERES" + " " * 57 + "|")
        print("+" + "-" * 68 + "+")
        print(f"| Caracteres envoyes aux APIs       : {self.caracteres_traduits:>6}          |")
        print("+" + "-" * 68 + "+")
        
        if self.termes_nouveaux_traduits > 0:
            print()
            print("+" + "-" * 68 + "+")
            print("| PAR FOURNISSEUR (nouvelles traductions)" + " " * 28 + "|")
            print("+" + "-" * 68 + "+")
            for fournisseur, count in self.par_fournisseur.items():
                if fournisseur != 'none' and count > 0:
                    print(f"| {fournisseur:<20} : {count:>6} ({self.pct(count, self.termes_nouveaux_traduits):>5.1f}%)" + " " * 18 + "|")
            print("+" + "-" * 68 + "+")
        
        if self.par_langue:
            print()
            print("+" + "-" * 68 + "+")
            print("| PAR LANGUE" + " " * 57 + "|")
            print("+" + "-" * 68 + "+")
            print(f"| {'Langue':<8} {'Glossaire':>10} {'Nouveaux':>10} {'Echecs':>10} {'Caract.':>10}   |")
            print("|" + "-" * 68 + "|")
            for lang, lstats in sorted(self.par_langue.items()):
                print(f"| {lang:<8} {lstats['deja_traduits']:>10} {lstats['nouveaux_traduits']:>10} {lstats['echecs']:>10} {lstats['caracteres']:>10}   |")
            print("+" + "-" * 68 + "+")


# Instances globales
stats = StatsTraduction()
audit = AuditTraduction()

# Glossaire en mémoire : {terme_fr: {lang: traduction, ...}, ...}
glossaire_memoire = {}

# Lignes du glossaire pour réécriture (conserve structure et commentaires)
glossaire_lignes = []
glossaire_colonnes = []
glossaire_commentaires = []


def standardise(texte):
    """Normalise un texte (minuscules, sans accents, sans ponctuation)."""
    if texte is None or texte == "":
        return ""
    texte = texte.lower()
    texte = unicodedata.normalize('NFD', texte)
    texte = ''.join(char for char in texte if unicodedata.category(char) != 'Mn')
    for char in ".!-_?":
        texte = texte.replace(char, " ")
    texte = re.sub(r'\s+', ' ', texte)
    return texte.strip()


def extraire_canonfr(frtags):
    """Extrait le canonfr (premier terme) de la liste frtags."""
    if not frtags or frtags.strip() == "":
        return ""
    return frtags.split(",")[0].strip()


# ============================================================================
# SERVICES DE TRADUCTION
# ============================================================================

def traduire_deepl(texte, source_lang='fr', target_lang='en', verbose=False):
    """Traduit via DeepL API."""
    if not texte or not texte.strip():
        return ""
    
    if not DEEPL_DISPONIBLE or not DEEPL_API_KEY:
        return None
    
    target_code = MAPPING_DEEPL.get(target_lang)
    if not target_code:
        return None
    
    try:
        translator = deepl.Translator(DEEPL_API_KEY)
        result = translator.translate_text(
            texte,
            source_lang=MAPPING_DEEPL.get(source_lang, 'FR'),
            target_lang=target_code
        )
        return result.text
    except Exception as e:
        if verbose:
            print(f"    [DEEPL] Erreur: {e}")
        return None


def traduire_mymemory(texte, source_lang='fr', target_lang='en', verbose=False):
    """Traduction via MyMemory API."""
    if not texte or not texte.strip():
        return ""
    
    url = "https://api.mymemory.translated.net/get"
    params = {"q": texte, "langpair": f"{source_lang}|{target_lang}"}
    
    try:
        response = requests.get(url, params=params, timeout=10)
        if response.status_code == 200:
            data = response.json()
            if data.get("responseStatus") == 200:
                return data["responseData"]["translatedText"]
    except Exception as e:
        if verbose:
            print(f"    [MYMEMORY] Erreur: {e}")
    
    return None


def traduire_libretranslate(texte, source_lang='fr', target_lang='en', verbose=False):
    """Traduction via LibreTranslate."""
    if not texte or not texte.strip():
        return ""
    
    url = "https://libretranslate.com/translate"
    
    try:
        response = requests.post(url, json={
            "q": texte, "source": source_lang, "target": target_lang, "format": "text"
        }, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            return data.get("translatedText")
    except Exception as e:
        if verbose:
            print(f"    [LIBRETRANSLATE] Erreur: {e}")
    
    return None


def traduire_avec_fallback(texte, source_lang='fr', target_lang='en', verbose=False):
    """Traduit avec cascade : DeepL → MyMemory → LibreTranslate."""
    if not texte or not texte.strip():
        return "", "none"
    
    result = traduire_deepl(texte, source_lang, target_lang, verbose)
    if result:
        return result, "deepl"
    
    result = traduire_mymemory(texte, source_lang, target_lang, verbose)
    if result:
        return result, "mymemory"
    
    result = traduire_libretranslate(texte, source_lang, target_lang, verbose)
    if result:
        return result, "libretranslate"
    
    return "", "none"


# ============================================================================
# FONCTIONS DE TRAITEMENT
# ============================================================================

def verifier_encodage_bom(filepath):
    """Vérifie si un fichier CSV est encodé en UTF-8 avec BOM."""
    try:
        with open(filepath, 'rb') as f:
            return f.read(3) == b'\xef\xbb\xbf'
    except:
        return False


def lire_csv_avec_commentaires(filepath):
    """Lit un fichier CSV en ignorant les lignes de commentaires."""
    lignes_donnees = []
    nb_commentaires = 0
    
    with open(filepath, 'r', encoding='utf-8-sig', newline='') as f:
        for ligne in f:
            if ligne.strip().startswith('#'):
                nb_commentaires += 1
                continue
            lignes_donnees.append(ligne)
    
    fichier_virtuel = io.StringIO(''.join(lignes_donnees))
    reader = csv.DictReader(fichier_virtuel, delimiter=';')
    
    return reader.fieldnames, list(reader), nb_commentaires


def charger_langues_actives(filepath, verbose=False):
    """Charge les langues actives depuis commun.csv (colonne langues)."""
    langues = []
    
    if not os.path.exists(filepath):
        print(f"ERREUR : Fichier {filepath} introuvable", file=sys.stderr)
        return langues
    
    try:
        fieldnames, rows, _ = lire_csv_avec_commentaires(filepath)
        
        if 'langues' not in fieldnames:
            print(f"ERREUR : Colonne 'langues' absente dans {filepath}", file=sys.stderr)
            return langues
        
        for row in rows:
            lang = row.get('langues', '').strip()
            if lang and lang not in langues:
                langues.append(lang)
        
        if verbose:
            print(f"Langues actives depuis {filepath} : {langues}")
        
    except Exception as e:
        print(f"ERREUR : {e}", file=sys.stderr)
    
    return langues


def charger_glossaire(filepath, langues_actives, verbose=False):
    """
    Charge le glossaire depuis glossaire.csv.
    
    Préserve TOUTES les colonnes existantes (même les langues non actives).
    Ne charge PAS les lignes de type 'z' en mémoire.
    
    Args:
        filepath: Chemin vers glossaire.csv
        langues_actives: Liste des langues actives (pour info)
        verbose: Affichage détaillé
    
    Returns:
        dict: {terme_fr: {lang: traduction, ...}, ...}
    """
    global glossaire_lignes, glossaire_colonnes, glossaire_commentaires
    
    glossaire = {}
    glossaire_lignes = []
    glossaire_commentaires = []
    
    if not os.path.exists(filepath):
        if verbose:
            print(f"Glossaire inexistant, creation : {filepath}")
        # Créer structure minimale avec colonnes actives
        glossaire_colonnes = ['type', 'fr'] + [l for l in langues_actives if l != 'fr']
        return glossaire
    
    # Lire le fichier complet pour préserver commentaires
    lignes_brutes = []
    with open(filepath, 'r', encoding='utf-8-sig', newline='') as f:
        for ligne in f:
            lignes_brutes.append(ligne)
    
    # Séparer commentaires et données
    lignes_donnees = []
    for ligne in lignes_brutes:
        if ligne.strip().startswith('#'):
            glossaire_commentaires.append(ligne.rstrip('\n\r'))
        else:
            lignes_donnees.append(ligne)
    
    # Parser les données
    fichier_virtuel = io.StringIO(''.join(lignes_donnees))
    reader = csv.DictReader(fichier_virtuel, delimiter=';')
    glossaire_colonnes = list(reader.fieldnames) if reader.fieldnames else ['type', 'fr']
    
    # Vérifier que les langues actives sont présentes, sinon les ajouter
    colonnes_ajoutees = []
    for lang in langues_actives:
        if lang != 'fr' and lang not in glossaire_colonnes:
            glossaire_colonnes.append(lang)
            colonnes_ajoutees.append(lang)
    
    if colonnes_ajoutees and verbose:
        print(f"Colonnes ajoutees au glossaire pour langues actives : {colonnes_ajoutees}")
    
    # Charger les lignes
    nb_z_ignores = 0
    for row in reader:
        type_terme = row.get('type', '').strip()
        terme_fr = row.get('fr', '').strip()
        
        # Stocker la ligne complète pour réécriture (toutes les colonnes)
        ligne_complete = {col: row.get(col, '') for col in glossaire_colonnes}
        glossaire_lignes.append(ligne_complete)
        
        # Ignorer type 'z' pour le glossaire en mémoire
        if type_terme == 'z':
            nb_z_ignores += 1
            continue
        
        if not terme_fr:
            continue
        
        # Charger les traductions existantes (toutes les langues présentes)
        glossaire[terme_fr] = {}
        for col in glossaire_colonnes:
            if col not in ('type', 'fr'):
                trad = row.get(col, '').strip()
                if trad:
                    glossaire[terme_fr][col] = trad
    
    if verbose:
        print(f"Glossaire charge depuis : {filepath}")
        print(f"  - Termes charges : {len(glossaire)}")
        print(f"  - Termes type 'z' ignores : {nb_z_ignores}")
        print(f"  - Colonnes existantes : {glossaire_colonnes}")
        print(f"  - Langues actives pour traduction : {[l for l in langues_actives if l != 'fr']}")
    
    return glossaire


def sauvegarder_glossaire(filepath, verbose=False):
    """
    Sauvegarde le glossaire enrichi dans glossaire.csv.
    
    Préserve les commentaires et la structure originale.
    Ajoute les nouveaux termes à la fin.
    """
    global glossaire_memoire, glossaire_lignes, glossaire_colonnes, glossaire_commentaires
    
    # Identifier les termes existants
    termes_existants = set()
    for ligne in glossaire_lignes:
        terme_fr = ligne.get('fr', '').strip()
        if terme_fr:
            termes_existants.add(terme_fr)
    
    # Mettre à jour les lignes existantes avec nouvelles traductions
    for ligne in glossaire_lignes:
        terme_fr = ligne.get('fr', '').strip()
        if terme_fr and terme_fr in glossaire_memoire:
            for lang, trad in glossaire_memoire[terme_fr].items():
                if lang in glossaire_colonnes:
                    # Ne mettre à jour que si la case est vide
                    if not ligne.get(lang, '').strip():
                        ligne[lang] = trad
    
    # Ajouter les nouveaux termes
    nouveaux_termes = []
    for terme_fr, traductions in glossaire_memoire.items():
        if terme_fr not in termes_existants:
            nouvelle_ligne = {col: '' for col in glossaire_colonnes}
            nouvelle_ligne['type'] = 'o'  # Type orthodontie par défaut
            nouvelle_ligne['fr'] = terme_fr
            for lang, trad in traductions.items():
                if lang in glossaire_colonnes:
                    nouvelle_ligne[lang] = trad
            glossaire_lignes.append(nouvelle_ligne)
            nouveaux_termes.append(terme_fr)
    
    # Écrire le fichier
    with open(filepath, 'w', encoding='utf-8-sig', newline='') as f:
        # Écrire les commentaires
        for comm in glossaire_commentaires:
            f.write(comm + '\n')
        
        # Écrire les données
        writer = csv.DictWriter(f, fieldnames=glossaire_colonnes, delimiter=';')
        writer.writeheader()
        for ligne in glossaire_lignes:
            writer.writerow(ligne)
    
    if verbose:
        print(f"Glossaire sauvegarde : {filepath}")
        print(f"  - Lignes totales : {len(glossaire_lignes)}")
        print(f"  - Nouveaux termes ajoutes : {len(nouveaux_termes)}")


def traduire_terme(terme_fr, target_lang, type_terme, verbose=False):
    """
    Traduit un terme en utilisant le glossaire.
    Si le terme existe dans le glossaire, on le réutilise.
    Sinon, on traduit et on l'ajoute au glossaire en mémoire.
    
    Args:
        terme_fr: Terme français à traduire
        target_lang: Langue cible
        type_terme: Type pour l'audit (tag/adjectif)
        verbose: Affichage détaillé
    
    Returns:
        tuple: (traduction, est_nouveau)
    """
    global glossaire_memoire
    
    if not terme_fr or not terme_fr.strip():
        return "", False
    
    terme_fr = terme_fr.strip()
    
    # Chercher dans le glossaire en mémoire
    if terme_fr in glossaire_memoire:
        if target_lang in glossaire_memoire[terme_fr]:
            trad = glossaire_memoire[terme_fr][target_lang]
            if trad:  # Case non vide
                stats.ajouter_reutilise(target_lang, 1)
                audit.ajouter(terme_fr, target_lang, trad, "glossaire", type_terme)
                return trad, False
    
    # Terme pas dans glossaire ou traduction manquante pour cette langue
    # → Traduire via API
    trad, fournisseur = traduire_avec_fallback(terme_fr, 'fr', target_lang, verbose)
    
    if trad and fournisseur != "none":
        # Ajouter au glossaire en mémoire
        if terme_fr not in glossaire_memoire:
            glossaire_memoire[terme_fr] = {}
        glossaire_memoire[terme_fr][target_lang] = trad
        
        stats.ajouter_traduit(target_lang, terme_fr, fournisseur)
        audit.ajouter(terme_fr, target_lang, trad, fournisseur, type_terme)
        return trad, True
    else:
        stats.ajouter_echec(target_lang)
        audit.ajouter(terme_fr, target_lang, terme_fr, "echec", type_terme)
        return terme_fr, True  # Garder l'original si échec


def extraire_termes_individuels(liste_csv):
    """
    Extrait tous les termes individuels d'une liste CSV.
    
    Format d'entrée : "terme1,terme2|terme3,terme4"
    Sortie : ['terme1', 'terme2', 'terme3', 'terme4']
    """
    if not liste_csv or liste_csv.strip() == "":
        return []
    
    termes = []
    for groupe in liste_csv.split(","):
        groupe = groupe.strip()
        if "|" in groupe:
            for sous_terme in groupe.split("|"):
                sous_terme = sous_terme.strip()
                if sous_terme:
                    termes.append(sous_terme)
        elif groupe:
            termes.append(groupe)
    
    return termes


def traduire_liste(liste_csv, target_lang, type_terme, verbose=False):
    """
    Traduit une liste CSV en préservant la structure.
    
    Format : "terme1,terme2|terme3,terme4"
    Chaque terme individuel est traduit via le glossaire.
    
    Returns:
        tuple: (liste_traduite, nb_nouveaux, nb_glossaire)
    """
    if not liste_csv or liste_csv.strip() == "":
        return "", 0, 0
    
    groupes = liste_csv.split(",")
    groupes_traduits = []
    nb_nouveaux = 0
    nb_glossaire = 0
    
    for groupe in groupes:
        groupe = groupe.strip()
        if not groupe:
            groupes_traduits.append("")
            continue
        
        if "|" in groupe:
            # Groupe de synonymes/variantes
            sous_termes = groupe.split("|")
            sous_traduits = []
            
            for st in sous_termes:
                st = st.strip()
                if not st:
                    sous_traduits.append("")
                    continue
                
                trad, est_nouveau = traduire_terme(st, target_lang, type_terme, verbose)
                sous_traduits.append(trad)
                if est_nouveau:
                    nb_nouveaux += 1
                    time.sleep(0.1)  # Pause entre appels API
                else:
                    nb_glossaire += 1
            
            groupes_traduits.append("|".join(sous_traduits))
        else:
            # Terme simple
            trad, est_nouveau = traduire_terme(groupe, target_lang, type_terme, verbose)
            groupes_traduits.append(trad)
            if est_nouveau:
                nb_nouveaux += 1
                time.sleep(0.1)
            else:
                nb_glossaire += 1
    
    return ",".join(groupes_traduits), nb_nouveaux, nb_glossaire


def standardise_liste(liste_csv):
    """Standardise chaque élément d'une liste CSV."""
    if not liste_csv or liste_csv.strip() == "":
        return ""
    
    elements = []
    for elem in liste_csv.split(","):
        if "|" in elem:
            sous = [standardise(se) for se in elem.split("|")]
            elements.append("|".join(sous))
        else:
            elements.append(standardise(elem))
    
    return ",".join(elements)


def main():
    global stats, audit, glossaire_memoire
    stats = StatsTraduction()
    audit = AuditTraduction()
    
    print(f"{__pgm__} V{__version__} - {__date__}")
    
    script_dir = os.path.dirname(os.path.abspath(__file__))
    refs_dir = os.path.join(script_dir, "refs")
    
    fichier_commun = os.path.join(refs_dir, "commun.csv")
    fichier_glossaire = os.path.join(refs_dir, "glossaire.csv")
    fichier_entree = os.path.join(refs_dir, "tagsfr.csv")
    fichier_sortie = os.path.join(refs_dir, "tags.csv")
    fichier_backup = os.path.join(refs_dir, "tagsold.csv")
    fichier_backup_glossaire = os.path.join(refs_dir, "glossaireold.csv")
    fichier_audit = os.path.join(refs_dir, "tags_audit.csv")
    
    print()
    print("=" * 70)
    print("FICHIERS")
    print("=" * 70)
    print(f"Fichier commun     : {fichier_commun}")
    print(f"Fichier glossaire  : {fichier_glossaire}")
    print(f"Fichier d'entree   : {fichier_entree}")
    print(f"Fichier de sortie  : {fichier_sortie}")
    print(f"Fichier audit      : {fichier_audit}")
    
    # Vérifications
    if not os.path.exists(refs_dir):
        print(f"ERREUR : Repertoire {refs_dir} inexistant", file=sys.stderr)
        sys.exit(1)
    
    for f in [fichier_commun, fichier_entree]:
        if not os.path.exists(f):
            print(f"ERREUR : Fichier {f} inexistant", file=sys.stderr)
            sys.exit(1)
    
    if not verifier_encodage_bom(fichier_entree):
        print(f"ERREUR : {fichier_entree} n'est pas UTF-8-BOM", file=sys.stderr)
        sys.exit(1)
    
    print()
    print("Encodage UTF-8-BOM verifie OK pour tagsfr.csv")
    
    if DEEPL_DISPONIBLE and DEEPL_API_KEY:
        print("DeepL : Disponible (prioritaire)")
    elif DEEPL_DISPONIBLE:
        print("DeepL : Module installe mais cle API manquante")
    else:
        print("DeepL : Non installe (fallback actif)")
    
    # Charger langues actives
    langues_actives = charger_langues_actives(fichier_commun, verbose=True)
    if not langues_actives:
        print("ERREUR : Aucune langue active trouvee", file=sys.stderr)
        sys.exit(1)
    
    # Filtrer pour ne garder que les langues autres que 'fr'
    langues_a_traduire = [l for l in langues_actives if l != 'fr']
    print(f"Langues a traduire : {langues_a_traduire}")
    
    # Charger glossaire
    print()
    print("=" * 70)
    print("CHARGEMENT GLOSSAIRE")
    print("=" * 70)
    
    if os.path.exists(fichier_glossaire):
        if not verifier_encodage_bom(fichier_glossaire):
            print(f"ERREUR : {fichier_glossaire} n'est pas UTF-8-BOM", file=sys.stderr)
            sys.exit(1)
        print("Encodage UTF-8-BOM verifie OK pour glossaire.csv")
        print(f"Creation backup : {fichier_backup_glossaire}")
        shutil.copy2(fichier_glossaire, fichier_backup_glossaire)
    
    glossaire_memoire = charger_glossaire(fichier_glossaire, langues_actives, verbose=True)
    
    # Lire tagsfr.csv
    print()
    print("=" * 70)
    print("LECTURE TAGSFR.CSV")
    print("=" * 70)
    
    try:
        fieldnames_fr, rows_fr, nb_comm = lire_csv_avec_commentaires(fichier_entree)
        print(f"Lignes a traiter : {len(rows_fr)}")
        if nb_comm > 0:
            print(f"Commentaires ignores : {nb_comm}")
    except Exception as e:
        print(f"ERREUR : {e}", file=sys.stderr)
        sys.exit(1)
    
    # Colonnes de sortie pour tags.csv
    colonnes_sortie = ['canonfr', 'type', 'frtags', 'stdfrtags', 'fradjs', 'stdfradjs']
    for lang in langues_a_traduire:
        colonnes_sortie.extend([f'{lang}tags', f'std{lang}tags', f'{lang}adjs', f'std{lang}adjs'])
    
    print(f"Colonnes de sortie tags.csv : {len(colonnes_sortie)}")
    
    # Backup tags.csv existant
    if os.path.exists(fichier_sortie):
        print(f"Creation backup : {fichier_backup}")
        shutil.copy2(fichier_sortie, fichier_backup)
    
    print()
    print("=" * 70)
    print("TRADUCTION EN COURS (glossaire.csv = source de verite)")
    print("=" * 70)
    
    lignes_sortie = []
    t0 = time.time()
    
    for i, row in enumerate(rows_fr):
        type_tag = row.get('type', '').strip()
        frtags = row.get('frtags', '').strip()
        stdfrtags = row.get('stdfrtags', '').strip()
        fradjs = row.get('fradjs', '').strip()
        stdfradjs = row.get('stdfradjs', '').strip()
        
        canonfr = extraire_canonfr(frtags)
        
        print(f"\n[{i+1}/{len(rows_fr)}] {canonfr}")
        
        ligne_sortie = {
            'canonfr': canonfr,
            'type': type_tag,
            'frtags': frtags,
            'stdfrtags': stdfrtags,
            'fradjs': fradjs,
            'stdfradjs': stdfradjs
        }
        
        for lang in langues_a_traduire:
            print(f"  -> {lang.upper()}: ", end="", flush=True)
            
            # Traduire tags
            tags_trad, nb_new_tags, nb_gloss_tags = traduire_liste(
                frtags, lang, 'tag', verbose=False
            )
            stdtags_trad = standardise_liste(tags_trad)
            
            # Traduire adjectifs
            adjs_trad, nb_new_adjs, nb_gloss_adjs = traduire_liste(
                fradjs, lang, 'adjectif', verbose=False
            )
            stdadjs_trad = standardise_liste(adjs_trad)
            
            ligne_sortie[f'{lang}tags'] = tags_trad
            ligne_sortie[f'std{lang}tags'] = stdtags_trad
            ligne_sortie[f'{lang}adjs'] = adjs_trad
            ligne_sortie[f'std{lang}adjs'] = stdadjs_trad
            
            total_new = nb_new_tags + nb_new_adjs
            total_gloss = nb_gloss_tags + nb_gloss_adjs
            
            if total_new > 0:
                print(f"nouveau:{total_new} glossaire:{total_gloss}")
            else:
                print(f"glossaire OK ({total_gloss} termes)")
        
        lignes_sortie.append(ligne_sortie)
    
    elapsed = time.time() - t0
    
    print()
    print("=" * 70)
    print("ECRITURE DES FICHIERS")
    print("=" * 70)
    
    # Sauvegarder glossaire enrichi
    sauvegarder_glossaire(fichier_glossaire, verbose=True)
    
    # Sauvegarder tags.csv
    try:
        with open(fichier_sortie, 'w', encoding='utf-8-sig', newline='') as f_out:
            writer = csv.DictWriter(f_out, fieldnames=colonnes_sortie, delimiter=';')
            writer.writeheader()
            for ligne in lignes_sortie:
                writer.writerow(ligne)
        
        print(f"Fichier tags.csv cree : {fichier_sortie}")
        
    except Exception as e:
        print(f"ERREUR : {e}", file=sys.stderr)
        sys.exit(1)
    
    audit.sauvegarder(fichier_audit)
    stats.afficher()
    
    print()
    print(f"Glossaire final : {len(glossaire_memoire)} termes uniques")
    print()
    print("=" * 70)
    print(f"TEMPS TOTAL : {elapsed:.1f} secondes")
    print("=" * 70)


if __name__ == "__main__":
    main()
