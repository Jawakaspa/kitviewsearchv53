# conv_demo30 — Synthèse de conversation

## Projet : demo30 — Interface démo simplifiée Kitview Search

---

### 11/02/2026 ~13h30 — Cadrage initial

**Question** : Créer demo30.html basé sur chat30.html avec simplification radicale — supprimer settings complexes, remplacer l'input de recherche par une zone textarea de config démo, CSS/JS 100% indépendants de chat30.

**Réponse** :
- Architecture définie : demo30.html (CSS embarqué) + 7 modules JS indépendants
- Fichiers demandés et reçus : chat30.html, 7 JS modules (*30.js), communb.csv, webparams.html, modedemploi30.html
- Clarifications obtenues : mécaniques démo (envoi séquentiel d'exemples), paramètres dans webparams, score de similarité inline

**Fichiers créés** :
| Fichier | Taille | Description |
|---|---|---|
| `demo30.html` | 36 Ko | Page HTML avec CSS embarqué, structure simplifiée |
| `js/demo30_utils.js` | 1.9 Ko | Copie indépendante de utils30.js |
| `js/demo30_search.js` | 35.7 Ko | Copie indépendante de search30.js |
| `js/demo30_i18n.js` | 33.1 Ko | Copie indépendante de i18n30.js |
| `js/demo30_illustrations.js` | 23.4 Ko | Copie indépendante de illustrations30.js |
| `js/demo30_meme.js` | 15.4 Ko | Copie indépendante de meme30.js |
| `js/demo30_voice.js` | 20 Ko | Copie indépendante de voice30.js |

---

### 11/02/2026 ~14h25 — Complétion des fichiers

**Question** : nc=demo30 (reprise après compaction)

**Réponse** : Création des 2 fichiers manquants :

| Fichier | Taille | Description |
|---|---|---|
| `js/demo30_main.js` | 49.7 Ko | Logique principale adaptée — supprime sidebar, settings, mode classique. Ajoute gestion textarea config démo, launch/stop, cycles automatiques |
| `modedemo30.html` | ~17 Ko | Mode d'emploi simplifié — 7 sections : présentation, interface, mode démo, recherche manuelle, résultats (fiches patient, même que, photofit), langue, exemples |

**Différences clés demo30_main.js vs main_chat30.js** :
- ❌ Supprimé : sidebar (renderRecentConversations, renderExamples), settings modal, toolbar toggle, mode classique compact, mode switching
- ❌ Supprimé : bouton gear/paramètres
- ✅ Conservé : filigrane, loading banner, démo cycles, search/pagination, patient cards chat, pathologies groupées, score similarité inline, rating, copie, thème
- ✅ Ajouté : `launchDemo()` / `stopDemo()` avec gestion textarea, `demoConfigContainer` show/hide, lecture exemples depuis textarea

---

## Inventaire complet des livrables

```
demo30/
├── demo30.html              (36 Ko)  Page principale avec CSS embarqué
├── modedemo30.html           (17 Ko)  Mode d'emploi simplifié
└── js/
    ├── demo30_main.js        (50 Ko)  Logique principale
    ├── demo30_search.js      (36 Ko)  API recherche
    ├── demo30_i18n.js        (33 Ko)  Internationalisation
    ├── demo30_illustrations.js (23 Ko) Gestion illustrations
    ├── demo30_voice.js       (20 Ko)  Recherche vocale
    ├── demo30_meme.js        (15 Ko)  Même X que...
    └── demo30_utils.js       (2 Ko)   Utilitaires
```

**Total : 9 fichiers, ~232 Ko — 100% indépendants de chat30**

---

### 11/02/2026 ~15h10 — Bugfix : doublons JS + améliorations modedemo30

**Question** : Les bases et modes de détection ne se chargent pas ("Chargement..."). Le bouton ? Aide ne fonctionne pas. modedemo30.html manque d'explications sur la création de fichiers de démo + exemple téléchargeable. Ajouter une zone de recherche dans le bandeau du mode d'emploi.

**Diagnostic** :
- **Bug critique** : Les variables `_filigraneFirstLoad` et `_forceRandomImage` étaient déclarées avec `let` dans **deux fichiers** (`demo30_illustrations.js` ET `demo30_main.js`). En JavaScript, deux `let` globaux identiques provoquent un `SyntaxError` qui **crashe tout le JS** → rien ne se charge.
- 6 fonctions filigrane dupliquées (setFiligraneImage, updateFiligraneGhost, applyFiligraneIntensity, hideFiligraneForResults, restoreFiligraneIntensity, animateFiligraneFromMax)
- 3 fonctions loading/lang dupliquées (updateLoadingBanner, detectLanguageFromText, getSearchingText)
- 3 fonctions utilitaires dupliquées (formatPaginationMessage, getNextPageText, updateBaseSubtitle)

**Corrections demo30_main.js** :
- Supprimé 2 variables dupliquées + 12 fonctions dupliquées
- Remplacé par commentaires pointant vers le module source
- Taille réduite de 1089 → 956 lignes

**Améliorations modedemo30.html** :
- ✅ **Barre de recherche dans le header** : champ avec highlighting, navigation ▲/▼, compteur, Ctrl+F intercepté
- ✅ **Section 3bis « Créer vos démos »** : format de fichier, règles de syntaxe, exemple complet commenté, bouton téléchargement
- ✅ **Bouton ⬇️ Télécharger** : génère `demo_exemple_salon.txt` (UTF-8 BOM) avec exemples multilingues
- ✅ **Bonnes pratiques** : conseils pour préparer des démos efficaces
- Taille augmentée de 665 → 1004 lignes
