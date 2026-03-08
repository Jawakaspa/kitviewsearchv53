# Prompt conv_modedemploiV5.1 V1.0.0 - 21/01/2026 16:31:52

# Synthèse de conversation : modedemploiV5.1

**Date de création** : 21/01/2026  
**Projet** : KITVIEW Search V5  
**Fichiers concernés** : modedemploi.html, web24.html, search.py

---

## 🕐 Échanges

### 21/01/2026 - 14:XX - Mise à jour modedemploi.html vers V5.1

**Question Thierry** :  
Mettre à jour modedemploi.html pour ajouter la section "Recherche par similarité" (même X que Patient), appliquer les métadonnées slides selon Prompt_MD_to_Slides_Ready.md, et vérifier la cohérence avec l'existant (web24.html, search.py).

**Réponse Claude** :

#### Actions réalisées :

1. **Nouvelle section 3.5 "Même X que..."** ajoutée avec :
   - Explication du principe (tous les éléments cliquables)
   - Guide étape par étape (7 étapes)
   - Tableau des éléments cliquables et recherches générées
   - Exemples visuels avec CSS simulant les tags/cartes
   - Syntaxe directe pour la barre de recherche
   - Notes sur le groupement des pathologies par tag

2. **Métadonnées slides** ajoutées :
   - `PRESENTATION_META` en en-tête
   - Balises `SLIDE`, `KEY`, `QUESTION`, `DIAGRAM`, `TABLE` sur toutes les sections
   - Templates appropriés (titre-section, 2colonnes, tableau, schema)
   - Timing estimé pour chaque section

3. **Corrections de cohérence** :
   - Version badge mise à jour : v5.0 → v5.1
   - Footer mis à jour : v5.0 → v5.1
   - Table des matières enrichie avec nouvelle section "🆕 Même X que..."
   - Modes de recherche dans section 6.2 : mis à jour avec `standard, ia, purstandard, puria` (aligné avec search.py V1.0.28)

4. **Nouveaux styles CSS** ajoutés :
   - `.demo-tag` (dark/light/active) pour simuler l'apparence des pathologies
   - `.demo-card` pour la carte patient de référence (fond jaune)
   - `.note-box.new` pour les encarts "nouveauté"
   - Variables CSS pour highlight-yellow, tag-dark, patho-light

5. **Vérifications de cohérence effectuées** :
   - ✅ Affichage ID patient (en haut à gauche) - conforme web24.html V1.1.0
   - ✅ Groupement pathologies par tag - conforme web24.html V1.1.0
   - ✅ Styles inversés Prénom/Nom - conforme web24.html V1.1.0
   - ✅ Fond jaune patient de référence - conforme web24.html (meme-reference-card)
   - ✅ Bordure rouge critères actifs - conforme web24.html (meme-active)
   - ✅ Modes détection disponibles - conforme search.py V1.0.28

---

## 📁 Fichiers générés

| Fichier | Version | Description |
|---------|---------|-------------|
| modedemploi.html | V5.1.0 | Guide utilisateur mis à jour avec section "Même X que" |
| conv_modedemploiV5.1.md | - | Ce fichier de synthèse |

---

## 📝 Prompt de recréation

Pour recréer `modedemploi.html` V5.1.0 à partir de zéro :

