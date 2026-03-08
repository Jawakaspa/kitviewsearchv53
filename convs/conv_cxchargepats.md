# Prompt conv_cxchargepats V1.0.4 - 24/12/2025 17:39:09

# conv_cxchargepats.md

**Conversation** : cxchargepats  
**Date de début** : 24/12/2025  
**Dernière mise à jour** : 24/12/2025 15:52

---

## Résumé de la conversation

### Échange 1 - 24/12/2025 15:42

**Question** : Recréer `cxchargepats.py` avec correction du champ `idportrait` (au lieu de `portrait`).

**Réponse** : Programme créé et testé avec succès.

**Fichiers créés** :
- `cxchargepats.py` - Chargement patients CSV vers SQLite

**Points clés** :
- 9 colonnes en entrée CSV, 11 dans la table patients
- Génération automatique de `oripathologies` à partir de `canontags` + `canonadjs`
- Tri alphabétique des adjectifs multiples vérifié

---

### Échange 2 - 24/12/2025 15:52

**Question** : Modifier `generepats.py` pour ne générer que 9 colonnes (plus rien après `idportrait`). Créer les prompts de recréation pour les deux programmes.

**Réponse** : Programme modifié et prompts créés.

**Modifications apportées à generepats.py** :
- `OUTPUT_COLUMNS` réduit de 32 à 9 colonnes
- Suppression de la génération de `oripathologies` (sera fait par cxchargepats)
- Suppression de la colonne `portrait` (seul `idportrait` est conservé)
- Simplification de la fonction `generate()` dans `PatientGenerator`
- Simplification du chargement des portraits (ne garde que `idportrait`)

**Fichiers créés** :
- `generepats.py` - Version simplifiée (9 colonnes)
- `Prompt_generepats.md` - Prompt de recréation v2.0.0
- `Prompt_cxchargepats.md` - Prompt de recréation v3.1.0 (mis à jour)

---

## Fichiers générés

| Fichier | Description | Statut |
|---------|-------------|--------|
| `cxchargepats.py` | Chargement patients CSV → SQLite | ✅ Livré |
| `generepats.py` | Génération patients fictifs (9 colonnes) | ✅ Livré |
| `Prompt_cxchargepats.md` | Prompt de recréation v3.1.0 | ✅ Livré |
| `Prompt_generepats.md` | Prompt de recréation v2.0.0 | ✅ Livré |

---

## Prompts de recréation

### Pour recréer cxchargepats.py

**Fichiers à joindre** :
1. `Prompt_contexte2312.md` (ou version actuelle du contexte)
2. `Prompt_cxchargepats.md` (v3.1.0)
3. `standardise.py`

**Instruction** :
> Crée le programme cxchargepats.py selon les spécifications du prompt Prompt_cxchargepats.md.

---

### Pour recréer generepats.py

**Fichiers à joindre** :
1. `Prompt_contexte2312.md` (ou version actuelle du contexte)
2. `Prompt_generepats.md` (v2.0.0)
3. `refs/portraits.csv`
4. `refs/tagsadjs.csv`
5. `refs/sexeorigine.csv`
6. `refs/commun.csv`

**Instruction** :
> Crée le programme generepats.py selon les spécifications du prompt Prompt_generepats.md. Le CSV de sortie doit contenir uniquement 9 colonnes : id, canontags, canonadjs, sexe, age, datenaissance, prenom, nom, idportrait.

---

## Chaîne de traitement

```
generepats.py          cxchargepats.py
     │                       │
     ▼                       ▼
pats{N}.csv ──────────► base{N}.db
(9 colonnes)            (11 colonnes + tables pathologies)
```

**Colonnes CSV (generepats)** :
```
id;canontags;canonadjs;sexe;age;datenaissance;prenom;nom;idportrait
```

**Colonnes table patients (cxchargepats)** :
```
id, canontags, canonadjs, sexe, age, datenaissance, prenom, nom, idportrait, oripathologies, pathologies
```

Les colonnes `oripathologies` et `pathologies` sont générées automatiquement par `cxchargepats.py`.

---

## Historique des versions

| Date | Action |
|------|--------|
| 24/12/2025 15:43 | Création initiale de cxchargepats.py |
| 24/12/2025 15:52 | Modification generepats.py (9 colonnes), création des prompts |
