# Prompt conv_web12_2026 V1.0.12 - 04/01/2026 08:22:35

# Synthèse de conversation : web12 2026

## Informations générales
- **Date de début** : 02/01/2026 ~19:45
- **Projet** : Kitview Search - Application de recherche multilingue orthodontique
- **Fichiers concernés** : web12.html

---

## Échange 1 — 02/01/2026 ~19:45

### Question
Corrections à apporter sur web12.html sans incrémenter le numéro de version :
1. Enlever les temporisations du logo Search quand la question arrive par l'URL
2. Corriger le texte "Search performed in French" en "Answers in French"
3. L'option d'afficher dans la langue d'origine ne fonctionne plus

### Réponse
Trois corrections appliquées (voir détails dans l'échange 2 pour la version finale).

---

## Échange 2 — 02/01/2026 ~07:45

### Question
Avec l'option "Auto → Origine" et une recherche en japonais, il reste encore trop de français dans l'interface. Le bandeau de langue devrait s'afficher tout le temps (régression). Seuls prénom et nom du patient devraient rester en français.

### Réponse
Corrections apportées :

#### 1. Bandeau de langue - Affiché TOUT LE TEMPS
- **`createLangInfoMessage`** : Supprimé les conditions qui masquaient le bandeau
- Le bandeau s'affiche maintenant pour toute langue ≠ français
- Message adapté selon `responseLanguage` :
  - Si `'fr'` → "Answers in French" (réponses forcées en français)
  - Si `'same'` → "Answers in original language" (réponses dans la langue d'origine)

#### 2. Textes UI internationalisés via t()
23 remplacements pour utiliser la fonction de traduction `t()` :
- `'📋 Copier'` → `t('Copier')`
- `'Cette recherche vous a-t-elle aidé ?'` → `t('...')`
- `'📊 Analyser cette cohorte'` → `t('...')`
- `'critères de recherche'` → `t('...')`
- `'Merci pour votre retour !'` → `t('...')`
- `'Commentaire'`, `'Annuler'`, `'Envoyer'`, `'Fermer'` → `t('...')`
- `'Analyse en cours...'` → `t('...')`
- `'Pathologies les plus fréquentes'` → `t('...')`
- `'Analyse IA'`, `'Tags'`, `'Commentaires cliniques'` → `t('...')`
- `'(pas de commentaire)'`, `'Aucun commentaire clinique disponible'` → `t('...')`
- `'Copié'` → `t('...')`

#### 3. Rappel : Temporisations (échange 1)
- `runSearchAnimation(skipDelays)` : Délais ignorés si requête via URL
- `searchPatients` : Exécution immédiate (setTimeout supprimé)

### ⚠️ Action requise
Pour que les traductions fonctionnent, il faut ajouter ces clés dans **glossaire.csv** :
```csv
fr;ja;en;de;es;it;pt;pl;ro;th;ar;cn
Copier;コピー;Copy;Kopieren;Copiar;Copia;Copiar;Kopiuj;Copiază;คัดลอก;نسخ;复制
Cette recherche vous a-t-elle aidé ?;この検索は役に立ちましたか？;Was this search helpful?;...
Analyser cette cohorte;このコホートを分析;Analyze this cohort;...
critères de recherche;検索条件;search criteria;...
critères;条件;criteria;...
Essayez avec d'autres critères;他の条件で試してください;Try with different criteria;...
Merci pour votre retour !;フィードバックありがとうございます！;Thank you for your feedback!;...
Commentaire;コメント;Comment;...
Annuler;キャンセル;Cancel;...
Envoyer;送信;Send;...
Fermer;閉じる;Close;...
Analyse en cours...;分析中...;Analysis in progress...;...
Pathologies les plus fréquentes;最も多い病理;Most frequent pathologies;...
Analyse IA;AI分析;AI Analysis;...
Tags;タグ;Tags;...
Commentaires cliniques;臨床コメント;Clinical comments;...
(pas de commentaire);(コメントなし);(no comment);...
Aucun commentaire clinique disponible;臨床コメントはありません;No clinical comment available;...
Copié;コピー完了;Copied;...
(facultatif);(任意);(optional);...
Quel type de problème souhaitez-vous signaler ?;どのような問題を報告しますか？;What type of problem would you like to report?;...
Veuillez fournir des détails :;詳細を入力してください：;Please provide details:;...
```

---

## Fichiers modifiés
| Fichier | Lignes modifiées |
|---------|------------------|
| web12.html | ~4442-4453 (MESSAGES_LANG_INFO), ~4462-4503 (createLangInfoMessage), ~4947-4950 (hasUrlQuery), ~4967-5000 (runSearchAnimation), ~5400, ~5485, ~5724, ~5953, et ~16 autres |

---

## Prompt de recréation complet de web12.html

```
PJ requises : web12.html (version originale V1.0.3), Prompt_contexte2312.md

Corrections à appliquer sur web12.html :

1. MESSAGES_LANG_INFO :
   - Remplacer "searchIn" par "answersIn" + "answersInOriginal"

2. createLangInfoMessage :
   - Supprimer les conditions qui masquent le bandeau
   - Garder uniquement : if (!langDetectee) et if (langDetectee === 'fr')

3. I18N : Ajouter I18N_CACHE_LOWER + améliorer t()

4. TRADUCTION PATHOLOGIES SIMPLIFIÉE (remplace l'algorithme glouton) :
   a) Simplifier tPatho() : traduire chaque terme avec t()
   b) Ajouter getTranslatedPathologies(patient) :
      - Utilise canontags + canonadjs si disponibles
      - Fallback sur oripathologies sinon
   c) Modifier createPatientCard() pour utiliser getTranslatedPathologies()
   d) Modifier createPatientMiniSummary() pour utiliser getTranslatedPathologies()

5. Chargement parallèle avec Promise.all()

6. Internationalisation UI avec t()

7. Appel /ia/cohorte avec paramètre langue

8. Modale cohorte - Internationaliser les textes

9. Traduction de "ans" dans l'âge

10. GARDE-FOU UI :
    - Après réception JSON : if (data.gardefou === true) → renderGardefouMessage()
    - Nouvelle fonction renderGardefouMessage()
```

## Prompt de recréation de server.py

```
PJ requises : server.py (version originale V1.0.26), Prompt_contexte2312.md

Modifications :

1. Chargement glossaire.csv - Supprimer tout filtre sur row_type :
   for row in reader:
       cle_fr = row.get('fr', '').strip()
       if cle_fr:  # Plus de filtre par type
           I18N_CACHE[cle_fr] = {}

2. Endpoint /ia/cohorte - Ajouter support multilingue :
   a) Ajouter le mapping LANGUES_NOMS au-dessus de CohorteRequest
   b) Ajouter `langue: Optional[str] = "fr"` au modèle CohorteRequest
   c) Modifier le prompt système pour utiliser la langue demandée :
      langue_nom = LANGUES_NOMS.get(request.langue, 'français')
      "IMPORTANT : Réponds UNIQUEMENT en {langue_nom}..."

3. Chargement commentaires.csv - Ajouter support multilingue :
   - Charger toutes les colonnes de langue (fr, en, de, es, it, ja, ...)
   - Stocker dans COMMENTAIRES_CACHE avec structure :
     {'commentaire': fr, 'traductions': {fr, en, ja, ...}, 'auteur': ...}

4. Endpoint /search - Enrichissement commentaires multilingue :
   - Récupérer lang_ui depuis resultat['response_lang'] ou resultat['lang']
   - Utiliser cache_entry['traductions'][lang_ui] si disponible
```

## Prompt de recréation de trouve.py

```
PJ requises : trouve.py (version originale V1.0.11), Prompt_contexte2312.md, gardefou.py

Modifications pour réactiver le garde-fou :

1. Ajouter l'import de gardefou (après ligne 33) :
   try:
       from gardefou import verifier_intention_tous, charger_syntags_pour_gardefou
       GARDEFOU_DISPONIBLE = True
   except ImportError:
       GARDEFOU_DISPONIBLE = False

2. Ajouter le cache des syntags (après ligne 102) :
   _SYNTAGS_GARDEFOU_CACHE = None
   SEUIL_GARDEFOU_POURCENTAGE = 80

3. Ajouter la fonction get_syntags_gardefou() :
   - Charge syntags.csv pour le garde-fou
   - Utilise le cache global

4. Ajouter l'ÉTAPE 4 : GARDE-FOU (après exécution SQL, avant construction résultat) :
   - Si GARDEFOU_DISPONIBLE AND len(criteres_detectes) == 0 AND nb_resultats > 100
   - Appeler verifier_intention_tous(question, syntags_data)
   - Si verdict['intention_tous'] == False → retourner nb=0 avec gardefou=True
```

## Prompt de recréation de lancesql.py

```
PJ requises : lancesql.py (version originale V1.0.3), Prompt_contexte2312.md

Modification unique - Ajouter canontags et canonadjs à l'extraction des patients :

Dans la fonction executer_sql(), section "if include_details", ajouter :
    "canontags": row['canontags'] if 'canontags' in row.keys() else '',
    "canonadjs": row['canonadjs'] if 'canonadjs' in row.keys() else ''

Ces champs permettent une traduction simplifiée des pathologies :
- canontags = liste de tags canoniques séparés par virgule
- canonadjs = liste d'adjectifs correspondants séparés par virgule
```

---

## Échange 3 — 02/01/2026 ~08:15

### Question
1. Donner la liste des mots français à ajouter dans glossaire.csv
2. Les pathologies (oripathologies) sont affichées en français au lieu d'être traduites dans la langue de l'interface

### Réponse

#### 1. Liste des textes français pour glossaire.csv (colonne fr)
```
(facultatif)
(pas de commentaire)
Analyse IA
Analyse en cours...
Analyser cette cohorte
Annuler
Aucun commentaire clinique disponible
Bienvenue
COMMENTAIRES CLINIQUES
Cette recherche vous a-t-elle aidé ?
Commentaire
Commentaires cliniques
Conversations récentes
Copier
Copié
Envoyer
Erreur réseau. La reconnaissance vocale nécessite une connexion Internet.
Exemples
Fermer
Merci pour votre retour !
Nouvelle recherche
Pathologies
Pathologies les plus fréquentes
Poser une autre question...
Quel type de problème souhaitez-vous signaler ?
Recherche en cours...
Rechercher un patient (ex: béance, classe 2, diabète...)
Rechercher un patient...
Réponse IA
Tags
Veuillez fournir des détails :
Veuillez saisir une question
critères
critères de recherche
```

#### 2. Traduction des pathologies via t()
4 modifications pour traduire les pathologies affichées :
- **Ligne 6445** : `tag.textContent = patho;` → `tag.textContent = t(patho);` (cartes patients)
- **Ligne 6146** : `label.textContent = p.pathologie;` → `label.textContent = t(p.pathologie);` (modale analyse)
- **Ligne 6233** : Texte copié → `t(p.pathologie)` dans le template string
- **Ligne 6839** : `capitalize(patho)` → `capitalize(t(patho))` (mini-résumé)

#### ⚠️ Prérequis pour que ça fonctionne
Les pathologies doivent être présentes dans **glossaire.csv** avec leurs traductions.
Exemple pour "Bruxisme" :
```csv
fr;ja;en;de;es;...
Bruxisme;歯軋り;Bruxism;Bruxismus;Bruxismo;...
Béance;開咬;Open bite;Offener Biss;Mordida abierta;...
```

---

## Échange 4 — 02/01/2026 ~10:30

### Question
1. Toujours le délai d'attente pour afficher le sélecteur de moteur dû à l'animation rouge/orange/vert
2. Pas de mieux sur les traductions des pathologies malgré la mise à jour du glossaire

### Réponse

#### 1. Chargement parallèle (DOMContentLoaded)
```javascript
const [basesResult, iaResult, illusResult, i18nResult] = await Promise.all([
    loadAvailableBases(hasUrlQuery),
    loadIAModels(),
    illustrationsManager.init(API_BASE_URL),
    loadI18n()
]);
```

#### 2. Fonction tPatho() initiale (mot par mot)
Première version qui traduit chaque mot séparément - insuffisant pour les tags composés.

#### 3. server.py - Tentative de filtrage par types
Essai de filtrage par `types_i18n = {'ui', 'tag', 'adj', ...}` - non fonctionnel car le type dans glossaire.csv est `t` et non `tag`.

---

## Échange 5 — 03/01/2026 ~08:00

### Question
Toujours pas de traduction des pathologies malgré les corrections précédentes. Le log serveur montre `ui:45` uniquement.

### Réponse

#### 1. server.py - Charger TOUTES les lignes du glossaire
Modification pour ne plus filtrer par type - charger toutes les lignes avec une clé `fr` :
```python
for row in reader:
    cle_fr = row.get('fr', '').strip()
    if cle_fr:  # Plus de filtre sur row_type
        I18N_CACHE[cle_fr] = {...}
```

#### 2. tPatho() - Algorithme glouton pour tags composés
**Problème identifié** : Les pathologies peuvent être des **tags composés** de 2+ mots :
- "Dentition Permanente" = 1 tag de 2 mots
- "Résorption Radiculaire" = 1 tag de 2 mots
- "Bruxisme Nocturne Sévère" = 1 tag + 2 adjectifs

L'ancienne fonction découpait tout en mots individuels, ce qui ne trouvait pas "dentition permanente" (le terme complet).

**Nouvel algorithme glouton** :
```javascript
function tPatho(pathologie, lang) {
    // 1. Essayer l'expression complète d'abord
    if (I18N_CACHE_LOWER[completeLower]) return trad;
    
    // 2. Sinon, chercher les plus longues correspondances
    const mots = pathologie.split(/\s+/);
    let i = 0;
    while (i < mots.length) {
        // Essayer des expressions de longueur décroissante
        for (let len = mots.length - i; len > 0; len--) {
            const expression = mots.slice(i, i + len).join(' ');
            if (I18N_CACHE_LOWER[expression.toLowerCase()]) {
                result.push(trad);
                i += len;
                break;
            }
        }
    }
    return result.join(' ');
}
```

**Exemple** : "Béance Antérieure Gauche Modérée"
1. Essaie "béance antérieure gauche modérée" → pas trouvé
2. Essaie "béance antérieure gauche" → pas trouvé
3. Essaie "béance antérieure" → pas trouvé
4. Essaie "béance" → **trouvé** → "がらんどう"
5. Continue à position 1 : "antérieure gauche modérée" → "antérieure gauche" → "antérieure" → **trouvé** → "前"
6. Continue : "gauche" → **trouvé** → "左"
7. Continue : "modérée" → **trouvé** → "控えめ"
8. Résultat : **"がらんどう 前 左 控えめ"**

---

## Échange 6 — 03/01/2026 ~09:00

### Question
Internationaliser la modale "Analyse de cohorte" :
1. UI de la modale avec t()
2. Analyse IA dans la langue courante (pas en français)

### Réponse

#### 1. server.py - Ajout du paramètre `langue` à /ia/cohorte

**Nouveau mapping des langues :**
```python
LANGUES_NOMS = {
    'fr': 'français', 'en': 'English', 'de': 'Deutsch', 
    'es': 'español', 'it': 'italiano', 'ja': '日本語',
    'pt': 'português', 'pl': 'polski', 'ro': 'română',
    'th': 'ไทย', 'ar': 'العربية', 'cn': '中文'
}
```

**Modification du modèle :**
```python
class CohorteRequest(BaseModel):
    moteur: Optional[str] = "gpt4o"
    patients: List[Dict[str, Any]]
    criteres_recherche: str
    nb_total: int
    langue: Optional[str] = "fr"  # NOUVEAU
```

**Modification du prompt système :**
```python
langue_nom = LANGUES_NOMS.get(request.langue, 'français')
# ...
prompt_systeme = f"""...
IMPORTANT : Réponds UNIQUEMENT en {langue_nom}, de manière professionnelle et concise."""
```

#### 2. web12.html - Passage de la langue et internationalisation UI

**Appel API avec langue :**
```javascript
body: JSON.stringify({
    moteur: moteur,
    patients: patientsData,
    criteres_recherche: criteres,
    nb_total: nbTotal,
    langue: currentUILang || 'fr'  // NOUVEAU
})
```

**Textes UI internationalisés :**
| Ancien | Nouveau |
|--------|---------|
| `📊 Analyse de cohorte` | `📊 ${t('Analyse de cohorte')}` |
| `Critères :` | `${t('Critères')} :` |
| `Patients :` | `${t('Patients')} :` |
| `Modèle :` | `${t('Modèle')} :` |
| `Temps :` | `${t('Temps')} :` |
| `Âge moyen` | `${t('Âge moyen')}` |
| `Répartition` | `${t('Répartition')}` |
| `Échantillon` | `${t('Échantillon')}` |

#### 3. Nouveaux textes à ajouter dans glossaire.csv (colonne fr)
```
Analyse de cohorte
Critères
Patients
Modèle
Temps
Âge moyen
Répartition
Échantillon
ans
```

---

## Échange 7 — 03/01/2026 ~09:30

### Question
1. Le mot "ans" n'est pas traduit dans l'âge (liste et détail patient)
2. Les commentaires cliniques sont affichés en français au lieu de la langue de l'interface

### Réponse

#### 1. web12.html - Traduction de "ans"
2 modifications :
- **Ligne 6483** (cartes patients) : `` `${Math.floor(patient.age)} ans` `` → `` `${Math.floor(patient.age)} ${t('ans')}` ``
- **Ligne 6890** (détail patient) : idem

#### 2. server.py - Commentaires multilingues

**a) Modification du chargement commentaires.csv :**
- Charger toutes les colonnes de langue (fr, en, de, es, it, ja, pt, pl, ro, th, ar, cn)
- Stocker dans COMMENTAIRES_CACHE avec structure :
```python
COMMENTAIRES_CACHE[patho] = {
    'commentaire': commentaire_fr,  # Rétrocompatibilité
    'traductions': {
        'fr': '...', 'en': '...', 'ja': '...', ...
    },
    'auteur': auteur
}
```

**b) Modification de l'enrichissement des patients :**
- Récupérer la langue d'interface depuis `resultat.get('response_lang')` ou `resultat.get('lang')`
- Utiliser `cache_entry['traductions'][lang_ui]` au lieu de `cache_entry['commentaire']`

