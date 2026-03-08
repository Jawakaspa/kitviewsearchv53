# Prompt conv_cxcharge V1.0.0 - 15/12/2025 17:47:44

# conv_cxcharge.md

**Synthèse de conversation** - Projet KITVIEW  
**Nom de la conversation** : cxcharge  
**Dernière mise à jour** : 15/12/2025 10:47

---

## Résumé

Cette conversation porte sur la création du programme `cxchargepats.py` qui charge des patients depuis un fichier CSV vers une base SQLite avec gestion des pathologies à préfixes progressifs.

---

## Échanges

### Échange 1 - 15/12/2025 10:47

**Question** : Exécuter le prompt `Prompt_cxchargepats.md` pour créer le programme de chargement patients.

**Clarifications demandées par Claude** :
1. **Nom du fichier** : Le prompt mentionnait `chargepatients.py` et `cxchargepats.py` → **Réponse** : utiliser `cxchargepats.py`
2. **Colonnes du CSV** : Vérification que les 31 colonnes sont bien présentes → **Confirmé**
3. **Colonne `pathologies`** : Confirmé qu'elle est calculée à partir de `oripathologies` après normalisation
4. **Module `standardise.py`** : Fourni par l'utilisateur (version corrigée ne touchant plus aux "-")
5. **Colonnes `canontags` et `canonadjs`** : Présentes dans le CSV mais pas dans la table `patients` initiale → **Décision** : créer 2 nouvelles colonnes dans la table `patients`

**Analyse de compatibilité effectuée** sur :
- `cherche.py` ✓ Compatible
- `suche.py` ✓ Compatible  
- `identall.py` ✓ Compatible
- `server.py` ✓ Compatible
- `index.html` ✓ Compatible

**Fichier créé** : `cxchargepats.py`

**Caractéristiques du programme** :
- 31 colonnes CSV en entrée
- 32 colonnes dans table `patients` (+ `canontags`, `canonadjs`)
- Gestion des préfixes progressifs pour pathologies
- Import dynamique de `standardise.py`
- Barre de progression avec tqdm-style
- Commit par ligne pour robustesse
- Index FTS5 pour recherche full-text

---

## Fichiers créés/modifiés

| Fichier | Version | Description |
|---------|---------|-------------|
| `cxchargepats.py` | 0.0.0 | Programme de chargement patients CSV → SQLite |

---

## Fichiers de référence utilisés

| Fichier | Description |
|---------|-------------|
| `Prompt_cxchargepats.md` | Prompt de création (v2.0.0) |
| `Prompt_contexte0412.md` | Contexte projet |
| `standardise.py` | Module de normalisation de texte |
| `cherche.py` | Module de recherche (compatibilité vérifiée) |
| `suche.py` | Module de recherche multilingue (compatibilité vérifiée) |
| `identall.py` | Orchestrateur de détection (compatibilité vérifiée) |
| `server.py` | API FastAPI (compatibilité vérifiée) |
| `index.html` | Interface web (compatibilité vérifiée) |

---

## Points techniques importants

1. **Structure de la table `patients`** : 32 colonnes incluant `canontags` et `canonadjs`
2. **Préfixes progressifs** : "béance antérieure gauche" → ["beance", "beance anterieure", "beance anterieure gauche"]
3. **Encodage** : UTF-8-SIG attendu, warning si autre
4. **Commit par ligne** : Pour robustesse en cas d'erreur
5. **Import dynamique** : `standardise.py` chargé via `importlib.util`

---

## Prochaines étapes potentielles

- [ ] Tester le programme avec un fichier CSV réel
- [ ] Vérifier les performances sur 25000 patients
- [ ] Valider le fonctionnement avec les programmes existants
