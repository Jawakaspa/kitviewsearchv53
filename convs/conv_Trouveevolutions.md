# Prompt conv_Trouveevolutions V1.0.1 - 19/12/2025 19:03:08

# Conversation : Trouveevolutions

## Résumé

Session de modifications sur trouve.py : mode compare, contrôle JSON verbose, alignement tableau, et traitement batch amélioré avec DictReader.

---

## Échanges

### 19/12/2025 16:45 UTC - Modifications trouve.py (V1)

**Demande :** 
Modifier trouve.py avec 3 évolutions :
1. Renommer le mode `mix` en `compare`
2. Afficher le JSON complet uniquement avec `--verbose`
3. Corriger l'alignement du tableau de comparaison

**Fichiers fournis :**
- generequestion.py (générateur de questions)
- trouve3.py (version antérieure)
- trouve4.py (version avec mode "mix")

**Réponse :**
Création de trouve.py (1015 lignes) avec :
- `mix` → `compare` partout
- JSON conditionnel via paramètre `verbose`
- Tableau corrigé avec fonction `cell()` et largeur fixe W=33

---

### 19/12/2025 17:15 UTC - Corrections batch CSV

**Demande :**
Corriger 3 irritants :
1. Chercher les .db dans `bases/` par défaut
2. Chercher les .csv dans `tests/` par défaut
3. Détecter la colonne "question" par nom et conserver toutes les colonnes

**Fichier fourni :** testgeneres100.csv

**Réponse :**
Modification de `traiter_fichier_batch()` :
- Utilise `csv.DictReader` pour lire par nom de colonne
- Détecte la colonne "question" (insensible à la casse)
- Conserve toutes les colonnes originales
- Cherche nb_attendu dans `nb_resultats` ou `nb_attendu`
- Cherche ids_attendus dans `ids_10`, `ids_attendus` ou `ids`
- Affichage : `✓ [  5/  5] question...`

**Fichier produit :** trouve.py (1086 lignes)

---

## Fichiers générés

| Fichier | Description | Lignes |
|---------|-------------|--------|
| trouve.py | Orchestrateur avec mode compare et batch amélioré | 1086 |

---

## Prompt de recréation trouve.py

```
Créer trouve.py, orchestrateur du pipeline de recherche patients.

PIPELINE :
Question → Détection (detall.py ou detia.py) → JSON → SQL (jsonsql.py) → Exécution (lancesql.py) → Résultats

MODES DE DÉTECTION :
- "traditionnel" : detall.py (regex, synonymes, rapide)
- "ia" : detia.py (Claude via Eden AI)
- "compare" : Exécute les deux et compare côte à côte
- "union" : Fusionne les résultats (A ∪ B)

FONCTIONS PRINCIPALES :
- rechercher(question, db_path, mode, references, include_details, verbose, debug) → dict
- rechercher_compare(question, db_path, ...) → dict avec 'traditionnel' et 'ia'
- rechercher_union(question, db_path, ...) → dict avec fusion A ∪ B
- traiter_fichier_batch(fichier_entree, db_path, mode, ...) → (nb_traitees, nb_ok, fichier_sortie)

TRAITEMENT BATCH :
- Utilise csv.DictReader pour lire par nom de colonne
- Détecte la colonne "question" (insensible à la casse)
- Conserve toutes les colonnes originales dans le fichier de sortie
- Cherche nb_attendu dans colonnes nb_resultats/nb_attendu
- Cherche ids_attendus dans colonnes ids_10/ids_attendus/ids
- Ajoute colonnes : nb_obtenu, match_nb, ids_obtenu, match_ids, temps_ms, residu, erreur

CHEMINS PAR DÉFAUT :
- Fichiers .db : cherche dans bases/ si non trouvé
- Fichiers .csv : cherche dans tests/ si non trouvé

AFFICHAGE :
- _afficher_resultat_standard(resultat, no_details, verbose) : résultat simple
- _afficher_comparaison_compare(resultat) : tableau côte à côte avec alignement corrigé (fonction cell() avec W=33)
- _afficher_resultat_union(resultat) : détails fusion

CONTRÔLE JSON :
- Sans --verbose : affiche "💡 JSON complet disponible avec --verbose"
- Avec --verbose : affiche le JSON complet

CLI (ordre libre des arguments) :
python trouve.py base100.db "question" [mode] [--verbose] [--debug] [--no-details] [--json]
python trouve.py base100.db testgeneres100.csv [mode]

CHAMP AUTEUR dans résultat :
- "cx" : detall.py
- "eden/claude-sonnet-3.7" : detia.py
- "cxgti" : mode union

Respecter Prompt_contexte0412.md (encodage, cartouche, séparateurs CSV).
```

**Pièces jointes requises :** Prompt_contexte0412.md
