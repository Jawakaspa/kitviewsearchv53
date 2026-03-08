# conv_maj.md — Synthèse de conversation

## 19/02/2026 ~15h00 — Création page majpats.html + endpoints + lien depuis simple30

### Question
Créer une page `majpats.html` permettant de modifier un patient dans une base SQLite, avec :
- Paramètres URL : `?base=base10.db&id=10002`
- Affichage de toutes les colonnes de `patients`
- Fusion canontags+canonadjs en lignes éditables triées alphabétiquement
- Résolution via dettags (backend) avec affichage des formes canoniques
- Confirmation avant mise à jour (diff avant/après)
- Recalcul complet des index (patients_pathologies)
- Modifier simple30 pour rendre l'ID cliquable si la base contient "007"

### Réponse — 3 livrables

**1. majpats.html** (nouveau)
- Page autonome avec thème clair/sombre (cohérent simple30)
- Formulaire : prénom, nom, sexe, âge (readonly), date naissance, id portrait
- Éditeur de lignes tags+adjs : ajout/suppression dynamique, min 1 ligne
- Bouton "Résoudre" → appel `POST /patient/resolve-tags` → affichage canoniques en vert
- Bouton "Valider" → modale confirmation avec diff complet → `PUT /patient/update`
- Responsive PC/mobile

**2. server.py v1.2.1** (modifié)
- `GET /patient?base=...&id=...` — lecture individuelle patient
- `POST /patient/resolve-tags` — résolution via `dettags.charger_tags`/`detecter_tags`
- `PUT /patient/update` — mise à jour patient + recalcul pathologies combinatoires + index patients_pathologies
- Fonction `_generate_pathologies_combinations()` — produit les combinaisons progressives (vérifié : correspond exactement au format en base)
- Models Pydantic : `ResolveTagsRequest`, `PatientUpdateRequest`

**3. simple30_main.js** (modifié)
- `createPatientCardChat()` : ID badge cliquable → `majpats.html` si `currentBase.includes('007')`
- `createPatientItemClassique()` : idem
- Style : cursor pointer + underline + title

### Fichiers fournis
| Fichier | Type | Description |
|---------|------|-------------|
| majpats.html | Nouveau | Page modification patient |
| server.py | Modifié v1.2.1 | +3 endpoints patient CRUD |
| simple30_main.js | Modifié | ID cliquable si base contient 007 |