#### 3. Structure requise pour commentaires.csv
Le fichier doit avoir des colonnes de traduction comme glossaire.csv :
```csv
oripathologie;commentaire;auteur;en;de;es;it;ja;pt;pl;ro;th;ar;cn
céphalométrie;Analyse céphalométrique...;Dr X;Cephalometric analysis...;Kephalometrische...;...
```

Si les colonnes de langue n'existent pas, le système utilise le fallback français.

---

## Échange 8 — 03/01/2026 ~14:15

### Question
Le garde-fou pour éviter de retourner tous les patients quand aucun critère n'est détecté ne fonctionne plus, ni en mode IA ni en mode standard.

### Diagnostic
**Problème identifié** : Le module `gardefou.py` existe mais n'était **jamais appelé** dans `trouve.py`. Le code passait directement de l'exécution SQL à la construction du résultat, sans vérifier si tous les patients étaient retournés par erreur.

Exemple : "Montre-moi les patients ayant une morsure" → "morsure" non reconnu → critères=[] → SQL sans WHERE → 25000 patients retournés.

### Réponse

#### Modification de trouve.py

**1. Ajout de l'import de gardefou (après ligne 33) :**
```python
# Import du garde-fou
try:
    from gardefou import verifier_intention_tous, charger_syntags_pour_gardefou
    GARDEFOU_DISPONIBLE = True
except ImportError:
    GARDEFOU_DISPONIBLE = False
```

