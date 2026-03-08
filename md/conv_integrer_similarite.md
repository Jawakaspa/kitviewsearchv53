# conv_integrer_similarite.md

## Synthèse de la conversation : Intégrer la similarité Photofit

---

### Échange 1 — 11/02/2026 ~11h00
**Q :** Intégrer la recherche par similarité faciale (photofit.db) dans le pipeline jsonsql.py  
**R :** Implémentation V1.2.0 de jsonsql.py avec :
- Seuil idportrait >= 1000 → similarité cosinus, < 1000 → match exact
- Poids : WEIGHT_HAIR=0.3, WEIGHT_FACE=0.7
- Fonctions : `_lire_config_photofit`, `_deserialize_float_vector`, `_cosine_distance`, `_rechercher_portraits_similaires_ids`
- Résultat : 20 patients trouvés, 1865ms

### Échange 2 — 11/02/2026 ~12h00  
**Q :** Ajouter scoring normalisé 0-100, tri par score, badges couleur  
**R :** Implémentation V1.3.0 de jsonsql.py avec :
- `_distance_to_score()` : conversion distance → score 0-100
- `_rechercher_portraits_similaires()` retourne `List[Tuple[str, int]]` (id, score)
- `generer_sql()` génère `ORDER BY CASE` et ajoute `portrait_scores` au dict résultat
- Seuils : 100=jaune référence, >=80=vert excellent, >=60=bleu bon, >=40=orange moyen, <30=exclu
- Tri et filtrage corrects, mais badges non visibles sur le frontend

### Échange 3 — 11/02/2026 ~13h00
**Q :** Les badges ne s'affichent pas sur les cartes patients, pourquoi ?  
**R :** Demande des fichiers lancesql.py, chat29.html, search.js, main_chat.js, trouve.py

### Échange 4 — 11/02/2026 ~14h30
**Q :** Fourniture de tous les fichiers JS + trouve.py  
**R :** Diagnostic complet de la chaîne de données portrait_scores :

**Pipeline cassé à 3 niveaux (pas 2 !) :**
```
jsonsql.generer_sql() → sql_dict['portrait_scores']     OK
trouve.py : portrait_scores NON propagé vers resultat    CASSÉ (corrigé)
search.py : portrait_scores NON propagé vers resultat_final  CASSÉ (corrigé)
main_chat.js : pas de badge de score sur les cartes      CASSÉ (corrigé)
```

**4 corrections livrées :**

| Fichier | Modification |
|---------|-------------|
| **trouve.py** | Ajout propagation `portrait_scores` de `sql_dict` vers `resultat` |
| **search.py** | Ajout `'portrait_scores': resultats.get('portrait_scores', None)` dans `resultat_final` (ligne 1758) |
| **main_chat.js** | Enrichissement patients avec `similarity_score` dans 3 boucles forEach |
| **main_chat.js** | Badge visuel dans `createPatientCardChat()` et `createPatientItemClassique()` |

**Détail des badges :**
- Score 100 → cible fond #ffc107 (jaune/gold) — Portrait de référence
- Score >= 80 → vert fond #28a745 — Excellent
- Score >= 60 → bleu fond #17a2b8 — Bon
- Score >= 40 → orange fond #fd7e14 — Moyen

**lancesql.py** : Aucune modification nécessaire.

---

### Fichiers livrés
- `trouve.py` (modifié — propagation portrait_scores vers resultat)
- `search.py` (modifié — propagation portrait_scores vers resultat_final API)
- `main_chat.js` (modifié — badges de similarité)
- `conv_integrer_similarite.md` (cette synthèse)

### Fichiers NON modifiés
- jsonsql.py (V1.3.0 — déjà correct)
- lancesql.py (V1.0.4 — pas concerné)
- search.js (frontend), chat29.html, i18n.js, meme.js, utils.js
- communb.csv, portraits.csv

### Prochaines étapes
1. ~~Tester le pipeline complet~~ ✅ FAIT — badges visibles et correctement colorés
2. **Ajuster la position des badges** quand la carte est étroite (le % masque partiellement le nom) → à intégrer dans simple30.html (nouvelle conversation)
3. Vérifier le comportement en mode sombre
4. Ajuster `distance_max` et `score_min` dans communb.csv selon la distribution réelle des scores
