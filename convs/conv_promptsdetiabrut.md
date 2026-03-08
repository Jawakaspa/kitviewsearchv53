# Synthèse de conversation : promptsdetiabrut

## Métadonnées
- **Nom de la conversation** : promptsdetiabrut
- **Date de création** : 06/01/2026 - 14:32
- **Fichier source analysé** : detiabrut.py V1.0.3

---

## 📅 06/01/2026 14:32 - Extraction des prompts de detiabrut.py

### Question
Extraction de tous les prompts utilisés par `detiabrut.py` selon les différentes options de configuration.

### Réponse

#### Architecture des prompts

`detiabrut.py` utilise **deux prompts** :
1. **Prompt système** : configurable selon les référentiels actifs
2. **Prompt utilisateur** : fixe, contient la question

#### Référentiels disponibles (5)

| Référentiel | Description | Impact |
|-------------|-------------|--------|
| `tags` | Liste des tags pathologiques | Injecté dans prompt IA |
| `adjs` | Liste des adjectifs | Injecté dans prompt IA |
| `ages` | Patterns âge/sexe | Injecté dans prompt IA |
| `angles` | Seuils ANB/SNA/SNB | Injecté dans prompt IA |
| `mapping` | Post-traitement détecté→canonique | **Hors prompt** (post-processing) |

---

## PROMPT UTILISATEUR (fixe)

```
Analyse cette question et retourne le JSON: "{question}"
```

---

## PROMPT SYSTÈME - VERSION COMPLÈTE (mode `all`)

Quand **tous les référentiels sont actifs** (comportement par défaut) :

```
Tu es un analyseur de requêtes orthodontiques. Tu dois IDENTIFIER les termes présents dans la question.

=== MISSION ===
1. Détecter les TAGS (pathologies) de la liste ci-dessous
2. Détecter les ADJECTIFS qualifiant ces tags
3. Détecter les critères d'ÂGE et de SEXE
4. Détecter les demandes de COMPTAGE (combien, nombre de)
5. Détecter les ANGLES céphalométriques (ANB, SNA, SNB)

=== TAGS PATHOLOGIQUES ===
{contenu de tags_liste - jusqu'à 800 éléments}

=== ADJECTIFS ===
{contenu de adjs_liste - jusqu'à 200 éléments}

=== ANGLES CÉPHALOMÉTRIQUES ===
| Angle | Condition | Seuil | Tag résultant |
|-------|-----------|-------|---------------|
| ANB   | BETWEEN   | 0-4   | classe i squelettique |
| ANB   | >         | 4     | classe ii squelettique |
| ANB   | <         | 0     | classe iii squelettique |

=== CRITÈRES D'ÂGE ET SEXE ===
- "moins de 30 ans" → age < 30
- femme/fille → "F", homme/garçon → "M"

=== COMPTAGE ===
- "combien", "nombre de" → listcount = "COUNT"
- Sinon → listcount = "LIST"

=== FORMAT DE SORTIE (JSON strict) ===
{
    "langue": "fr",
    "listcount": "COUNT" ou "LIST",
    "criteres": [
        {"type": "tag", "detecte": "terme", "adjectifs": ["adj1"]},
        {"type": "age", "detecte": "...", "operateur": "<", "valeur": 30},
        {"type": "sexe", "detecte": "...", "valeur": "M|F"}
    ],
    "residu": "mots non reconnus"
}

RÈGLES: Retourne UNIQUEMENT du JSON valide.
```

---

## PROMPT SYSTÈME - VERSION BRUTE (mode `none`)

Quand **aucun référentiel n'est actif** :

