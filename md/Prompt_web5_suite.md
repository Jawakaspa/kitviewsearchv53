# Prompt web5 - Suite du développement

## Fichiers à joindre en PJ :
1. `web5.html` (version 1.0.0 générée le 24/12/2025)
2. `server.py` (version 1.1.0)
3. `commun.csv` (configuration langues)
4. `Prompt_contexte2312.md` (règles du projet)
5. `conv_py.md` (synthèse des échanges précédents)

---

## Contexte

Session précédente (24/12/2025) :
- ✅ Bug portraits corrigé dans `server.py`
- ✅ `Compare5.html` créé comme fork pour future page de comparaison
- ✅ `web5.html` créé avec :
  - Page paramètres en tableau 4 colonnes style Excel (Paramètre/Actif/Bandeau/Valeur)
  - Mode Union simplifié (checkbox + sélecteur IA dans paramètres)
  - Suppression des checkboxes Compare/Union de la toolbar
  - Fonctions `applyActiveStates()`, `applyBandeauStates()`, `applyPanelVisibility()` ajoutées

---

## Points restants à implémenter

### 3. Comportement changement de base

Quand on change de base depuis les paramètres OU depuis la toolbar :
- Fermer la modale paramètres (si ouverte)
- Revenir à l'écran d'accueil (comme "Nouvelle recherche")
- Rejouer l'animation Search (Rouge → Orange → Vert)

### 4. Toolbar dynamique selon paramètres "Bandeau"

Vérifier/compléter le comportement :
- Les éléments cochés dans la colonne "Bandeau" apparaissent dans la toolbar du header
- Les éléments non cochés restent uniquement accessibles dans les paramètres
- Éléments concernés :
  - Bases (dropdown) - par défaut dans bandeau
  - Internationalisation (bouton langue) - par défaut dans bandeau
  - Jour/Nuit (toggle) - par défaut PAS dans bandeau
  - Style visuel - par défaut PAS dans bandeau
  - Nom utilisateur - par défaut PAS dans bandeau

### 5. Panel gauche configurable

Vérifier/compléter le comportement :
- Si "Panel gauche" est décoché → sidebar masquée entièrement
- Si "Historique" est décoché → section "Conversations récentes" masquée
- Si "Exemples" est décoché → section "Exemples" masquée
- Règle de gestion : si Panel gauche décoché, Historique et Exemples sont automatiquement désactivés

---

## Bugs éventuels à corriger

(À compléter après test de web5.html)

---

## Notes techniques

### Structure actuelle de la page paramètres

```html
<table class="settings-table">
  <thead>
    <tr>
      <th>Paramètre</th>
      <th>Actif</th>
      <th>Bandeau</th>
      <th>Valeur</th>
    </tr>
  </thead>
  <tbody>
    <!-- Lignes de paramètres -->
  </tbody>
</table>
```

### Éléments DOM ajoutés (v5.0)

Checkboxes Actif :
- `activeTheme`, `activeStyle`, `activeUsername`, `activeI18n`, `activeUnion`
- `activePanel`, `activeHistorique`, `activeExemples`
- `activeDemo`, `activeLimit`, `activePagesize`

Checkboxes Bandeau :
- `bandeauTheme`, `bandeauStyle`, `bandeauUsername`
- `bandeauBases`, `bandeauI18n`

Autres :
- `unionIASelect` (sélecteur IA pour mode Union)

### Fonctions JS ajoutées (v5.0)

```javascript
applyActiveStates(settings)    // Désactive contrôles si Actif décoché
applyBandeauStates(settings)   // Masque éléments toolbar si Bandeau décoché
applyPanelVisibility(settings) // Gère visibilité panel gauche + sections
```

---

## Rappel des conventions

- Nom de la conversation pour synthèse : `py`
- Fichier de synthèse : `conv_py.md`
- Les fichiers .html gardent leur numéro de version dans le nom (web5, web6...)
- Style paramètres : Excel minimaliste, pas de fioritures
