# Prompt conv_vocalweb13 V1.0.2 - 05/01/2026 08:20:12

# Synthèse Conversation : vocalweb13

**Projet** : Kitview Search - Application de recherche multilingue orthodontique  
**Date de début** : 30/12/2025

---

## Échanges

### 🕐 30/12/2025 14:32 - Demande initiale : Ajout recherche vocale

**Question utilisateur** :
> Je voudrais rajouter la recherche vocale. Pour cela il faudrait simplement rajouter au niveau des zones de saisie un micro qu'on peut activer ou désactiver.

**Clarifications demandées par Claude** :
1. Compatibilité navigateurs → Masquer sur navigateurs non supportés
2. Comportement désactivation → Clic OU silence (les deux)
3. Langue de reconnaissance → Synchronisée avec langue sélectionnée
4. Position du micro → Entre input et bouton ⬆️
5. Après transcription → Lancer recherche automatiquement
6. Indicateur visuel → Pulsation rouge simple

**Réponse** : Création de web12.html avec :
- Module `voiceSearchManager` (Web Speech API)
- Boutons micro 🎤 sur les 3 zones de saisie
- CSS inline pour l'animation pulsation
- Masquage auto sur Firefox

---

### 🕐 30/12/2025 14:45 - Création web13 demandée

**Question utilisateur** :
> nomdelaconversation:vocalweb13. Crée maintenant web13 à partir du nouveau web12 joint

**Contexte** :
- Fichier web12.html joint (7907 lignes) = version autonome avec CSS intégré
- Recherche vocale déjà fonctionnelle dans web12

**Résolution** :
L'utilisateur s'est souvenu que la recherche vocale était déjà implémentée dans web12.html.
→ Phase de test validée ✅

---

### 🕐 30/12/2025 15:02 - Tests validés + Questions complémentaires

**Retour utilisateur** :
> Je viens de tester et cela fonctionne bien. 2 questions complémentaires :
> * est-ce qu'il est possible de lancer la recherche automatiquement au bout de 5 secondes de silence
> * est-il possible d'activer la détection vocale par un mot clé (siri, alexa, ok google)

**Réponse Claude** :

| Fonctionnalité | Faisabilité | Décision |
|----------------|-------------|----------|
| Timer 5s silence | ✅ Facile | Implémenté dans web13 |
| Raccourci clavier Ctrl+Shift+M | ✅ Facile | Implémenté dans web13 |
| Mot-clé wake word | ⚠️ Problématique | Non recommandé (batterie, vie privée, autorisation permanente) |

---

### 🕐 30/12/2025 15:10 - Création web13.html

**Fichier créé** : web13.html

**Modifications Voice Search v1.1.0** :
1. **Timer de silence 5 secondes** : Après 5s sans parole détectée, la recherche se lance automatiquement
2. **Raccourci clavier Ctrl+Shift+M** : Active/désactive le micro depuis n'importe où sur la page
3. **Mode continuous** : `recognition.continuous = true` pour permettre de dicter plusieurs phrases
4. **Détection intelligente** : Le raccourci clavier utilise automatiquement l'input visible (center, top ou bottom)

---

## Statut actuel

| Élément | Statut |
|---------|--------|
| Recherche vocale | ✅ Implémentée dans web12/web13/web14 |
| Timer silence 5s | ✅ Implémenté dans web13/web14 |
| Raccourci Ctrl+Shift+M | ✅ Implémenté dans web13/web14 |
| Mode mains libres | ✅ Implémenté dans web14 |
| webparams.html | ✅ Créé (fichier fixe) |
| webanalyse.html | ✅ Créé (fichier fixe) |

---

## Architecture finale

```
web14.html → web15.html → web16.html → ...  (incrémente à chaque modif)
     ↓            ↓            ↓
webparams.html ←──────────────────────────── (fichier fixe, partagé)
     ↓
webanalyse.html ←─────────────────────────── (fichier fixe, partagé)
```

**Principe** : Seul webN.html s'incrémente. Les pages params et analyse sont fixes et utilisent `history.back()` pour revenir.

---

### 🕐 30/12/2025 16:05 - Création web14 + webparams + webanalyse

**Fichiers créés** :

#### webparams.html
- Basé sur web12params.html
- Ajout paramètre "Durée mode mains libres 🎤" (1-10 min)
- Lien vers webanalyse.html
- Bouton retour via `history.back()`

#### webanalyse.html  
- Basé sur analyse12.html
- Correction des dates invalides/futures dans les graphiques
- Bouton "⬅️ Retour" au lieu de "🔍 Recherche"

