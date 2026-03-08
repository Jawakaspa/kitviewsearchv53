# Prompt AUDIT_PAGINATION V1.0.0 - 28/01/2026 16:39:30

# AUDIT PAGINATION KITVIEW SEARCH
## Date : 28/01/2026 17:25

---

## 1. PROBLÈMES CONSTATÉS (Screenshots)

### Image 1 - Mode Chat après "Page suivante"
- **Symptôme** : Affiche TOUS les patients d'un coup (6407 patients chargés immédiatement)
- **Preuve** : Taille de l'ascenseur montre une page très longue
- **Debug console** : "Chargement de 100 patients supplémentaires" puis "6407 patients supplémentaires chargés"

### Image 2 - Mode Classique après "Page suivante"  
- **Symptôme** : Affiche "60 / 6407 patients" = accumulation au lieu de remplacement
- **Attendu** : Devrait afficher "21-40 / 6407" et REMPLACER les patients précédents

---

## 2. ANALYSE DU CODE ORIGINAL (main.js V2.1.0)

### Variables clés (lignes 751-753)
```javascript
let pageSize = 20;      // Patients affichés par page
let resultsLimit = 100; // Patients chargés par requête API
```

### Flux de la pagination (lignes 1536-1680)

```
1. Clic sur "Page suivante"
2. offset = parseInt(this.dataset.currentOffset)  // = 20 au premier clic
3. conversationItem = conversationHistory.find(...)
4. SI offset < conversationItem.response.patients.length ALORS
     → Afficher nextBatch (patients[offset:offset+pageSize])
     → SI mode classique: patientsContainer.innerHTML = '' (VIDER)
     → Ajouter les patients
     → newOffset = offset + nextBatch.length
     → SI newOffset >= patients.length ET newOffset < nb_patients
         → Charger plus depuis serveur (/trouve)
         → newPatients.forEach → patientsContainer.appendChild (AJOUTER!)
   SINON
     → RIEN (pas de else!)
```

### BUG #1 : Mode Chat affiche tout d'un coup

**Cause** : Ligne 1628 - Après chargement serveur, on fait `newPatients.forEach(appendChild)`
- `resultsLimit = 100` mais le serveur retourne TOUS les patients restants (6407-20=6387)
- On les affiche TOUS d'un coup au lieu de pageSize (20)

**Code problématique** :
```javascript
// Ligne 1614-1631
const newPatients = data.patients || [];  // = 6387 patients!
conversationItem.response.patients = conversationItem.response.patients.concat(newPatients);
newPatients.forEach(patient => {  // BOUCLE SUR 6387 PATIENTS!
    patientsContainer.appendChild(element);
});
```

**Solution** : Après chargement serveur, ne montrer que `pageSize` patients, pas tous.

### BUG #2 : Mode Classique accumule au lieu de remplacer

**Cause** : Ligne 1622-1624 - Le `innerHTML = ''` est dans le bloc de chargement serveur
- Au premier clic (offset=20, patients en mémoire), on VIDE puis AJOUTE (OK)
- Au deuxième clic, on charge depuis serveur, on VIDE, mais ensuite on AJOUTE TOUS les newPatients

**Code problématique** :
```javascript
// Ligne 1622-1631 (dans le bloc chargement serveur)
if (currentMode === 'classique') {
    patientsContainer.innerHTML = '';  // OK, on vide
}
newPatients.forEach(patient => {  // MAIS on ajoute TOUS les nouveaux (6387!)
    patientsContainer.appendChild(element);
});
```

**Solution** : En mode Classique, après vidage, n'afficher que `pageSize` patients.

### BUG #3 : Endpoint API incorrect

**Cause** : Ligne 1591 utilise `/trouve` mais l'API est `/search`
```javascript
const response = await fetch(`${API_BASE_URL}/trouve`, {  // 404!
```

**Mais** : Les screenshots montrent que ça fonctionne... donc soit :
- L'API `/trouve` existe sur ce serveur
- Soit les patients sont déjà tous en mémoire (pas de requête serveur)

---

## 3. FLUX ATTENDU vs FLUX ACTUEL

### Mode Chat - Attendu
```
Initial: Afficher patients[0:20]
Clic 1:  AJOUTER patients[20:40] → Total visible: 40
Clic 2:  AJOUTER patients[40:60] → Total visible: 60
...
Si besoin: Charger 100 de plus depuis serveur, continuer par 20
```

### Mode Chat - Actuel (BUGUÉ)
```
Initial: Afficher patients[0:20]
Clic 1:  AJOUTER patients[20:40] → Total visible: 40
Clic 2:  AJOUTER patients[40:60] → Total visible: 60
...
Clic N:  Charger TOUS les restants → Afficher 6387 d'un coup!
```

### Mode Classique - Attendu
```
Initial: Afficher patients[0:20]
Clic 1:  REMPLACER par patients[20:40] → Total visible: 20
Clic 2:  REMPLACER par patients[40:60] → Total visible: 20
...
```

