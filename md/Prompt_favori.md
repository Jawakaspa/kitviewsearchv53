# Prompt_favori.md

**Version :** 1.0.0  
**Date :** 07/01/2026  
**Objectif :** Ajouter un système de favoris avec cœur cliquable sur les fiches patients

---

## 🎯 Objectif du développement

Implémenter un système de favoris pour les patients avec :
- Affichage d'un cœur (❤️ plein ou 🤍 vide) en haut à droite de chaque carte patient
- Possibilité de toggler le favori par simple clic
- Mise à jour immédiate en base de données
- Endpoint API générique réutilisable pour d'autres tags

---

## 📋 Spécifications fonctionnelles

### Affichage du cœur

| État | Icône | Description |
|------|-------|-------------|
| Favori | ❤️ (ou `♥` rouge) | Cœur plein rouge |
| Non favori | 🤍 (ou `♡` gris) | Cœur vide/contour |

**Position** : En haut à droite de la carte patient, visible en mode condensé ET expanded.

### Comportement au clic

1. Clic sur le cœur → appel API immédiat
2. Feedback visuel instantané (optimistic update)
3. En cas d'erreur API → rollback visuel + message d'erreur discret
4. Le clic sur le cœur ne doit PAS déclencher l'expansion de la carte

### Accessibilité

- Clic possible en mode condensé ET en mode expanded
- Cursor `pointer` sur le cœur
- Tooltip au survol : "Ajouter aux favoris" / "Retirer des favoris"

---

## 🗃️ Structure de données

### Rappel : Stockage des tags

Le tag "favori" est stocké à **deux endroits** (comme tous les tags) :

1. **Table de jointure `patients_pathologies`** : Pour la recherche rapide
2. **Colonne `canontags` de la table `patients`** : Pour l'affichage

**Note** : Bien que la table s'appelle `patients_pathologies`, elle gère aussi les tags. Le tag "favori" n'a pas d'adjectif associé.

### Structure de la table patients (rappel)

```sql
CREATE TABLE patients (
    id INTEGER PRIMARY KEY,
    canontags TEXT,        -- Tags séparés par virgule, inclut "favori" si présent
    canonadjs TEXT,
    sexe TEXT,
    age DECIMAL(5, 3),
    datenaissance DATE,
    prenom TEXT,
    nom TEXT,
    idportrait TEXT,
    oripathologies TEXT,
    pathologies TEXT
);
```

### Structure de la table pathologies (rappel)

```sql
CREATE TABLE pathologies (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    pathologie TEXT UNIQUE NOT NULL
);
```

### Structure de la table de jointure (rappel)

```sql
CREATE TABLE patients_pathologies (
    patient_id INTEGER NOT NULL,
    pathologie_id INTEGER NOT NULL,
    PRIMARY KEY (patient_id, pathologie_id),
    FOREIGN KEY (patient_id) REFERENCES patients(id) ON DELETE CASCADE,
    FOREIGN KEY (pathologie_id) REFERENCES pathologies(id) ON DELETE CASCADE
);
```

---

## 🔌 API Backend

### Endpoint générique pour toggle de tag

```
POST /api/patient/{patient_id}/tag
Content-Type: application/json

{
    "tag": "favori",
    "action": "toggle"  // ou "add" ou "remove"
}
```

**Réponse succès :**
```json
{
    "success": true,
    "patient_id": 123,
    "tag": "favori",
    "is_set": true,
    "message": "Tag favori ajouté"
}
```

**Réponse erreur :**
```json
{
    "success": false,
    "error": "Patient introuvable",
    "patient_id": 123
}
```

### Actions à effectuer côté serveur

Lors d'un toggle du tag "favori" :

1. **Vérifier** si le patient existe
2. **Vérifier** si le tag existe dans la table `pathologies` (le créer si nécessaire)
3. **Toggle dans `patients_pathologies`** :
   - Si liaison existe → la supprimer
   - Si liaison n'existe pas → la créer
4. **Mettre à jour `canontags`** dans la table `patients` :
   - Ajouter ou retirer "favori" de la liste
5. **Retourner** le nouvel état

### Exemple de requête SQL

```sql
-- Vérifier si le tag existe déjà pour ce patient
SELECT 1 FROM patients_pathologies pp
JOIN pathologies p ON pp.pathologie_id = p.id
WHERE pp.patient_id = ? AND p.pathologie = 'favori';

-- Ajouter le tag
INSERT INTO patients_pathologies (patient_id, pathologie_id)
SELECT ?, id FROM pathologies WHERE pathologie = 'favori';

-- Retirer le tag
DELETE FROM patients_pathologies 
WHERE patient_id = ? 
AND pathologie_id = (SELECT id FROM pathologies WHERE pathologie = 'favori');

-- Mettre à jour canontags (ajouter)
UPDATE patients 
SET canontags = CASE 
    WHEN canontags IS NULL OR canontags = '' THEN 'favori'
    ELSE canontags || ',favori'
END
WHERE id = ?;

-- Mettre à jour canontags (retirer)
UPDATE patients 
SET canontags = REPLACE(REPLACE(REPLACE(canontags, ',favori', ''), 'favori,', ''), 'favori', '')
WHERE id = ?;
```

---

## 🖥️ Frontend (web18.html)

### Modifications de `createPatientCardIA(patient)`

Ajouter un élément cœur cliquable dans le header de la carte :

