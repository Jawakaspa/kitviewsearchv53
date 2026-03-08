# Prompt_creefakelog.md

## Objet

Ce prompt permet de recréer le fichier `creefakelog.py`, un générateur de fichier de logs de recherches fictives pour tester et analyser le système de recherche orthodontique multilingue.

---

## Contexte

Le projet dispose d'un fichier `logrecherche.csv` qui enregistre les recherches réelles effectuées par les utilisateurs. Pour les besoins de tests, d'analyse statistique et de démonstration, il est nécessaire de générer un fichier de logs fictifs plus volumineux avec des données réalistes.

---

## Spécifications fonctionnelles

### Usage

```
python creefakelog.py N z.csv
```

- `N` : Nombre de lignes souhaité dans le fichier de sortie (doit être ≥ 3 × LR où LR = nombre de lignes de logrecherche.csv)
- `z.csv` : Fichier de questions avec colonnes `fr`, `en`, `ja`

### Fichiers

- **Entrée** : `logs/logrecherche.csv` (log existant)
- **Entrée** : `z.csv` (fichier de questions, ex: `fr100.csv`)
- **Entrée** : `refs/motsvides.csv` (mots vides pour diversification)
- **Sortie** : `logs/logrechercheout.csv`

### Structure du fichier de sortie

Le fichier est composé de 3 phases :

#### Phase 1 : Copie des lignes originales
- Toutes les lignes de `logrecherche.csv` sont recopiées telles quelles

#### Phase 2 : Duplication avec modifications (1er - 17 décembre 2025)
- Les lignes originales sont dupliquées avec :
  - Nouveau timestamp aléatoire entre le 1er et le 17 décembre 2025
  - Nouveau session_id (UUID)
  - Nouvelle IP
  - **Rating obligatoire** :
    - 1/3 : 👍 avec commentaire élogieux généré aléatoirement
    - 2/3 : 👎 avec `type_probleme` équiréparti entre :
      - "Bug IHM"
      - "Trop de patients"
      - "Pas assez de patients"
      - "Autre"
    - Et commentaire négatif correspondant

#### Phase 3 : Nouvelles lignes (18 décembre 2025 - 5 janvier 2026)
- Nombre de lignes = N - 2 × LR
- **Limitation des doublons** : Maximum 2 questions strictement identiques
  - Si une question est tirée une 3ème fois, un mot de `motsvides.csv` est ajouté :
    - Avant le `?` final si présent
    - À la fin sinon
- Pour chaque ligne :
  - Timestamp aléatoire entre le 18 décembre 2025 et le 5 janvier 2026
  - Question tirée au hasard dans le fichier de questions avec répartition :
    - 20% japonais (colonne `ja`)
    - 25% anglais (colonne `en`)
    - 55% français (colonne `fr`)
  - Si la colonne tirée au sort est vide → ignorer et retirer une autre
  - **Résultats de recherche simulés** :
    - `temps_ms` : 10-150ms pour mode rapide, 1500-5000ms pour mode IA
    - `nb_patients` : distribution exponentielle (tendance petits nombres), max 25000
    - `mode` : aléatoire parmi ["rapide", "ia", "compare", "union"]
    - `modulelangue` : adapté à la langue
    - `filtres` : JSON simplifié
    - `pathologies` : parfois vide, parfois une pathologie aléatoire
  - **Rating 1 fois sur 2** avec même répartition que phase 2
  - `base` : toujours "base25000.db"

### Tri final
Le fichier de sortie est trié par timestamp croissant.

---

## Spécifications techniques

### Format CSV
- Encodage : UTF-8-SIG (avec BOM)
- Séparateur : `;`
- Première ligne : commentaire de version `# logrechercheout.csv V1.0.0 - DD/MM/YYYY HH:MM:SS`
- Deuxième ligne : en-tête des colonnes

