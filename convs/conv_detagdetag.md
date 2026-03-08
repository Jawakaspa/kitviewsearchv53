# Prompt conv_detagdetag V1.0.3 - 08/12/2025 23:34:38

# conv_detagdetag.md

## Synthèse de la conversation "detagdetag"

---

### 08/12/2025 ~21:00 - Début de conversation

**Contexte** : Suite de conversations interrompues. L'objectif initial était de créer `dettags.py` et `detadjs.py` mais un bug dans `fr2tags.py` a été identifié et doit être corrigé en priorité.

---

### 08/12/2025 21:15 - Tentatives de correction fr2tags.py (V1.0.5, V1.0.6)

**Problème initial** : Le programme retraduisait tous les termes (282) au lieu de seulement les nouveaux (6) quand on ajoutait des synonymes.

**Tentatives échouées** :
- V1.0.5 : Indexation par `canontag` extrait → problème de matching
- V1.0.6 : Colonne `canonfr` explicite → décalages de position persistants

**Diagnostic** : Le problème venait de l'indexation par position qui cassait dès que le nombre de termes différait entre `frtags` et `{lang}tags`.

---

### 08/12/2025 23:10 - Solution définitive : Glossaire Global (V1.1.0)

**Principe** : Clé = `(terme_fr_std, langue, type)` → Un terme français = une seule traduction par langue, peu importe la pathologie.

**Avantages** :
- **Robuste** : Pas de dépendance à la position ou au canonfr
- **Optimisé** : Un terme traduit une fois n'est jamais retraduit (glossaire cumulatif)
- **Simple** : Glossaire réutilisable

**Résultats** :
- Run 1 (après V1.0.6) : 240 nouveaux termes traduits
- Run 2, 3, 4 (V1.1.0) : `glossaire OK` partout, **0 nouveau**, **0.0 secondes**
- Glossaire final : **408 termes uniques**

**Fichier livré** : `fr2tags.py` V1.1.0

---

### Points clarifiés

1. **Traductions UI dans JSON** (pour dettags/detadjs) : OUI, inclure traduction du canontag dans la langue détectée
2. **commun.csv** : 3 colonnes indépendantes (combien, devant, langues), pas de lien entre lignes
3. **Adjectifs "devant"** : Si "sévère" peut précéder en FR, ses traductions aussi dans les autres langues

---

### Décisions prises (héritées des conversations précédentes)

| Point | Décision | Implication |
|-------|----------|-------------|
| Position adjectifs "devant" | Colonne `devant` dans `commun.csv` | Lecture de commun.csv pour les adjectifs précédant le tag |
| Source de vérité | `tagssaisis.csv` → pipeline → `syntags.csv` + `synadjs.csv` | Les fichiers lookup sont générés, pas sources |
| Adjectifs orphelins | Ignorer | Un adjectif sans tag n'a pas de sens |
| Structure JSON | Validée avec traductions UI | À enrichir pour les messages multilingues |
| Signature dettags | CLI : `python dettags.py "question"` → JSON formaté | Mode autonome pour tests |
| Signature detadjs | CLI : `python detadjs.py synonyme_tag "question"` | Recherche autour du 1er synonyme trouvé |
| Algorithme recherche | `synonyme in question` (substring) | Plus long d'abord, pas de découpe par mots |
| Prétraitement | Standardisation + espace début/fin + retrait virgules | À faire côté appelant |
| Chevauchements | Plus long d'abord | Logique cohérente avec le tri |

---

### Fichiers du projet

| Fichier | Rôle | État |
|---------|------|------|
| `fr2tags.py` | Internationalise tagsfr.csv → tags.csv | **V1.1.0 - OK** ✅ |
| `tagssaisis.csv` | Source manuelle des tags/synonymes/adjectifs | Fourni |
| `tagsfr.csv` | Tags français générés par saisis2fr.py | Fourni |
| `tags.csv` | Tags multilingues (sortie de fr2tags.py) | **Généré** ✅ |
| `commun.csv` | Configuration (langues, adjectifs devant, etc.) | Fourni |
| `dettags.py` | Détection des tags dans une question | À créer |
| `detadjs.py` | Détection des adjectifs autour d'un tag | À créer |
| `syntags.csv` | Lookup synonymes → canontag | Nécessaire pour dettags |
| `synadjs.csv` | Lookup synonymes adjectifs | Nécessaire pour detadjs |

---

### Prochaines étapes

1. ~~Corriger fr2tags.py~~ ✅ **FAIT**
2. **Créer `detlang.py`** → Détection de la langue (conversation séparée)
3. **Migrer `detcount.py`, `detage.py`, `detall.py`** → Nouveau format JSON (conversation séparée)
4. Créer `dettags.py` et `detadjs.py` (après les migrations)

---

### Prompts disponibles pour recréer les programmes

| Programme | Prompt | PJ nécessaires |
|-----------|--------|----------------|
| `fr2tags.py` | `Prompt_fr2tags.md` | `Prompt_contexte0412.md`, `commun.csv`, `tagsfr.csv` |
| `detlang.py` | `Prompt_detlang.md` | `Prompt_contexte0412.md`, `tags.csv`, `commun.csv` |
| `detcount.py`, `detage.py`, `detall.py` | `Prompt_detcount_detage_detall.md` | `Prompt_contexte0412.md`, `identcount.py`, `identages.py`, `identall.py`, `ages.csv`, `commun.csv` |
| `dettags.py`, `detadjs.py` | `Prompt_dettags_detadjs.md` | `Prompt_contexte0412.md`, `tags.csv`, `commun.csv` |

---

### Format JSON unifié des critères (référence rapide)

```json
{
  "type": "age|sexe|tag|adjectif|count",
  "detecte": "texte détecté",
  "canonique": "forme canonique (tags/adjs)",
  "label": "libellé utilisateur",
  "sql": {
    "colonne": "nom_colonne",
    "operateur": "=|<|>|<=|>=|BETWEEN|IN",
    "valeur": "valeur ou [v1, v2]"
  }
}
```

---

**FIN DU DOCUMENT** - Dernière mise à jour : 08/12/2025 23:45
