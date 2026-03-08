# Prompt conv_debugaffichageIAs V1.0.1 - 15/01/2026 20:34:25

# Synthèse Conversation : debugaffichageIAs

**Date de création** : 15/01/2026 15:45

---

## Échange 1 - 15/01/2026 15:45

### Question
Deux problèmes avec web21.html et webparams.html :
1. **Problème 1** : Dans la combo des IAs du bandeau, les 3ème et 4ème items sont identiques ("Recherche IA SANS fallback DeepL") alors que les lignes `ia` et `puria` sont différentes dans ia.csv
2. **Problème 2** (uniquement sur Render) : Quand on coche "affichage bandeau pour l'IA" dans webparams.html, le changement n'apparaît pas dans la combo de index.html sans rafraîchissement de la page

### Diagnostic

#### Problème 1 : Doublon dans la combo des IAs
- **Cause** : Dans `ia.csv`, les lignes 13 (`ia`) et 14 (`puria`) ont **exactement la même description** dans la colonne `notes` :
  ```
  ia;;O;gpt-4.1-mini par défaut;0.40;Recherche IA SANS fallback DeepL (tests/debug);...
  puria;;O;gpt-4.1-mini dans deepl;0.40;Recherche IA SANS fallback DeepL (tests/debug);...
  ```
- Le code `web21.html` (ligne 5721) affiche `info.notes`, donc les deux apparaissent identiques
- **Type** : Problème de données, pas de code

#### Problème 2 : Synchronisation localStorage entre pages
- **Cause** : `index.html` lit `localStorage` uniquement au chargement (`DOMContentLoaded`) et n'écoute **pas** l'événement `storage`
- L'événement `storage` se déclenche uniquement dans les **autres onglets** quand localStorage est modifié
- **Type** : Fonctionnalité manquante dans web21.html

### Solutions

#### Solution Problème 1
Corriger `ia.csv` pour différencier les descriptions :
- Ligne `ia` : "Recherche IA SANS fallback DeepL (tests/debug)"
- Ligne `puria` : "Recherche IA AVEC fallback DeepL (tests/debug)"

#### Solution Problème 2
Ajouter un listener `window.addEventListener('storage', ...)` dans `web21.html` pour détecter les changements faits depuis `webparams.html` et mettre à jour l'affichage en temps réel.

### Fichiers générés
1. `ia.csv` - Version corrigée avec descriptions différenciées
2. `PATCH_web21_sync_localStorage.md` - Instructions et code pour ajouter la synchronisation

---

## Fichiers concernés

| Fichier | Rôle | Modification |
|---------|------|--------------|
| `ia.csv` | Configuration des moteurs IA | Corriger colonne `notes` lignes 13-14 |
| `web21.html` (index.html) | Interface principale | Ajouter listener `storage` |
| `webparams.html` | Page paramètres | Aucune modification nécessaire |

---

## Prompts de recréation

### Pour ia.csv
**Prompt** : "Créer ia.csv avec les mêmes données mais en différenciant les descriptions (notes) des lignes `ia` et `puria`. `ia` = SANS fallback DeepL, `puria` = AVEC fallback DeepL"

**PJ nécessaires** : ia.csv original

### Pour le patch web21.html
**Prompt** : "Ajouter à web21.html un listener sur l'événement 'storage' de localStorage pour synchroniser l'affichage du bandeau (bases, moteur IA, micro, switches, analyse, nom utilisateur) quand les paramètres sont modifiés depuis webparams.html dans un autre onglet"

**PJ nécessaires** : web21.html, webparams.html

---

## Échange 2 - 15/01/2026 16:02

### Question
Appliquer le patch de synchronisation localStorage dans web22.html (version avec CSS séparé).

### Actions réalisées
1. Copie de web22.html
2. Conversion des fins de ligne CRLF → LF
3. Insertion du bloc `window.addEventListener('storage', ...)` après le `DOMContentLoaded` (ligne 6322)
4. Le fichier passe de 6325 à 6428 lignes (+103 lignes)

### Code ajouté
Le listener `storage` gère les clés suivantes :
- `bandeauBases` → affichage sélecteur bases
- `bandeauMoteur` → affichage sélecteur moteur IA
- `activeMicro` → affichage boutons micro
- `bandeauSwitchDemo` → affichage switch démo
- `bandeauSwitchChat` → affichage switch chat/IA
- `bandeauAnalyse` → affichage bouton analyse
- `activeUsername` / `userName` → message de bienvenue
- `currentBase` → base sélectionnée
- `detectionMode` → mode de détection + filigrane

### Fichiers générés
- `web22.html` - Version avec patch de synchronisation intégré

### Prompt de recréation pour web22.html
**Prompt** : "Ajouter à web22.html un listener sur l'événement 'storage' de localStorage pour synchroniser l'affichage du bandeau quand les paramètres sont modifiés depuis webparams.html. Le code doit être inséré après la fermeture du DOMContentLoaded, juste avant </script>. Gérer les clés : bandeauBases, bandeauMoteur, activeMicro, bandeauSwitchDemo, bandeauSwitchChat, bandeauAnalyse, activeUsername, userName, currentBase, detectionMode."

**PJ nécessaires** : web22.html, web22.css

---

## Échange 3 - 15/01/2026 16:08

### Question
Correction : le patch devait aussi être appliqué à web21.html (index.html).

### Actions réalisées
1. Copie de web21.html
2. Conversion des fins de ligne CRLF → LF
3. Insertion du bloc `window.addEventListener('storage', ...)` après le `DOMContentLoaded` (ligne 8864)
4. Le fichier passe de 8867 à 8970 lignes (+103 lignes)

### Différence web21 vs web22
- web21 utilise `iaSwitchContainer` avec clé `bandeauSwitchIA`
- web22 utilise `chatSwitchContainer` avec clé `bandeauSwitchChat`
- Le patch a été adapté en conséquence pour chaque fichier

### Fichiers générés
- `web21.html` - Version avec patch de synchronisation intégré
