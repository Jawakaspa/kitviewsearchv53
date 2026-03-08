# Prompt_web9_i18n_ia.md

## Objectif

Améliorer l'application de recherche orthodontique multilingue avec :
1. **Internationalisation complète** (tout en japonais quand langue=ja)
2. **Affichage des pathologies** sur les cards patients
3. **Zone de chat IA** dans le détail patient
4. **Correction API /ia** pour la gestion des moteurs actifs/inactifs

---

## Contexte projet

Application de recherche multilingue sur 25 000+ patients orthodontiques.
- Backend : FastAPI (server.py)
- Frontend : HTML/JS (web9.html, web9params.html)
- Données : SQLite + CSV de référence
- Langues supportées : fr, en, de, es, it, ja, pt, pl, ro, th, ar, cn

---

## Fichiers joints obligatoires

1. **Prompt_contexte2312.md** - Règles du projet (encodage, versioning, etc.)
2. **server.py** - API FastAPI actuelle
3. **web8.html** - Interface web actuelle (base pour web9)
4. **web8params.html** - Page paramètres actuelle
5. **glossaire.csv** - Glossaire multilingue (à enrichir avec type `ui`)
6. **commentaires.csv** - Commentaires cliniques par pathologie
7. **ia.csv** - Configuration des moteurs IA

---

## Étape 1 : Enrichir glossaire.csv avec les textes UI

### Action
Ajouter des entrées de type `ui` dans glossaire.csv pour tous les textes d'interface.

### Structure
```csv
type;fr;en;de;es;it;ja;pt;pl;ro;th;ar;cn
ui;Nouvelle recherche;New search;Neue Suche;Nueva búsqueda;Nuova ricerca;新しい検索;Nova pesquisa;Nowe wyszukiwanie;Căutare nouă;การค้นหาใหม่;بحث جديد;新搜索
```

### Textes à traduire

**Navigation & Actions :**
| Clé FR | EN | JA |
|--------|----|----|
| Nouvelle recherche | New search | 新しい検索 |
| CONVERSATIONS RÉCENTES | RECENT CONVERSATIONS | 最近の会話 |
| EXEMPLES | EXAMPLES | 例 |
| Poser une autre question... | Ask another question... | 別の質問をする... |
| Copier | Copy | コピー |
| Page suivante | Next page | 次のページ |
| Page précédente | Previous page | 前のページ |

**Résultats :**
| Clé FR | EN | JA |
|--------|----|----|
| patients | patients | 患者 |
| trouvé(s) | found | 見つかりました |
| avec | with | で |
| critères de recherche | search criteria | 検索条件 |
| en | in | で |
| ms | ms | ms |
| affichés | displayed | 表示中 |
| tous | all | すべて |
| ans | years old | 歳 |

**Feedback :**
| Clé FR | EN | JA |
|--------|----|----|
| Cette recherche vous a-t-elle aidé ? | Was this search helpful? | この検索は役に立ちましたか？ |

**Card détail :**
| Clé FR | EN | JA |
|--------|----|----|
| COMMENTAIRES CLINIQUES | CLINICAL COMMENTS | 臨床コメント |
| Pathologies | Pathologies | 病理 |
| Votre question pour l'IA... | Your question for AI... | AIへの質問... |
| Demander à l'IA | Ask AI | AIに質問する |

**Modale IA :**
| Clé FR | EN | JA |
|--------|----|----|
| Réponse IA | AI Response | AI回答 |
| Fermer | Close | 閉じる |

### Livrable
- glossaire.csv enrichi avec toutes les langues traduites

---

## Étape 2 : Modifier server.py

### 2.1 Modifier GET /ia
Retourner **tous** les moteurs (actifs ET inactifs) avec tous les champs :
```json
{
  "moteurs": [
    {
      "moteur": "gpt4o",
      "via": "openai",
      "actif": "O",
      "complet": "gpt-4o",
      "cout": "$$$",
      "notes": "Modèle principal OpenAI",
      "image": "https://..."
    },
    ...
  ],
  "count": 16,
  "count_actifs": 10
}
```

### 2.2 Ajouter PUT /ia/{moteur}
Modifier le champ `actif` d'un moteur dans ia.csv :
```
PUT /ia/gpt4o
Body: {"actif": "N"}
Response: {"status": "ok", "moteur": "gpt4o", "actif": "N"}
```

