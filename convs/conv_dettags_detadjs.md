# Prompt conv_dettags_detadjs V1.0.2 - 09/12/2025 22:02:57

# Synthèse conversation : dettags&detadjs

---

## Informations générales

| Élément | Valeur |
|---------|--------|
| **Nom de conversation** | dettags&detadjs |
| **Date de création** | 08/12/2025 |
| **Dernière mise à jour** | 09/12/2025 |
| **Projet** | Kitview - Recherche multilingue orthodontie |

---

## Échanges

### Échange 1 - 08/12/2025 15:42

**Question :** Exécuter le prompt `Prompt_dettags_detadjs.md` avec les fichiers fournis.

**Réponse :** Création de `dettags.py` V1 et `detadjs.py` V1 avec :
- Détection des tags de pathologie
- Détection des adjectifs qualificatifs
- Format JSON unifié des critères

---

### Échange 2 - 09/12/2025 10:15

**Question :** Affiner les programmes avec :
1. Import de `detlang.py` pour détection automatique de langue
2. Passage du tag détecté au lieu de la position dans `detadjs`
3. Création de `detquals.py` (orchestration tags qualifiés)
4. Création de `detecte.py` (détection complète)
5. Création de `motsvides.py` (suppression mots vides)

**Analyse architecture :**
- Architecture à 3 modules indépendants validée
- Algorithme "cueillette de groseilles" : traiter un tag à la fois, dans l'ordre d'apparition
- Option B retenue : un seul tag par itération

**Réponse :** Création/modification des programmes :

#### 1. dettags.py V2.0.0
- Import de `detlang` pour détection automatique de langue
- Paramètre `langue="auto"` par défaut
- Mode `single_tag` pour ne retourner qu'un seul tag
- **Correction importante** : En mode single_tag, retourne le tag le plus à gauche (par position) pour garantir le bon ordre de traitement

#### 2. detadjs.py V2.0.0
- Passage du tag détecté (`--tag-detecte`) au lieu de la position
- Calcul automatique de la position à partir du tag
- Interface CLI plus user-friendly

#### 3. detquals.py V1.0.0 (nouveau)
- Orchestre la détection des tags qualifiés
- Boucle "cueillette de groseilles" : tag → adjectifs → résidu → répéter
- **Correction importante** : Les adjectifs sont cherchés dans la question standardisée complète (pas dans le résidu)

#### 4. motsvides.py V1.0.0 (nouveau)
- Suppression des mots vides
- Support format multilingue (colonnes par langue) et monolingue (legacy)
- Cache pour performances

#### 5. detecte.py V1.0.0 (nouveau)
- Orchestration complète : detquals → detages → motsvides
- Gestion gracieuse des modules optionnels (detages non disponible actuellement)
- JSON complet prêt pour génération SQL

---

## Fichiers produits

### Programmes Python

| Fichier | Version | Description |
|---------|---------|-------------|
| `dettags.py` | 2.0.0 | Détection des tags avec détection auto de langue |
| `detadjs.py` | 2.0.0 | Détection des adjectifs par tag détecté |
| `detquals.py` | 1.0.0 | Orchestration tags qualifiés |
| `motsvides.py` | 1.0.0 | Suppression des mots vides |
| `detecte.py` | 1.0.0 | Détection complète |

### Prompts de documentation

| Fichier | Description |
|---------|-------------|
| `Prompt_dettags_detadjs.md` | Spécifications dettags et detadjs |
| `Prompt_detquals.md` | Spécifications detquals |
| `Prompt_motsvides.md` | Spécifications motsvides |
| `Prompt_detecte.md` | Spécifications detecte |

---

## Architecture finale

```
Question utilisateur
        │
        ▼
┌─────────────────────────────────────────┐
│             detecte.py                   │
├─────────────────────────────────────────┤
│                                          │
│  ÉTAPE 1: detquals.py                   │
│     │                                    │
│     ├── detlang.py (langue)             │
│     │                                    │
│     └── Boucle "groseilles":            │
│            ├── dettags.py (1 tag)       │
│            ├── detadjs.py (adjectifs)   │
│            └── Répéter sur résidu       │
│                                          │
│  ÉTAPE 2: detages.py (âge/sexe)         │
│                                          │
│  ÉTAPE 3: motsvides.py (nettoyage)      │
│                                          │
└─────────────────────────────────────────┘
        │
        ▼
    JSON complet → SQL
```

---

## Tests validés

| Test | Résultat |
|------|----------|
| `"patients avec béance sévère"` | ✅ béance + [sévère] |
| `"béance sévère et bruxisme nocturne"` | ✅ béance + [sévère], bruxisme + [nocturne] |
| `"patients avec de la"` → motsvides | ✅ "patients" (3 mots supprimés) |
| Détection auto de langue | ✅ fr détecté |

---

## Fichiers requis pour le fonctionnement

Dans le répertoire `refs/` :
- `syntags.csv` - Synonymes de tags
- `synadjs.csv` - Synonymes d'adjectifs
- `commun.csv` - Configuration (langues, adjectifs devant)
- `motsvides.csv` - Mots vides
- `glossaire.csv` - Vocabulaire pour détection de langue
- `tags.csv` - Fichier maître multilingue

---

## Prompts de recréation

### Pour recréer dettags.py et detadjs.py

**Pièces jointes :**
1. `Prompt_contexte0412.md`
2. `Prompt_dettags_detadjs.md`
3. `tags.csv`, `commun.csv`, `syntags.csv`, `synadjs.csv`
4. `detlang.py`

**Instruction :**
> Crée dettags.py V2 avec import de detlang pour détection auto de langue, mode single_tag retournant le tag le plus à gauche. Crée detadjs.py V2 acceptant le tag détecté au lieu de la position.

### Pour recréer detquals.py

**Pièces jointes :**
1. `Prompt_contexte0412.md`
2. `Prompt_detquals.md`
3. `dettags.py`, `detadjs.py`

**Instruction :**
> Crée detquals.py qui orchestre la détection des tags qualifiés en utilisant l'algorithme "cueillette de groseilles" (un tag à la fois, dans l'ordre d'apparition).

### Pour recréer motsvides.py

**Pièces jointes :**
1. `Prompt_contexte0412.md`
2. `Prompt_motsvides.md`
3. `motsvides.csv`, `commun.csv`

**Instruction :**
> Crée motsvides.py pour supprimer les mots vides, avec support multilingue.

### Pour recréer detecte.py

**Pièces jointes :**
1. `Prompt_contexte0412.md`
2. `Prompt_detecte.md`
3. `detquals.py`, `motsvides.py`

**Instruction :**
> Crée detecte.py qui orchestre la détection complète (detquals → detages → motsvides).

---

## Notes et observations

1. **Ordre de détection** : Le tag le plus à gauche est détecté en premier, ce qui garantit que les adjectifs sont correctement attribués.

2. **Zone de proximité** : Les adjectifs sont cherchés dans la question standardisée complète, mais la zone de proximité (3 mots avant, 5 mots après le tag) évite les attributions erronées.

3. **Module detages** : Non encore développé. `detecte.py` gère son absence gracieusement.

4. **Format motsvides.csv** : Le programme détecte automatiquement le format (monolingue legacy ou multilingue).

5. **Performances** : Les caches globaux évitent les rechargements multiples des fichiers de référence.

---

**FIN DE SYNTHÈSE**
