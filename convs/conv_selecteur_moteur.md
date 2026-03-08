# Prompt conv_selecteur_moteur V1.0.0 - 11/01/2026 16:32:08

# Conversation : sélecteur moteur

## Synthèse de conversation Kitview Search

---

## 🕐 11/01/2026 21:05 - ERRATUM : Simplification du sélecteur Moteur IA

### Correction demandée
- Pas de combo dans webparams.html pour choisir le moteur par défaut
- Le moteur par défaut est fixe et non configurable :
  - Mode standard : "standard" (toujours en tête de la combo du bandeau)
  - Mode ia/puria : "gpt41mini" (hardcodé dans l'application)

### Actions réalisées
- Suppression de la combo `defaultIAMoteur` dans webparams.html
- Suppression de la fonction `populateDefaultIAMoteur()`
- Conservation uniquement : V fixe + checkbox Bandeau

---

## 🕐 11/01/2026 20:47 - Ajout sélecteur Moteur IA dans le bandeau

### Question initiale
Ajout d'un sélecteur permettant d'afficher la sélection du moteur de recherche IA dans le bandeau, similaire au sélecteur de base :
- V fixe dans la colonne Actif (non désactivable)
- Case à cocher pour le Bandeau
- Position : dans la frame Toolbar de webparams.html

### Réponse / Actions réalisées

**Fichiers modifiés :**

1. **webparams.html** (V1.0.11 → V1.0.12)
   - Ajout d'un nouvel élément "🤖 Moteur IA" dans la carte "Toolbar & Fonctionnalités"
   - Structure finale : V fixe + checkbox `bandeauMoteur`
   - Ajout de `bandeauMoteur` dans le dictionnaire `elements`
   - Ajout de `bandeauMoteur` dans loadSettings/saveSettings

2. **web19.html → web20.html** (V1.0.8 → V1.0.9)
   - Renommage de web19 en web20
   - Le sélecteur `detectionModeSelector` existait déjà
   - La logique de visibilité via `bandeauMoteur` dans localStorage était déjà présente
   - Mise à jour des numéros de version

**Logique de fonctionnement :**
- `bandeauMoteur` : si `true`, affiche le sélecteur de moteur IA dans le bandeau de web20.html
- Moteur par défaut dans le bandeau : toujours "standard" en tête
- Moteur utilisé pour ia/puria : toujours "gpt41mini" (hardcodé)

---

## Prompt de recréation

### webparams.html V1.0.12

**Fichiers PJ requis :**
- webparams.html V1.0.11 (base)

**Prompt :**
```
À partir de webparams.html V1.0.11, ajouter un élément "Moteur IA" dans la carte "Toolbar & Fonctionnalités" :

1. STRUCTURE HTML (après la légende "A = Actif | B = Bandeau", avant fermeture du card-body) :
   - Nouveau bloc avec classe setting-row, séparé par une bordure top
   - Label "🤖 Moteur IA"
   - V fixe (span class="locked")
   - Checkbox id="bandeauMoteur" avec label "Bandeau"
   - PAS DE COMBO (moteur par défaut non configurable)

2. ÉLÉMENTS JS (dans const elements, section Checkboxes Bandeau) :
   - bandeauMoteur: document.getElementById('bandeauMoteur')

3. LOAD SETTINGS :
   - Ajouter loadCheckbox('bandeauMoteur', false)

4. SAVE SETTINGS :
   - Ajouter saveCheckbox('bandeauMoteur')

5. Mettre à jour version → V1.0.12

Note : Le moteur par défaut est hardcodé :
- Bandeau : "standard" toujours en tête
- ia/puria : "gpt41mini" toujours utilisé
```

### web20.html V1.0.9

**Fichiers PJ requis :**
- web19.html V1.0.8 (base)

**Prompt :**
```
À partir de web19.html, renommer en web20.html :
- Mettre à jour version → V1.0.9
- Mettre à jour le console.log d'initialisation → 'Kitview Search v20'
- Le sélecteur detectionModeSelector et la gestion bandeauMoteur existent déjà
```

---

## Fichiers livrés

| Fichier | Version | Description |
|---------|---------|-------------|
| webparams.html | V1.0.12 | Page paramètres avec checkbox Bandeau pour Moteur IA |
| web20.html | V1.0.9 | Page principale (ex web19) |
| conv_selecteur_moteur.md | - | Cette synthèse |
