# Prompt api V1.0.1 - 20/12/2025 16:23:33

# Conversation : API ParkStras

## Date de début : 19 décembre 2025

## Contexte
Duplication de https://dorninem.github.io/ParkStras/ avec une approche différente :
- Logique métier en Python (exposée via FastAPI)
- Frontend léger consommant l'API
- Éviter l'échec de juin (tout en JavaScript)

## Plan initial (juin - échec)
10 prompts séquentiels tout-en-un JavaScript.

## Nouvelle approche
À définir ensemble - architecture Python backend + frontend simple.

---

## Échanges

### Échange 1 - Analyse initiale
**Question** : Avis initial et proposition de pipeline.

**Réponse** :

## APIs identifiées

### 1. Données descriptives des parkings
- **Dataset** : `parkings`
- **URL** : `https://data.strasbourg.eu/api/explore/v2.1/catalog/datasets/parkings/records`
- **Contenu** : description, adresse, position géographique, horaires

### 2. Occupation temps réel
- **Dataset** : `occupation-parkings-temps-reel`
- **URL** : `https://data.strasbourg.eu/api/explore/v2.1/catalog/datasets/occupation-parkings-temps-reel/records`
- **Contenu** : places disponibles (rafraîchi toutes les 3 minutes)

⚠️ **Limite environnement** : `data.strasbourg.eu` n'est pas dans les domaines autorisés pour les appels réseau depuis ce container. Les tests API devront être faits de ton côté.

---

## Mon avis sur le plan de juin

Le plan en 10 étapes était **méthodologiquement correct** mais présentait un risque majeur : **tout en JavaScript côté client** = difficile à débugger, état dispersé, gestion d'erreurs complexe.

### Pourquoi l'échec était prévisible
1. Mélange logique métier + affichage dans le même code JS
2. Pas de maîtrise sur ce qui se passe entre les appels API
3. Débug en aveugle (console browser uniquement)

---

## Ma proposition de pipeline (nouvelle approche)

### Architecture cible
```
[APIs Strasbourg] → [FastAPI Python] → [Frontend simple]
                         ↓
                    Logique métier
                    - Fusion des datasets
                    - Calcul % disponible
                    - Gestion erreurs
```

### Pipeline en 6 étapes

**Étape 1 : Service Python de récupération des données**
- Script Python qui appelle les 2 APIs
- Parse et valide les données
- Exporte en JSON propre
- Tu testes en local, tu valides

**Étape 2 : Fusion des données**
- Joindre parkings + occupation par identifiant commun
- Calculer les métriques (% disponible, état)
- Structure de données unifiée

**Étape 3 : API FastAPI**
- Endpoint `/parkings` retournant les données fusionnées
- Endpoint `/parkings/{id}` pour un parking spécifique
- Gestion d'erreurs propre avec codes HTTP

**Étape 4 : Frontend minimal (HTML/CSS)**
- Page statique
- Appelle TON API FastAPI (pas Strasbourg directement)
- Affiche tableau + carte

**Étape 5 : Rafraîchissement automatique**
- Le frontend poll ton API toutes les X secondes
- Ton API gère le cache et les appels Strasbourg

**Étape 6 : Polish**
- Gestion erreurs côté frontend
- UI/UX
- Déploiement

### Avantages
- Tu **maîtrises** la logique métier (Python lisible)
- Tu peux **tester** chaque partie indépendamment
- Les erreurs sont **claires** (stack traces Python)
- Le frontend est **bête** : il affiche ce qu'on lui donne

---

## Question avant de continuer

Avant de démarrer l'étape 1, j'ai besoin de savoir :

1. **Où vas-tu héberger l'API FastAPI ?** (local uniquement pour commencer ? Render ? Railway ? autre ?)
2. **As-tu accès à un terminal Python sur ta machine ?** (pour tester les scripts)

Sans ces infos, je risque de te produire du code que tu ne pourras pas exécuter.

---

### Échange 2 - Réponses et lancement

**Réponses utilisateur :**
1. Hébergement API : **Render**
2. Environnement local : **Windows CMD + Python**

**Prochaine étape :** Étape 1 - Service Python de récupération des données

---

### Échange 3 - Résultats Étape 1

**Test réussi ✓**

**Champs API Descriptive (parkings):**
`friendlyurl, description, phone, address, types, name, position, idsurfs, normalizedalias, access, periods, websiteurl, modification_date`

**Champs API Temps Réel (occupation-parkings-temps-reel):**
`nom_parking, idsurfs, ident, etat, etat_descriptif, total, libre, infousager, realtimestatus, infoappli, taux_occup, position, couleur_occup`

**Observations:**
- Clé de jointure : `idsurfs` (présent dans les deux)
- 38 parkings descriptifs vs 34 en temps réel
- API Descriptive : nom = `name`, adresse = `address`

**Prochaine étape :** Étape 2 - Fusion des données

---

### Échange 4 - Résultats Étape 2

**Test réussi ✓**

- Fusion OK sur clé `idsurfs`
- 38 parkings fusionnés, 34 avec données temps réel
- Noms, adresses, places libres et pourcentages corrects
- Tri par places libres décroissant fonctionnel

**Prochaine étape :** Étape 3 - API FastAPI
