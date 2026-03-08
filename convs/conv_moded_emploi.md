# Prompt conv_moded_emploi V1.0.5 - 12/01/2026 14:32:55

# Synthèse de conversation : moded'emploi

**Projet** : Kitview Search - Application de recherche multilingue pour cabinet d'orthodontie
**Date de début** : 06/01/2026

---

## Échange 1 - 06/01/2026 14:32

### Demande
Rédaction du mode d'emploi de l'application Kitview Search à partir de 3 fichiers HTML constituant l'IHM :
- `web17.html` : Page principale de recherche
- `webparams.html` : Page des paramètres
- `webanalyse.html` : Page d'analyse des logs

Structure demandée :
1. Commencer par le plus simple (page web17 avec bandeau vidé)
2. Utilisation de base
3. Fonctionnalités avancées après avoir coché la case entre "Kitview" et "Search"

### Réponse
Création du fichier **Kitview_Search_Mode_Emploi.md** contenant 7 sections :

1. **Présentation** de l'application
2. **Premier démarrage** avec interface simplifiée (schéma ASCII, éléments par défaut, indicateur d'état)
3. **Utilisation de base** (recherche texte, vocale, panneau latéral, résultats)
4. **Mode avancé - Barre d'outils** (activation checkbox, éléments, langue, démo, IA/Classique)
5. **Page Paramètres** (tableau des 15+ paramètres, moteurs IA, options détection)
6. **Page Analyse** (stats, filtres, 3 vues, 6 graphiques)
7. **Raccourcis et astuces**

### Fichiers générés
- `Kitview_Search_Mode_Emploi.md`

---

## Échange 2 - 06/01/2026 15:02

### Demande
Transformer le mode d'emploi markdown en page HTML (`modedemploi.html`) accessible via un bouton ❓ dans l'IHM principale. Préparer le sélecteur de langue (style web17) pour traduction lazy loading (à la demande).

### Réponse
Création du fichier **modedemploi.html** avec :

**1. Style harmonisé avec web17.html**
- Variables CSS identiques (couleurs, thème jour/nuit)
- Même charte graphique

**2. Structure de la page**
- Header sticky : logo, titre "Mode d'emploi", sélecteur langue, thème 🌙, retour
- Sidebar : table des matières sticky avec surlignage actif au scroll
- Contenu principal : 7 sections dans une card
- Footer avec version

**3. Sélecteur de langue préparé pour lazy loading**
- 11 langues : FR, EN, DE, ES, IT, PT, PL, RO, TH, AR, CN
- Popup avec chips et drapeaux (style identique à web17)
- Stockage préférence dans localStorage (`helpLang`)
- Infrastructure prête :
  - Vérifie si `modedemploi_{lang}.html` existe (HEAD request)
  - Redirige si fichier trouvé
  - Affiche message si traduction non disponible
  - TODO commenté pour appel API de génération à la volée

**4. Fonctionnalités JavaScript**
- `initTheme()` : synchronisation thème avec localStorage
- `renderLanguageChips()` : génération dynamique des chips
- `selectLanguage(langCode)` : gestion de la sélection
- `loadTranslation(langCode)` : chargement lazy
- `initTocHighlight()` : surlignage table des matières via IntersectionObserver
- `goBack()` : retour intelligent (history.back ou web17.html)

### Fichiers générés
- `modedemploi.html`

---

## Fichiers de référence analysés

| Fichier | Lignes | Description |
|---------|--------|-------------|
| web17.html | 8597 | Page principale avec recherche, sidebar, modes IA/Classique |
| webparams.html | 1295 | Page de configuration avec tableau de paramètres |
| webanalyse.html | 1760 | Page d'analyse avec stats, filtres et graphiques |

---

## Points clés de l'architecture

### Interface principale (web17)
- **Checkbox cachée** entre logo et "Search" → active mode avancé
- **Toolbar masquable** avec tous les contrôles avancés
- **Indicateur d'état coloré** : rouge (chargement) → orange (connexion) → vert (prêt)

### Fonctionnalités
- Recherche textuelle en langage naturel
- Recherche vocale : mode normal + mains libres (mot-clé "Kitview")
- Mode Démo avec cycle automatique
- Mode IA (cartes) vs Classique (liste)
- Support multilingue (12 langues)

### Page Paramètres
- Tableau Actif/Bandeau/Valeur pour chaque paramètre
- Section Moteurs IA avec activation/désactivation
- Options detiabrut (tags, adjs, ages, angles, mapping)

### Page Analyse
- 6 graphiques (Chart.js)
- 3 vues (Récap IA, Cards, Stats)
- Filtres par période, mode, moteur

---

## À faire (prochaine étape)

- [x] Implémenter la génération lazy des traductions
- [x] Corriger le bouton retour dans modedemploi.html
- [x] Implémenter le cache versionné dans /ihm
- [x] Corriger le mode fichier local (file://)
- [x] Mettre à jour le mode d'emploi (Paramètres cartes, Illustrations)
- [x] Créer userguide.html avec Google Translate
- [ ] Ajouter le bouton ❓ dans web17.html → déjà fait dans web18
- [ ] Tester les 10 langues avec DeepL

---

## Échange 5 - 06/01/2026 17:00

### Demande
1. Mettre à jour le mode d'emploi pour refléter les modifications (webparams redesigné, illustrations.html)
2. Trouver la conversation sur la traduction automatique des navigateurs
3. Créer userguide.html avec traduction Google Translate (pas de DeepL)

### Réponse

**1. Mise à jour de modedemploi.html (v1.1.0)**

Section 5 - Page Paramètres entièrement réécrite :
- Nouveau design en cartes thématiques
- Navigation rapide (boutons Illustrations, Analytics, Recherche)
- 5 cartes : Apparence, Durées, Limites, Moteurs IA, Détection

Nouvelle section 5bis - Page Illustrations :
- Types d'illustrations (medical, rmedical, search, rsearch, zero)
- Fonctionnalités CRUD (Ajouter, Éditer, Copier, Supprimer)
- Statistiques en temps réel

**2. Traduction automatique des navigateurs**

Pas de conversation trouvée, mais voici le principe :

| Approche | Mécanisme | Avantages | Inconvénients |
|----------|-----------|-----------|---------------|
| **DeepL (modedemploi.html)** | API serveur, traduction lazy | Qualité pro, cache versionné | Coût (500k/mois), serveur requis |
| **Google Translate (userguide.html)** | Widget côté client | Gratuit, 100+ langues, instantané | Qualité variable, UI Google |

**3. Création de userguide.html (v1.0.0)**

Même contenu que modedemploi.html mais avec :

```html
<!-- Widget Google Translate dans le header -->
<div id="google_translate_element"></div>

<!-- Script d'initialisation -->
<script type="text/javascript">
function googleTranslateElementInit() {
    new google.translate.TranslateElement({
        pageLanguage: 'fr',
        includedLanguages: 'en,de,es,it,pt,pl,ro,th,ar,zh-CN,ja,ko,ru,nl,sv...',
        layout: google.translate.TranslateElement.InlineLayout.HORIZONTAL,
        autoDisplay: false
    }, 'google_translate_element');
}
</script>

<!-- Chargement de l'API Google -->
<script src="//translate.google.com/translate_a/element.js?cb=googleTranslateElementInit"></script>
```

**CSS ajouté pour personnaliser le widget :**
- Masquer "Powered by Google"
- Style cohérent avec le thème de l'application
- Classe `.notranslate` pour les éléments à ne pas traduire

### Fichiers générés/modifiés
- `modedemploi.html` v1.1.0 : MAJ Paramètres + Illustrations
- `userguide.html` v1.0.0 : Version avec Google Translate

### Comparaison des deux approches

| Critère | modedemploi.html | userguide.html |
|---------|------------------|----------------|
| Traduction | DeepL (serveur) | Google Translate (client) |
| Langues | 10 langues | 100+ langues |
| Coût | ~15-20 ko/langue/màj | Gratuit |
| Qualité | Excellente (DeepL) | Bonne (Google) |
| Cache | Oui (/ihm) | Non (à la volée) |
| Serveur requis | Oui | Non |
| Fonctionne offline | Non | Non |

---

## Échange 4 - 06/01/2026 16:35

### Problème signalé
Erreur CORS quand on ouvre modedemploi.html directement depuis le système de fichiers (`file:///C:/cx/ihm/modedemploi.html`). Les appels fetch vers `/api/...` sont interprétés comme `file:///C:/api/...`.

### Solution
Ajout de détection automatique du mode fichier local :

```javascript
// URL de base de l'API - détection automatique du mode fichier local
const API_BASE = window.location.protocol === 'file:' 
    ? 'http://localhost:8000' 
    : '';

// URL de base pour les redirections
const HELP_BASE = window.location.protocol === 'file:'
    ? 'http://localhost:8000/help'
    : '/help';
```

**modedemploi.html v1.0.1** : 
- Appels API : `${API_BASE}/api/help/translate/${lang}`
- Redirections : `${HELP_BASE}/${lang}`

### Nouvelles pages documentées

#### webparams.html (v1.0.8) - Page Paramètres redesignée

**Nouveau design en cartes :**
- Interface en grille de cartes (`cards-grid`) responsive
- Chaque carte a un header avec icône + titre
- Lignes de paramètres (`setting-row`) avec label et contrôles
- Navigation rapide en haut avec boutons stylisés sur fond bleu dégradé

**Catégories de cartes :**
| Carte | Paramètres |
|-------|------------|
| 🎨 Apparence | Thème, Style (Windows/LiquidGlass), Filigrane |
| ⏱️ Durées | Timeout toast, Durée session, Délai micro |
| 📊 Limites | Max patients, Lignes récent, Limite suggestions |
| 🧠 Moteurs IA | Liste des moteurs avec checkboxes actif/inactif |
| 🔍 Détection | Tags, Adjs, Ages, Angles, Mapping |

**Style visuel :**
- Hover sur cartes : légère élévation
- Checkboxes avec `accent-color: var(--primary-color)`
- Sliders stylisés avec valeur affichée
- Support thème clair/sombre

#### illustrations.html (v1.0.0) - Nouvelle page gestion images

**Fonctionnalités :**
- Grille d'images avec vignettes
- Filtres : recherche texte + type (medical, search, zero, rmedical, rsearch)
- Compteurs statistiques en haut (Total, Medical, Search, Zero...)
- Actions par carte : Éditer ✏️, Copier 📋, Supprimer 🗑️

**API utilisée :**
| Endpoint | Méthode | Description |
|----------|---------|-------------|
| `/api/illustrations` | GET | Liste toutes les illustrations |
| `/api/illustrations` | POST | Ajoute une illustration |
| `/api/illustrations/{id}` | PUT | Modifie une illustration |
| `/api/illustrations/{id}` | DELETE | Supprime une illustration |

**UI :**
- Modal d'ajout/édition avec prévisualisation image
- Badge type coloré (medical=bleu, search=vert, zero=orange)
- Badge ID (#1, #2, ...)
- Toast notifications (success/error/warning)
- Loading overlay avec spinner

**Accès :** Bouton dans webparams.html → ouvre illustrations.html

### Fichiers modifiés
- `modedemploi.html` v1.0.1 : support mode fichier local

---

## Échange 3 - 06/01/2026 15:40 → 16:15

### Demande
1. Corriger le bouton retour de modedemploi.html (retournait sur web17 au lieu de la page d'origine)
2. Implémenter la traduction lazy côté serveur (server.py)
3. Ajouter un cache versionné pour ne pas retraduire si la version n'a pas changé

### Réponse

**1. Correction du retour dans modedemploi.html**
- Fonction `goBack()` modifiée pour utiliser `window.history.back()` proprement
- Si pas d'historique (accès direct), ferme l'onglet ou redirige vers `/`

**2. Ajout balise meta version dans modedemploi.html**
```html
<meta name="help-version" content="1.0.0">
```
À incrémenter manuellement à chaque modification du mode d'emploi.

**3. Cache versionné dans /ihm (server.py v1.0.42)**

Structure du répertoire :
```
/ihm/
├── help_versions.json          # Métadonnées des versions
├── modedemploi_en.html         # Traduction anglaise
├── modedemploi_de.html         # etc.
└── ...
```

Fichier help_versions.json :
```json
{
  "source_version": "1.0.0",
  "translations": {
    "en": {"version": "1.0.0", "date": "2026-01-06 16:00:00", "size": 55420},
    "de": {"version": "1.0.0", "date": "2026-01-06 16:05:00", "size": 56100}
  }
}
```

**4. Nouveaux endpoints dans server.py (v1.0.42)**

| Endpoint | Méthode | Description |
|----------|---------|-------------|
| `/help` | GET | Sert modedemploi.html |
| `/help/{lang}` | GET | Sert modedemploi_{lang}.html depuis /ihm |
| `/api/help/translate/{lang}` | GET | Génère traduction si version différente |
| `/api/help/versions` | GET | État du cache (versions, dates, tailles) |

**5. Logique de cache**

```
Client demande /api/help/translate/en
    ↓
Lecture version source (meta tag)
    ↓
Lecture help_versions.json
    ↓
Si version EN == version source → retourne cache (pas d'appel DeepL)
    ↓
Sinon → lance traduction DeepL, sauvegarde dans /ihm, MAJ JSON
```

**6. Fonctions ajoutées**
- `_get_source_version()` : Lit la meta tag help-version
- `_load_versions_cache()` : Charge help_versions.json
- `_save_versions_cache()` : Sauvegarde help_versions.json
- `_is_translation_up_to_date()` : Compare versions

**7. Initialisation au démarrage**
- Création automatique du répertoire /ihm si absent
- Log du nombre de traductions en cache

### Fichiers modifiés
- `modedemploi.html` : meta version + retour corrigé + chemin /help/{lang}
- `server.py` : v1.0.42 avec cache versionné dans /ihm

### Économie DeepL estimée
- Sans cache : ~150-200 ko par mise à jour (10 langues × 15-20 ko)
- Avec cache : ~15-20 ko par mise à jour (1 langue modifiée)
- **Économie : ~90% des appels**

---

## Prompt de recréation de modedemploi.html

```
À partir du mode d'emploi Kitview Search, créer une page HTML modedemploi.html avec :

1. Balise meta version : <meta name="help-version" content="X.Y.Z">
   (incrémenter X.Y.Z à chaque modification pour invalider le cache)
2. Style harmonisé avec web17.html (variables CSS, thème jour/nuit)
3. Header sticky : logo Kitview, titre "Mode d'emploi", sélecteur langue, thème, retour
4. Sidebar sticky : table des matières avec surlignage actif au scroll
5. Contenu : 7 sections (Présentation, Premier démarrage, Utilisation base, Mode avancé, Paramètres, Analyse, Raccourcis)
6. Sélecteur langue avec chips et drapeaux (10 langues : EN, DE, ES, IT, PT, PL, RO, TH, AR, CN)
7. Détection mode fichier local (file://) → API_BASE = 'http://localhost:8000'
8. Appel API ${API_BASE}/api/help/translate/{lang} pour traduction lazy
9. Redirection vers ${HELP_BASE}/${lang} après traduction
10. Bouton retour utilisant window.history.back()
11. Responsive (mobile/tablette/desktop)

PJ requises : aucune (contenu intégré directement)
```

## Récapitulatif des fichiers IHM

| Fichier | Version | Description |
|---------|---------|-------------|
| `web17.html` / `web18.html` | - | Page principale de recherche |
| `webparams.html` | 1.0.8 | Page paramètres (design cartes) |
| `webanalyse.html` | - | Page analyse des logs |
| `modedemploi.html` | 1.1.0 | Mode d'emploi (traduction DeepL) |
| `userguide.html` | 1.0.0 | Mode d'emploi (traduction Google) |
| `illustrations.html` | 1.0.0 | Gestion des illustrations |

## Prompt pour ajouter endpoints help à server.py

```
Ajouter à server.py les endpoints de mode d'emploi avec cache versionné :

1. Variable globale IHM_CACHE_DIR initialisée dans lifespan
2. Répertoire /ihm créé au démarrage si absent

3. Endpoints :
   - GET /help : sert modedemploi.html
   - GET /help/{lang} : sert /ihm/modedemploi_{lang}.html
   - GET /api/help/translate/{lang} : traduction lazy avec versioning
   - GET /api/help/versions : état du cache

4. Fonctions helper :
   - _get_source_version() : lit meta tag help-version
   - _load_versions_cache() / _save_versions_cache() : gère help_versions.json
   - _is_translation_up_to_date() : compare versions
   - _generate_translation() : traduit via DeepL
   - _translate_html_content() : traduit le body HTML
   - _call_deepl_translate() : appel API DeepL avec tag_handling=html
   - _split_html_safely() : découpe HTML si > 100ko

5. Cache help_versions.json :
   {"source_version": "X.Y.Z", "translations": {"en": {"version": "X.Y.Z", "date": "...", "size": N}}}

6. Logique : ne retraduit que si version source != version cache

PJ requises : server.py existant
```

---

*Dernière mise à jour : 06/01/2026 17:20*