**2. Ajout du cache et seuil (après ligne 102) :**
```python
# Cache global pour les syntags du garde-fou
_SYNTAGS_GARDEFOU_CACHE = None

# Seuil pour déclencher le garde-fou
SEUIL_GARDEFOU_POURCENTAGE = 80
```

**3. Ajout de la fonction get_syntags_gardefou() :**
```python
def get_syntags_gardefou() -> List[Dict]:
    """Retourne les syntags pour le garde-fou (avec cache)."""
    global _SYNTAGS_GARDEFOU_CACHE
    if _SYNTAGS_GARDEFOU_CACHE is None and GARDEFOU_DISPONIBLE:
        script_dir = Path(__file__).parent
        syntags_path = script_dir / "refs" / "syntags.csv"
        if syntags_path.exists():
            _SYNTAGS_GARDEFOU_CACHE = charger_syntags_pour_gardefou(str(syntags_path))
    return _SYNTAGS_GARDEFOU_CACHE or []
```

**4. Ajout de l'ÉTAPE 4 : GARDE-FOU (après exécution SQL, ~ligne 285) :**
```python
# === ÉTAPE 4 : GARDE-FOU ===
if GARDEFOU_DISPONIBLE and len(criteres_detectes) == 0 and nb_resultats > 100:
    syntags_data = get_syntags_gardefou()
    verdict = verifier_intention_tous(question, syntags_data, verbose, debug)
    
    if not verdict['intention_tous']:
        return {
            "nb": 0,
            "gardefou": True,
            "gardefou_raison": verdict['raison'],
            "gardefou_message": verdict['message'],
            "gardefou_suggestions": verdict.get('suggestions', []),
            ...
        }
```

