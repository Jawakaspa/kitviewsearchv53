# Conversation : search id

## 2026-02-16 ~19:10 — Livraison complète detid

### Question
Livraison des 3 fichiers manquants : detid.py, detmeme.py, jsonsql.py (non présentés lors de la session précédente).

### Réponse
Extraction des fichiers depuis le transcript de la session du 15/02 et livraison des 6 fichiers complets.

---

## 2026-02-16 ~19:30 — Bugs CLI + Bug principal IHM

### Problèmes remontés

**Bugs mineurs CLI :**
- detmeme.py ligne 37 : SyntaxWarning `\d+` dans docstring
- detmeme.py / jsonsql.py : `-v`/`-d` non reconnus (formes courtes manquantes)
- jsonsql.py / detmeme.py : pas d'aide quand appelés sans argument

**Bug principal IHM (1964 patients au lieu de 1) :**
- DeepL traduit "id 10122" → "ce 10122" (détecté comme Latin)
- DeepL traduit "patient id 10122" → "numéro d'identification du patient 10122" (Danois)
- Le pattern `id XXX` est détruit AVANT que detid.py ne le traite
- Résultat : aucun critère → tous les patients retournés

### Corrections livrées

| Fichier | Corrections |
|---------|-------------|
| detmeme.py | `\\d+` dans docstring, `-v`/`-d` ajoutés, no-args=aide |
| jsonsql.py | `-v`/`-d` ajoutés, no-args=aide |

### En attente
- **server.py** nécessaire pour corriger le bug DeepL (extraction pattern `id XXX` avant traduction)
- Intégration IHM de la recherche par ID dans les similitudes

---

## 2026-02-16 ~20:00 — Fix DeepL + IHM "même que" par ID

### Problème
1. **Bug DeepL** : `search.py` envoie "id 10122" à DeepL qui le traduit ("ce 10122" en Latin, "numéro d'identification du patient 10122" en Danois) → pattern détruit → 1964 patients au lieu de 1
2. **IHM "même que"** : les clics sur portrait/nom/prénom/etc. génèrent `même portrait que Guillaume Moulin` → fragile avec prénoms composés. Demande : utiliser `id XXX` à la place.

### Analyse
- Seuls **2 fichiers** à modifier (pas tous les JS)
- `simple30_meme.js` == `meme30.js` (identiques)
- Les 3 fichiers main.js passent déjà `patientId` + `patientFullName` à `handleMemeClick()` → aucun changement requis

### Corrections livrées

| Fichier | Modification |
|---------|-------------|
| **search.py** | ÉTAPE 0 ajoutée : si `\bid\s+[a-zA-Z0-9]+` détecté → force `lang='fr'`, skip traduction DeepL |
| **simple30_meme.js** | `generateMemeQuestion()` : technical passe de `"même X que Nom"` à `"même X que id 10122 Nom"` |
| **meme30.js** | Copie identique de simple30_meme.js |

### Détail technique

**search.py** — Nouvelle ÉTAPE 0 (avant détection langue) :
```python
_PATTERN_ID_TECHNIQUE = re.compile(r'\bid\s+[a-zA-Z0-9]+', re.IGNORECASE)
if _PATTERN_ID_TECHNIQUE.search(question):
    lang = 'fr'
    modulelangue = 'id_technique'
```

**meme.js** — `generateMemeQuestion()` :
```javascript
// Avant : technical: "même portrait que Guillaume Moulin"
// Après : technical: "même portrait que id 10122 Guillaume Moulin"
//         display  : "même portrait que Guillaume Moulin"  (inchangé)
```

### Fichiers NON modifiés (pas nécessaire)
server.py, simple30_main.js, demo30_main.js, main_chat30.js, simple30_search.js, search30.js, et tous les autres JS → aucun changement requis
