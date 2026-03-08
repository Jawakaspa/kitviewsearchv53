# Prompt conv_audit1000 V1.0.1 - 05/01/2026 14:56:34

# Conversation audit1000 - Synthèse

## Résumé

Analyse d'audit comparant la détection locale (detall) vs IA (detia) sur 1001 questions orthodontiques, suivie d'implémentation de corrections et améliorations.

---

## Historique des échanges

### 05/01/2026 09:15 - Analyse associations sémantiques et routage

**Demande** : 
1. Fusionner les associations sémantiques dans tags.csv
2. Gérer le cas adultes/enfants
3. Implémenter un routage intelligent avec emojis indicateurs
4. Ajouter fallback traduction DeepL

**Réponse** :
- Confirmé fusion des associations (prognathisme mandibulaire→classe iii, rétrusion→classe ii, tong e→dysfonction linguale, proalvéolie→bipro, spacing→diastème)
- Pour adultes/enfants : conversion en critère d'âge dans le prompt IA (pas en tag)
- Emojis de routage : 🤖 (IA), 🌐 (traduction), 🤖🌐 (les deux)
- Nouveau champ `question_affichee` pour affichage dans la barre bleue

### 05/01/2026 09:52 - Implémentation des modifications

**Fichiers créés** :
- `tags.csv` V1.0.2 - Associations sémantiques fusionnées
- `detia.py` V1.0.26 - Prompt amélioré, règle adultes/enfants, normalisation
- `search.py` V1.0.15 - Routage intelligent avec fallback

---

## Modifications apportées

### 1. tags.csv V1.0.2

**Fusions réalisées** :
| Terme source | Fusionné dans | Patterns ajoutés |
|--------------|---------------|------------------|
| prognathisme mandibulaire | classe iii d'angle | prognathisme mandibulaire, mandibule avancée, mandibule en avant, mandibule proéminente, prognathie mandibulaire, mâchoire du bas en avant, menton en avant, menton proéminent, machoire qui avance |
| rétrusion | classe ii d'angle | rétrusion, rétroversion |
| tong e | dysfonction linguale | tong e, tong-e |
| proalvéolie | bipro | proalvéolie |
| spacing | diastème | spacing |

### 2. detia.py V1.0.26

**Améliorations du prompt** :
- Liste complète des tags CANONIQUES (pas les patterns) pour forcer le matching exact
- Règle explicite adultes/enfants → critères d'âge :
  - "adultes"/"adulte" → `{"type": "age", "operateur": ">=", "valeur": 18}`
  - "enfants"/"enfant" → `{"type": "age", "operateur": "<", "valeur": 12}`
- Instruction explicite : "NE JAMAIS créer de tag dentition permanente pour adultes"

**Normalisation** :
- Tous les tags normalisés en minuscules en sortie (`.lower()`)
- Adjectifs également normalisés

**Nouveau dans charger_references()** :
- Retourne maintenant `tags_canoniques` et `adjs_canoniques` (listes des formes canoniques uniquement)

### 3. search.py V1.0.15

**Routage intelligent** (mode rapide par défaut) :
```
Question originale
    ↓
[1] Recherche RAPIDE (detall)
    ↓
Si 0 résultat → [2] Recherche IA (detia) + 🤖
    ↓
Si toujours 0 ET langue != fr → [3] Traduction DeepL + retry + 🌐
    ↓
Résultat final avec emojis appropriés
```

**Nouveaux champs dans le résultat** :
- `indicateurs_routage` : Emojis seuls ("🤖", "🌐", "🤖🌐")
- `question_affichee` : Question + emojis pour affichage UI
- `mode_effectif` : Mode réellement utilisé ("rapide", "ia (fallback)", "ia (après traduction)")

**Emojis** :
- 🤖 = Fallback IA utilisé
- 🌐 = Traduction DeepL utilisée  
- 🤖🌐 = Les deux

---

## Métriques de l'audit initial (rappel)