#### Comportement après correction
- Si critères=[] ET nb_résultats > 100 → garde-fou activé
- Le garde-fou analyse la question pour vérifier si l'utilisateur voulait vraiment "tous"
- Si non → retourne `nb=0` avec `gardefou=True` et un message d'erreur/suggestions

#### Modification de web12.html pour afficher le message garde-fou

**1. Détection du garde-fou (après réception réponse JSON) :**
```javascript
if (data.gardefou === true) {
    addDebugLog(`⚠️ Garde-fou activé: ${data.gardefou_raison}`, 'warning');
    renderGardefouMessage(gardefouResponse);
    return;
}
```

**2. Nouvelle fonction renderGardefouMessage() :**
- Affiche un bandeau jaune d'avertissement avec icône ⚠️
- Montre le message explicatif du garde-fou
- Liste les suggestions cliquables (boutons qui relancent une recherche)

#### Nouveaux textes à ajouter dans glossaire.csv
```
ui;Aucun critère de recherche détecté;No search criteria detected;Keine Suchkriterien erkannt;...
ui;Votre recherche ne correspond à aucun terme reconnu;Your search does not match any recognized term;...
ui;Suggestions;Suggestions;Vorschläge;Sugerencias;Suggerimenti;提案;...
```

---

## Échange 9 — 03/01/2026 ~15:30

