# Prompt_tests_meme.md - Tests fonctionnalité "même que"

## Contexte du projet

**KITVIEW** est une application de recherche de patients orthodontiques avec une fonctionnalité "même que" permettant de trouver des patients similaires à un patient de référence.

### Architecture actuelle (après refactoring session 3)

```
C:/cx/ihm/
├── web25.html
├── web25.css
├── web25.cmd          ← Lance en nouvelle fenêtre Chrome
└── js/
    ├── utils.js       (61 lignes) - Utilitaires
    ├── voice.js       (539 lignes) - Reconnaissance vocale
    ├── illustrations.js (547 lignes) - Gestion images/filigrane
    ├── search.js      (809 lignes) - API et recherche
    ├── i18n.js        (707 lignes) - Internationalisation
    ├── meme.js        (370 lignes) - Logique "même que"
    └── main.js        (4442 lignes) - Code principal
```

### Fichiers de référence à joindre

Pour toute session de debug/test, joindre :
- `Prompt_contexte1301.md` (contexte projet)
- `meme.js` (logique "même que")
- `search.js` (API recherche)
- `main.js` (si modifications rendu)

---

## Plan de tests "même que"

### Phase 1 : Tests de détection de base

#### Test 1.1 : Recherche simple
```
Requête : "patients qui grincent des dents"
Attendu : Liste de patients avec bruxisme
Vérifier : 
- [ ] Résultats affichés
- [ ] Temps de réponse < 2s
- [ ] Pathologies cliquables
```

#### Test 1.2 : Recherche avec critères multiples
```
Requête : "patients avec béance et classe 2"
Attendu : Patients avec les deux pathologies
Vérifier :
- [ ] Intersection correcte des critères
- [ ] Tous les patients affichés ont les deux pathologies
```

#### Test 1.3 : Recherche avec âge
```
Requête : "patients de moins de 15 ans avec bruxisme"
Attendu : Patients < 15 ans avec bruxisme
Vérifier :
- [ ] Filtre d'âge appliqué
- [ ] Tous les patients ont l'âge correct
```

---

### Phase 2 : Tests "même que" - Critères simples

#### Test 2.1 : Même pathologie
```
1. Rechercher "bruxisme"
2. Cliquer sur un tag pathologie d'un patient (ex: "Béance" sur Guillaume)
Attendu : 
- Recherche "même béance que Guillaume Moulin"
- Liste de patients avec béance
Vérifier :
- [ ] Message "même X que Patient" affiché
- [ ] Critère actif visuellement (bordure rouge)
- [ ] Résultats filtrés correctement
```

#### Test 2.2 : Même âge
```
1. Rechercher "bruxisme"
2. Cliquer sur l'âge d'un patient (ex: "19 ans")
Attendu :
- Recherche patients du même âge
Vérifier :
- [ ] Filtre âge appliqué
- [ ] Tous les patients ont ~19 ans
```

#### Test 2.3 : Même sexe
```
1. Rechercher "bruxisme"
2. Cliquer sur l'icône sexe (♂/♀)
Attendu :
- Recherche patients du même sexe
Vérifier :
- [ ] Filtre sexe appliqué
```

---

### Phase 3 : Tests "même que" - Portrait (BUG CONNU)

#### Test 3.1 : Même portrait
```
1. Rechercher "bruxisme"
2. Cliquer sur le PORTRAIT (photo) d'un patient
Attendu :
- Recherche "même portrait que Patient"
- Patients avec portrait similaire
BUG CONNU : "même undefined" au lieu de "même portrait"
Vérifier :
- [ ] critereType = 'portrait' passé correctement
- [ ] Pas de "undefined" dans le message
```

#### Test 3.2 : Même nom
```
1. Rechercher "bruxisme"  
2. Cliquer sur le NOM d'un patient
Attendu :
- Recherche "même nom que Patient"
BUG CONNU : Possible confusion avec portrait
Vérifier :
- [ ] critereType = 'nom' passé correctement
```

---

### Phase 4 : Tests "même que" - Critères multiples

#### Test 4.1 : Combinaison pathologie + âge
```
1. Rechercher "bruxisme"
2. Cliquer sur "Béance" d'un patient → devient référence
3. Cliquer sur l'âge du MÊME patient
Attendu :
- "même béance et même âge que Patient"
Vérifier :
- [ ] Deux critères actifs
- [ ] Les deux bordures rouges visibles
- [ ] Résultats = intersection des deux critères
```