### Mode Classique - Actuel (BUGUÉ)
```
Initial: Afficher patients[0:20]
Clic 1:  VIDER + AJOUTER patients[20:40] → Total visible: 20 (OK)
...
Clic N:  VIDER + AJOUTER TOUS les nouveaux → Total visible: 6387!
```

---

## 4. CORRECTIONS NÉCESSAIRES

### Correction #1 : Limiter l'affichage après chargement serveur

```javascript
// APRÈS: const newPatients = data.patients || [];
// AJOUTER:
const patientsToDisplay = currentMode === 'classique' 
    ? newPatients.slice(0, pageSize)  // Classique: une page
    : newPatients.slice(0, pageSize); // Chat: une page aussi!

// REMPLACER forEach sur newPatients par:
patientsToDisplay.forEach(patient => {
    const element = createPatientElement(patient);
    patientsContainer.appendChild(element);
});

// METTRE À JOUR l'offset correctement:
const finalOffset = newOffset + patientsToDisplay.length;
```

### Correction #2 : Même logique pour les patients en mémoire

Le bug existe aussi dans le bloc "patients en mémoire" (ligne 1545-1559).
Quand on charge depuis le serveur, on ajoute au tableau `patients`, puis au prochain clic on prend `slice(offset, offset+pageSize)` ce qui est correct.

MAIS le problème est que `newPatients.forEach` affiche TOUS les nouveaux patients, pas juste `pageSize`.

### Correction #3 : Endpoint API

Remplacer `/trouve` par `/search` ou vérifier quel endpoint existe.

---

## 5. CODE CORRIGÉ PROPOSÉ

### Principe de la correction :

1. **Après chargement serveur** : Ne jamais afficher plus de `pageSize` patients
2. **Mode Chat** : Ajouter `pageSize` patients à chaque clic
3. **Mode Classique** : Remplacer par `pageSize` patients à chaque clic
4. **Stockage mémoire** : Garder tous les patients chargés pour navigation rapide

### Section à remplacer (lignes 1614-1658)

```javascript
const newPatients = data.patients || [];

// Fusionner les nouveaux patients avec ceux déjà en mémoire
conversationItem.response.patients = conversationItem.response.patients.concat(newPatients);

// ╔═══════════════════════════════════════════════════════════════
// ║ FIX V2.2.0 : Afficher seulement pageSize patients, pas tous
// ╚═══════════════════════════════════════════════════════════════
const patientsToDisplay = newPatients.slice(0, pageSize);

if (currentMode === 'classique') {
    patientsContainer.innerHTML = '';
}

patientsToDisplay.forEach(patient => {
    const element = createPatientElement(patient);
    patientsContainer.appendChild(element);
});

if (currentMode === 'classique') {
    patientsContainer.scrollIntoView({ behavior: 'smooth', block: 'start' });
}

const finalOffset = newOffset + patientsToDisplay.length;
this.dataset.currentOffset = finalOffset.toString();
this.disabled = false;
this.textContent = getNextPageText(effLang);

countDiv.textContent = formatPaginationMessage(finalOffset, conversationItem.response.nb_patients, descFiltres, effLang);

addDebugLog(`${patientsToDisplay.length} patients affichés (${newPatients.length} chargés en mémoire)`, 'success');

if (finalOffset >= conversationItem.response.nb_patients) {
    this.style.display = 'none';
    countDiv.textContent = formatPaginationMessage(finalOffset, finalOffset, descFiltres, effLang, true);
}
```

---

## 6. VÉRIFICATIONS À FAIRE

### Question pour Thierry :

1. **Quel endpoint API existe ?** 
   - `/search` ou `/trouve` ?
   - Le serveur retourne-t-il `limit` patients ou tous ?

2. **Comportement initial attendu**
   - La recherche initiale charge combien de patients ? 20, 100, ou tous ?

3. **Mode Classique - Navigation**
   - Bouton "Page précédente" est-il prévu ?
   - Si oui, faut-il garder les patients en mémoire pour naviguer sans re-requêter ?

---

## 7. RÉSUMÉ EXÉCUTIF

| Bug | Cause | Impact | Correction |
|-----|-------|--------|------------|
| Chat affiche tout | `newPatients.forEach` sans limite | 6407 patients d'un coup | `slice(0, pageSize)` |
| Classique accumule | Même cause | 60 au lieu de 20 | `slice(0, pageSize)` |
| Endpoint 404 | `/trouve` vs `/search` | Erreur possible | Vérifier avec Thierry |

**Le bug fondamental** : Le code charge correctement les patients en mémoire, mais au moment de les AFFICHER, il affiche TOUS les nouveaux patients (`newPatients.forEach`) au lieu de seulement `pageSize` (`newPatients.slice(0, pageSize).forEach`).

---

## 8. PROCHAINES ÉTAPES

1. ✅ Audit terminé
2. ⏳ Validation avec Thierry des questions ci-dessus
3. ⏳ Correction ciblée du code (une seule ligne à changer!)
4. ⏳ Test et validation
5. ⏳ Puis seulement : améliorations UI (bandeau Google, toggle, etc.)
