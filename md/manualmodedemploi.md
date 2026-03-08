# Prompt manualmodedemploi V1.0.0 - 23/01/2026 12:53:03

# Mode d'emploi - Manuel Kitview

<!-- PRESENTATION_META
titre_court: "Manuel Kitview - Mode d'emploi"
sous_titre: "Guide pratique pour maintenir le manuel multilingue"
duree_estimee: "10min"
niveau: "débutant"
audience: "Responsable documentation, assistante, toute personne non technique"
fichiers_concernes: "translations.csv (Excel)"
emoji_principal: "📖"
-->

**Version** : 1.0.0  
**Date** : 23 janvier 2026

---

<!-- SLIDE
id: "introduction"
titre: "À quoi sert ce document ?"
template: "contenu"
emoji: "👋"
timing: "1min"
-->

## Introduction

<!-- KEY: Ce guide explique comment modifier les textes du manuel Kitview sans aucune compétence technique. -->

Ce document explique **comment modifier les textes du manuel Kitview** de façon simple.

**Vous n'avez pas besoin de :**
- Savoir programmer
- Installer des logiciels spéciaux
- Comprendre le HTML ou Python

**Vous avez juste besoin de :**
- Excel (ou LibreOffice Calc)
- Savoir modifier des cellules dans un tableau

---

<!-- SLIDE
id: "ce-quon-a"
titre: "Ce qu'on a"
template: "2colonnes"
emoji: "📁"
timing: "2min"
-->

## 1. Ce qu'on a

<!-- KEY: Un fichier Excel central (translations.csv) contient tous les textes. Modifier ce fichier = modifier le manuel. -->

### Le fichier principal

**`translations.csv`** - C'est le fichier que vous allez modifier.

Il contient **474 lignes** de texte, chacune avec :
- Le texte français original
- La traduction anglaise
- Les versions adaptées (Débutant, Intermédiaire, Expert)

### Les manuels générés

| Fichier | Description |
|---------|-------------|
| `kitviewmanuals.html` | Manuel Standard (français) |
| `kitviewmanuals_en.html` | Manuel Standard (anglais) |
| `kitviewmanuald.html` | Manuel Débutant |
| `kitviewmanuali.html` | Manuel Intermédiaire |
| `kitviewmanuale.html` | Manuel Expert |

---

<!-- SLIDE
id: "ouvrir-csv"
titre: "Ouvrir le fichier CSV"
template: "contenu"
emoji: "📂"
timing: "2min"
-->

## 2. Comment ouvrir le fichier

<!-- KEY: Ouvrir translations.csv avec Excel en choisissant le bon séparateur (point-virgule). -->

### Étape 1 : Ouvrir Excel

Double-cliquez sur `translations.csv` ou ouvrez Excel puis :
- Fichier → Ouvrir → Sélectionnez `translations.csv`

### Étape 2 : Choisir le bon format

Si Excel vous demande comment importer le fichier :
- **Séparateur** : Point-virgule (;)
- **Encodage** : UTF-8

### Ce que vous voyez

| id | fr | en | EN | d | D | i | I | e | E |
|----|----|----|----|----|----|----|----|----|-----|
| txt_0001 | Texte français | Traduction auto | | Version débutant | | ... | | ... | |

---

<!-- SLIDE
id: "colonnes"
titre: "Comprendre les colonnes"
template: "tableau"
emoji: "📊"
timing: "3min"
-->

## 3. Les colonnes du fichier

<!-- KEY: Colonnes minuscules = automatique (ne pas toucher). Colonnes MAJUSCULES = vos corrections manuelles. -->

<!-- QUESTION: Pourquoi avoir deux colonnes pour chaque langue/niveau ? -->

### Les 10 colonnes expliquées

