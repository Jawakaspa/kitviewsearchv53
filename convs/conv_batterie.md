# Prompt conv_batterie V1.0.3 - 12/01/2026 17:49:36

# Synthèse Conversation : batterie

## Informations générales
- **Nom de la conversation** : batterie
- **Projet** : KITVIEW - Recherche multilingue orthodontique
- **Objectif** : Créer un système de tests en batterie pour valider les modules de détection

---

## Échanges

### 📅 09/01/2026 - Analyse initiale et conception

**Question utilisateur :**
Créer un système de tests en batterie basé sur `batterie.csv` qui contient :
- Une colonne Q avec des questions de test (15 questions multilingues + 1 phrase "poubelle")
- Des colonnes avec des templates CLI pour différents programmes de détection

**Analyse Claude :**

1. **Structure de batterie.csv identifiée :**
   | Colonne | Programme testé |
   |---------|-----------------|
   | Q | Questions de test |
   | dettags.py Q | Détection tags + adjectifs |
   | detages Q | Détection âge/sexe |
   | detangles Q | Détection angles céphalo |
   | detall Q | Orchestrateur complet |
   | trouve base25000.db -v Q | Recherche avec base |

2. **Problème identifié :** Les programmes produisent du JSON verbeux, pas adapté à une cellule de matrice.

3. **Deux approches proposées :**
   - **Option A** : Modifier chaque programme avec `--synth`
   - **Option B** : Créer un wrapper `batterie.py` ✅ **CHOISI**

**Décisions utilisateur :**
1. ✅ Option B (wrapper batterie.py)
2. ✅ Format lisible : "2 tags: béance, bruxisme | 1 adj: antérieur | residu: xxx"
3. ✅ Pour trouve.py : avec mode "42 patients | standard | 125ms"
4. ✅ Typo confirmée : `detags.py` → `dettags.py`
5. ✅ Ajouter `detia.py` pour comparaison IA vs algorithmique
6. ✅ Base `base25000.db` disponible dans `/bases`

---

### 📅 09/01/2026 23:52 - Premier test et corrections V1.0.1

**Problème signalé :**
Tous les tests ont échoué avec "❌ erreur (code 1)" ou "❌ erreur (code 2)".

**Analyse du fichier batterie.csv utilisé :**
```csv
Q;python detags.py Q;python detage.py Q;python detangles.py Q;...
```

**Problèmes identifiés :**
1. `detags.py` au lieu de `dettags.py` (typo)
2. `trouve` sans `.py`
3. Colonnes `search.py` présentes mais non supportées

**Corrections appliquées (V1.0.1) :**
- Fonction `normaliser_commande()` ajoutée :
  - Ajoute `python ` si absent
  - Ajoute `.py` si absent (`trouve` → `trouve.py`)
  - Corrige `detags` → `dettags`
- Support de `search.py` ajouté avec synthèse dédiée
- Mode debug amélioré (affiche stderr)

---

## Architecture décidée

### Programme `batterie.py`

**Entrée :** `batterie.csv`
```csv
Q;dettags.py Q;detage.py Q;detangles.py Q;detall.py Q;detia.py Q;trouve base25000.db -v Q
patients qui grincent des dents;;;;;
歯ぎしり;;;;;
...
```

**Sortie :** `batterie_YYYYMMDD_HHMMSS.csv`
```csv
Q;dettags;detage;detangles;detall;detia;trouve
patients qui grincent des dents;1 tag: bruxisme | residu: patients qui;0 crit;0 angle;...;...;...
```

**Format des synthèses :**
| Programme | Format synthèse |
|-----------|-----------------|
| dettags.py | `N tags: t1, t2 \| N adjs: a1, a2 \| residu: xxx` |
| detage.py | `N crit: <30 ans, Femme \| residu: xxx` |
| detangles.py | `N angles: classe II squelettique \| residu: xxx` |
| detall.py | `MODE \| N tags: t1 \| N ages: a1 \| residu: xxx` |
| detia.py | `IA \| N tags: t1 \| Nms \| residu: xxx` |
| trouve.py | `N patients \| mode \| Nms` |

**En cas d'erreur :** `❌ erreur: message`

---

## Fichiers à créer

| Fichier | Description |
|---------|-------------|
| `batterie.py` | Programme principal de tests en batterie |
| `batterie.csv` | Fichier d'entrée (corrigé avec dettags.py + detia.py) |

---

## Prompts de recréation

### Pour recréer `batterie.py`
```
Crée un programme Python batterie.py qui :
1. Lit un fichier CSV (batterie.csv) avec une colonne Q (questions) et des colonnes de templates CLI
2. Pour chaque question × template CLI, exécute la commande en remplaçant Q par la question
3. Parse le JSON de sortie de chaque programme
4. Génère une synthèse lisible dans chaque cellule
5. Écrit le résultat dans batterie_YYYYMMDD_HHMMSS.csv

Formats de synthèse :
- dettags : "N tags: t1, t2 | N adjs: a1 | residu: xxx"
- detage : "N crit: label1, label2 | residu: xxx"  
- detangles : "N angles: classe II | residu: xxx"
- detall : "MODE | N tags | N ages | residu: xxx"
- detia : "IA | N tags | Nms | residu: xxx"
- trouve : "N patients | mode | Nms"

Pièces jointes nécessaires :
- Prompt_contexte2312.md (conventions projet)
- batterie.csv (fichier d'entrée)
- dettags.py, detage.py, detangles.py, detall.py, detia.py, trouve.py (pour référence formats JSON)
```

---

## Prochaines étapes

1. [x] Créer `batterie.py` avec parsing JSON et synthèses ✅ FAIT
2. [x] Corriger `batterie.csv` (dettags.py au lieu de detags.py, ajouter detia.py) ✅ FAIT
3. [ ] Tester sur les 15 questions
4. [ ] Analyser les résultats comparatifs IA vs algorithmique

---

## Fichiers créés

### batterie.py (V1.0.1)
Programme principal de tests en batterie. Fonctionnalités :
- Lit `batterie.csv` avec questions et templates CLI
- Exécute chaque commande via subprocess
- Parse le JSON de sortie (après "RÉSULTAT (JSON)")
- Génère des synthèses lisibles par programme
- Écrit `batterie_YYYYMMDD_HHMMSS.csv`
- Gestion timeout et erreurs
- Barre de progression

**Corrections V1.0.1 :**
- Normalisation automatique des commandes :
  - Ajoute `python ` si absent au début
  - Ajoute `.py` au nom du programme si omis (ex: `trouve` → `trouve.py`)
  - Corrige la typo `detags` → `dettags`
  - Gère Q en milieu ou fin de commande
- Support de `search.py` ajouté
- Mode debug amélioré (affiche stderr en cas d'erreur)

### batterie.csv (corrigé)
Fichier de test avec :
- 15 questions multilingues (FR, JA, EN, DE, IT, PT, ES)
- 6 templates CLI : dettags, detage, detangles, detall, detia, trouve
- 1 question "poubelle" pour tester la robustesse

---

**Dernière mise à jour :** 09/01/2026
