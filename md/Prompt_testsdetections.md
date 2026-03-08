# Prompt de continuation : testsdetections

## Contexte

Cette conversation fait suite à **conv_phrasecorrecte** où nous avons :
1. Créé `exquis.csv` (74 patterns de phrases cadavres exquis)
2. Créé `tags2synta.py` qui génère `syntags.csv` et `synadjs.csv`
3. Défini le pipeline complet de détection de tags

Tu viens de créer `dettags.py` et `detadjs.py` qui sont prêts à être testés.

## Objectif de cette conversation

Créer des **données de test** pour valider la chaîne de détection :

### 1. Détection de langue
Générer des questions de test dans les 4 langues (fr, en, de, th) qui permettent de détecter automatiquement la langue à partir des synonymes présents dans `tags.csv`.

### 2. Détection de tags + adjectifs
Une fois la langue détectée, valider que `dettags.py` et `detadjs.py` détectent correctement les tags et leurs adjectifs qualificatifs.

## Fichiers de référence (PJ obligatoires)

| Fichier | Description |
|---------|-------------|
| `Prompt_contexte.md` | Contexte général du projet Kitview |
| `tags.csv` | Référence multilingue des tags (11 tags × 4 langues) |
| `syntags.csv` | Lookup stdtag → canontag français |
| `synadjs.csv` | Lookup stdadj → canonadj français + tag parent |
| `dettags.py` | Programme de détection de tags (à tester) |
| `detadjs.py` | Programme de détection d'adjectifs (à tester) |
| `conv_phrasecorrecte.md` | Synthèse de la conversation précédente |

## Tags disponibles dans tags.csv (11 tags)

| Tag canonique français | Type |
|------------------------|------|
| Classe I squelettique | p |
| Classe II squelettique | p |
| Classe III squelettique | p |
| rétrognathie mandibulaire | p |
| rétrognathie maxillaire | p |
| Prognathisme mandibulaire | p |
| Prognathisme maxillaire | p |
| béance | p |
| Bruxisme | p |
| avulsion | p |

## Adjectifs disponibles (par tag)

| Tag | Adjectifs français |
|-----|-------------------|
| Classe I squelettique | idéale, parfaite, harmonieuse |
| Classe II squelettique | division 1, division 2 |
| rétrognathie mandibulaire | sévère, modérée |
| rétrognathie maxillaire | sévère, modéré |
| Prognathisme mandibulaire | sévère, modéré |
| Prognathisme maxillaire | sévère, modéré |
| béance | antérieure, postérieure, latérale, gauche, droite, sévère, modérée |
| Bruxisme | nocturne, diurne, des dents, sévère, modéré |
| avulsion | immédiate, différée, programmée |

## Langues supportées

- **fr** : Français
- **en** : Anglais  
- **de** : Allemand
- **th** : Thaï

## Livrables attendus

1. **testquestions.csv** : Questions de test multilingues avec résultats attendus
   - Structure : `langue;question;tags_attendus;adjs_attendus`
   
2. **Script de test** (optionnel) : Pour automatiser la validation

## Contraintes

- Les questions doivent utiliser des synonymes variés (pas toujours la forme canonique)
- Mélanger des questions simples (1 tag) et complexes (2-4 tags)
- Inclure des cas avec et sans adjectifs
- Tester les cas limites (synonymes proches, ambiguïtés)

## Exemple de questions attendues

```csv
langue;question;tags_attendus;adjs_attendus
fr;Quels patients ont une béance antérieure sévère ?;béance;antérieure,sévère
en;Find patients with Class II skeletal division 1;Classe II squelettique;division 1
de;Zeige mir Patienten mit Bruxismus nachts;Bruxisme;nocturne
th;ค้นหาผู้ป่วยที่มีช่องว่างด้านหน้า;béance;antérieure
fr;Patients avec rétrognathie mandibulaire modérée et béance latérale gauche;rétrognathie mandibulaire,béance;modérée,latérale,gauche
```

---

**conv: testsdetections**
