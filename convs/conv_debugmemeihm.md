# Prompt conv_debugmemeihm V1.0.0 - 25/01/2026 19:05:05

# Conversation : debugmemeihm

## Synthèse des échanges

---

### 25/01/2026 16:45 - Identification des bugs IHM "même que"

**Contexte** : Tests IHM de la fonctionnalité "même que" après amélioration de `detmeme.py`

**Problèmes signalés** :

1. **Bug de dérive des critères** :
   - Recherches successives avec critères croissants
   - Les critères ne se "déchargent" pas correctement au retour en arrière

2. **Bug de mise en évidence du patient de référence** :
   - Le patient de référence devrait avoir une bordure dorée/jaune
   - Pas de bordure visible sur Mohamed Touré

---

### 25/01/2026 17:08 - Analyse complète et bugs identifiés

**Fichiers analysés** :
- `web25.html` : CSS définit `.reference-patient` avec jaune stabilo
- `meme.js` : État `memeState` avec `referenceId`, `referenceName`, `criteres[]`
- `main.js` : Rendu des cartes patients ligne 2492-2650
- `search.js` : Appels API et traitement réponse

---

## 🐛 BUGS IDENTIFIÉS

### BUG 1 : Classe CSS incorrecte (mise en évidence)

| Fichier | Ligne | Problème |
|---------|-------|----------|
| `main.js` | 2507 | Utilise `meme-reference-card` |
| `web25.html` | 32-37 | CSS définit `.reference-patient` |

**Conséquence** : La bordure jaune ne s'applique JAMAIS car les classes ne correspondent pas.

**Correction** : Dans `main.js` ligne 2507, remplacer :
```javascript
// AVANT
card.classList.add('meme-reference-card');

// APRÈS
card.classList.add('reference-patient');
```

---

### BUG 2 : memeState jamais initialisé depuis la réponse backend

**Problème** : Quand l'utilisateur tape textuellement "même portrait que Mohamed Touré" :
1. Le backend détecte les critères et renvoie `reference_id` + `criteres_detectes`
2. Le frontend **n'utilise JAMAIS** ces données pour initialiser `memeState`
3. `memeState.referenceId` reste `null`
4. `memeState.isReference(patientId)` retourne toujours `false`

**Localisation** : `search.js` lignes 684-690 stocke `data.criteres` dans `lastSearchCriteria` mais **pas de code pour initialiser memeState**.

**Correction** : Ajouter dans `search.js` après ligne 690 :

```javascript
// Initialiser memeState depuis la réponse backend (recherche textuelle "même")
if (data.reference_id && typeof memeState !== 'undefined') {
    // Trouver le patient de référence dans les résultats
    const refPatient = data.patients?.find(p => p.id === data.reference_id);
    if (refPatient) {
        memeState.referenceId = data.reference_id;
        memeState.referenceName = `${refPatient.prenom || ''} ${refPatient.nom || ''}`.trim();
        
        // Initialiser les critères depuis criteres_detectes
        if (data.criteres_detectes && Array.isArray(data.criteres_detectes)) {
            memeState.criteres = [];
            for (const c of data.criteres_detectes) {
                if (c.type === 'meme') {
                    memeState.addCritere(c.cible, c.valeur || null);
                }
            }
        }
        
        if (window.DEBUG) {
            console.log('[MÊME] State initialisé depuis backend:', {
                referenceId: memeState.referenceId,
                referenceName: memeState.referenceName,
                criteres: memeState.criteres
            });
        }
    }
}
```

---

### BUG 3 (potentiel) : Dérive des critères

**Cause probable** : Le reset conditionnel (lignes 563-577 de `search.js`) ne fonctionne pas correctement :

```javascript
// Condition actuelle
if (!query.toLowerCase().includes('même ') && !query.toLowerCase().includes('meme ')) {
    // Reset...
}
```

**Problème** : Si la question contient "même" mais que c'est une NOUVELLE recherche "même" (pas un ajout de critère), l'état précédent persiste.

