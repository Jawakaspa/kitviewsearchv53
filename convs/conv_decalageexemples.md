# Prompt conv_decalageexemples V1.0.2 - 07/01/2026 15:19:52

# Synthèse conversation : décalageexemples

## Session du 07/01/2026 15:47 → 19:30

### Problème initial identifié

Décalages multiples entre `webparams.html` et `web18.html` concernant les exemples de recherche et plusieurs bugs.

### Bugs corrigés

#### web19.html V1.0.3 (DERNIER)

| Bug | Cause | Correction |
|-----|-------|------------|
| **Erreur JSON.parse** | webparams sauvegarde en texte brut, web19 faisait JSON.parse | Nouvelle fonction `parseExamples()` qui gère les 2 formats |
| **Conversations récentes perdues** | `conversationHistory: []` ne chargeait pas localStorage | `JSON.parse(localStorage.getItem('conversationHistory') \|\| '[]')` |
| **Clé exemples différente** | webparams: `searchExamples` vs web18: `examples` | Harmonisé sur `searchExamples` partout |
| **Bouton Voir fait COUNT** | Regex incomplet | Ajout de tous les mots de commun.csv colonne "combien" |
| **Base non affichée** | `updateBaseSubtitle()` pas appelé | Appel dans catch + appel forcé après init |
| **Chips langue vides** | Timing de génération | Appel forcé à `generateLangChips()` après init |

#### webparams.html V1.1.1 (DERNIER)

| Modification | Détail |
|--------------|--------|
| Libellé exemples | "Exemples de recherche (démo et suggestions)" |
| DEFAULT_EXAMPLES | 12 exemples multilingues |
| Libellé I18n | "Choix de la langue" (au lieu de "Internationalisation") |
| **Option Micro** | Ajout de 🎤 Recherche vocale avec checkbox A |

### Fichiers livrés

- `web19.html` V1.0.3
- `webparams.html` V1.1.1
- `conv_decalageexemples.md`

### Commandes utiles pour tester (Console F12)

**Mettre les exemples multilingues :**
```javascript
localStorage.setItem('searchExamples', `patients qui grincent des dents
歯ぎしり
Nombre de patients avec linguo-version avec déviation maxillaire ?
Number of patients with linguo-version with maxillary deviation?
Patientes souffrant de béance antérieure et avec classe II
Patientinnen mit Frontzahnlücke und Klasse II
Patientes de moins de 39 ans présentant un encombrement et une rotation dentaire antihoraire
Pazienti di età inferiore ai 39 anni con affollamento e rotazione dei denti in senso antiorario
ado diabétique avec problème de bruxisme
Adolescente diabético com problema de bruxismo
Patientes d'environ 14 ans avec malocclusion et bruxisme sévère
Pacientes de unos 14 años con maloclusión y bruxismo severo`);
location.reload();
```

**Masquer le bouton langue :**
```javascript
localStorage.setItem('bandeauI18n', 'false');
localStorage.setItem('activeI18n', 'false');
location.reload();
```

**Masquer le micro :**
```javascript
localStorage.setItem('activeMicro', 'false');
location.reload();
```

**Vérifier une valeur :**
```javascript
localStorage.getItem('searchExamples')
localStorage.getItem('bandeauI18n')
```

### Prompt de recréation

**Fichiers nécessaires en PJ :**
- web18.html
- webparams.html (V1.0.8)
- commun.csv

**Demande :**
```
Créer web19.html et webparams.html avec les corrections suivantes :

1. Bug conversations récentes : charger conversationHistory depuis localStorage au lieu de []
2. Harmoniser clé localStorage exemples sur 'searchExamples' (web18 utilisait 'examples')
3. Mettre à jour DEFAULT_EXAMPLES avec les exemples multilingues de commun.csv
4. Améliorer le bouton Voir pour retirer tous les mots COUNT de commun.csv colonne "combien"
5. Ajouter affichage base sous "Search" (élément baseSubtitle avec CSS)
6. Retirer "avec critères de recherche" du bandeau COUNT
7. Changer libellé webparams en "Exemples de recherche (démo et suggestions)"
8. Renommer "Internationalisation" en "Choix de la langue"
9. Forcer generateLangChips() et updateBaseSubtitle() après init
10. Ajouter fallback base dans le catch de loadAvailableBases
11. Créer fonction parseExamples() pour gérer texte brut ET JSON
12. Ajouter option "Recherche vocale" (activeMicro) dans webparams
```