| Colonne | Quoi ? | Qui remplit ? | Vous modifiez ? |
|---------|--------|---------------|-----------------|
| `id` | Numéro unique | Automatique | ❌ Jamais |
| `fr` | Texte français original | Automatique | ❌ Jamais |
| `en` | Traduction anglaise (DeepL) | Automatique | ❌ Non |
| `EN` | **Correction anglaise** | **Vous** | ✅ **Oui** |
| `d` | Version Débutant (Claude) | Automatique | ❌ Non |
| `D` | **Correction Débutant** | **Vous** | ✅ **Oui** |
| `i` | Version Intermédiaire | Automatique | ❌ Non |
| `I` | **Correction Intermédiaire** | **Vous** | ✅ **Oui** |
| `e` | Version Expert | Automatique | ❌ Non |
| `E` | **Correction Expert** | **Vous** | ✅ **Oui** |

### Règle simple

**Minuscules** = rempli automatiquement → ne pas toucher  
**MAJUSCULES** = vos corrections → vous pouvez modifier

---

<!-- SLIDE
id: "corriger-traduction"
titre: "Corriger une traduction"
template: "contenu"
emoji: "✏️"
timing: "2min"
-->

## 4. Comment corriger une traduction anglaise

<!-- KEY: Pour corriger une traduction, écrire votre version dans la colonne EN (majuscule). Elle remplacera la version automatique. -->

### Exemple

Vous trouvez que la traduction automatique n'est pas bonne :

| fr | en | EN |
|----|----|----|
| Cliquez sur Valider | Click on Validate | |

La traduction "Click on Validate" ne vous plaît pas.

**Solution** : Écrivez votre correction dans la colonne `EN` :

| fr | en | EN |
|----|----|----|
| Cliquez sur Valider | Click on Validate | **Click the Confirm button** |

Quand le manuel sera régénéré, c'est votre texte (colonne `EN`) qui sera utilisé.

---

<!-- SLIDE
id: "marqueurs"
titre: "Les marqueurs spéciaux"
template: "tableau"
emoji: "🏷️"
timing: "2min"
-->

## 5. Les marqueurs spéciaux (niveaux D/I/E)

<!-- KEY: [=] signifie "garder le texte standard", [X] signifie "supprimer ce texte pour ce niveau". -->

Pour les colonnes Débutant/Intermédiaire/Expert, vous verrez parfois des codes :

| Marqueur | Signification | Exemple |
|----------|---------------|---------|
| `[=]` | Garder le texte standard (celui de la colonne `fr`) | Texte déjà simple, pas besoin de changer |
| `[X]` | Supprimer ce texte pour ce niveau | Texte trop technique pour un débutant |
| (vide) | Utiliser la version générée automatiquement | Cas normal |

### Exemple concret

| fr | d | D |
|----|---|---|
| Configuration API REST | [X] | |

Le `[X]` signifie : "Ce texte sur l'API REST est trop technique, on le supprime de la version Débutant."

---

<!-- SLIDE
id: "workflow-correction"
titre: "Processus de correction"
template: "schema"
emoji: "🔄"
timing: "2min"
-->

## 6. Le processus complet

<!-- KEY: Vous modifiez le CSV, vous demandez à Thierry de lancer les scripts Python, les fichiers HTML sont régénérés. -->

<!-- DIAGRAM
type: "flux"
titre: "Workflow de mise à jour"
-->