**Suggestion** : Ajouter une logique pour détecter le changement de patient de référence :
- Si `data.reference_id !== memeState.referenceId` → reset avant d'initialiser

---

## Structure de la réponse backend attendue

```json
{
  "nb_patients": 398,
  "patients": [...],
  "reference_id": 2015,           // ID du patient de référence
  "criteres_detectes": [          // Critères "même" détectés
    {
      "type": "meme",
      "cible": "portrait",
      "valeur": null
    }
  ],
  "criteres": [...],              // Tous les critères SQL
  "temps_ms": 1547
}
```

**Question** : Le backend renvoie-t-il bien `reference_id` et `criteres_detectes` ? À vérifier avec un test CLI.

---

## Fichiers fournis

| Fichier | Description |
|---------|-------------|
| `web25.html` | Interface principale |
| `meme.js` | Module gestion "même que" |
| `main.js` | Code principal (4443 lignes) |
| `search.js` | Module recherche frontend |
| `utils.js` | Utilitaires |
| `i18n.js` | Internationalisation |
| `search.py` | Backend recherche |
| `trouveid.py` | Enrichissement référence patient |

---

## Actions proposées

1. ~~**Immédiat** : Corriger la classe CSS (`meme-reference-card` → `reference-patient`)~~ ✅ FAIT
2. ~~**Priorité haute** : Ajouter l'initialisation de `memeState` depuis la réponse backend~~ ✅ FAIT
3. **À valider** : Tester avec l'IHM les fichiers corrigés
4. **À tester** : La séquence complète de recherches "même" (ajout/retrait critères)

---

## Corrections effectuées (25/01/2026 17:32)

### Fichier `main.js` - Ligne 2507
```javascript
// AVANT
card.classList.add('meme-reference-card');

// APRÈS
card.classList.add('reference-patient');
```

### Fichier `search.js` - Après ligne 690
Ajout d'un bloc complet pour initialiser `memeState` depuis `data.criteres_detectes` :
- Extraction de `reference_id` depuis le premier critère "meme"
- Construction du nom depuis `reference_patient` ou recherche dans les résultats
- Initialisation de tous les critères "meme" détectés
- Log DEBUG pour validation

---

## Corrections effectuées (25/01/2026 18:05)

### Fichier `meme.js` - Fonction `isReference()` (ligne ~115)

**Problème** : Comparaison stricte `===` échouait car `referenceId` (number du clic) ≠ `patientId` (string du JSON)

```javascript
// AVANT
isReference(patientId) {
    return this.referenceId === patientId;
}

// APRÈS  
isReference(patientId) {
    return Number(this.referenceId) === Number(patientId);
}
```

### Fichier `meme.js` - Fonction `handleMemeClick()` (ligne ~206)

**Problème** : Le tag était automatiquement désélectionné quand on cliquait sur une pathologie avec adjectifs, empêchant de retirer les critères un par un.

```javascript
// SUPPRIMÉ :
if (critereType === 'pathologie' && critereValue) {
    const tag = critereValue.split(/\s+/)[0];
    if (memeState.hasCritere('tag', tag)) {
        memeState.removeCritere('tag', tag);
    }
}
```

**Comportement attendu maintenant** :
- Clic sur "Béance" → critère tag "béance" ajouté
- Clic sur "Béance Antérieure Gauche Modérée" → critère pathologie ajouté (tag reste)
- Question affichée : "même portrait et même béance et même béance antérieure gauche modérée que X"
- Re-clic sur pathologie → retrait pathologie seule (tag reste)
- Re-clic sur tag → retrait tag

---

## Corrections effectuées (25/01/2026 18:20) - FOND JAUNE

### Fichier `web25.html` - CSS inline (ligne ~32)

**Problème** : Le sélecteur CSS `.patient-card.reference-patient` ne matchait pas les cartes qui ont la classe `patient-card-chat` (mode Chat).