### Question
La traduction des pathologies avec l'algorithme glouton `tPatho()` est trop complexe. Proposition : utiliser directement les données structurées `canontags` + `canonadjs` qui sont déjà séparées dans la base, et les traduire simplement avec `t()`.

### Réponse

#### Analyse du problème
- **Avant** : `oripathologies` = chaîne combinée dynamiquement ("Bruxisme Nocturne Sévère")
- L'algorithme glouton devait deviner où couper → complexe et fragile
- **Après** : `canontags` = tag(s) séparés, `canonadjs` = adjectifs par tag
- Chaque terme canonique est dans le glossaire → traduction simple avec `t()`

#### Modifications

**1. lancesql.py — Ajouter canontags/canonadjs à l'extraction :**
```python
patients.append({
    ...
    "oripathologies": row['oripathologies'] if 'oripathologies' in row.keys() else '',
    "canontags": row['canontags'] if 'canontags' in row.keys() else '',
    "canonadjs": row['canonadjs'] if 'canonadjs' in row.keys() else ''
})
```

**2. web12.html — Nouvelle architecture simplifiée :**

a) **tPatho() simplifié** (fallback uniquement) :
```javascript
function tPatho(pathologie, lang = null) {
    if (!pathologie) return pathologie;
    const targetLang = lang || currentUILang || 'fr';
    if (targetLang === 'fr') return pathologie;
    
    // Traduire chaque terme séparément avec t()
    const termes = pathologie.trim().split(/\s+/);
    return termes.map(terme => t(terme) || terme).join(' ');
}
```