```
Tu es un analyseur de requêtes orthodontiques. Tu dois IDENTIFIER les termes présents dans la question.

=== MISSION ===
1. Détecter les TAGS (pathologies) de la liste ci-dessous
2. Détecter les ADJECTIFS qualifiant ces tags
3. Détecter les critères d'ÂGE et de SEXE
4. Détecter les demandes de COMPTAGE (combien, nombre de)
5. Détecter les ANGLES céphalométriques (ANB, SNA, SNB)

=== TAGS PATHOLOGIQUES ===
(Utilise tes connaissances générales en orthodontie pour détecter les pathologies)

=== ADJECTIFS ===
(Utilise tes connaissances générales pour détecter les adjectifs qualificatifs)

=== ANGLES CÉPHALOMÉTRIQUES ===
(Angles non pris en charge dans ce mode)

=== CRITÈRES D'ÂGE ET SEXE ===
(Critères âge/sexe non pris en charge dans ce mode)

=== COMPTAGE ===
- "combien", "nombre de" → listcount = "COUNT"
- Sinon → listcount = "LIST"

=== FORMAT DE SORTIE (JSON strict) ===
{
    "langue": "fr",
    "listcount": "COUNT" ou "LIST",
    "criteres": [
        {"type": "tag", "detecte": "terme", "adjectifs": ["adj1"]},
        {"type": "age", "detecte": "...", "operateur": "<", "valeur": 30},
        {"type": "sexe", "detecte": "...", "valeur": "M|F"}
    ],
    "residu": "mots non reconnus"
}

RÈGLES: Retourne UNIQUEMENT du JSON valide.
```

---

## SECTIONS INDIVIDUELLES - ÉTAT ACTIF vs INACTIF

### Section TAGS

**Actif** (`+tags` ou `all`) :
```
=== TAGS PATHOLOGIQUES ===
{contenu de references['tags_liste'] - jusqu'à 800 éléments, un par ligne}
```

**Inactif** (`-tags` ou `none`) :
```
=== TAGS PATHOLOGIQUES ===
(Utilise tes connaissances générales en orthodontie pour détecter les pathologies)
```

---

### Section ADJECTIFS

**Actif** (`+adjs` ou `all`) :
```
=== ADJECTIFS ===
{contenu de references['adjs_liste'] - jusqu'à 200 éléments, un par ligne}
```

**Inactif** (`-adjs` ou `none`) :
```
=== ADJECTIFS ===
(Utilise tes connaissances générales pour détecter les adjectifs qualificatifs)
```

---

### Section ANGLES

**Actif** (`+angles` ou `all`) :
```
=== ANGLES CÉPHALOMÉTRIQUES ===
| Angle | Condition | Seuil | Tag résultant |
|-------|-----------|-------|---------------|
| ANB   | BETWEEN   | 0-4   | classe i squelettique |
| ANB   | >         | 4     | classe ii squelettique |
| ANB   | <         | 0     | classe iii squelettique |
```

**Inactif** (`-angles` ou `none`) :
```
=== ANGLES CÉPHALOMÉTRIQUES ===
(Angles non pris en charge dans ce mode)
```

---

### Section AGES

**Actif** (`+ages` ou `all`) :
```
=== CRITÈRES D'ÂGE ET SEXE ===
- "moins de 30 ans" → age < 30
- femme/fille → "F", homme/garçon → "M"
```

**Inactif** (`-ages` ou `none`) :
```
=== CRITÈRES D'ÂGE ET SEXE ===
(Critères âge/sexe non pris en charge dans ce mode)
```

---

### Référentiel MAPPING (post-traitement)

**Note** : Ce référentiel n'affecte **PAS** le prompt. Il contrôle le post-traitement des résultats IA.

**Actif** (`+mapping` ou `all`) :
- Utilise `tags_map` et `adjs_map` pour convertir les termes détectés vers leur forme canonique
- Exemple : "grincement" → "bruxisme"

**Inactif** (`-mapping` ou `none`) :
- Applique `.title()` aux termes détectés pour la présentation
- Exemple : "grincement" → "Grincement"

---

## EXEMPLES DE COMBINAISONS

### Cas 1 : `python detiabrut.py "bruxisme sévère" all`
- Prompt complet avec toutes les listes
- Mapping actif en post-traitement

### Cas 2 : `python detiabrut.py "bruxisme sévère" none`
- Prompt minimal (IA brute, connaissances générales)
- Pas de mapping, title() utilisé

### Cas 3 : `python detiabrut.py "bruxisme sévère" -tags`
- Tout sauf la liste des tags
- L'IA utilise ses connaissances pour les pathologies
- Mais a les listes d'adjectifs, angles, ages
- Mapping actif