| Métrique | Valeur |
|----------|--------|
| Concordance listcount | 99.7% |
| Concordance tags exacte | 85.7% |
| Concordance Jaccard | 89.3% |
| Latence detall | 0 ms |
| Latence detia | ~2089 ms |

---

## Fichiers à tester

1. **Test unitaire detia.py** :
```bash
python detia.py "patients adultes avec bruxisme"
# Doit donner : critère age >= 18 + tag bruxisme (pas de tag "dentition permanente")

python detia.py "avec torque sévère"
# Doit donner : tag torque + adjectif sévère
```

2. **Test routage search.py** :
```bash
python search.py base1000.db "xyz123"  
# Doit montrer fallback IA puis traduction si configuré

python search.py base1000.db "bruxisme"
# Mode rapide, pas de fallback
```

3. **Rejouer l'audit complet** :
```bash
python pipeline.py audit 1000 verbose
```

---

## Prompts de recréation

### Prompt pour recréer detia.py

```
Crée le fichier detia.py V1.0.26 pour la détection de critères orthodontiques par IA.

Fonctionnalités clés :
1. Charge tags.csv et adjectifs.csv pour construire le prompt
2. Prompt amélioré avec liste des tags CANONIQUES (pas les patterns)
3. Règle adultes/enfants : convertir en critères d'âge, jamais en tags
   - "adultes"/"adulte" → age >= 18
   - "enfants"/"enfant" → age < 12
4. Normalisation des tags en minuscules en sortie
5. Support OpenAI et Eden AI avec retry/backoff
6. Mode batch pour traiter des fichiers CSV

Fichiers à joindre :
- Prompt_contexte2312.md (contexte projet)
- tags.csv (référentiel tags)
- adjectifs.csv (référentiel adjectifs)
- ia.csv (configuration moteurs IA)
```

### Prompt pour recréer search.py

```
Crée le fichier search.py V1.0.15 pour la recherche multilingue avec routage intelligent.

Fonctionnalités clés :
1. Routage intelligent avec fallback automatique :
   - Recherche RAPIDE (detall) en premier
   - Si 0 résultat → fallback IA + emoji 🤖
   - Si toujours 0 et langue != fr → traduction DeepL + retry + emoji 🌐
2. Nouveaux champs : indicateurs_routage, question_affichee
3. Résolution sémantique via glossaire.csv
4. Traduction des résultats vers la langue de sortie
5. Logging complet avec indicateurs de routage

Fichiers à joindre :
- Prompt_contexte2312.md (contexte projet)
- trouve.py (orchestrateur recherche)
- glossaire.csv (résolution sémantique)
- messages.csv (messages multilingues)
- pathoori.csv (traductions pathologies)
```

### Prompt pour modifier tags.csv

```
Modifie tags.csv pour fusionner les associations sémantiques identifiées dans l'audit :

1. prognathisme mandibulaire → ajouter dans patterns de "classe iii d'angle"
2. rétrusion → ajouter dans patterns de "classe ii d'angle"  
3. tong e, tong-e → ajouter dans patterns de "dysfonction linguale"
4. proalvéolie → ajouter dans patterns de "bipro"
5. spacing → ajouter dans patterns de "diastème"

Fichiers à joindre :
- tags.csv actuel
```

---

## Actions restantes

- [ ] Tester detia.py avec questions "adultes"
- [ ] Tester routage search.py avec termes inconnus
- [ ] Rejouer audit complet pour mesurer amélioration convergence
- [ ] Vérifier que les tags fusionnés sont bien détectés

---

## Fichiers livrés

| Fichier | Version | Description |
|---------|---------|-------------|
| tags.csv | 1.0.2 | Associations sémantiques fusionnées |
| detia.py | 1.0.26 | Prompt amélioré, règle adultes/enfants |
| search.py | 1.0.15 | Routage intelligent avec fallback |

---

*Dernière mise à jour : 05/01/2026 09:52*
