# Prompt_glossaire.md

## Objet

Documentation et création du système de glossaire multilingue pour l'application Kitview, comprenant :
1. Le fichier `glossaire.csv` : référentiel central de traductions
2. Le programme `traduis.py` : utilitaire de gestion des traductions

---

## Contexte

L'application Kitview gère des recherches multilingues sur des patients orthodontiques. Jusqu'à présent, les traductions étaient gérées de façon dispersée :
- `fr2tags.py` traduisait les termes médicaux vers `tags.csv`
- Le dictionnaire de traduction était reconstruit en mémoire à chaque exécution

Le glossaire centralise **toutes les traductions** en un seul fichier référentiel, réutilisable par tous les programmes.

---

## Architecture du système

```
┌─────────────────────────────────────────────────────────────────────┐
│                        glossaire.csv                                │
│              (Référentiel central de traductions)                   │
│                                                                     │
│  type;fr;en;de;th;ar;cn;es;it;pt;pl;ro                             │
│  ─────────────────────────────────────────────────────────────────  │
│  p;avec;with;mit;กับ;مع;与;con;con;com;z;cu                         │
│  o;béance;open bite;offener Biss;...                               │
│  z;SNA>4°;SNA>4°;SNA>4°;...  (ne pas traduire)                     │
└─────────────────────────────────────────────────────────────────────┘
           │                    │                    │
           ▼                    ▼                    ▼
    ┌─────────────┐      ┌─────────────┐      ┌─────────────┐
    │ traduis.py  │      │ fr2tags.py  │      │ detlang.py  │
    │ (gestion)   │      │ (tags méd.) │      │ (détection) │
    └─────────────┘      └─────────────┘      └─────────────┘
```

---

## Fichier : refs/glossaire.csv

### Structure

```csv
type;fr;en;de;th;ar;cn;es;it;pt;pl;ro
```

**Note** : Les colonnes de langue suivent celles définies dans `commun.csv`. Si de nouvelles langues sont ajoutées à `commun.csv`, elles seront automatiquement ajoutées au glossaire.

### Colonne `type`

| Type | Signification | Exemple |
|------|---------------|---------|
| `p` | **Permanent** - Mots fondamentaux, ne changent jamais | avec, sans, les, qui |
| `c` | **Courant** - Expressions utiles, stables | les patients qui ont, cherche |
| `o` | **Orthodontie** - Vocabulaire médical orthodontique | béance, bruxisme, prognathie |
| `a` | **Appareils** - Appareils orthodontiques | appareil lingual, bagues |
| `z` | **Ne pas traduire** - Expressions à conserver telles quelles | SNA>4°, ANB=0° |
| `m` | **Manuel** - Traduction validée manuellement | (après correction humaine) |
| `jjmmaaaa` | **Temporaire** - Date de création, peut être purgé | 09122025 |

### Règles importantes

1. **Une ligne = un terme français unique**
2. **Colonne `fr` = clé unique** (pas de doublons)
3. **Cellule vide = traduction à effectuer**
4. **Type `z`** : toutes les colonnes langue recopient la valeur `fr`

### Exemple de contenu

```csv
type;fr;en;de;th
p;avec;with;mit;กับ
p;sans;without;ohne;โดยไม่มี
p;les;the;;
c;les patients qui ont;patients who have;Patienten mit;ผู้ป่วยที่มี
o;béance;open bite;offener Biss;ช่องว่างระหว่างฟัน
o;bruxisme;bruxism;Bruxismus;ภาวะนอนกัดฟัน
a;appareil lingual;lingual appliance;Lingualapparatur;เครื่องมือจัดฟันลิ้น
z;SNA>4°;SNA>4°;SNA>4°;SNA>4°
m;sourire gingival;gummy smile;Zahnfleischlächeln;รอยยิ้มเหงือก
09122025;béance sévère antérieure;severe anterior open bite;schwere vordere Zahnlücke;ช่องว่างด้านหน้าที่รุนแรง
```

