# Prompt conv_tagssaisis_propre V1.0.0 - 08/12/2025 19:43:02

# Synthèse conversation : tagssaisis propre

## Informations
- **Fichier** : conv_tagssaisis_propre.md
- **Projet** : Kitview - Application de recherche orthodontique multilingue

---

## Échanges

### 2025-12-08 18:41:17 - Correction du fichier tagssaisis.csv

**Question** : Correction du fichier tagssaisis.csv pour respecter la logique canonique (terme officiel → synonymes → adjectifs qualificatifs).

**Clarifications obtenues** :

1. **Synonymes = pointeurs vers le canonique** : Tout terme qui, s'il est détecté, doit ramener au tag canonique. Inclut les critères diagnostiques (ex: ANB>4°) si et seulement si l'implication est absolue.

2. **ANB et Classes squelettiques** :
   - ANB > 4° → Classe II squelettique (toujours vrai)
   - ANB < 0° → Classe III squelettique (toujours vrai)
   - ANB entre 0° et 4° → Classe I squelettique (plage normale)

3. **Rétrognathie/Prognathie** : Lignes canoniques séparées créées car décrivent quelle mâchoire est mal positionnée (pas le résultat final) :
   - Rétrognathie mandibulaire (mandibule en arrière)
   - Rétrognathie maxillaire (maxillaire en arrière)
   - Prognathisme mandibulaire (mandibule en avant)
   - Prognathisme maxillaire (maxillaire en avant)

4. **Format des adjectifs** : `adj_canonique1|syn1|syn2, adj_canonique2|syn3|syn4`
   - Premier terme = adjectif officiel
   - `|` sépare les synonymes de cet adjectif
   - `,` sépare les groupes d'adjectifs

5. **Compléments circonstanciels (ex: "nocturne", "des dents")** : Gardés comme synonymes d'adjectifs car ils seront éliminés par le moteur de détection, évitant des résidus parasites.

**Résultat** : Fichier tagssaisis.csv V1.1.0 corrigé avec :
- Classe I/II/III squelettiques avec variantes ANB
- Rétrognathies (mandibulaire/maxillaire)
- Prognathismes (mandibulaire/maxillaire)
- Béance avec adjectifs de localisation et sévérité
- Bruxisme avec compléments temporels
- Avulsion avec adjectifs de timing

---

## Fichiers générés

| Fichier | Description |
|---------|-------------|
| tagssaisis.csv | Fichier des tags canoniques orthodontiques V1.1.0 |

---

## Points en suspens

*Aucun pour l'instant*