```css
/* AVANT - ne matchait pas patient-card-chat */
.patient-card.reference-patient,
.patient-item.reference-patient { ... }

/* APRÈS - ajout de .patient-card-chat */
.patient-card.reference-patient,
.patient-card-chat.reference-patient,
.patient-item.reference-patient { ... }
```

Même correction pour le mode sombre `[data-theme="dark"]`.

---

## Fichiers livrés

| Fichier | Emplacement | Description |
|---------|-------------|-------------|
| `web25.html` | `C:\cx\ihm\` | Corrigé - CSS sélecteur .patient-card-chat |
| `main.js` | `C:\cx\ihm\js\` | Corrigé - classe CSS reference-patient |
| `search.js` | `C:\cx\ihm\js\` | Corrigé - initialisation memeState depuis backend |
| `meme.js` | `C:\cx\ihm\js\` | Corrigé - comparaison types + critères séparés |
| `jsonsql.py` | `C:\cx\` | **NOUVEAU** - Corrigé - utilise valeur spécifique du critère |
| `conv_debugmemeihm.md` | | Cette synthèse |

---

## Prochaines étapes

- [x] ~~Copier `web25.html` vers `c:/cx/ihm/web25.html`~~ ✅
- [x] ~~Copier `main.js`, `search.js` et `meme.js` vers `c:/cx/ihm/js/`~~ ✅
- [x] ~~Tester "même portrait que Guillaume Moulin" → bordure jaune visible~~ ✅ **FONCTIONNE !**
- [x] ~~Tester séquence ajout critères~~ ✅ Fonctionne !
- [x] ~~Tester retrait critères un par un~~ ✅ Fonctionne !

---

## 🐛 NOUVEAU BUG IDENTIFIÉ (25/01/2026 18:45)

### Bug "même X" quand la référence n'a pas X

**Scénario** :
1. Guillaume Moulin a : béance antérieure gauche modérée, diabète, bruxisme
2. Ahmed Keita (ID 7163, 7 ans) a : béance antérieure gauche modérée, diastemata centraux (PAS de bruxisme, PAS de diabète)
3. Recherche : "même portrait et même béance et même béance antérieure gauche modérée et même bruxisme et même diabète que Guillaume Moulin"
4. Résultat : 2 patients (Guillaume Moulin ET Ahmed Keita)

**Problème** : Ahmed Keita ne devrait PAS être dans les résultats car il n'a ni bruxisme ni diabète !

**Cause identifiée** (18:52) : Dans `jsonsql.py`, le critère "même bruxisme" utilisait le **PREMIER TAG** du patient référence (béance) au lieu du tag **DEMANDÉ** (bruxisme).

---

## Corrections effectuées (25/01/2026 18:55) - BACKEND

### Fichier `jsonsql.py` - Fonction `_generer_clause_meme()` - cible "tag" (ligne ~255)

**Problème** : Le code ignorait la `valeur` spécifique du critère et prenait le premier tag du patient.

```python
# AVANT (bug)
canontags_ref = ref_patient.get('canontags', '')  # "béance,diabète,bruxisme"
tags = [t.strip() for t in canontags_ref.split(',')]
tag = tags[0]  # ← "béance" au lieu de "bruxisme" !

# APRÈS (fix)
valeur_specifique = critere.get('valeur', '')  # "bruxisme"
if valeur_specifique:
    # Utiliser le tag demandé, vérifier que le patient ref l'a
    patient_a_ce_tag = any(tag_std in t for t in tags_ref)
    if patient_a_ce_tag:
        where_clause = f"pathologie LIKE '{tag_std}%'"
    else:
        where_clause = "1 = 0"  # Patient ref n'a pas ce tag → 0 résultats
```

### Même correction pour cible "pathologie" (ligne ~314)

**Comportement attendu maintenant** :
- "même bruxisme que Guillaume Moulin" → patients avec bruxisme (Guillaume l'a)
- "même bruxisme que Ahmed Keita (7 ans)" → **0 résultats** (Ahmed n'a pas bruxisme)
- "même diabète que Ahmed Keita (7 ans)" → **0 résultats** (Ahmed n'a pas diabète)
