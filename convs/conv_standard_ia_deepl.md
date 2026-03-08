# Prompt conv_standard_ia_deepl V1.0.1 - 05/01/2026 21:30:49

# Conversation : standard&ia&deepl

## Objectif
Tester les différents modes de détection et les différentes langues dans KITVIEW.

---

## Échange 1 - 05/01/2026 20:15

### Question utilisateur
Analyse des logs serveur montrant :
- La langue non détectée pour "esprit es tu là" (normal car pas de tag)
- La langue détectée mais non affichée correctement pour "béance antérieure gauche"
- Absence des logs d'escalade (standard → standardia → standarddeepl, etc.)

Demande :
1. Corriger les logs pour afficher les escalades
2. Remplacer "rapide" par "standard" partout
3. Proposer un test montrant les 5 cas (standard, ia, standardia, standarddeepl, iadeepl)

### Analyse Claude
**Fichiers analysés :**
- `search.py` V1.0.20 - Module de recherche avec routage intelligent
- `server.py` V1.0.35 - API FastAPI
- `base25000.db` - Base de 25000 patients

**Question posée :** Le mode `ia` forcé doit-il aussi escalader vers DeepL si 0 résultats ?
- **Réponse utilisateur** : Option A (escalade vers DeepL même en mode IA forcé)

---

## Échange 2 - 05/01/2026 20:30

### Modifications effectuées

#### search.py V1.0.20 → V1.1.0

| Modification | Détail |
|--------------|--------|
| Constante `MODES_VALIDES` | `['rapide', 'ia']` → `['standard', 'ia']` |
| Paramètre `mode_detection` | Défaut `'standard'` au lieu de `'rapide'` |
| Modèles par défaut | `'rapide'` → `'standard'` dans `default_modeles` |
| Variable `parcours_detection` | Nouvelle liste traçant les escalades |
| Mode IA forcé | Ajout escalade DeepL si 0 résultats |
| Champ résultat | Nouveau `parcours_detection` dans la réponse |
| CLI | Affichage du parcours dans les résultats |
| Messages d'aide | Tous mis à jour avec "standard" |
| Rétrocompatibilité | Mapping `rapide` → `standard` pour ia.csv |

**Format du parcours :**
```
standard:6403                          → Résultat direct
standard:0→ia:42                       → Fallback IA (standardia)
standard:0→ia:0→deepl→standard:42      → Traduction puis standard (standarddeepl)
standard:0→ia:0→deepl→ia:42            → Traduction puis IA (iadeepl)
ia:42                                  → Mode IA forcé direct
ia:0→deepl→ia:42                       → Mode IA forcé avec traduction (iadeepl)
```

#### server.py V1.0.35 → V1.1.0

| Modification | Détail |
|--------------|--------|
| Validation modes | `['standard', 'ia']` au lieu de `['rapide', 'ia', 'compare', 'union']` |
| Rétrocompatibilité | `rapide` → `standard` automatique |
| `SearchRequest.mode_detection` | Défaut `"standard"` au lieu de `"rapide"` |
| Logs POST /search | Nouvelle ligne `Parcours: ...` |
| Commentaires | Tous mis à jour avec "standard" |

**Nouveau format de logs :**
```
POST /search - Question: 'bruxisme' Lang: auto
              Base: base25000.db, Mode détection: standard
              Session: xxx, IP: 127.0.0.1
POST /search - 6403 patient(s) en 229ms
              Parcours: standard:6403
              Auteur: cx, Langue: fr → fr
```

#### test_modes_detection.csv (nouveau)

Fichier de test avec 11 scénarios couvrant :
- Termes français directs (bruxisme, béance, classe ii)
- Termes anglais nécessitant traduction (deep bite, open bite)
- Termes allemands (Tiefbiss)
- Termes espagnols (mordida abierta)
- Termes japonais et chinois (歯軋り, 磨牙症)

---

## Fichiers livrés

| Fichier | Version | Description |
|---------|---------|-------------|
| `search.py` | V1.1.0 | Module recherche avec parcours_detection |
| `server.py` | V1.1.0 | API avec logs enrichis |
| `trouve.py` | V1.0.17 | Correction références 'rapide' → 'standard' |
| `test_modes_detection.csv` | - | Scénarios de test |

---

## Échange 3 - 05/01/2026 20:45

### Fichier trouve.py

**Problème identifié :** Deux occurrences de `'rapide'` restaient dans le code :
- Ligne 359 : `'cx' if mode == 'rapide' else 'eden'` (garde-fou)
- Ligne 380 : `'cx' if mode == 'rapide' else 'eden'` (résultat final)

**Correction :** Remplacé par `mode == 'standard'`

#### trouve.py V1.0.16 → V1.0.17

| Modification | Détail |
|--------------|--------|
| Ligne 359 | `mode == 'rapide'` → `mode == 'standard'` |
| Ligne 380 | `mode == 'rapide'` → `mode == 'standard'` |
| Rétrocompatibilité CLI | Conservée (lignes 444-447) |

---

## Les 5 modes de détection

| Mode | Parcours type | Déclencheur |
|------|---------------|-------------|
| **standard** | `standard:N` | Terme français trouvé directement |
| **ia** | `ia:N` | Mode IA forcé (`--mode=ia`) |
| **standardia** | `standard:0→ia:N` | Standard échoue, IA trouve |
| **standarddeepl** | `standard:0→ia:0→deepl→standard:N` | Traduction nécessaire, standard trouve |
| **iadeepl** | `ia:0→deepl→ia:N` ou `standard:0→ia:0→deepl→ia:N` | Traduction nécessaire, IA trouve |

---

## Prompts de recréation

### Pour recréer search.py V1.1.0
```
Fichiers PJ requis : 
- search.py V1.0.20
- Prompt_contexte2312.md
- conv_standard_ia_deepl.md

Demande : Modifier search.py pour :
1. Remplacer "rapide" par "standard" dans MODES_VALIDES et partout
2. Ajouter une variable parcours_detection = [] initialisée dans search()
3. Tracer chaque étape avec parcours_detection.append(f"mode:nb_resultats")
4. Ajouter "deepl" au parcours quand traduction DeepL utilisée
5. Ajouter escalade DeepL pour le mode IA forcé (si 0 résultats et langue != fr)
6. Retourner 'parcours_detection': '→'.join(parcours_detection) dans resultat_final
7. Afficher le parcours dans la CLI
```

### Pour recréer server.py V1.1.0
```
Fichiers PJ requis :
- server.py V1.0.35
- Prompt_contexte2312.md

Demande : Modifier server.py pour :
1. Remplacer modes_valides = ['rapide', 'ia', 'compare', 'union'] par ['standard', 'ia']
2. Mapper 'rapide' → 'standard' pour rétrocompatibilité
3. Ajouter logger.info(f"              Parcours: {parcours}") après le log des résultats
4. Extraire parcours = resultat.get('parcours_detection', '')
```

### Pour recréer trouve.py V1.0.17
```
Fichiers PJ requis :
- trouve.py V1.0.16
- Prompt_contexte2312.md

Demande : Corriger trouve.py pour :
1. Ligne 359 : remplacer mode == 'rapide' par mode == 'standard'
2. Ligne 380 : remplacer mode == 'rapide' par mode == 'standard'
3. Conserver la rétrocompatibilité CLI (lignes 444-447 qui mappent 'rapide' → 'standard')
```

---

*Document mis à jour : 05/01/2026 20:30*
