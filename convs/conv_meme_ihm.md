# Prompt conv_meme_ihm V1.0.0 - 14/01/2026 17:18:11

# Synthèse conversation : même ihm

## Informations générales
- **Date de début** : 14/01/2026
- **Objectif** : Implémenter une fonctionnalité de recherche "même X" cliquable depuis l'interface web

---

## Échange 1 - 14/01/2026 15:xx

### Demande utilisateur
Créer une fonctionnalité permettant de cliquer sur les éléments d'un patient affiché pour déclencher une recherche "même X" (même portrait, même âge, même sexe, même nom, même prénom, tags, adjectifs).

### Précisions obtenues
1. **Pas de boutons "même"** mais des libellés avec fond arrondi (style bouton "?")
2. **Exception portrait** : Bordure colorée au survol uniquement (ou bordure permanente si patient de référence)
3. **Affichage utilisateur** : `même béance que Jean Valjean` (lisible)
4. **Question technique** : `même béance que id 42` (pour la recherche)
5. **Tags et adjectifs séparés** : clic sur "béance" → `même béance`, clic sur "latérale" → `même béance latérale`
6. **Renommage "IA" → "Chat"** : Partout (switch, classes CSS, variables, localStorage)
7. **Séparation CSS/HTML** : Fichiers séparés pour réduire la taille
8. **Tooltips** : En français uniquement (pas d'impact i18n)

### Règles de gestion V5.1 (1 seul patient de référence)
- Changement de patient → réinitialise tous les critères "même"
- Clic sur même du patient de référence pour un critère déjà utilisé → désactivé (pas de fond)
- Clic sur nouveau critère du même patient → affine (cumule)

---

## Fichiers créés

| Fichier | Lignes | Taille | Description |
|---------|--------|--------|-------------|
| web22.html | ~6324 | 314K | HTML allégé avec lien vers CSS externe |
| web22.css | ~3028 | 89K | Styles CSS séparés |

### Comparaison
- **Avant** : web21.html = 8867 lignes (~400K)
- **Après** : web22.html + web22.css = ~9350 lignes (~403K) mais mieux organisé

---

## Fonctionnalités ajoutées

### Module "MÊME" (memeState)
- État global des critères en cours
- Gestion du patient de référence
- Génération des questions (display vs technical)
- Désactivation des critères déjà utilisés

### Éléments cliquables
| Élément | Type critère | Exemple question |
|---------|--------------|------------------|
| Portrait | portrait | `même portrait que id 42` |
| Sexe (♂/♀) | sexe | `même sexe que id 42` |
| Âge | age | `même age que id 42` |
| Nom | nom | `même nom que id 42` |
| Prénom | prenom | `même prenom que id 42` |
| Tag (béance) | tag + valeur | `même béance que id 42` |
| Adjectif (latérale) | pathologie + valeur | `même béance latérale que id 42` |

### Styles CSS ajoutés
- `.meme-clickable` : Fond arrondi style bouton "?"
- `.meme-disabled` : Élément désactivé (transparent)
- `.meme-portrait-clickable` : Bordure orange au survol
- `.meme-portrait-reference` : Bordure rouge permanente
- `.pathology-word.meme-word-clickable` : Mot cliquable dans pathologie

---

## Prompt de recréation

### Pour recréer web22.html et web22.css

```
Contexte : Application de recherche patients orthodontie (Kitview Search)

Fichiers nécessaires en PJ :
- web21.html (version de base)
- detmeme.py (détection expressions "même")
- trouveid.py (identification patient référence)

Demande :
1. Séparer le CSS de web21.html dans un fichier web22.css externe
2. Renommer "IA" → "Chat" partout (switch, classes, variables, localStorage)
3. Ajouter fonctionnalité "même X" cliquable sur les cartes patients :
   - Portrait : bordure orange au survol, rouge si patient de référence
   - Sexe, âge, nom, prénom : fond arrondi cliquable (style bouton "?")
   - Pathologies : chaque mot (tag, adjectif) cliquable séparément
4. Comportement :
   - Clic génère question technique avec ID mais affiche avec nom
   - Changement de patient réinitialise les critères
   - Critères déjà utilisés sont désactivés (sans fond)
5. Tooltips en français uniquement
```

---

## Notes techniques
- L'ID patient vient de `patient.id` dans les données JSON
- Les fonctions `handleMemeClick`, `generateMemeQuestion`, `isMemeDisabled` gèrent la logique
- Le mode Chat (ex-IA) et le mode Classique sont tous deux supportés

