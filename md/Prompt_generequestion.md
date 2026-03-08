# Prompt_generequestion.md

## Objectif

Créer le programme `generequestion.py` qui génère N questions en français à partir de patients réels de la base de données. La méthode "cheat" garantit que chaque question générée aura au moins un patient correspondant.

---

## Fichiers à joindre en PJ

1. **base100.db** (ou autre base) : Base de données SQLite des patients
2. **templatequestion.csv** : Templates de questions générés par templatequestion.py
3. **tagsadjs.xlsx** : Pathologies et adjectifs avec accords grammaticaux
4. **ages.csv** : Critères d'âge
5. **angles.csv** : Correspondance tags ↔ angles céphalométriques
6. **Prompt_contexte0412.md** : Contexte du projet Kitview

---

## Usage

```bash
python generequestion.py base.db N
```

- `base.db` : Chemin vers la base de données SQLite
- `N` : Nombre de questions à générer

---

## Structure de la base de données

```sql
-- Table patients
id INTEGER PRIMARY KEY
canontags TEXT        -- Tags séparés par virgule (ex: "béance,bruxisme,classe ii")
canonadjs TEXT        -- Adjectifs par position, séparés par virgule, alternatifs par | 
                      -- (ex: ",sévère|modéré,division 1")
sexe TEXT             -- 'M' ou 'F'
age DECIMAL           -- Âge en années décimales (ex: 12.5)
prenom TEXT
nom TEXT
```

---

## Méthode "cheat" - Principe

Le principe est de lire d'abord les données des patients puis générer des questions qui correspondent à leurs caractéristiques :

### Phase 1 : Questions avec angles (~10%)

1. Chercher les patients ayant un tag correspondant à un `tag_canonique` de angles.csv
2. Générer une expression d'angle appropriée (ANB/SNA/SNB > ou < valeur)
3. Ajouter optionnellement d'autres tags du patient
4. Les angles doivent être écrits en MAJUSCULES dans la question

### Phase 2 : Questions sans angles (~90%)

1. Tirer un patient au hasard
2. Utiliser ses tags (canontags) et adjectifs (canonadjs)
3. Optionnellement ajouter un critère d'âge basé sur son âge réel
4. Sélectionner un template compatible avec le nombre de critères disponibles

---

## Spécifications détaillées

### Mapping angles (angles.csv)

| tag_canonique | angle | seuil |
|---------------|-------|-------|
| classe i squelettique | ANB | BETWEEN 0,4 |
| classe ii squelettique | ANB | > 4 |
| classe iii squelettique | ANB | < 0 |
| prognathisme maxillaire | SNA | > 84 |
| rétrognathisme maxillaire | SNA | < 80 |
| prognathisme mandibulaire | SNB | > 82 |
| rétrognathisme mandibulaire | SNB | < 78 |

### Génération d'expressions d'angle

- `>` : Générer valeur au-dessus du seuil + random(1,4)
- `<` : Générer valeur en-dessous du seuil - random(1,4)
- `BETWEEN` : Utiliser directement les bornes

**⚠️ ATTENTION** : Le seuil lu depuis angles.csv est une **string** ("82"), pas un int !

```python
# MAUVAIS - bug isinstance
seuil_int = int(seuil) if isinstance(seuil, (int, float)) else 4  # Toujours 4 !

# BON - conversion explicite
def parse_seuil(s):
    try:
        return int(float(str(s)))
    except (ValueError, TypeError):
        return 4
seuil_int = parse_seuil(seuil)  # 82 correct !
```

Exemples : "ANB > 6", "SNA < 78", "SNB > 85", "ANB entre 0 et 4"

### Génération de critères d'âge

À partir de l'âge réel du patient, générer aléatoirement :
- Âge exact : "12 ans"
- Fourchette : "entre 9 et 15 ans"
- Catégorie : "adolescents", "adultes", "enfants", "mineurs"
- Comparaison : "plus de 10 ans", "moins de 20 ans"

### Accords grammaticaux

- Les adjectifs doivent être accordés selon le genre (Xgn) du tag dans tagsadjs.xlsx
- Utiliser les colonnes m, f, mp, fp pour les formes accordées

---

## Fichier de sortie

**testspatsN.csv** (où N est extrait du nom de la base, ex: testspats100.csv pour base100.db) avec colonnes :

| Colonne | Description |
|---------|-------------|
| question | La question en français |
| type | COUNT ou LIST |
| nb_criteres | Nombre de critères (1 à 4) |
| nb_resultats | Nombre de patients correspondants |
| ids_10 | Les 10 premiers IDs séparés par virgule |

---

## Points critiques

### Normalisation des tags
Les tags doivent être générés en **minuscules** pour correspondre au système de détection :
- ✅ "bruxisme", "classe ii squelettique", "béance"
- ❌ "Bruxisme", "Classe II squelettique", "Béance"

### Comptage des patients
Utiliser `stdcanontags` et `stdcanonadjs` (colonnes normalisées) au lieu de `canontags` et `canonadjs`.

---

## Nettoyage des questions

Les questions doivent être nettoyées pour supprimer :
- Les placeholders non remplis ({T1}, {A1}, etc.)
- Les connecteurs orphelins ("et ?", "avec .")
- Les doubles connecteurs ("avec avec", "et et")
- Les patterns mal formés ("les de X ans", "les entre")

---

## Contraintes techniques (cf. Prompt_contexte0412.md)

- Python 3.13+
- Encodage UTF-8 sans BOM pour .py
- Encodage UTF-8-SIG (avec BOM) pour .csv
- Séparateur CSV : `;`
- Variables `__pgm__`, `__version__`, `__date__` en début de fichier
- Affichage initial dans main() avec version
- Chemins absolus dans les affichages console
- Messages de progression pendant la génération

---

## Exemple de sortie

```csv
question;type;nb_criteres;nb_resultats;ids_10
Trouve les patients avec béance sévère?;LIST;1;5;3,4,10,29,78
Combien de patients ont ANB > 6 et bruxisme nocturne?;COUNT;2;2;12,55
Je cherche les patients avec classe ii squelettique division 2 et prognathisme maxillaire ayant également ANB > 7.;LIST;3;1;12
```