```
┌─────────────────────────────────────────────────────────────┐
│                                                             │
│  1. VOUS : Ouvrir translations.csv avec Excel               │
│            ↓                                                │
│  2. VOUS : Trouver le texte à corriger (recherche Ctrl+F)   │
│            ↓                                                │
│  3. VOUS : Écrire votre correction dans la colonne          │
│            MAJUSCULE correspondante (EN, D, I ou E)         │
│            ↓                                                │
│  4. VOUS : Enregistrer le fichier CSV                       │
│            ↓                                                │
│  5. VOUS : Envoyer le fichier à Thierry                     │
│            ↓                                                │
│  6. THIERRY : Lance les scripts Python                      │
│            ↓                                                │
│  7. THIERRY : Vous renvoie les fichiers HTML mis à jour     │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

<!-- /DIAGRAM -->

---

<!-- SLIDE
id: "enregistrer"
titre: "Bien enregistrer le fichier"
template: "contenu"
emoji: "💾"
timing: "1min"
-->

## 7. Comment bien enregistrer

<!-- KEY: Toujours enregistrer en CSV avec séparateur point-virgule et encodage UTF-8. -->

### ⚠️ Important

Quand vous enregistrez avec Excel :
1. Fichier → Enregistrer sous
2. Type : **CSV UTF-8 (délimité par des virgules)** ou **CSV (séparateur point-virgule)**
3. Cliquez sur **Enregistrer**
4. Si Excel demande confirmation, cliquez **Oui**

### Vérification

Le fichier doit s'appeler `translations.csv` (pas `.xlsx`)

---

<!-- SLIDE
id: "ce-que-fait-thierry"
titre: "Ce que fait Thierry"
template: "contenu"
emoji: "🔧"
timing: "2min"
-->

## 8. Ce que fait Thierry (technique)

<!-- KEY: Thierry exécute 4 commandes Python pour régénérer tous les fichiers HTML à partir du CSV modifié. -->

Quand vous lui envoyez le CSV modifié, Thierry exécute ces commandes :

```
python gene.py fr    → Vérifie le français
python gene.py en    → Génère la version anglaise
python gene.py d     → Génère la version Débutant
python gene.py i     → Génère la version Intermédiaire
python gene.py e     → Génère la version Expert
```

**Temps d'exécution** : quelques secondes

Si vous avez ajouté beaucoup de corrections, Thierry peut aussi relancer les traductions/adaptations automatiques :

```
python trad.py translations.csv   → Traduit les nouveaux textes
python adapt.py all translations.csv   → Adapte les nouveaux textes
```

---

<!-- SLIDE
id: "rechercher-texte"
titre: "Trouver un texte à corriger"
template: "contenu"
emoji: "🔍"
timing: "1min"
-->

## 9. Astuce : Trouver un texte rapidement

<!-- KEY: Utilisez Ctrl+F dans Excel pour rechercher le texte français que vous voulez corriger. -->

### Dans Excel

1. Appuyez sur **Ctrl + F**
2. Tapez quelques mots du texte français
3. Cliquez sur **Rechercher suivant**
4. Vous êtes sur la bonne ligne !

### Exemple

Vous voulez corriger la traduction de "Cliquez sur Paramètres" :
1. Ctrl + F
2. Tapez : `Paramètres`
3. Vous trouvez la ligne
4. Allez dans la colonne `EN` et tapez votre correction

---

<!-- SLIDE
id: "resume"
titre: "Résumé"
template: "synthese"
emoji: "📝"
timing: "1min"
-->

## 10. Résumé

<!-- KEY: Ouvrir le CSV, écrire dans les colonnes MAJUSCULES, enregistrer, envoyer à Thierry. C'est tout ! -->

| Étape | Action |
|-------|--------|
| 1 | Ouvrir `translations.csv` avec Excel |
| 2 | Chercher le texte (Ctrl+F) |
| 3 | Écrire votre correction dans la colonne MAJUSCULE |
| 4 | Enregistrer en CSV |
| 5 | Envoyer à Thierry |

### Les colonnes que VOUS pouvez modifier

- `EN` → Corrections anglaises
- `D` → Corrections Débutant
- `I` → Corrections Intermédiaire
- `E` → Corrections Expert

### Les colonnes à NE PAS toucher

- `id`, `fr`, `en`, `d`, `i`, `e`

---

<!-- NO_SLIDE -->

## Annexe : Questions fréquentes

### "J'ai fait une erreur, comment annuler ?"

Supprimez simplement le contenu de la cellule MAJUSCULE. La version automatique sera utilisée.

### "Je veux supprimer un texte d'un niveau"

Écrivez `[X]` dans la colonne du niveau concerné.

### "Le texte est bien, je ne veux pas le changer"

Ne faites rien ! Laissez la cellule vide.

### "Je ne trouve pas le texte que je cherche"

Vérifiez l'orthographe. Le texte est peut-être légèrement différent dans le manuel affiché.

### "Excel me demande plein de choses à l'ouverture"

Choisissez : Séparateur = Point-virgule, Encodage = UTF-8

<!-- /NO_SLIDE -->

---

**Fin du mode d'emploi**

*Pour toute question, contactez Thierry.*
