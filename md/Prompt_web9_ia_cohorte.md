# Prompt_web9_ia_cohorte.md

## Contexte du projet

Ce prompt fait suite au projet **web9_i18n_ia** qui a ajouté :
- Endpoints API : GET/PUT /ia, POST /ia/ask, GET /i18n
- Système i18n avec chargement depuis glossaire.csv
- Zone IA dans les cards patients (chat individuel)
- Gestion des moteurs IA dans web9params.html

---

## Partie 1 : Suggestions de saisie et actions sidebar

### 1.1 Datalist pour les suggestions

**Objectif** : Quand l'utilisateur tape dans le champ de recherche, proposer en autocomplétion :
- Les **recherches récentes** (conversationHistory)
- Les **exemples** (DEFAULT_EXAMPLES ou depuis localStorage)

**Implémentation** :
```html
<input type="text" id="searchInputCenter" list="searchSuggestions" ...>
<datalist id="searchSuggestions">
    <!-- Peuplé dynamiquement -->
</datalist>
```

**Fonction** `updateSearchSuggestions()` :
- Vider le datalist
- Ajouter les queries de conversationHistory (les plus récentes en premier)
- Ajouter les exemples
- Dédupliquer

**Appel** : Au chargement + après chaque recherche

---

### 1.2 Double action dans la sidebar (Copier OU Exécuter)

**Problème actuel** : Un clic sur un item de la sidebar le copie dans le champ de recherche, mais ne l'exécute pas.

**Solution proposée** : Deux zones cliquables sur chaque item

```
┌─────────────────────────────────────┬─────┐
│  bruxisme classe 2                  │  ▶  │
│  (zone cliquable = copier)          │ run │
└─────────────────────────────────────┴─────┘
```

**Comportement** :
- **Clic sur le texte** : Copie dans le champ de recherche (comportement actuel)
- **Clic sur ▶** : Exécute directement la recherche

**Alternative UX** : 
- Simple clic = copier
- Double clic = exécuter
- Ou : clic = exécuter, Shift+clic = copier

**Question à l'utilisateur** : Quelle interaction préfères-tu ?
1. Deux zones (texte + bouton ▶)
2. Simple clic / Double clic
3. Clic / Shift+clic
4. Autre proposition

---

## Partie 2 : Analyse de cohorte par IA

Après une recherche retournant N patients, permettre à l'utilisateur d'obtenir un **résumé analytique de la cohorte** généré par IA.

---

## Fonctionnalité demandée

### 1. Bouton "📊 Analyser cette cohorte"

**Emplacement** : Sous le message de résultats (après "X patients trouvés avec Y")

**Conditions d'affichage** :
- Seulement si nb_patients > 0
- Seulement si un moteur IA est disponible (detectionMode !== 'standard' ou au moins un moteur actif)

**Action au clic** :
- Ouvre une modale avec loading
- Appelle le nouvel endpoint POST /ia/cohorte
- Affiche le résumé généré

---

### 2. Nouvel endpoint : POST /ia/cohorte

**URL** : `/ia/cohorte`

**Body** :
```json
{
    "moteur": "gpt4o",
    "patients": [
        {
            "age": 25,
            "sexe": "F",
            "oripathologies": "Béance Antérieure, Classe II Division 1",
            "commentaires": [...]
        },
        ...
    ],
    "criteres_recherche": "béance antérieure classe 2",
    "nb_total": 42
}
```

**Réponse** :
```json
{
    "resume": "Texte du résumé...",
    "statistiques": {
        "age_moyen": 28.5,
        "repartition_sexe": {"M": 18, "F": 24},
        "pathologies_frequentes": [
            {"pathologie": "Béance Antérieure", "count": 42, "pct": 100},
            {"pathologie": "Classe II", "count": 38, "pct": 90.5},
            ...
        ]
    },
    "moteur": "gpt4o",
    "temps_ms": 1234
}
```

---

### 3. Prompt système pour l'IA

```
Tu es un assistant médical spécialisé en orthodontie.
Tu analyses une cohorte de {nb_total} patients correspondant à la recherche "{criteres}".

DONNÉES DE LA COHORTE :
- Âge moyen : {age_moyen} ans
- Répartition : {nb_hommes} hommes, {nb_femmes} femmes
- Pathologies les plus fréquentes : {top_pathologies}

PATIENTS (échantillon de {nb_echantillon}) :
{liste_patients}

INSTRUCTIONS :
1. Fournis un résumé synthétique de la cohorte (3-5 phrases)
2. Identifie les tendances ou corrélations notables
3. Suggère des points d'attention cliniques
4. Si pertinent, compare avec les normes orthodontiques

Réponds en français, de manière professionnelle et concise.
```

---

### 4. Modale d'affichage du résumé

**Structure** :
- Header : "📊 Analyse de cohorte" + bouton fermer
- Stats visuelles : 
  - Compteur patients
  - Âge moyen avec graphique
  - Répartition H/F (bar chart simple)
  - Top 5 pathologies (bar chart horizontal)
- Résumé IA : texte formaté
- Footer : Bouton copier, bouton fermer

**Optionnel** : Export PDF/CSV des statistiques

---

## Fichiers à modifier

### server.py
- Ajouter endpoint POST /ia/cohorte
- Calculer les statistiques côté serveur
- Construire le prompt et appeler le LLM
- Limiter à un échantillon (ex: 50 patients max) pour éviter les prompts trop longs

### web9.html

**Pour les suggestions et sidebar** :
- Ajouter `<datalist id="searchSuggestions">` lié aux 3 inputs
- Fonction `updateSearchSuggestions()` 
- Modifier `renderRecentConversations()` pour ajouter bouton ▶
- Modifier la section Exemples pour ajouter bouton ▶
- Styles CSS pour le bouton d'exécution

**Pour l'analyse de cohorte** :
- Ajouter bouton "📊 Analyser" après les résultats
- Fonction `analyzeCohorte(patients, criteres)` 
- Fonction `showCohorteModal(response)`
- Styles pour la modale avec graphiques simples (CSS pur ou mini-charts)

---

## Contraintes techniques

- Limite de tokens : Ne pas envoyer plus de 50 patients au LLM
- Si > 50 patients : envoyer un échantillon représentatif + stats calculées
- Les stats (âge moyen, répartition, top pathologies) doivent être calculées côté serveur, pas par l'IA
- L'IA ne fait que l'analyse textuelle

---

## Fichiers PJ nécessaires

1. `Prompt_contexte2312.md` - Règles du projet
2. `server.py` - Version actuelle avec endpoints IA
3. `web9.html` - Version actuelle avec zone IA
4. `ia.csv` - Configuration des moteurs

---

## Évolutions futures possibles

1. **Comparaison de cohortes** : Comparer deux recherches différentes
2. **Export rapport** : Générer un PDF avec le résumé et les graphiques
3. **Détection d'anomalies** : Identifier les patients "atypiques" dans la cohorte
4. **Suivi temporel** : Si données historiques, analyser l'évolution

---

**FIN DU PROMPT**