---

## Programme : traduis.py

### Fonctionnalités

1. **Vérification du glossaire** : Détecte et complète les traductions manquantes
2. **Traduction CLI** : Traduit une phrase passée en argument
3. **Traduction fichier** : Traduit un fichier CSV d'entrée
4. **Optimisation** : Réutilise les mots déjà traduits avant de traduire

### Signature CLI

```bash
# Mode vérification (met à jour le glossaire si nécessaire)
python traduis.py

# Mode phrase unique
python traduis.py "béance sévère antérieure"

# Mode fichier
python traduis.py phrases_a_traduire.csv
```

### Sortie JSON (mode phrase)

```json
{
  "fr": "béance sévère antérieure",
  "en": "severe anterior open bite",
  "de": "schwere vordere Zahnlücke",
  "th": "ช่องว่างด้านหน้าที่รุนแรง",
  "source": "glossaire",
  "mots_nouveaux": 0
}
```

### Mode fichier

**Entrée** : `phrases.csv`
```csv
type;fr;en;de;th
c;bonjour;;;
c;merci;;;
```

**Sortie** : `phrases_out.csv`
```csv
type;fr;en;de;th
c;bonjour;hello;Hallo;สวัสดี
c;merci;thank you;Danke;ขอบคุณ
```

Le glossaire est également mis à jour avec les nouvelles entrées.

---

## Algorithme de traduis.py

### 1. Mode vérification (sans argument)

```
1. Charger glossaire.csv
2. Charger langues depuis commun.csv
3. Pour chaque ligne du glossaire :
   - Si type = 'z' → copier fr dans toutes les colonnes langue
   - Pour chaque langue :
     - Si cellule vide → traduire via API
4. Sauvegarder glossaire.csv mis à jour
5. Afficher statistiques
```

### 2. Mode phrase unique

```
1. Charger glossaire.csv en dictionnaire (clé = fr)
2. Standardiser la phrase
3. Si phrase existe dans glossaire :
   → Retourner les traductions existantes
4. Sinon :
   a. Découper la phrase en mots
   b. Pour chaque mot :
      - Si mot dans glossaire → récupérer traductions
      - Sinon → traduire via API, ajouter au glossaire
   c. Reconstituer la phrase traduite par assemblage
   d. Ajouter la phrase complète au glossaire (type=jjmmaaaa)
5. Retourner JSON avec traductions
```

### 3. Mode fichier

```
1. Charger glossaire.csv
2. Charger fichier d'entrée
3. Pour chaque ligne :
   - Appliquer l'algorithme du mode phrase
   - Stocker le résultat
4. Sauvegarder glossaire.csv mis à jour
5. Créer fichier_out.csv avec les traductions
```

---

## Services de traduction (cascade)

Identique à `fr2tags.py` :

1. **DeepL** (prioritaire si clé API disponible)
2. **MyMemory** (fallback gratuit)
3. **LibreTranslate** (fallback gratuit)

### Mapping codes langue → DeepL

| Code interne | Code DeepL |
|--------------|------------|
| fr | FR |
| en | EN-GB |
| de | DE |
| es | ES |
| it | IT |
| pt | PT-PT |
| pl | PL |
| ro | RO |
| th | TH |
| ar | AR |
| cn | ZH-HANS |

---

## Fonctions exportables

```python
def charger_glossaire(chemin: str = "refs/glossaire.csv") -> dict:
    """
    Charge le glossaire en dictionnaire.
    Clé = terme français, Valeur = dict des traductions par langue
    """

def traduire_terme(terme: str, langue_cible: str, glossaire: dict) -> str:
    """
    Traduit un terme vers une langue cible.
    Utilise le glossaire si disponible, sinon API.
    """

def traduire_phrase(phrase: str, glossaire: dict) -> dict:
    """
    Traduit une phrase complète.
    Retourne un dict avec toutes les traductions.
    """

def sauvegarder_glossaire(glossaire: dict, chemin: str = "refs/glossaire.csv"):
    """
    Sauvegarde le glossaire dans le fichier CSV.
    """
```