b) **Nouvelle fonction getTranslatedPathologies()** :
```javascript
function getTranslatedPathologies(patient) {
    const canontags = patient.canontags || '';
    const canonadjs = patient.canonadjs || '';
    
    // Utiliser données structurées si disponibles
    if (canontags) {
        const tags = canontags.split(',').map(s => s.trim());
        const adjsList = canonadjs.split(',').map(s => s.trim());
        
        return tags.map((tag, i) => {
            const translatedTag = t(tag);
            const adjs = adjsList[i] || '';
            const translatedAdjs = adjs.split(/\s+/).map(adj => t(adj)).join(' ');
            return translatedAdjs ? `${translatedTag} ${translatedAdjs}` : translatedTag;
        });
    }
    
    // Fallback sur oripathologies
    return oripathologies.split(',').map(p => tPatho(p.trim()));
}
```

c) **Modification des affichages** :
- `createPatientCard()` : utilise `getTranslatedPathologies(patient)`
- `createPatientMiniSummary()` : utilise `getTranslatedPathologies(patient)`
- Analyse cohorte : garde `tPatho()` car pathologies individuelles

#### Avantages de la nouvelle architecture
| Avant (glouton) | Après (structuré) |
|-----------------|-------------------|
| Algorithme complexe | Traduction directe |
| Fragile aux espaces | Données séparées |
| Glossaire doit contenir combos | Chaque terme = 1 entrée |
| Debug difficile | Comportement prévisible |

---

## Fichiers générés
- `lancesql.py` - Version avec canontags/canonadjs
- `web12.html` - Version avec getTranslatedPathologies()
- `server.py` - Version avec commentaires multilingues
- `trouve.py` - Version avec appel au garde-fou
- `conv_web12_2026.md` - Ce document de synthèse