```
Fichiers à joindre en PJ :
- Prompt_contexte1301.md
- Prompt_MD_to_Slides_Ready.md
- web24.html (pour vérification cohérence)
- search.py (pour vérification modes disponibles)
- modedemploi.html V5.0 (version de base à mettre à jour)

Demande :
Mettre à jour modedemploi.html vers V5.1 avec les modifications suivantes :

1. NOUVELLE SECTION 3.5 "Recherche par similarité - Même X que..."
   - Fonctionnalité permettant de trouver des patients similaires
   - Tous les éléments des cartes patients sont cliquables
   - Éléments cliquables : portrait, prénom, nom, sexe, âge, tag, pathologie complète
   - Patient de référence affiché avec fond jaune
   - Critères actifs entourés d'une bordure rouge
   - Possibilité de combiner plusieurs critères
   - Syntaxe directe dans la barre de recherche

2. MÉTADONNÉES SLIDES selon Prompt_MD_to_Slides_Ready.md
   - PRESENTATION_META en en-tête
   - Balises SLIDE, KEY, QUESTION sur chaque section
   - Templates appropriés (titre-section, 2colonnes, tableau, schema)

3. VÉRIFICATION COHÉRENCE avec web24.html et search.py
   - Affichage ID patient en haut à gauche
   - Groupement pathologies par tag
   - Modes détection : standard, ia, purstandard, puria

4. NE PAS TOUCHER à la structure technique Google Translate
   - Widget invisible mais fonctionnel
   - Sélecteur de langue custom avec chips

5. STYLES CSS à ajouter pour la nouvelle section :
   - .demo-tag (dark/light/active)
   - .demo-card (fond jaune)
   - .note-box.new (encart nouveauté)
```

---

## 🔍 Points de vérification cohérence

### Comparaison web24.html V1.1.0 ↔ modedemploi.html V5.1.0

| Élément | web24.html | modedemploi.html | Statut |
|---------|------------|------------------|--------|
| ID patient position | Haut gauche (sans #) | Documenté section 3.4 | ✅ |
| Fond patient référence | .meme-reference-card (jaune) | Documenté + demo-card CSS | ✅ |
| Bordure critère actif | .meme-active (rouge) | Documenté + demo-tag.active CSS | ✅ |
| Groupement pathologies | Tag + pathologies ensemble | Documenté section 3.5 | ✅ |
| Tags fond sombre | Style dark | Documenté + demo-tag.dark CSS | ✅ |
| Pathologies fond clair | Style light | Documenté + demo-tag.light CSS | ✅ |
| Désélection auto tag | Clic patho → tag désélectionné | Documenté (astuce) | ✅ |
| Question technique | Utilise nom (pas id) | Documenté (syntaxe) | ✅ |

### Comparaison search.py V1.0.28 ↔ modedemploi.html V5.1.0

| Élément | search.py | modedemploi.html | Statut |
|---------|-----------|------------------|--------|
| Modes détection | standard, ia, purstandard, puria | Section 6.2 mise à jour | ✅ |
| Escalade IA | standard→ia, deepl fallback | Non détaillé (trop technique) | ⚠️ |
| Glossaire prioritaire | glossaire.csv avant DeepL | Non mentionné | ⚠️ |

> Note : Les détails techniques d'escalade et de traduction ne sont pas inclus dans le mode d'emploi utilisateur car trop complexes pour l'audience cible (praticiens).

---

## 📊 Statistiques du document

- **Sections principales** : 7 (+ 1 sous-section 5bis)
- **Nouvelles sections** : 1 (section 3.5)
- **Tableaux** : 15
- **Schémas ASCII** : 2
- **Notes/encarts** : 12 (info, tip, warning, new)
- **Métadonnées slides** : ~20 balises
- **Durée présentation estimée** : 25 minutes

---

## ⚠️ Points d'attention

1. **Structure Google Translate** : NE PAS MODIFIER - fonctionne après plusieurs itérations
2. **Fichier protégé** : modedemploi.html contient des données utilisateur (préférences langue)
3. **Recherches "même"** : Non enregistrées dans l'historique (comportement voulu)
4. **Modes purstandard/puria** : Pour tests CLI uniquement, pas pour utilisateurs finaux

---

## 🔄 Historique des versions modedemploi.html

| Version | Date | Modifications |
|---------|------|---------------|
| V1.0.9 | 20/01/2026 | Version initiale V5.0 |
| V5.1.0 | 21/01/2026 | + Section "Même X que", + métadonnées slides, cohérence web24 |

---

*Fin de synthèse - conv_modedemploiV5.1.md*