### 2.3 Ajouter POST /ia/ask
Interroger un LLM avec contexte patient :
```json
// Request
{
  "moteur": "gpt4o",
  "patient": {
    "nom": "Guillaume Moulin",
    "prenom": "Guillaume",
    "age": 19,
    "sexe": "M",
    "oripathologies": "Béance Antérieure Gauche Modérée, Infraclusion",
    "commentaires": [...]
  },
  "question": "Quel traitement recommandez-vous ?"
}

// Response
{
  "reponse": "Pour ce patient présentant...",
  "moteur": "gpt4o",
  "temps_ms": 1234
}
```

### 2.4 Ajouter GET /i18n
Retourner les textes UI traduits depuis glossaire.csv :
```json
{
  "ui": {
    "Nouvelle recherche": {
      "fr": "Nouvelle recherche",
      "en": "New search",
      "ja": "新しい検索",
      ...
    },
    ...
  }
}
```

### Livrable
- server.py modifié avec les 4 endpoints

---

## Étape 3 : Modifier web9.html

### 3.1 Système i18n
- Charger les textes UI via `GET /i18n` au démarrage
- Fonction `t(cle)` qui retourne le texte dans la langue courante
- Remplacer tous les textes en dur par des appels à `t()`

### 3.2 Affichage oripathologies sur cards
- Sur la card fermée : afficher `oripathologies` du patient
- En **gras** : les pathologies qui correspondent aux critères de recherche
- Format : liste horizontale séparée par des virgules

### 3.3 Zone IA dans le détail
- Ajouter en bas de la card détaillée :
  - Un `<textarea>` pour la question utilisateur
  - Un bouton "🤖 IA" (ou icône robot)
- Au clic :
  - Envoyer `POST /ia/ask` avec contexte patient + question
  - Afficher la réponse dans une **modale**
  - Modale avec : texte réponse, signature "GPT-4o", bouton copier (icône 📋), bouton fermer

### 3.4 Commentaires cliniques multilingues
- Utiliser la colonne de langue appropriée depuis commentaires.csv
- Le serveur doit enrichir les commentaires avec la bonne langue

### Livrable
- web9.html avec internationalisation complète et zone IA

---

## Étape 4 : Modifier web9params.html

### 4.1 Section moteurs IA
- Charger tous les moteurs via `GET /ia` (actifs ET inactifs)
- Afficher une grille de checkboxes avec :
  - Logo du moteur (image)
  - Nom du moteur
  - Notes
  - Checkbox activé/désactivé
- Au changement : `PUT /ia/{moteur}` pour persister

### 4.2 Gestion d'erreur
- Afficher message clair si API échoue
- Permettre retry

### Livrable
- web9params.html fonctionnel avec gestion des moteurs IA

---

## Spécifications techniques

### Encodage
- Fichiers .py : UTF-8 sans BOM
- Fichiers .csv : UTF-8-SIG avec BOM
- Séparateur CSV : `;`

### Versioning
```python
__pgm__ = "nom_du_programme.py"
__version__ = "0.0.0"
__date__ = "01/01/1970 00:00"
```

### API ia.csv structure
```csv
moteur;via;actif;complet;cout;notes;image
gpt4o;openai;O;gpt-4o;$$$;Modèle principal OpenAI;https://...
```

### Séparation pathologies
- Dans `oripathologies` : virgule (`,`)
- Exemple : "Béance Antérieure, Infraclusion, Bruxisme"

---

## Ordre d'exécution recommandé

1. **glossaire.csv** - Base pour l'i18n
2. **server.py** - APIs nécessaires pour le frontend
3. **web9.html** - Interface principale
4. **web9params.html** - Page paramètres

Valider chaque étape avant de passer à la suivante.

---

## Notes importantes

- Ne jamais écraser les fichiers utilisateur protégés
- Respecter les conventions de nommage (pas d'underscore dans les noms de fichiers CSV)
- Les commentaires cliniques sont dans commentaires.csv avec colonnes par langue
- Le champ `oripathologies` est déjà retourné par l'API `/search`
- La modale IA doit avoir un bouton copier avec icône (évite traduction)

---

**FIN DU PROMPT**