### Cas 4 : `python detiabrut.py "bruxisme sévère" none +mapping`
- Prompt minimal (IA brute)
- Mais mapping actif pour normaliser les résultats

### Cas 5 : `python detiabrut.py "bruxisme sévère" -tags -adjs`
- Pas de listes tags ni adjectifs
- Angles et ages actifs
- Mapping actif

---

## SIGNATURE AUTEUR DANS LE JSON

Le champ `auteur` du résultat indique la configuration :

| Configuration | Signature |
|---------------|-----------|
| Tout actif | `openai/gpt-4o` |
| Tout désactivé | `openai/gpt-4o [none]` |
| Tags et mapping désactivés | `openai/gpt-4o [-mapping,-tags]` |
| Brut sauf mapping | `openai/gpt-4o [none,+mapping]` |

---

## Résumé des actions

✅ Analyse complète de `detiabrut.py` V1.0.3  
✅ Extraction du prompt système configurable  
✅ Extraction du prompt utilisateur  
✅ Documentation des 5 référentiels et leur impact  
✅ Exemples de toutes les combinaisons possibles  

---

## Fichiers liés

- **Source analysé** : `detiabrut.py` (pièce jointe fournie)
- **Dépendance** : `detia.py` (imports des fonctions de base)

---

## 📅 06/01/2026 16:15 - Correction séparation classe d'Angle / classe squelettique

### Problème identifié
Les synonymes squelettiques étaient mélangés avec les classes d'Angle (dentaires) dans `tags.csv` :
- `classe ii d'angle` contenait des synonymes comme "rétrognathie mandibulaire", "mandibule en retrait"
- `classe iii d'angle` contenait "prognathisme mandibulaire", "rétrognathie maxillaire", etc.

### Corrections apportées

#### 1. Nettoyage de `classe ii d'angle`
**Synonymes RETIRÉS** (squelettiques) :
- rétrognathie, rétrognathie mandibulaire, rétrognathe, rétrognathes
- mandibule en arrière, mandibule en retrait, mandibule reculée
- rétromandibulaire, rétromandibulaires, rétromandibulisme, rétromandibulismes
- rétrusion, rétroposition, rétropositions

**Synonymes CONSERVÉS** (dentaires) :
- classe 2, classe ii, disto-occlusion, distocclusion
- overjet augmenté, rétrusion dentaire, surplomb horizontal
- cl2, cl ii, cl.ii, malocclusion classe 2, rétroversion

#### 2. Nettoyage de `classe iii d'angle`
**Synonymes RETIRÉS** (squelettiques) :
- prognathisme mandibulaire, prognathie mandibulaire
- rétrognathie maxillaire, rétromaxillaire, rétromaxillaires
- mandibule avancée, mandibule en avant, mandibule proéminente
- maxillaire en arrière, maxillaire en retrait, maxillaire reculé
- mâchoire du bas en avant, menton en avant, menton proéminent
- hypoplasie, hypoplasie maxillaire, hypoplasies

**Synonymes CONSERVÉS** (dentaires) :
- classe 3, classe iii, mésio-occlusion, mésiocclusion
- delaire, masque de delaire, prognathie dentaire
- cl3, cl iii, malocclusion classe 3, sous-occlusion dentaire

#### 3. Nouveaux tags squelettiques créés

| Tag | Adjectifs | Synonymes |
|-----|-----------|-----------|
| `rétrognathie mandibulaire` | sévère,modéré | mandibule en arrière, mandibule en retrait, mandibule reculée, rétrognathe, rétrognathes, rétrognathie, rétromandibulaire, rétromandibulisme, menton en retrait, menton reculé, petit menton |
| `prognathie mandibulaire` | sévère,modéré | mandibule avancée, mandibule en avant, mandibule proéminente, prognathisme mandibulaire, mâchoire du bas en avant, menton en avant, menton proéminent, prognathe, promandibulie |
| `rétrognathie maxillaire` | sévère,modéré | maxillaire en arrière, maxillaire en retrait, maxillaire reculé, rétromaxillaire, hypoplasie maxillaire, hypoplasie, déficit maxillaire antérieur, face plate |
| `prognathisme maxillaire` | *(existait déjà)* | maxillaire avancé, maxillaire en avant, maxillaire proéminent, prognathie maxillaire |

