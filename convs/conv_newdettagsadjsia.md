# Prompt conv_newdettagsadjsia V1.0.0 - 28/12/2025 17:21:27

# Synthèse Conversation : newdettagsadjsia

## Informations
- **Date** : 28 décembre 2025, ~11h00-11h45
- **Objet** : Adaptation de detadjs.py, dettags.py et detia.py pour la nouvelle structure de fichiers

---

## Contexte Initial

Le référentiel `tagsadjs.csv` a été scindé en deux fichiers séparés :
- **tags.csv** : colonnes `t;gn;as;pts` (tag, genre/nombre, adjectifs autorisés, patterns)
- **adjectifs.csv** : colonnes `a;f;mp;fp;pas` (formes accordées + patterns adjectifs)

Les fichiers intermédiaires `syntags.csv` et `synadjs.csv` sont supprimés car ils peuvent être générés à la volée en mémoire.

La notion de "synonyme" est remplacée par celle de "patterns" = synonymes unidirectionnels pointant vers le tag ou l'adjectif canonique.

---

## Questions de Clarification Posées

1. **Colonne `as` dans tags.csv** → C'est la liste des adjectifs autorisés pour ce tag
2. **Génération à la volée** → Oui, génération en mémoire au moment du chargement
3. **Format de sortie JSON** → Reste identique (canonique, sql, adjectifs[])
4. **Tri par longueur** → Oui, décroissant pour éviter les faux positifs ("à gauche" avant "gauche")
5. **detia.py** → Même logique, charge tags.csv et adjectifs.csv directement

---

## Travail Réalisé

### 1. detadjs.py (V4)
- **Fonction `charger_adjectifs()`** : Charge `adjectifs.csv` et génère en mémoire :
  - `lookup` : Dict {stdadj → canonadj} trié par longueur décroissante
  - `adjectifs` : Dict {canon_lower → info complète avec formes et patterns}
- **Fonction `detecter_adjectifs()`** : Prend maintenant `adjs_autorises` (liste) au lieu de `tag_canonique`
- Tri par longueur décroissante pour matcher les patterns multi-mots d'abord

### 2. dettags.py (V4)
- **Fonction `charger_tags()`** : Charge `tags.csv` et génère en mémoire :
  - `lookup` : Liste de {stdtag, canontag, nb_mots} triée par nb_mots décroissant
  - `tags` : Dict {canon_lower → {canon, gn, adjs_autorises, patterns}}
- Récupère automatiquement les adjectifs autorisés par tag depuis la colonne `as`
- Appelle `detadjs.detecter_adjectifs()` avec la liste des adjectifs autorisés

### 3. detia.py (V4)
- **Fonction `_charger_tags_csv()`** : Charge tags.csv pour le prompt IA
- **Fonction `_charger_adjectifs_csv()`** : Charge adjectifs.csv pour le prompt IA
- **Fonction `charger_references()`** : Remplace les anciens `syntags_map`/`synadjs_map` par `tags_map`/`adjs_map`
- Le prompt système utilise directement les listes générées
- Le post-traitement `_mapper_vers_canonique()` utilise les nouveaux mappings

---

## Fichiers Générés

| Fichier | Lignes | Description |
|---------|--------|-------------|
| detadjs.py | 660 | Détection adjectifs V4 |
| dettags.py | 710 | Détection tags V4 |
| detia.py | 771 | Détection IA V4 |

---

## Prompts de Recréation

### Pour recréer detadjs.py

**Fichiers à joindre en PJ :**
- `adjectifs.csv` (structure: a;f;mp;fp;pas)
- `Prompt_contexte2312.md`