---

## Évolution de fr2tags.py

Une fois le glossaire en place, `fr2tags.py` sera simplifié :

```python
# Avant (V1.1.0) : reconstruction du glossaire depuis tags.csv
glossaire = {}
for ligne in tags_existants:
    for terme in ligne['frtags'].split(','):
        glossaire[(terme_std, lang, type)] = traduction

# Après (V2.0.0) : utilisation directe de glossaire.csv
glossaire = charger_glossaire()
for terme in termes_a_traduire:
    if terme in glossaire:
        traduction = glossaire[terme][lang]
    else:
        traduction = traduire_et_ajouter(terme, lang, glossaire)
```

---

## Cas particuliers

### Type `z` (ne pas traduire)

Pour les expressions mathématiques ou les sigles :
- `SNA>4°` → reste `SNA>4°` dans toutes les langues
- `ANB=0°` → reste `ANB=0°` dans toutes les langues

**Astuce** : Pour "Angle SNA>4°", on aura :
- `z;SNA>4°` (ne pas traduire)
- `o;Angle;Angle;Winkel;มุม` (traduire "Angle")

Ainsi "Angle SNA>4°" devient "Winkel SNA>4°" en allemand.

### Phrases assemblées (type temporaire)

Quand on traduit "béance sévère antérieure" :
1. On traduit mot par mot (ou on récupère du glossaire)
2. On assemble : "severe" + "anterior" + "open bite"
3. On ajoute la phrase complète avec type = date du jour

Avantage : on peut purger les traductions temporaires sans perdre les mots de base.

### Correction manuelle

Si une traduction assemblée est incorrecte :
1. Modifier manuellement dans glossaire.csv
2. Changer le type de `jjmmaaaa` à `m` (manuel/validé)

---

## Affichage console

```
traduis.py V1.0.0 - 09/12/2025 00:35
Chemin : D:\find\py\traduis.py

Chargement du glossaire : refs/glossaire.csv
  -> 1247 entrées chargées
  -> Langues : fr, en, de, th, ar, cn

Vérification des traductions manquantes...
  [██████████████████████████████] 100% - 1247/1247

Traductions effectuées :
  -> Nouveaux termes : 12
  -> Depuis glossaire : 1235
  -> API DeepL : 10
  -> API MyMemory : 2

Glossaire mis à jour : refs/glossaire.csv
  -> 1259 entrées (+ 12)

Temps total : 2.3 secondes
```

---

## Fichier initial : glossaire.csv

Le fichier initial contiendra :
1. Les mots courants (type `p` et `c`)
2. Les termes orthodontiques existants dans `tags.csv` (type `o`)

### Peuplement initial

Un script `init_glossaire.py` pourra être créé pour :
1. Extraire tous les termes de `tags.csv`
2. Les formater dans `glossaire.csv`
3. Ajouter les mots courants de base

---

## Pièces jointes nécessaires pour recréer les programmes

1. `Prompt_contexte0412.md` — Contexte général du projet
2. `Prompt_glossaire.md` — Ce document
3. `commun.csv` — Configuration des langues
4. `tags.csv` — Pour extraction initiale des termes médicaux (optionnel)

---

## Tests recommandés

| Test | Commande | Résultat attendu |
|------|----------|------------------|
| Vérification glossaire | `python traduis.py` | Stats + màj si nécessaire |
| Phrase connue | `python traduis.py "béance"` | Traductions depuis glossaire |
| Phrase nouvelle | `python traduis.py "test nouveau"` | Traduction API + ajout glossaire |
| Fichier | `python traduis.py test.csv` | Création test_out.csv |
| Type z | Entrée `z;ANB>4°` | Même valeur dans toutes les langues |

---

**FIN DU DOCUMENT** - Version 1.0.0 - 09/12/2025