#### web14.html
- Voice Search v2.0.0 avec mode mains libres
- Liens vers webparams.html et webanalyse.html

---

## Voice Search v2.0.0 - Mode mains libres

### Comportement

| Action | Résultat |
|--------|----------|
| **Clic court** sur 🎤 | Mode normal (comme avant) |
| **Clic long** (500ms) sur 🎤 | Mode mains libres activé |
| **Ctrl+Shift+M** | Toggle mode normal |
| **Ctrl+Alt+Shift+M** | Toggle mode mains libres |

### Mode mains libres

```
[Clic long sur 🎤]
     ↓
[Cercle progressif démarre - durée paramétrable]
     ↓
[Praticien parle : "blabla... Kitview béance classe 2"]
     ↓
[Mot-clé détecté → Recherche "béance classe 2"]
     ↓
[Résultats affichés]
```

### Variantes phonétiques reconnues
- "kitview", "kit view", "kitvue", "kit vue", "quitte view", "quitte vue"

---

## Fichiers générés

| Fichier | Version | Description |
|---------|---------|-------------|
| web12.html | 1.0.0 | Première version avec recherche vocale (Voice Search v1.0.0) |
| web13.html | 1.0.0 | Voice Search v1.1.0 : timer silence 5s + raccourci Ctrl+Shift+M |
| **web14.html** | **1.0.0** | **Voice Search v2.0.0 : mode mains libres + mot-clé "Kitview"** |
| **webparams.html** | **1.0.0** | **Page paramètres fixe (remplace web12params.html)** |
| **webanalyse.html** | **1.0.0** | **Page analyse fixe (remplace analyse12.html)** |

---

## Spécifications techniques - Recherche vocale

### Module voiceSearchManager v1.1.0

```javascript
// API publique
voiceSearchManager.isSupported       // Boolean - API supportée ?
voiceSearchManager.initButtons([])   // Initialise les boutons + raccourci clavier
voiceSearchManager.startListening()  // Démarre écoute
voiceSearchManager.stopListening()   // Arrête écoute
voiceSearchManager.toggleListening() // Bascule état
voiceSearchManager.isListening()     // État actuel
voiceSearchManager.getActiveConfig() // Retourne l'input/bouton actif (pour raccourci)
voiceSearchManager.SILENCE_TIMEOUT   // Constante : 5000ms
```

### Comportement du timer de silence

```
[Clic micro] → Écoute démarre
     ↓
[Parole détectée] → Timer 5s (re)démarre
     ↓
[Silence 5s] → Recherche lancée automatiquement
```

### Raccourci clavier Ctrl+Shift+M

| Contexte | Comportement |
|----------|--------------|
| Page d'accueil | Active le micro sur `searchInputCenter` |
| Mode IA (après recherche) | Active le micro sur `searchInputBottom` |
| Mode Classique | Active le micro sur `searchInputTop` |
| Pendant écoute | Arrête l'écoute |

### Mapping langues → codes BCP-47

| Langue | Code |
|--------|------|
| fr | fr-FR |
| en | en-US |
| de | de-DE |
| es | es-ES |
| it | it-IT |
| pt | pt-PT |
| pl | pl-PL |
| ro | ro-RO |
| th | th-TH |
| ar | ar-SA |
| cn | zh-CN |
| ja | ja-JP |

### CSS du bouton micro

```css
.voice-btn           → Style par défaut (gris)
.voice-btn:hover     → État survol
.voice-btn.listening → État écoute (rouge + pulsation)
.voice-btn.unsupported → Masqué (display: none)
```

---

## Prompt de recréation

### Pour recréer web13.html à partir de web12.html :

**Fichiers nécessaires en PJ :**
- web12.html (version avec recherche vocale v1.0.0)

**Instructions :**
1. Remplacer le module `voiceSearchManager` par la version v1.1.0 :
   - Ajouter `SILENCE_TIMEOUT = 5000`
   - Ajouter `silenceTimer`, `hasReceivedSpeech`, `buttonConfigs`
   - Passer `recognition.continuous = true`
   - Ajouter fonctions `resetSilenceTimer()`, `clearSilenceTimer()`, `launchSearchAndStop()`, `getActiveConfig()`
   - Ajouter le listener clavier `Ctrl+Shift+M` dans `initButtons()`
2. Mettre à jour les commentaires de version
3. Mettre à jour le log de console

---

*Document mis à jour le 30/12/2025 à 15:15*