**Prompt :**
```
Crée le module detadjs.py V4 pour détecter les adjectifs qualifiant un tag orthodontique.

ARCHITECTURE :
- Charge directement adjectifs.csv (colonnes: a;f;mp;fp;pas)
- Génère en mémoire la structure de recherche (pas de synadjs.csv)
- La colonne 'pas' contient les patterns (synonymes unidirectionnels)

FONCTION charger_adjectifs(fichier_csv) :
- Retourne un dict avec :
  - 'lookup': {stdadj: canonadj} trié par longueur décroissante
  - 'adjectifs': {canon_lower: {canon, formes, patterns, m, f, mp, fp}}

FONCTION detecter_adjectifs(question, adjs_autorises, position_tag, adjs_data) :
- adjs_autorises: liste des adjectifs autorisés (pas un tag canonique)
- Cherche dans une fenêtre de 5 mots autour du tag
- Retourne {'adjectifs': [...], 'mots_utilises': set()}

FORMAT SORTIE adjectifs:
{'detecte': str, 'canonique': str, 'standardise': str}

Respecter les conventions du projet (cartouche, UTF-8-SIG pour CSV, etc.)
```

### Pour recréer dettags.py

**Fichiers à joindre en PJ :**
- `tags.csv` (structure: t;gn;as;pts)
- `adjectifs.csv` (structure: a;f;mp;fp;pas)
- `Prompt_contexte2312.md`

**Prompt :**
```
Crée le module dettags.py V4 pour détecter les tags orthodontiques et leurs adjectifs.

ARCHITECTURE :
- Charge directement tags.csv (colonnes: t;gn;as;pts)
- Charge adjectifs.csv via detadjs.charger_adjectifs()
- Génère en mémoire la structure de recherche (pas de syntags.csv)
- La colonne 'pts' contient les patterns tags
- La colonne 'as' contient les adjectifs autorisés pour ce tag

FONCTION charger_tags(fichier_tags, fichier_adjs) :
- Retourne tuple (tags_data, adjs_data)
- tags_data: {'lookup': [{stdtag, canontag, nb_mots}], 'tags': {canon_lower: info}}

FONCTION detecter_tags(question, tags_data, adjs_data) :
- Parcourt les tags du plus long au plus court
- Pour chaque tag trouvé, appelle detadjs.detecter_adjectifs avec adjs_autorises
- Retourne {'criteres': [...], 'residu': str, 'question_standardisee': str}

FORMAT SORTIE critères:
{
    'type': 'tag',
    'detecte': str,
    'canonique': str,
    'label': str,
    'sql': {'colonne': 'canontags', 'operateur': '=', 'valeur': str},
    'adjectifs': [{'detecte', 'canonique', 'sql': {...}}]
}
```

### Pour recréer detia.py

**Fichiers à joindre en PJ :**
- `tags.csv` (structure: t;gn;as;pts)
- `adjectifs.csv` (structure: a;f;mp;fp;pas)
- `ia.csv` (configuration moteurs IA)
- `Prompt_contexte2312.md`

**Prompt :**
```
Crée le module detia.py V4 pour la détection par IA des critères orthodontiques.

ARCHITECTURE V4 :
- Charge directement tags.csv et adjectifs.csv (plus de syntags/synadjs)
- Génère les listes pour le prompt IA + mappings pour post-traitement

FONCTION charger_references() :
- Charge tags.csv → tags_liste + tags_map {std: canon}
- Charge adjectifs.csv → adjs_liste + adjs_map {std: canon}
- Charge ages.csv et angles.csv comme texte

FONCTION _construire_prompt_systeme(references) :
- Utilise tags_liste et adjs_liste pour le prompt

FONCTION _mapper_vers_canonique(resultat_ia, references) :
- Utilise tags_map et adjs_map pour le post-traitement

FONCTION detecter_tout(question, references, model) :
- Compatible avec l'ancienne signature
- Retourne le même format JSON que detall.py

Modes d'appel API : OpenAI direct ou Eden AI selon le modèle.
```

---

## Points d'Attention

1. **Tri par longueur** : Essentiel pour éviter les faux positifs (ex: "à gauche" vs "gauche")
2. **Adjectifs autorisés** : La colonne `as` de tags.csv filtre les adjectifs applicables
3. **Patterns unidirectionnels** : Un pattern pointe vers le canonique, pas l'inverse
4. **Signature préservée** : Le format JSON de sortie est identique à l'ancienne version

---

## Prochaines Étapes Suggérées

1. Tester les programmes avec des fichiers de test
2. Vérifier la compatibilité avec `detall.py`
3. Supprimer les anciens fichiers `syntags.csv` et `synadjs.csv` une fois validé
