# Prompt_templatequestion.md

## Objectif

Créer le programme `templatequestion.py` qui génère 100 templates de questions pour la recherche de patients orthodontiques, en utilisant le principe du "cadavre exquis" pour créer des phrases variées mais syntaxiquement correctes.

---

## Fichiers à joindre en PJ

1. **tagsadjs.xlsx** : Fichier Excel contenant les pathologies (type='p') et adjectifs (type='a')
   - Colonnes : canon, type, Xgn, synonymes, XX, adjs, XY, m, f, mp, fp
   - Xgn indique le genre du tag (m, f, mp, fp)
   - adjs contient les adjectifs compatibles séparés par virgule
   - m, f, mp, fp contiennent les formes accordées des adjectifs

2. **ages.csv** : Critères d'âge et de sexe
   - Colonnes : expression, operateur, valeur_sql, sexe, label, pourquestion
   - pourquestion indique l'article (un, une, des)

3. **angles.csv** : Angles céphalométriques (ANB, SNA, SNB)
   - Colonnes : expression, operateur, seuil, tag_canonique, adjectifs_possibles, label

4. **cadavreexquis.csv** : Composants de phrases pour le cadavre exquis
   - Colonnes : categorie, texte, variante, article
   - Catégories : debut_list, debut_count, liaison, liaison_age, connecteur, fin

5. **Prompt_contexte0412.md** : Contexte du projet Kitview

---

## Spécifications

### Répartition des 100 templates

| Critères | Templates | Contraintes |
|----------|-----------|-------------|
| 1 critère | 1-25 | 1 tag OU 1 angle OU 1 âge |
| 2 critères | 26-50 | ≥2 éléments, au moins 1 tag avec adjectif |
| 3 critères | 51-75 | ≥3 éléments, au moins 1 tag avec adjectif |
| 4 critères | 76-100 | ≥4 éléments, au moins 1 tag avec adjectif |

### Distribution globale
- **30 COUNT / 70 LIST** : répartis aléatoirement
- **10 avec angles** : répartis aléatoirement

### Placeholders à utiliser
- `{T1}`, `{T2}`, `{T3}`, `{T4}` : Tags (pathologies)
- `{A1}`, `{A2}`, `{A3}`, `{A4}` : Adjectifs (accordés selon le genre du tag associé)
- `{AGE}` : Critère d'âge/sexe
- `{ANG}` : Angle céphalométrique

### Structure des templates

```
[DEBUT] [LIAISON?] [CRITERE1] [CONNECTEUR1?] [CRITERE2?] ... [FIN]
```

- **DEBUT** : Choisi selon le type (COUNT ou LIST)
  - LIST : "Trouve les", "Je cherche les", "Montre-moi les", etc.
  - COUNT : "Combien de patients ont", "Quel est le nombre de", etc.
- **LIAISON** : "patients avec", "patients qui ont", "personnes ayant", etc.
- **CONNECTEUR** : "et", "avec", "ayant également", "présentant aussi", etc.
- **FIN** : "?" ou "."

### Principe "cadavre exquis"
- Combiner aléatoirement les composants de `cadavreexquis.csv`
- Varier les débuts, liaisons et connecteurs
- Produire des phrases différentes à chaque exécution

---

## Fichier de sortie

**templatequestion.csv** avec colonnes :
- `id` : Identifiant (1 à 100)
- `nb_criteres` : Nombre de critères (1 à 4)
- `type` : COUNT ou LIST
- `has_angle` : OUI ou NON
- `template` : Le template de question avec placeholders

**tagsadjs_enrichi.xlsx** : tagsadjs avec colonne `article` ajoutée (un, une, des selon Xgn)

---

## Contraintes techniques (cf. Prompt_contexte0412.md)

- Python 3.13+
- Encodage UTF-8 sans BOM pour .py
- Encodage UTF-8-SIG (avec BOM) pour .csv
- Séparateur CSV : `;`
- Variables `__pgm__`, `__version__`, `__date__` en début de fichier
- Affichage initial dans main() avec version
- Chemins absolus dans les affichages console
- Pas de données en dur (utiliser les fichiers CSV)

---

## Exemple de templates attendus

```csv
id;nb_criteres;type;has_angle;template
1;1;LIST;NON;Trouve les patients avec {T1}?
26;2;COUNT;NON;Combien de patients ont {T1} {A1} et {AGE}?
51;3;LIST;OUI;Montre-moi les cas avec {T1} {A1} plus {T2} et qui ont {ANG}.
76;4;LIST;NON;Je cherche les patients ayant {T1} {A1} et {T2} plus {AGE} avec {T3}?
```
