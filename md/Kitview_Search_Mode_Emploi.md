# Prompt Kitview_Search_Mode_Emploi V1.0.0 - 06/01/2026 08:35:24

# Kitview Search - Mode d'Emploi

**Version 1.0 - 06/01/2026**

---

## Table des matières

1. [Présentation](#1-présentation)
2. [Premier démarrage - Interface simplifiée](#2-premier-démarrage---interface-simplifiée)
3. [Utilisation de base](#3-utilisation-de-base)
4. [Mode avancé - Barre d'outils](#4-mode-avancé---barre-doutils)
5. [Page Paramètres](#5-page-paramètres)
6. [Page Analyse](#6-page-analyse)
7. [Raccourcis et astuces](#7-raccourcis-et-astuces)

---

## 1. Présentation

**Kitview Search** est une application web de recherche multilingue permettant d'interroger une base de données de patients orthodontiques. L'interface s'adapte à tous les écrans (PC, tablette, mobile) et propose deux niveaux d'utilisation :

- **Mode simplifié** : interface épurée pour une prise en main immédiate
- **Mode avancé** : accès complet aux outils de configuration et d'analyse

---

## 2. Premier démarrage - Interface simplifiée

### 2.1 Écran d'accueil

Au lancement, vous êtes accueilli par une interface minimaliste :

```
┌─────────────────────────────────────────────────────────────┐
│  ☰  [logo Kitview] ☐ Search                                 │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────┐                                            │
│  │ ✨ Nouvelle │     Bienvenue 👋                           │
│  │  recherche  │                                            │
│  └─────────────┘     ┌─────────────────────────────────┐   │
│                      │ Rechercher un patient...     🎤 ⬆️ │   │
│  Conversations       └─────────────────────────────────┘   │
│  récentes                                                   │
│  ─────────────                                              │
│  Exemples                                                   │
│  ─────────────                                              │
│                                                             │
│  F1.1.0/S...                                                │
└─────────────────────────────────────────────────────────────┘
```

### 2.2 Éléments visibles par défaut

| Élément | Position | Description |
|---------|----------|-------------|
| ☰ (Menu) | En-tête gauche | Afficher/masquer le panneau latéral |
| Logo Kitview | En-tête gauche | Logo de l'application |
| ☐ (Checkbox cachée) | Entre logo et "Search" | Active le mode avancé |
| "Search" | En-tête | Indicateur d'état (couleur variable) |
| Panneau latéral | Gauche | Historique, exemples, nouvelle recherche |
| Zone de recherche | Centre | Champ de saisie principal |

### 2.3 Indicateur d'état "Search"

Le mot "Search" change de couleur selon l'état du système :

| Couleur | Signification |
|---------|---------------|
| 🔴 Rouge | Chargement en cours |
| 🟠 Orange | Connexion au serveur |
| 🟢 Vert | Prêt à l'emploi |

---

## 3. Utilisation de base

### 3.1 Effectuer une recherche

1. **Cliquez dans la zone de recherche** au centre de l'écran
2. **Saisissez votre requête** en langage naturel, par exemple :
   - `patients avec béance`
   - `classe II division 1`
   - `adultes avec encombrement`
   - `enfants de moins de 12 ans`
3. **Lancez la recherche** en cliquant sur ⬆️ ou en appuyant sur Entrée

### 3.2 Recherche vocale 🎤

Le bouton microphone permet deux modes :

| Action | Mode | Description |
|--------|------|-------------|
| Clic simple | Normal | Écoute unique, recherche après 5 sec de silence |
| Clic long | Mains libres | Écoute prolongée, dites "Kitview" + votre recherche |

**Exemple en mode mains libres** : *"Kitview patients avec bruxisme de moins de 30 ans"*

### 3.3 Panneau latéral

Le panneau gauche propose :

- **✨ Nouvelle recherche** : Réinitialise l'interface
- **Conversations récentes** : Historique des recherches effectuées (cliquez pour copier, ▶ pour relancer)
- **Exemples** : Suggestions de recherches prédéfinies

**Astuce** : La bordure droite du panneau est redimensionnable par glisser-déposer.

### 3.4 Affichage des résultats

Les résultats s'affichent sous forme de cartes patient contenant :

- Nom et prénom
- Âge et sexe
- Date de naissance
- Pathologies (tags colorés)

**Cliquez sur une carte** pour voir les détails complets du patient.

---

## 4. Mode avancé - Barre d'outils

### 4.1 Activer la barre d'outils

Pour accéder aux fonctionnalités avancées :

1. **Localisez la checkbox** entre le logo Kitview et le mot "Search"
2. **Cochez la case** pour faire apparaître la barre d'outils

```
┌────────────────────────────────────────────────────────────────────────────┐
│  ☰  [logo] ☑ Search  │ [Base ▼] │ 🌐FR │ [IA ▼] │ Démo ○ │ IA ○ │ 📊 🌙 ⚙️ │
└────────────────────────────────────────────────────────────────────────────┘
```

### 4.2 Éléments de la barre d'outils

| Élément | Description |
|---------|-------------|
| **[Base ▼]** | Sélecteur de base de données |
| **🌐 FR** | Bouton langue (popup de sélection) |
| **[Mode IA ▼]** | Sélecteur du moteur de détection |
| **Démo ○** | Active/désactive le mode démonstration |
| **IA ○** | Bascule entre mode IA (cartes) et Classique (liste) |
| **📊** | Accès à la page d'analyse (si activé) |
| **🌙** | Bascule mode jour/nuit |
| **⚙️** | Accès aux paramètres |

### 4.3 Sélection de la langue 🌐

Cliquez sur le bouton langue pour ouvrir le panneau de sélection :

**Question** : Choisissez la langue de votre requête
- AUTO (détection automatique - en rouge)
- FR 🇫🇷, EN 🇬🇧, DE 🇩🇪, ES 🇪🇸, IT 🇮🇹, PT 🇵🇹, PL 🇵🇱, RO 🇷🇴, TH 🇹🇭, AR 🇸🇦, CN 🇨🇳

**Réponse** : Choisissez le format de réponse
- Origine : Affiche les données dans leur langue d'origine
- FR : Traduit les résultats en français

### 4.4 Mode Démo

Le switch "Démo" lance un cycle automatique de recherches exemples. Un disque de progression indique l'avancement du cycle.

### 4.5 Mode IA vs Classique

| Mode | Affichage | Zone de recherche |
|------|-----------|-------------------|
| **IA** | Grille de cartes | En bas de l'écran |
| **Classique** | Liste verticale | En haut de l'écran |

---

## 5. Page Paramètres

Accès : cliquez sur ⚙️ dans la barre d'outils

### 5.1 Tableau des paramètres

Chaque paramètre possède trois colonnes de contrôle :

| Colonne | Description |
|---------|-------------|
| **Actif** | Active/désactive la fonctionnalité |
| **Bandeau** | Affiche/masque l'élément dans la barre d'outils |
| **Valeur** | Configuration de la fonctionnalité |

### 5.2 Paramètres disponibles

| Paramètre | Description | Valeurs |
|-----------|-------------|---------|
| Jour/Nuit | Thème de l'interface | Auto, Clair, Sombre |
| Style visuel | Apparence graphique | Windows, LiquidGlass |
| Filigrane | Intensité de l'image de fond | 0-100% |
| Nom d'utilisateur | Nom affiché dans le message de bienvenue | Texte libre |
| Bases | Base de données par défaut | Liste dynamique |
| Internationalisation | Sélecteur de langue | Oui/Non |
| Switch Démo | Bouton mode démo | Oui/Non |
| Switch IA/Classique | Bouton de mode d'affichage | Oui/Non |
| Accès Analyse | Bouton 📊 | Oui/Non |
| Panel gauche | Panneau latéral | Oui/Non |
| ↳ Historique | Section historique | Oui/Non |
| ↳ Exemples | Section exemples | Oui/Non |
| Durée cycle démo | Intervalle entre recherches démo | 10-120 sec |
| Durée mains libres | Durée d'écoute vocale prolongée | 1-10 min |
| Limite résultats | Nombre max de patients | 10-200 |
| Nombre par page | Pagination | 10-100 |

### 5.3 Section Moteurs IA

Cette section permet d'activer/désactiver les différents moteurs d'intelligence artificielle disponibles pour l'analyse des requêtes. Chaque moteur affiche :
- Son nom
- Le fournisseur (OpenAI, Eden AI, Local)
- Le coût (Gratuit ou $X)

### 5.4 Options de détection IA

Configure les référentiels utilisés par l'IA pour interpréter vos requêtes :

| Option | Description |
|--------|-------------|
| **Tags** | Détection des pathologies |
| **Adjectifs** | Qualificatifs (sévère, léger...) |
| **Âges** | Patterns d'âge et de sexe |
| **Angles** | Seuils ANB/SNA/SNB |
| **Mapping** | Conversion détecté → canonique |

Boutons rapides : **Tout activer** / **Tout désactiver**

### 5.5 Exemples de recherche

Zone de texte pour personnaliser les exemples affichés dans le panneau latéral et utilisés par le mode démo. Un exemple par ligne.

### 5.6 Actions

- **📊 Analyse** : Ouvre la page d'analyse
- **← Retour** : Retourne à l'écran de recherche
- **💾 Enregistrer et retourner** : Sauvegarde les paramètres et revient

---

## 6. Page Analyse

Accès : cliquez sur 📊 dans la barre d'outils ou depuis les paramètres

### 6.1 Cartes de statistiques

En haut de page, des cartes affichent les indicateurs clés :
- Total des recherches
- Temps de réponse moyen
- Taux de succès (avec/sans résultats)
- Répartition par mode

### 6.2 Filtres

Un panneau de filtres permet d'affiner l'analyse :

| Filtre | Description |
|--------|-------------|
| Période | Date de début et fin |
| Mode | rapide, ia, compare, union |
| Moteur | Filtre par moteur IA |
| Recherche | Filtrage textuel |

### 6.3 Vues disponibles

Trois onglets de visualisation :

#### Vue "Récap IA"
Synthèse globale avec :
- Statistiques générales
- Recommandations d'optimisation
- Top des termes recherchés

#### Vue "Cards"
Affichage en grille des recherches effectuées. Chaque carte montre :
- La question posée
- Le nombre de résultats
- Le temps de réponse
- Le mode et moteur utilisés
- Un bouton ▶ pour relancer la recherche

#### Vue "Stats"
Graphiques détaillés :
- Recherches par jour (barres)
- Résultats avec/sans patients (donut)
- Répartition par mode (barres horizontales)
- Temps de réponse moyen par jour (courbe)
- Top 10 des termes recherchés (barres)
- Répartition par moteur IA (donut)

### 6.4 Navigation

- **← Retour** : Revient à l'écran précédent
- **⚙️ Paramètres** : Ouvre les paramètres
- **🔄 Actualiser** : Recharge les données

---

## 7. Raccourcis et astuces

### 7.1 Raccourcis clavier

| Raccourci | Action |
|-----------|--------|
| **Entrée** | Lancer la recherche |
| **Ctrl+Shift+M** | Activer la recherche vocale (mode normal) |
| **Ctrl+Alt+Shift+M** | Activer le mode mains libres |
| **Escape** | Fermer une modale ou arrêter l'écoute vocale |

### 7.2 Astuces

- **Autocomplétion** : Le champ de recherche propose des suggestions basées sur l'historique et les exemples
- **Panneau redimensionnable** : Glissez la bordure droite du panneau latéral
- **Cartes patients** : Cliquez pour développer, cliquez à nouveau pour réduire
- **Mode mains libres** : Dites "Kitview" suivi de votre recherche pour déclencher automatiquement
- **Thème automatique** : Le mode "Auto" suit les préférences système de votre appareil

### 7.3 Exemples de requêtes

```
patients avec béance
classe II division 1
adultes avec encombrement
enfants de moins de 12 ans
patients traités par invisalign
bruxisme et classe 3
femmes de plus de 40 ans avec supraclusion
```

---

## Support

Pour toute question ou suggestion, utilisez le bouton 👎 sous les réponses de recherche pour envoyer vos retours.

---

*Kitview Search - Mode d'emploi v1.0 - Janvier 2026*
