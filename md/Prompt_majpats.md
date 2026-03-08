# Prompt_majpats.md — Prompt de recréation

## Objectif
Créer/recréer la page `majpats.html` et les modifications associées pour permettre l'édition d'un patient depuis l'interface Kitview Search.

## Fichiers à joindre en PJ
1. `Prompt_contexte0502.md` — contexte projet
2. `base10.db` — base de données exemple (structure de référence)
3. `dettags.py` — module de détection des tags (pour comprendre l'API resolve)
4. `detadjs.py` — module de détection des adjectifs
5. `server.py` — serveur API à modifier
6. `simple30_main.js` — JS principal à modifier
7. `simple30.html` — pour référence structure

## Spécifications

### majpats.html
Page HTML autonome responsive (PC/mobile) avec thème clair/sombre.

**Paramètres URL** : `?base=base10.db&id=10002`

**Affichage** :
- Tous les champs de la table `patients` : id, prénom, nom, sexe, âge (readonly), date naissance, id portrait
- Éditeur canontags+canonadjs fusionnés en lignes :
  - canontags="béance,macrodontie" + canonadjs="droite|sévère,maxillaire|mandibulaire"
  - Affiche 2 lignes : "béance droite sévère" et "macrodontie mandibulaire maxillaire" (adjs triés alpha)
  - Lignes dynamiques (ajout/suppression, minimum 1)
  - À droite de chaque ligne : affichage de la résolution canonique (canontag → canonadjs)

**Workflow** :
1. Chargement patient via `GET /patient?base=...&id=...`
2. Saisie/modification des lignes tags+adjectifs (synonymes acceptés)
3. Bouton "Résoudre" → `POST /patient/resolve-tags` → affiche les canoniques en vert
4. Bouton "Valider" → modale de confirmation avec diff avant/après
5. Confirmation → `PUT /patient/update` → mise à jour patient + recalcul pathologies combinatoires + index

### server.py — 3 endpoints à ajouter

```
GET  /patient?base=...&id=...         → lecture patient (toutes colonnes)
POST /patient/resolve-tags             → { lines: [...] } → résolution dettags
PUT  /patient/update                   → mise à jour + recalcul index
```

Le `PUT /patient/update` doit :
- Mettre à jour les colonnes patients
- Recalculer le champ `pathologies` (combinaisons progressives : tag, tag adj1, tag adj1 adj2...)
- Supprimer les anciennes entrées `patients_pathologies`
- Créer les nouvelles pathologies si nécessaire (`INSERT OR IGNORE`)
- Recréer les entrées `patients_pathologies`

### simple30_main.js — ID cliquable

Dans les fonctions `createPatientCardChat()` et `createPatientItemClassique()` :
- Si `currentBase.includes('007')` → l'ID badge devient cliquable
- Clic → `window.open('majpats.html?base=...&id=...', '_blank')`
- Style : cursor pointer, underline, title
