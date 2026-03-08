# Prompt_gardefou.md

## Objectif

Créer `gardefou.py`, un module de vérification "dernière chance" qui empêche de retourner tous les patients quand la détection échoue.

---

## Problème résolu

Quand la détection (IA ou regex) échoue et retourne `criteres=[]`, le système retournait TOUS les patients, ce qui n'est presque jamais l'intention de l'utilisateur.

---

## Logique de vérification

### 1. L'utilisateur veut-il vraiment TOUS les patients ?

**Mots explicites** (français, anglais, allemand, espagnol, italien) :
- "tous", "tout", "toutes", "tous les patients"
- "all", "everyone", "everybody", "all patients"
- "alle", "alle patienten", "ohne filter"
- "todos", "todos los pacientes"
- "sans filtre", "liste complète", "l'ensemble des patients"

**Patterns regex** :
- `\btous\s+les\s+patients?\b`
- `\ball\s+patients?\b`
- `\beveryone\b`
- `\bsans\s+(aucun\s+)?filtre\b`

### 2. La question ressemble-t-elle à une recherche de pathologie ?

**Correspondance avec syntags.csv** (LIKE%) :
- Exacte : "bruxisme" = "bruxisme" → tag non détecté mais devrait l'être
- Préfixe : "brux" → "bruxisme" → suggestion
- Contenu : "gnath" → "rétrognathie" → suggestion

**Termes médicaux (heuristique)** :
- Suffixes : -isme, -ite, -ose, -ie, -pathie, -gnathie, -doncie
- Si la question contient un mot avec ces suffixes → contexte pathologique

**Contexte pathologique** :
- Mots : "avec", "ayant", "présentant", "souffrant", "diagnostiqué"
- Si présents → l'utilisateur cherche une pathologie, pas "tous"

---

## Décision finale

| Situation | Verdict | Action |
|-----------|---------|--------|
| Mots "tous" trouvés, pas de correspondance tag | ✅ intention_tous | Retourner tout |
| Mots "tous" + correspondance tag | ❌ ambigu | Demander clarification |
| Correspondance exacte non détectée | ❌ tag_exact_non_detecte | Suggérer le tag |
| Correspondance partielle | ❌ tag_partiel_suggere | Suggérer les tags proches |
| Contexte patho sans tag | ❌ contexte_patho_sans_tag | Demander reformulation |
| Question trop courte | ❌ question_trop_courte | Demander précision |
| Rien de clair | ❌ aucun_critere_clair | Bloquer par sécurité |

---

## Signature de la fonction principale

```python
def verifier_intention_tous(
    question: str,
    syntags_data: List[Dict] = None,  # [{stdtag, canontag}, ...]
    verbose: bool = False,
    debug: bool = False
) -> Dict[str, Any]:
    """
    Returns:
        {
            'intention_tous': bool,
            'raison': str,
            'message': str (message utilisateur si blocage),
            'suggestions': [str] (tags suggérés),
            'analyse': {
                'mots_tous_trouves': [str],
                'correspondances_tags': [dict],
                'contexte_patho': bool,
                'termes_medicaux': [str]
            }
        }
    """
```

---

## Intégration dans trouve.py

```python
from gardefou import verifier_intention_tous, charger_syntags_pour_gardefou

# Après exécution SQL
if nb_patients >= total_base * 0.8 and len(criteres_detectes) == 0:
    verdict = verifier_intention_tous(question, syntags_data, verbose=verbose)
    
    if not verdict['intention_tous']:
        return {
            'nb': 0,
            'patients': [],
            'erreur': verdict['message'],
            'suggestions': verdict['suggestions'],
            'garde_fou_actif': True
        }
```

---

## Fonctions auxiliaires

### charger_syntags_pour_gardefou(syntags_path)

Charge syntags.csv en format simplifié pour le garde-fou.

### _chercher_correspondance_tags(question_std, syntags_data)

Cherche si un mot de la question correspond (LIKE%) à un tag connu.

### _ressemble_terme_medical(mot)

Vérifie si un mot ressemble à un terme médical (suffixes courants).

### _detecter_contexte_pathologique(question_std)

Détecte si la question a un contexte de recherche pathologique.

---

## Usage CLI (tests)

```bash
python gardefou.py "tous les patients"
# ✅ Intention 'TOUS LES PATIENTS' confirmée

python gardefou.py "bruxisme"
# ❌ Le terme 'bruxisme' correspond au tag 'Bruxisme' mais n'a pas été détecté.

python gardefou.py "brux"
# ❌ Vouliez-vous dire : Bruxisme ?

python gardefou.py "patients avec xyz"
# ❌ La question semble concerner une pathologie mais aucun terme reconnu n'a été trouvé.
```

---

## Fichiers nécessaires en PJ

Pour recréer `gardefou.py` :
- `Prompt_contexte0412.md`
- `Prompt_gardefou.md` (ce fichier)

---

## Notes importantes

1. **Sécurité par défaut** : En cas de doute, bloquer plutôt que retourner tout
2. **Suggestions utiles** : Toujours proposer des alternatives si possible
3. **Messages clairs** : L'utilisateur doit comprendre pourquoi sa recherche a échoué
4. **Performance** : Cette vérification n'est appelée que si nb_patients ≈ total_base
