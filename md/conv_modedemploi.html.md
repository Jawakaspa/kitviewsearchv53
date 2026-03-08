# Conversation : modedemploi.html

## 11/02/2026 ~13:00 — Migration chat29 → chat30 + modedemploi30

### Question
Réactualiser le mode d'emploi (modedemploi.html) suite à l'intégration de Photofit, en s'appuyant sur une copie d'écran de simple30 comme référence visuelle. Deux demandes :
1. **Corriger l'affichage des scores de similarité** dans chat29 en copiant le style inline de simple30 (badge score devant PATHOLOGIES au lieu d'un badge absolu en haut à droite). Nouveau nom : chat30.
2. **Renommer tous les JS et CSS** avec le suffixe 30.
3. **Mettre à jour le mode d'emploi** → modedemploi30.html avec section Photofit + relecture complète.

### Réponse — Fichiers livrés

| Fichier | Description |
|---------|-------------|
| `chat30.html` | Page HTML mise à jour (réf CSS/JS en 30, lien modedemploi30) |
| `css/chat30.css` | CSS renommé depuis chat29.css (header version mis à jour) |
| `js/main_chat30.js` | **Modifié** : score de similarité déplacé de position absolute (haut droite) vers inline flex avant le titre PATHOLOGIES. Appliqué aux cartes normales ET compact. |
| `js/utils30.js` | Renommé (inchangé) |
| `js/voice30.js` | Renommé (inchangé) |
| `js/search30.js` | Renommé (inchangé) |
| `js/i18n30.js` | Renommé (inchangé) |
| `js/meme30.js` | Renommé (inchangé) |
| `js/illustrations30.js` | Renommé (inchangé) |
| `modedemploi30.html` | Mode d'emploi V5.2 mis à jour |

### Détail des modifications main_chat30.js

- **Supprimé** : badge `position: absolute; top: 6px; right: 8px;` dans `createPatientElement`
- **Ajouté** : div flex `pathoHeader` contenant le badge score inline + le titre PATHOLOGIES
- **Appliqué** aux 2 endroits : cartes normales (ligne ~2770) et cartes compact (ligne ~3270)
- Seuils de couleur conservés : 100%=🎯 jaune, ≥80%=🟢 vert, ≥60%=🔵 bleu, <60%=🟠 orange

### Détail des modifications modedemploi30.html

- Version passée de V5.1 à **V5.2**
- Toutes les références `chat29.html` → `chat30.html`, `clas29.html` → `clas30.html`
- **Nouveautés V5.2** : ajout Photofit et scores de similarité en tête de liste
- **Section 3.5** enrichie : sous-section `Photofit` avec tableau des badges colorés, explication de la recherche par portrait, lecture des résultats
- **TOC** : ajout lien 📸 Photofit
- **Section 7.2 Astuces** : ajout tip Photofit
- **Section 7.3 Exemples** : ajout `même portrait que id 456`
- **Footer** : V5.2