### Colonnes du log
```
module;timestamp;temps_ms;languesaisie;langueutilisee;modulelangue;questionoriginale;question;filtres;sql;tri;base;mode;nb_patients;pathologies;ages;residu;erreur;session_id;ip_utilisateur;rating;type_probleme;commentaire
```

### Cartouche Python
```python
#*TO*#
__pgm__ = "creefakelog.py"
__version__ = "0.0.0"
__date__ = "01/01/1970 00:00"
```

### Affichage
- Affichage du cartouche au démarrage
- Progression pour les traitements longs
- Résumé final avec statistiques
- Indication du nombre de questions diversifiées

---

## Fichiers à joindre pour recréation

1. `Prompt_contexte.md` (contexte général du projet)
2. `logrecherche.csv` (exemple du format de log)
3. `fr100.csv` (exemple de fichier de questions)
4. `motsvides.csv` (liste des mots vides pour diversification)

---

## Exemple d'exécution

```bash
python creefakelog.py 300 fr100.csv
```

Sortie attendue :
```
╔════════════════════════════════════════════════════════════════
║ creefakelog.py V1.0.0 - 02/01/2026 10:15:00
║ Générateur de fichier de logs de recherches fictives
╚════════════════════════════════════════════════════════════════

Configuration:
  N souhaité        : 300
  Fichier questions : C:\g\fr100.csv
  Log entrée        : C:\g\logs\logrecherche.csv
  Log sortie        : C:\g\logs\logrechercheout.csv

Phase 0 : Chargement des données...
  → 70 lignes existantes chargées (LR = 70)
  → 98 questions chargées depuis C:\g\fr100.csv
  → 210 mots vides chargés depuis C:\g\refs\motsvides.csv
  → LR (lignes originales) = 70
  → N minimum requis = 3 × 70 = 210

Phase 1 : Copie des lignes originales...
  → Phase 1 : 70 lignes copiées

Phase 2 : Duplication avec timestamps 1-17 déc et ratings...
  → Phase 2 : 70 lignes générées (1-17 déc)

Phase 3 : Génération de 160 nouvelles lignes (18 déc - 5 jan)...
  → Questions disponibles : fr=98, en=97, ja=97
    [50/160] lignes générées...
    [100/160] lignes générées...
    [150/160] lignes générées...
  → Phase 3 : 160 lignes générées (18 déc - 5 jan)
  → 17 questions diversifiées (> 2 occurrences)

Fusion et tri...
  → Total avant tri : 300 lignes
  → Tri par timestamp croissant effectué

Écriture du fichier de sortie...

══════════════════════════════════════════════════════════════════════
✅ Fichier généré : C:\g\logs\logrechercheout.csv
   → 300 lignes écrites
   → Phase 1 : 70 (originales)
   → Phase 2 : 70 (dupliquées 1-17 déc)
   → Phase 3 : 160 (nouvelles 18 déc - 5 jan)
══════════════════════════════════════════════════════════════════════
```

---

## Notes de conception

- **Pas d'appel réel à search.py** : Les résultats sont entièrement simulés pour éviter les dépendances complexes
- **Distribution exponentielle** pour `nb_patients` : Reproduit le comportement réel où la plupart des recherches retournent peu de patients
- **Commentaires réalistes** : Banque de commentaires positifs/négatifs variés pour un rendu crédible
- **Gestion des colonnes vides** : Si une question n'existe pas dans la langue tirée au sort, fallback sur français
- **Diversification des questions** : Maximum 2 questions identiques, puis ajout d'un mot vide de `motsvides.csv`

### Algorithme de diversification

```
Pour chaque question tirée au sort:
    Si occurrences[question] >= 2:
        Si question se termine par '?':
            question = question[:-1] + " " + mot_vide_aleatoire + " ?"
        Sinon:
            question = question + " " + mot_vide_aleatoire
    occurrences[question_base] += 1
```

---

**FIN DU PROMPT**