```javascript
// Dans createPatientCardIA(), après création du header

// Cœur favori en haut à droite
const favoriteBtn = document.createElement('button');
favoriteBtn.className = 'favorite-btn';
favoriteBtn.setAttribute('data-patient-id', patient.id);

// Vérifier si "favori" est dans les tags
const isFavorite = patient.canontags && patient.canontags.toLowerCase().includes('favori');
favoriteBtn.innerHTML = isFavorite ? '❤️' : '🤍';
favoriteBtn.title = isFavorite ? t('Retirer des favoris') : t('Ajouter aux favoris');

favoriteBtn.onclick = async (e) => {
    e.stopPropagation(); // Empêcher l'expansion de la carte
    await toggleFavorite(patient.id, favoriteBtn);
};

header.appendChild(favoriteBtn);
```

### Nouvelle fonction `toggleFavorite()`

```javascript
async function toggleFavorite(patientId, buttonElement) {
    const currentState = buttonElement.innerHTML === '❤️';
    
    // Optimistic update
    buttonElement.innerHTML = currentState ? '🤍' : '❤️';
    buttonElement.title = currentState ? t('Ajouter aux favoris') : t('Retirer des favoris');
    
    try {
        const response = await fetch(`${API_BASE}/api/patient/${patientId}/tag`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ tag: 'favori', action: 'toggle' })
        });
        
        const data = await response.json();
        
        if (!data.success) {
            // Rollback
            buttonElement.innerHTML = currentState ? '❤️' : '🤍';
            buttonElement.title = currentState ? t('Retirer des favoris') : t('Ajouter aux favoris');
            console.error('Erreur toggle favori:', data.error);
        }
    } catch (error) {
        // Rollback en cas d'erreur réseau
        buttonElement.innerHTML = currentState ? '❤️' : '🤍';
        buttonElement.title = currentState ? t('Retirer des favoris') : t('Ajouter aux favoris');
        console.error('Erreur réseau toggle favori:', error);
    }
}
```

### Styles CSS à ajouter

```css
/* Bouton favori (cœur) */
.favorite-btn {
    position: absolute;
    top: 8px;
    right: 8px;
    background: transparent;
    border: none;
    font-size: 20px;
    cursor: pointer;
    padding: 4px;
    line-height: 1;
    transition: transform 0.2s ease;
    z-index: 10;
}

.favorite-btn:hover {
    transform: scale(1.2);
}

.favorite-btn:active {
    transform: scale(0.95);
}

/* Assurer que la carte a position relative pour le positionnement absolu du cœur */
.patient-card-ia {
    position: relative;
}
```

### Exclusion du tag "favori" de la section Tags

Dans la boucle d'affichage des tags, exclure "favori" :

```javascript
tagsList.forEach(tag => {
    // Ne pas afficher "favori" dans la section tags (affiché comme cœur)
    if (tag.toLowerCase() === 'favori') return;
    
    const tagSpan = document.createElement('span');
    tagSpan.className = 'tag-badge';
    tagSpan.textContent = capitalize(tag);
    tagsDiv.appendChild(tagSpan);
});
```

---

## 🔄 Mode classique (createPatientItemClassique)

Appliquer les mêmes modifications pour le mode classique :
- Ajouter le cœur dans le header
- Même logique de toggle
- Mêmes styles CSS

---

## 📝 Traductions à ajouter

Dans le système de traduction existant :

| Clé | FR | EN | DE | ES |
|-----|----|----|----|----|
| `Ajouter aux favoris` | Ajouter aux favoris | Add to favorites | Zu Favoriten hinzufügen | Añadir a favoritos |
| `Retirer des favoris` | Retirer des favoris | Remove from favorites | Aus Favoriten entfernen | Quitar de favoritos |

---

## ⚠️ Points critiques

1. **Deux mises à jour en base** : Table de jointure ET colonne `canontags`
2. **stopPropagation()** : Empêcher le clic de déclencher l'expansion de la carte
3. **Optimistic update** : Feedback visuel immédiat, rollback si erreur
4. **ID patient** : S'assurer que `patient.id` est bien transmis par l'API search
5. **Position relative** : La carte doit avoir `position: relative` pour le positionnement absolu du cœur
6. **Exclusion affichage** : Ne pas afficher "favori" dans la section tags classique

---

## 🧪 Tests à effectuer

1. **Toggle favori** : Cliquer sur cœur vide → devient plein, et vice-versa
2. **Persistance** : Recharger la page → l'état favori est conservé
3. **Recherche** : Rechercher "favori" → retourne les patients marqués favoris
4. **Non-expansion** : Cliquer sur cœur ne doit PAS agrandir la carte
5. **Mode déconnecté** : Vérifier le comportement offline (rollback)
6. **Mode classique** : Même fonctionnement qu'en mode IA

---

## 📎 Fichiers nécessaires en PJ

| Fichier | Emplacement | Description |
|---------|-------------|-------------|
| `server.py` | racine | Serveur FastAPI pour créer l'endpoint |
| `web18.html` | racine | Interface à modifier |
| `search.py` | racine | Pour vérifier que `patient.id` est retourné |
| `Prompt_contexte2312.md` | projet | Contexte général |
| `Prompt_cxchargepats.md` | projet | Structure de la base (référence) |

---

## 📅 Historique des versions du prompt

| Version | Date | Modifications |
|---------|------|---------------|
| 1.0.0 | 07/01/2026 | Version initiale |

---

**Fin du prompt**
