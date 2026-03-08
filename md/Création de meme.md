## Création de meme.md

```
Contexte : Projet KITVIEW - Interface de recherche patients orthodontie

Fichiers à joindre en PJ :
- Prompt_contexte1301.md
- detmeme.py (V2.1.0)
- trouveid.py (V2.0.0)
- jsonsql.py
- web24.html (V1.1.1)
- web24.css (V1.1.0)
- Prompt_MD_to_Slides_v2_meta.md

Demande :
Créer un document meme.md qui documente de façon exhaustive la fonctionnalité "Recherche par similarité" (même X que Patient) pour un public technique averti.

Structure du document :

Applique les règles de rajout de meta définies dans Prompt_MD_to_Slides_v2_meta pour pouvoir convertir le document en slides si souhaité.

# Système de recherche par similarité (Même X)

## 1. Vue d'ensemble fonctionnelle
- Objectif de la fonctionnalité
- Cas d'usage typiques en orthodontie
- Expérience utilisateur cible

## 2. Syntaxes supportées
Formats acceptés par le parser :
- "même X que Nom Prénom"
- "même X et même Y que Nom"
- "même X même Y que Nom" (sans "et")
- "même X, Y, Z que Nom" (liste avec virgules)
- "mêmes X, Y et Z que Nom" (pluriel français)
- "même X que id 123" (référence par ID)

## 3. Critères de similarité disponibles
Table des critères avec :
| Critère | Cible | Comportement | Exemple SQL |
- portrait → idportrait exact
- sexe → sexe exact  
- age → age ±3 ans (BETWEEN)
- nom → nom exact (insensible casse)
- prenom → prenom exact
- tag → recherche dans pathologies (1 mot)
- pathologie → recherche pathologie complète (plusieurs mots)

## 4. Architecture technique

### 4.1 Pipeline de traitement
```

Question utilisateur
↓
detmeme.py (parsing syntaxe)
↓
JSON intermédiaire avec reference: {type, valeur}
↓
trouveid.py (résolution nom → ID + données patient)
↓
JSON enrichi avec reference_id + reference_patient
↓
jsonsql.py (génération SQL)
↓
lancesql.py (exécution)
↓
Résultats

```
### 4.2 Format JSON intermédiaire
Exemple complet avec tous les champs

### 4.3 Génération SQL
Exemples de SQL généré pour chaque type de critère

## 5. Interface utilisateur (web24)

### 5.1 Affichage des fiches patients
- Structure des badges (light/dark)
- Groupement des pathologies par tag
- Position de l'ID patient

### 5.2 États visuels
- Patient de référence : fond jaune (#fff9c4)
- Critères actifs : bordure rouge
- Éléments cliquables : curseur pointer + hover

### 5.3 Logique d'interaction JavaScript
- memeState : gestion de l'état
- handleMemeClick() : traitement des clics
- generateMemeQuestion() : construction de la requête
- Désélection automatique tag quand pathologie sélectionnée

## 6. Fichiers impliqués
Table récapitulative :
| Fichier | Version | Rôle |
- detmeme.py V2.1.0 - Parser syntaxe "même"
- trouveid.py V2.0.0 - Résolution nom → ID
- jsonsql.py V1.0.7 - Génération SQL
- web24.html V1.1.1 - Interface utilisateur
- web24.css V1.1.0 - Styles

## 7. Tests et validation
Référence au plan de tests (tests_meme_v2.md)
Cas de tests critiques à vérifier

## 8. Limitations connues et évolutions futures
- V5.2 : multiple patients de référence
- API externe avec authentification
- Améliorations UX envisagées

Le document doit être technique, précis, avec des exemples de code/JSON/SQL concrets.
Utiliser le format Markdown avec des blocs de code appropriés.
```