#### 4. Création de `angles.csv`

```csv
# angles.csv V1.0.0
angle;condition;seuil_min;seuil_max;tag_resultat
ANB;BETWEEN;0;4;classe i squelettique
ANB;>;4;;classe ii squelettique
ANB;<;0;;classe iii squelettique
SNA;BETWEEN;80;84;maxillaire normopositionné
SNA;>;84;;prognathisme maxillaire
SNA;<;80;;rétrognathie maxillaire
SNB;BETWEEN;78;82;mandibule normopositionnée
SNB;>;82;;prognathie mandibulaire
SNB;<;78;rétrognathie mandibulaire
```

### Fichiers générés
- `tags.csv` V1.1.0 - Corrigé avec séparation stricte
- `angles.csv` V1.0.0 - Nouveau fichier de seuils

### TODO
- [ ] Mettre à jour `glossaire.csv` pour les traductions des nouveaux tags
- [ ] Mettre à jour le prompt dans `detiabrut.py` pour utiliser le nouveau format `angles.csv`

---

## 📅 06/01/2026 17:00 - Correction format angles.csv + seuils

### Problème identifié
Le format de `angles.csv` que j'avais créé était **incompatible** avec `detangles.py`.

### Format correct (conservé)
```
expression;operateur;seuil;tag_canonique;adjectifs_possibles;label
anb > {n}|anb>{n}|...;>;4;classe ii squelettique;...;Classe II squelettique
```

Les patterns utilisent `{n}` pour capturer les valeurs numériques via regex.

### Seuils corrigés selon le cours DR H.CHIBANI

| Angle | Ancien seuil | Nouveau seuil | Diagnostic |
|-------|--------------|---------------|------------|
| ANB BETWEEN | 0,4 | **2,4** | Classe I squelettique |
| ANB > | 4 | 4 (inchangé) | Classe II squelettique |
| ANB < | 0 | **2** | Classe III squelettique |
| SNA BETWEEN | 80,84 | **80,86** | Maxillaire normopositionné |
| SNA > | 84 | **86** | Prognathisme maxillaire |
| SNA < | 80 | 80 (inchangé) | Rétrognathie maxillaire |
| SNB BETWEEN | 78,82 | **77,83** | Mandibule normopositionnée |
| SNB > | 82 | **83** | Prognathie mandibulaire |
| SNB < | 78 | **77** | Rétrognathie mandibulaire |

### Tags ajoutés dans tags.csv V1.2.0
- `mandibule normopositionnée` - pour SNB entre 77° et 83°
- `maxillaire normopositionné` - pour SNA entre 80° et 86°

### Harmonisation terminologique
| angles.csv (ancien) | angles.csv (nouveau) | Cohérent avec tags.csv |
|---------------------|----------------------|------------------------|
| rétrognathisme maxillaire | rétrognathie maxillaire | ✓ |
| rétrognathisme mandibulaire | rétrognathie mandibulaire | ✓ |
| prognathisme mandibulaire | prognathie mandibulaire | ✓ |
| position maxillaire normale | maxillaire normopositionné | ✓ |
| position mandibulaire normale | mandibule normopositionnée | ✓ |

### Fichiers générés/mis à jour
- `angles.csv` V1.1.0 - Format conservé, seuils et tags corrigés
- `tags.csv` V1.2.0 - Ajout des 2 tags "normopositionné(e)"
- `AnglesANBSNASNB.txt` V1.0.0 - Texte condensé pour injection IA

### TODO
- [ ] Mettre à jour `glossaire.csv` pour les traductions
- [ ] Modifier `detiabrut.py` pour charger angles.csv dynamiquement
- [ ] Implémenter l'injection de `AnglesANBSNASNB.txt` quand `-tags` est actif

---

*Fin de synthèse - Version 1.2*
