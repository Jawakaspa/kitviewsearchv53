# Prompt conv_cerbere_generalise V1.0.0 - 10/01/2026 07:48:58

# Conversation : Cerbère Généralisé

**Fichier :** conv_cerbere_generalise.md  
**Créé le :** 09/01/2026  
**Dernière mise à jour :** 09/01/2026 14:45 UTC

---

## Résumé

Cette conversation porte sur la généralisation de `cerbere.py` pour supporter plusieurs environnements cibles, l'externalisation des règles de dispatch, et l'ajout d'une fonctionnalité d'exécution distante de commandes Python.

---

## Historique des échanges

### 🕐 09/01/2026 14:32 UTC - Question initiale

**Demande :** Généraliser Cerbère sur 3 axes :
1. Multi-cibles : Déployer vers tests (`c:\cx`) ET prod (`c:\kitviewsearchV5`) simultanément ou séparément
2. Externalisation des règles : Règles de dispatch dans un fichier CSV externe
3. Exécution distante : Déposer des commandes Python dans un fichier et récupérer les résultats

**Questions de clarification posées par Claude :**
- Structure identique des sous-répertoires entre cibles ? → **Oui**
- Dispatch systématique ou au choix ? → **Au choix via 3 dossiers d'entrée**
- Sauvegardes dupliquées par cible ? → **Oui**
- Fichier de config unique ou par cible ? → **Par cible**
- Type de commandes Python → **Scripts complets (`python script.py args`)**
- Où déposer les fichiers d'exécution → **Dans les dossiers cerbere***

### 🕐 09/01/2026 14:45 UTC - Proposition complète

**Réponse de Claude :**

Architecture proposée avec 3 points d'entrée :
```
c:\cerberetests\    → c:\cx\ (+ cxsauve, cxarchives)
c:\cerbereprod\     → c:\kitviewsearchV5\ (+ kitviewsearchV5sauve, ...)
c:\cerbereall\      → Les deux cibles simultanément
```

Chaque dossier d'entrée (sauf `cerbereall`) contient :
- `grandlivre.csv` - Situation actuelle des versions
- `journal.csv` - Historique des versions
- `cerbere_config.csv` - Configuration et règles de dispatch

Format du fichier de configuration (`cerbere_config.csv`) :
- Section `cible` : définit le nom, chemin, sauve, archives, actif
- Section `regle` : règles de dispatch avec pattern, extension, destination

Format d'exécution distante (`*.exec.csv`) :
- Entrée : `commande;arguments`
- Sortie : `commande;arguments;statut;resultat;duree_sec`
- Fichier renommé en `*.exec.done.csv` après exécution

---

## Fichiers créés

| Fichier | Description |
|---------|-------------|
| `cerbere.py` | **Code v2.0.0 complet** (~1100 lignes) |
| `Prompt_cerbere_generalise.md` | Prompt complet de recréation v3.0.0 |
| `cerbere_config_tests_EXEMPLE.csv` | Exemple de config pour environnement tests |
| `cerbere_config_prod_EXEMPLE.csv` | Exemple de config pour environnement prod |
| `batch_EXEMPLE.exec.csv` | Exemple de fichier d'exécution distante |

---

## Décisions prises

1. **3 points d'entrée** : `cerberetests`, `cerbereprod`, `cerbereall`
2. **Versionning indépendant** : `grandlivre.csv` et `journal.csv` dans chaque dossier cerbere (sauf all)
3. **Règles externalisées** : Un fichier `cerbere_config.csv` par cible définissant à la fois la cible et les règles
4. **Exécution sécurisée** : Seules les commandes `python` sont autorisées
5. **Résultats persistants** : Fichiers `.exec.csv` renommés en `.exec.done.csv` avec résultats

---

### 🕐 09/01/2026 14:52 UTC - Développement cerbere.py v2.0.0

**Action :** Développement complet de cerbere.py v2.0.0

**Fonctionnalités implémentées :**

1. **Architecture multi-cibles**
   - 3 points d'entrée : `cerberetests`, `cerbereprod`, `cerbereall`
   - Classes `CibleConfig`, `PointEntree`, `RegleDispatch`
   - Chargement dynamique des configurations

2. **Règles externalisées**
   - Lecture du fichier `cerbere_config.csv` par point d'entrée
   - Pattern matching avec `fnmatch` pour les règles de dispatch
   - Évaluation dans l'ordre (première règle qui matche gagne)

3. **Exécution distante**
   - Détection des fichiers `*.exec.csv`
   - Exécution des commandes `python` uniquement (sécurité)
   - Génération du fichier `*.exec.done.csv` avec résultats
   - Timeout de 5 minutes par commande

4. **Versionning indépendant**
   - `grandlivre.csv` et `journal.csv` par point d'entrée
   - Pour `cerbereall`, utilise le versionning de `tests`

5. **Sauvegardes par cible**
   - Chaque cible a son propre répertoire de sauvegarde
   - Archives séparées par cible

6. **Création automatique**
   - Crée les dossiers d'entrée s'ils n'existent pas
   - Génère les `cerbere_config.csv` par défaut
   - Crée la structure complète des sous-répertoires

**Métriques du code :**
- 1329 lignes de code
- 3 dataclasses
- 40 fonctions
- Commentaires détaillés

---

## Prochaines étapes

1. ✅ **Valider la structure proposée** - Fait
2. ✅ **Développer cerbere.py v2.0.0** - Fait
3. **Tester avec environnement réel** - À faire
4. **Migrer depuis v1.4.6** - Copier les grandlivre/journal existants

---

## Fichiers à joindre pour recréer cerbere.py v2.x

| Fichier | Obligatoire | Description |
|---------|-------------|-------------|
| `Prompt_cerbere_generalise.md` | ✅ Oui | Prompt de recréation complet |
| `Prompt_contexte2312.md` | ✅ Oui | Contexte projet KITVIEW |
| `cerbere.py` (v1.4.6) | 📎 Recommandé | Base de code existante |
| `cerbere_config_tests_EXEMPLE.csv` | 📎 Recommandé | Exemple de configuration |
| `grandlivre.csv` | 📎 Optionnel | Structure du fichier de versions |

---

## Notes techniques

### Format des fichiers de configuration

Le fichier `cerbere_config.csv` utilise une structure clé-valeur avec le préfixe de type :
- Lignes `cible;...` : définition de la cible
- Lignes `regle;...` : règles de dispatch

Cette approche permet d'avoir un seul fichier par cible tout en séparant clairement les sections.

### Gestion de `cerbereall`

Le dossier `cerbereall` n'a pas ses propres fichiers `grandlivre.csv` / `journal.csv`. Le versionning est géré par les cibles individuelles, ce qui peut créer des décalages de version si un fichier a été déployé uniquement dans une cible avant.

---

**Fin de synthèse**
