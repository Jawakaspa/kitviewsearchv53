# Prompt conv_mode_d_emploi_51 V1.0.0 - 28/01/2026 09:38:14

# Synthèse de conversation : mode d'emploi 51

**Date de début** : 27/01/2026 - 18:30

---

## Résumé de la session

### Demande initiale
Mise à jour du mode d'emploi v5.1 de KITVIEW Search pour documenter :
1. La recherche de similarités ("même X que...")
2. Les modifications de démarrage avec préférences utilisateur persistantes
3. La gestion des préférences dans webparams.html avec reset
4. Simplification du sélecteur de langues (suppression du bouton OK)

### Fichiers fournis en entrée
- `modedemploi.html` : Mode d'emploi existant (v5.1)
- `communb.csv` : Fichier de configuration centralisé (préférences utilisateur)
- `webparams.html` : Page de paramétrage détaillé
- `index.html` : Page principale de recherche (web26.html)

### Clarifications obtenues
1. La section "recherche de similarités" existait déjà → rien à modifier de fond
2. Le démarrage charge désormais les préférences depuis `communb.csv`
3. webparams.html contient les boutons de reset (préférences et exemples)
4. Le sélecteur de langue applique maintenant la traduction immédiatement au clic (plus de bouton OK)
5. Version : reste en v5.1

---

## Modifications apportées

### 27/01/2026 - 18:35 - Mise à jour modedemploi.html

**Contenu mis à jour :**

1. **Section 1 - Présentation** : Ajout d'une note-box listant les nouveautés V5.1

2. **Section 2 - Premier démarrage** :
   - Ajout de la sous-section 2.3 "Préférences utilisateur" expliquant :
     - Sauvegarde automatique dans `communb.csv`
     - Types de préférences (apparence, comportement, fonctionnalités, exemples)
     - Possibilité de reset

3. **Section 4 - Mode avancé** :
   - Mise à jour 4.3 : mention que la langue s'applique immédiatement au clic
   - Ajout de l'explication de la checkbox "→fr"

4. **Section 5 - Page Paramètres** :
   - Ajout de la sous-section 5.4 "Réinitialisation des préférences" avec :
     - Bouton 🔄 Réinitialiser (reset complet)
     - Bouton 🔄 Réinitialiser les exemples (reset partiel)
     - Warning sur la confirmation requise
   - Ajout de la sous-section 5.5 "Enregistrement et annulation"
   - Mise à jour du tableau des cartes de configuration

5. **Section 7 - Raccourcis** :
   - Ajout de l'astuce "Langue instantanée"

**Sélecteur de langue simplifié (CSS + JS) :**
- Suppression du footer avec bouton OK
- Fonction `applyLanguage()` remplace `selectLanguage()` + `applyLanguage()`
- La traduction Google Translate s'applique immédiatement au clic sur un chip

**Table des matières** :
- Ajout des entrées : "Préférences", "Reset préférences"

---

## Fichiers produits

| Fichier | Description |
|---------|-------------|
| `modedemploi.html` | Mode d'emploi v5.1 mis à jour |

---

## Prompts de recréation

### Pour recréer modedemploi.html

**Prompt** :
```
Crée le mode d'emploi v5.1 de KITVIEW Search (modedemploi.html) avec :

1. Structure HTML complète avec CSS intégré
2. Header avec sélecteur de langue simplifié (clic direct = application immédiate, plus de bouton OK)
3. Table des matières sticky dans une sidebar
4. Sections documentant :
   - Présentation avec nouveautés V5.1
   - Premier démarrage (écran d'accueil, préférences utilisateur persistantes, indicateur d'état)
   - Utilisation de base (recherche texte, vocale, panneau latéral, résultats)
   - Recherche par similarité "même X que" (fonctionnalité V5.1)
   - Mode avancé (barre d'outils, sélection langue simplifiée)
   - Page Paramètres (cartes thématiques, reset préférences, reset exemples)
   - Page Illustrations
   - Page Analyse
   - Raccourcis clavier et astuces

5. JavaScript pour :
   - Google Translate invisible
   - Changement de thème (clair/sombre/auto)
   - Surlignage TOC au scroll
   - Sélecteur de langue avec application immédiate

6. Responsive design (desktop, tablette, mobile)
7. Thème clair/sombre avec CSS variables
```

**Pièces jointes requises** : Aucune (fichier autonome)

---

## Notes techniques

- Le fichier `communb.csv` utilise le format vertical clé-valeur : `section;parametre;valeur;description`
- Les préférences sont organisées en sections : synonymes, langues, theme, utilisateur, fonctionnalites, erreurs, bandeau, comportement, detiabrut, exemples
- La page webparams.html utilise une architecture en cartes thématiques avec navigation hiérarchique
- Le bouton reset appelle `confirmResetAll()` qui demande confirmation avant `resetAllSettings()`
