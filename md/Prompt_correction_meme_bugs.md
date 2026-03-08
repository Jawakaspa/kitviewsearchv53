# Prompt : Correction des bugs IHM "même que"

## Contexte

L'application KITVIEW permet de rechercher des patients similaires avec la syntaxe "même X que Patient".
Deux bugs ont été identifiés dans l'interface web :

1. **Bug mise en évidence** : Le patient de référence n'a pas de bordure jaune
2. **Bug initialisation** : `memeState` n'est pas initialisé depuis la réponse backend

## Fichiers à joindre en PJ

- `main.js` (version actuelle)
- `search.js` (version actuelle)
- `web25.html` (pour référence CSS)
- `meme.js` (pour référence structure memeState)

## Instructions

### Correction 1 : Classe CSS dans main.js

Dans la fonction `createPatientCardChat()` (vers ligne 2507), la classe CSS utilisée pour le patient de référence est incorrecte.

**Rechercher** :
```javascript
card.classList.add('meme-reference-card');
```

**Remplacer par** :
```javascript
card.classList.add('reference-patient');
```

Le CSS dans `web25.html` définit `.reference-patient` avec le style jaune stabilo :
```css
.patient-card.reference-patient,
.patient-item.reference-patient {
    background: linear-gradient(135deg, #ffff00 0%, #ffeb3b 100%) !important;
    border: 3px solid #ffc107 !important;
    box-shadow: 0 4px 15px rgba(255, 235, 59, 0.5) !important;
}
```

### Correction 2 : Initialisation memeState dans search.js

Après le bloc qui stocke `lastSearchCriteria` (vers ligne 690), ajouter le code suivant pour initialiser `memeState` depuis la réponse backend :

```javascript
// ╔═══════════════════════════════════════════════════════════════
// ║ FIX 25/01/2026 : Initialiser memeState depuis la réponse backend
// ║ Permet la mise en évidence du patient de référence pour les
// ║ recherches textuelles "même X que Patient"
// ╚═══════════════════════════════════════════════════════════════
if (typeof memeState !== 'undefined' && data.criteres_detectes && Array.isArray(data.criteres_detectes)) {
    // Chercher un critère 'meme' avec reference_id
    const memeCritere = data.criteres_detectes.find(c => c.type === 'meme' && c.reference_id);
    
    if (memeCritere) {
        const refId = memeCritere.reference_id;
        const refPatient = memeCritere.reference_patient;
        
        // Vérifier si c'est une nouvelle référence (changement de patient)
        if (memeState.referenceId !== refId) {
            // Reset et initialiser avec la nouvelle référence
            memeState.reset();
            memeState.referenceId = refId;
            
            // Construire le nom depuis reference_patient ou chercher dans les résultats
            if (refPatient) {
                memeState.referenceName = `${refPatient.prenom || ''} ${refPatient.nom || ''}`.trim();
            } else {
                // Fallback : chercher dans les patients retournés
                const patientInResults = data.patients?.find(p => p.id === refId);
                if (patientInResults) {
                    memeState.referenceName = `${patientInResults.prenom || ''} ${patientInResults.nom || ''}`.trim();
                }
            }
            
            // Initialiser les critères depuis criteres_detectes
            for (const c of data.criteres_detectes) {
                if (c.type === 'meme') {
                    memeState.addCritere(c.cible, c.valeur || null);
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
}
```

## Structure de données attendue

Le backend (`search.py` via `trouveid.py`) renvoie `criteres_detectes` avec cette structure :

```json
{
  "criteres_detectes": [
    {
      "type": "meme",
      "cible": "portrait",
      "valeur": null,
      "reference_id": 394,
      "reference_patient": {
        "id": 394,
        "prenom": "Mohamed",
        "nom": "Touré",
        "sexe": "M",
        "age": 12,
        ...
      }
    },
    {
      "type": "meme",
      "cible": "tag",
      "valeur": "beance",
      "reference_id": 394,
      "reference_patient": {...}
    }
  ]
}
```

## Tests de validation

1. **Test mise en évidence** :
   - Taper "même portrait que Mohamed Touré"
   - Vérifier que Mohamed Touré a une bordure jaune dans les résultats

2. **Test ajout critères** :
   - Cliquer sur un tag (ex: béance) du patient de référence
   - Vérifier que la recherche se met à jour
   - Vérifier que la bordure jaune persiste

3. **Test retrait critères** :
   - Cliquer sur un critère actif pour le retirer
   - Vérifier que la recherche se met à jour
   - Si plus de critères, vérifier le retour à la recherche initiale

4. **Test changement référence** :
   - Cliquer sur le portrait d'un autre patient
   - Vérifier que la référence change (nouveau patient en jaune)

## Fichiers produits

- `main.js` corrigé
- `search.js` corrigé
