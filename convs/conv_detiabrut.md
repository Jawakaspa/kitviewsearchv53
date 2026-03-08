# Prompt conv_detiabrut V1.0.2 - 04/01/2026 08:20:35

# Conversation : detiabrut

## Résumé

Création de `detiabrut.py`, une version configurable de `detia.py` permettant de désactiver sélectivement les référentiels utilisés pour la détection IA. L'objectif est de mesurer l'importance de chaque référentiel en comparant les résultats avec/sans leur utilisation.

---

## Échanges

### 02/01/2026 14:35 - Demande initiale et analyse

**Question** : Créer `detiabrut.py` qui est une version de détection IA "brute", c'est-à-dire avec aucun ou uniquement certains des fichiers de références (tags, adjectifs, angles, ages). Le but est de proposer cette méthode de détection en plus des méthodes existantes pour se rendre compte de l'importance des référentiels.

**Analyse Claude** :
- Examen de `detia.py` pour comprendre les référentiels utilisés
- Identification des fichiers : `tags.csv`, `adjectifs.csv`, `ages.csv`, `angles.csv`
- Questions posées sur l'architecture (fichier séparé vs options, niveau de brutalité, mapping canonique)

**Réponses Thierry** :
1. Fichier séparé `detiabrut.py`
2. Configurable par référentiel
3. Mapping canonique requis (JSON strictement identique sauf signature auteur)
4. Outil permanent

### 02/01/2026 14:40 - Clarification sur le mapping

**Question Claude** : Option A (brut dans le prompt, mapping en post-traitement) ou Option B (brut partout) ?

**Réponse Thierry** : Traiter le mapping comme une autre option de référentiel

### 02/01/2026 14:45 - Précisions sur la syntaxe CLI

**Demandes Thierry** :
- Enlever tous les `-` et `--no` dans les options → syntaxe simple : `tags ages mapping`
- Sans argument = afficher les options disponibles
- Pour tout activer : `detia` (pendant de `brut` qui enlève tout)
- Rajouter options `glossaire` et `deepl`

**Clarification Claude** : `glossaire` et `deepl` sont utilisés en amont (search) et non dans `detia.py`

**Décision Thierry** : On laisse tomber `glossaire` et `deepl` car trop complexe

### 02/01/2026 14:50 - Interface web

**Demande** : Mettre à jour `web12params.html` avec une section dédiée aux options de `detiabrut`

**Réalisation** :
- Ajout du CSS pour la nouvelle section (styles .detiabrut-*)
- Ajout du HTML avec grille de 5 cases à cocher + boutons raccourcis
- Ajout du JavaScript pour la gestion des options et l'affichage dynamique de la commande CLI
- Intégration avec localStorage (load/save)
- Version mise à jour : 1.0.3 → 1.1.0

---

## Spécifications finales

### Options de désactivation

| Option | Effet |
|--------|-------|
| `tags` | N'injecte pas la liste des 800 tags dans le prompt IA |
| `adjs` | N'injecte pas la liste des 200 adjectifs dans le prompt IA |
| `ages` | N'injecte pas les patterns âge/sexe dans le prompt IA |
| `angles` | N'injecte pas les seuils ANB/SNA/SNB dans le prompt IA |
| `mapping` | Ne mappe pas détecté → canonique (utilise `detecte.title()`) |

### Raccourcis

| Raccourci | Équivalent |
|-----------|------------|
| `brut` | Tout désactiver (`tags adjs ages angles mapping`) |
| `detia` | Tout activer (comportement identique à `detia.py`) |

### Usage CLI

```bash
python detiabrut.py                              # Affiche l'aide
python detiabrut.py "bruxisme sévère" detia      # Mode complet
python detiabrut.py "bruxisme sévère" brut       # Mode brut total
python detiabrut.py "bruxisme sévère" tags       # Sans tags uniquement
python detiabrut.py "bruxisme sévère" tags mapping gpt4o  # Sans tags ni mapping
python detiabrut.py tests.csv brut sonnet        # Batch mode brut
```

