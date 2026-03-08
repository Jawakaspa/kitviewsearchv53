# conv_detection_archi

## Synthèse de la conversation

---

### 22/02/2026 ~13:18 — Documentation architecture chaîne de détection

**Question** : Créer un DOCX pour ingénieur documentant la chaîne de détection KITVIEW Search V5.2, incluant :
- Schéma d'architecture avec sortie vers jsonsql et lancesql
- Gestion des langues (traitement français uniquement dans trouve et sous-programmes)
- Fonctionnement détaillé des 2 modes de recherche (avec/sans IA)
- Différence entre detia et detiabrut
- Annexes : prompts système des modules IA
- Annexe 2 : problèmes identifiés lors des tests quentin.csv
- Section prochaines étapes (intégration bases KitView/Siméon, similarité prospects, recherche phonétique)

**Fichiers analysés** (14 modules Python) :
| Module | Rôle |
|--------|------|
| detfull.py | Exécution batch complète de tous les modules |
| detall.py V5.2 | Orchestrateur standard (8 sous-modules) |
| detcount.py | LIST/COUNT |
| detmeme.py | Similarités (même X) |
| detid.py | Identifiant patient (id XXX) |
| detangles.py | Angles céphalométriques |
| dettags.py | Tags pathologiques |
| detadjs.py | Adjectifs |
| detage.py | Âge et sexe |
| detia.py | Détection IA avec référentiels |
| detiabrut.py | Détection IA configurable |
| jsonsql.py | JSON → SQL |
| lancesql.py | Exécution SQL |

**Réponse** : Document DOCX de ~8 pages livré (detection_chain_v52.docx) contenant les 6 sections + 2 annexes demandées.