#### Test 4.2 : Changement de patient référence
```
1. Activer "même béance que Patient A"
2. Cliquer sur une pathologie de Patient B
Attendu :
- Patient B devient la nouvelle référence
- "même X que Patient B"
Vérifier :
- [ ] Référence change correctement
- [ ] Ancien patient n'a plus de bordure rouge
```

#### Test 4.3 : Désactivation d'un critère
```
1. Activer "même béance et même bruxisme que Patient"
2. Re-cliquer sur "béance" du patient référence
Attendu :
- Critère béance désactivé
- "même bruxisme que Patient"
Vérifier :
- [ ] Un seul critère reste
- [ ] Bordure rouge retirée du critère désactivé
```

---

### Phase 5 : Tests retour et reset

#### Test 5.1 : Nouvelle recherche
```
1. Activer "même X que Patient"
2. Cliquer "Nouvelle recherche"
Attendu :
- Reset complet de memeState
- Interface vierge
Vérifier :
- [ ] memeState.reset() appelé
- [ ] Plus de bordures rouges
- [ ] Champ de recherche vide
```

#### Test 5.2 : Retour à la recherche initiale
```
1. Rechercher "bruxisme" → 6407 résultats
2. Cliquer "même béance que Guillaume" → N résultats
3. Cliquer sur "bruxisme" dans historique (ou bouton retour)
Attendu :
- Retour aux 6407 résultats initiaux
BUG CONNU : Le retour ne fonctionne pas (patient 458)
Vérifier :
- [ ] lastSearchQuery sauvegardé
- [ ] Retour possible à la recherche d'origine
```

---

### Phase 6 : Tests visuels

#### Test 6.1 : Bordure rouge critère actif
```
Vérifier :
- [ ] Bordure rouge 2px visible sur critère actif
- [ ] Couleur : #dc3545 ou similar
- [ ] Pas de bordure sur critères inactifs
```

#### Test 6.2 : Curseur pointer
```
Vérifier :
- [ ] cursor: pointer sur éléments cliquables
- [ ] Tooltip au survol indiquant l'action
```

#### Test 6.3 : Message de recherche "même"
```
Vérifier :
- [ ] Format : "même X que Prénom Nom"
- [ ] Critères multiples : "même X et même Y que Prénom Nom"
- [ ] Pas de "undefined" dans le message
```

---

## Bugs connus à corriger

### Bug #1 : "même undefined"
- **Symptôme** : Message affiche "même undefined que Patient"
- **Cause probable** : `critereType` non passé lors du clic sur portrait
- **Fichier** : `meme.js` fonction `handleMemeClick()`
- **Fix** : Vérifier que `makePortraitMemeClickable()` passe `'portrait'` comme critereType

### Bug #2 : Bordure rouge manquante
- **Symptôme** : Pas de bordure rouge sur critère actif
- **Cause probable** : CSS non appliqué ou mauvais sélecteur
- **Fichier** : `web25.css` ou style inline dans `meme.js`
- **Fix** : Vérifier `.meme-active { border: 2px solid red; }`

### Bug #3 : Pas de retour au patient 458
- **Symptôme** : Impossible de revenir à la recherche initiale
- **Cause probable** : `lastSearchQuery` non sauvegardé ou `memeState` non reset
- **Fichier** : `meme.js` et `search.js`
- **Fix** : Sauvegarder la requête avant d'activer le mode "même"

---

## Commandes de debug console

```javascript
// Voir l'état actuel de memeState
console.log(memeState);

// Vérifier si un patient est référence
console.log(memeState.isReference(123));

// Voir les critères actifs
console.log(memeState.criteres);

// Reset manuel
memeState.reset();

// Vérifier lastSearchQuery
console.log(lastSearchQuery);
```

---

## Prompt de reprise

```
Nom de la conversation : tests_meme_session4

Contexte : Suite du refactoring web25 (session 3 terminée). L'interface fonctionne 
avec 6407 patients. On doit maintenant tester et corriger la fonctionnalité "même que".

Fichiers joints :
- Prompt_contexte1301.md
- Prompt_tests_meme.md (ce fichier)
- meme.js
- search.js
- main.js (si besoin)

Objectif session 4 :
1. Tester la fonctionnalité "même que" selon le plan de tests
2. Corriger le bug "même undefined" 
3. Corriger la bordure rouge manquante
4. Corriger le retour à la recherche initiale

Merci de commencer par lire Prompt_tests_meme.md puis d'exécuter les tests 
de la Phase 1 et 2 pour vérifier l'état actuel.
```

---

**FIN DU DOCUMENT** - Version 1.0.0 - 24/01/2026