### Signature JSON

Le champ `auteur` indique les options désactivées :
- `"auteur": "openai/gpt-4o"` → mode detia (tout activé)
- `"auteur": "openai/gpt-4o [brut]"` → mode brut total
- `"auteur": "openai/gpt-4o [-tags,-mapping]"` → options spécifiques désactivées

---

## Fichiers produits

| Fichier | Description |
|---------|-------------|
| `detiabrut.py` | Programme principal - importe `detia.py` et ajoute les options de désactivation |
| `web12params.html` | Page paramètres mise à jour avec section "Options de détection IA" |
| `conv_detiabrut.md` | Ce document de synthèse |

---

## Modifications apportées à web12params.html

### Nouvelle section ajoutée
- **Section "🔬 Options de détection IA"** : grille de cases à cocher pour activer/désactiver les référentiels
- **5 options** : tags, adjs, ages, angles, mapping
- **Boutons raccourcis** : "Tout activer (detia)" / "Tout désactiver (brut)"
- **Affichage dynamique** de la commande CLI équivalente

### CSS ajouté
- Classes `.detiabrut-section`, `.detiabrut-grid`, `.detiabrut-item`, etc.
- Style visuel cohérent avec la section Moteurs IA existante
- Indicateur visuel rouge quand une option est désactivée

### JavaScript ajouté
- `updateDetiabrut()` : met à jour l'affichage et la commande CLI
- `setDetiabrut(mode)` : active/désactive tout
- `loadDetiabrutSettings()` : charge depuis localStorage
- `saveDetiabrutSettings()` : sauvegarde dans localStorage

---

## Prompt de recréation de detiabrut.py

Pour recréer `detiabrut.py` à partir de zéro :

### Fichiers à joindre en PJ
- `detia.py` (le module de base à importer)
- `Prompt_contexte2312.md` (contexte du projet)

### Prompt

```
Crée detiabrut.py, une version configurable de detia.py permettant de désactiver sélectivement les référentiels pour la détection IA.

ARCHITECTURE :
- Importe detia.py (charger_references, detecter_tout, etc.)
- Surcharge les fonctions nécessaires pour supporter les options

OPTIONS DE DÉSACTIVATION (sans tirets dans la CLI) :
- tags : N'injecte pas la liste des tags dans le prompt IA
- adjs : N'injecte pas la liste des adjectifs dans le prompt IA
- ages : N'injecte pas les patterns âge/sexe dans le prompt IA
- angles : N'injecte pas les seuils ANB/SNA/SNB dans le prompt IA
- mapping : Ne mappe pas détecté → canonique (utilise detecte.title())

RACCOURCIS :
- brut : Désactive tout
- detia : Active tout

SYNTAXE CLI :
- Sans argument : affiche l'aide avec toutes les options
- python detiabrut.py "question" detia → mode complet
- python detiabrut.py "question" brut → mode brut
- python detiabrut.py "question" tags mapping → sans tags ni mapping
- python detiabrut.py fichier.csv brut sonnet → batch brut avec Sonnet

SIGNATURE JSON :
Le champ "auteur" doit indiquer les options désactivées :
- "openai/gpt-4o" → tout activé
- "openai/gpt-4o [brut]" → tout désactivé
- "openai/gpt-4o [-tags,-mapping]" → options spécifiques

FORMAT JSON SORTIE : Strictement identique à detia.py sauf le champ auteur.
Ajouter un champ "options_desactivees": [] dans le JSON.

Mode batch : générer un suffixe de fichier selon les options (_out_brut, _out_tags_mapping, etc.)
```

---

## À faire (évolutions futures)

- [x] ~~Intégrer les options dans l'interface web `web12params.html`~~ ✓ Fait
- [ ] Permettre l'appel depuis `trouve.py` avec les options
- [ ] Ajouter des statistiques de comparaison entre modes

---

**Dernière mise à jour** : 02/01/2026 14:55
