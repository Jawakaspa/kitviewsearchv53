## Prompt_contexte_light

Contexte projet : recherche multilingue sur 25 000+ patients d'orthodontie. Utilisateurs en France. Philosophie TDD ou autres projets de type création automatique de présentations par exemples.

---

## Reporting hebdomadaire.

Nouveauté très importante : à partir de maintenant note tout ce que je fais avec toi sur tous les projets pour me fournir chaque lundi une synthèse de ce que j'ai fait la semaine passée.

---

## Versionning détaillé

****Format SemVer** *

**MAJOR.MINOR.PATCH** (ex: v1.2.3)

- MAJOR : Changements incompatibles (breaking changes)
- MINOR : Ajouts rétrocompatibles
- PATCH : Corrections de bugs rétrocompatibles

La date dans le cartouche est celle de la création de la version.

Tu gères les versions et tu décides des versions MINOR et PATCH mais pas de MAJOR que je gère.

Chaque fichier .py commence par les lignes suivantes **avant les imports** :

```python
#*TO*#
__pgm__ = "nom_du_programme.py"
__version__ = version
__date__ = date
```

L'affichage initial rappelle la version :

```python
def main():
    print(f"{__pgm__} V{__version__} - {__date__}")
```

---

## Contraintes techniques

- **Python 3.13+** uniquement, aucun downgrade
- Exécution `python script.py` ou `.cmd` (aucun PowerShell)
- Scripts indépendants du chemin (`%~dp0`). Déploiement final : AWS
- Temps de réponse < 10s. Barres de progression tqdm pour traitements longs
- Interface web responsive (PC, iPhone, iPad, Android), mode clair/sombre

## Encodage

- `.py`, `.cmd`, `.txt`, `.md` : **UTF-8 sans BOM**
- `.csv`, `.xlsx` : **UTF-8-SIG avec BOM** (obligatoire)

## Cartouche (avant les imports)

```python
#*TO*#
__pgm__ = "nom.py"
__version__ = "x.y.z"
__date__ = "JJ/MM/AAAA HH:MM"
```

Change systématiquement la date et l'heure pour chaque version. Ne touche pas au x mais incrémente comme tu sens y ou z suivant l'importance des modifs. Et en CLI affiche toujours ces éléments en début de programme.

## Structure des répertoires

- Racine : `.py` et `.cmd`
- `/bases` : bases `.db`
- `/data` : CSV patients (`pat*.csv`)
- `/refs` : CSV de référence (tags, adjectifs, ages, angles…)
- `/tests` : fichiers de test (`test*.csv` etc.)

## CSV

- Séparateur colonnes : `;` | Multivaleurs : `,` | Commentaires : `#`
- Toujours UTF-8-SIG. Toujours une entête. Accès par **nom de colonne**, jamais par position.

## CLI

- Sans argument → affiche l'aide (jamais de traitement sans option/paramètre)
- Options `-v`/`--verbose` et `-d`/`--debug` toujours proposées

## 🔒 Fichiers protégés — NE JAMAIS écraser

Fichiers contenant des données utilisateur (motsvides.csv, ages.csv, glossaire.csv, etc.) : **JAMAIS créés, modifiés ou écrasés**. Pour les exemples → suffixe `_EXEMPLE`.

## Données

- Aucune donnée en dur sauf : M/F, Oui/Non, constantes techniques, énumérations exhaustives du prompt
- Tout le reste via fichiers externes

## Modularité

- Un fichier Python par opération de transformation
- Debug intégré dès la conception

## Sécurité

On ne fait aucune confiance au client. Toute la sécurité doit être du côté serveur même si je n'ai rien contre une protection complémentaire côté client. Tout le code que tu produis doit être à l'état de l'art de la sécurité web en évitant les XSS, injections SQL, etc...

Une implémentation comme celle que jci-dessous 'ai découverte dans un projet est totalement innaceptable : 

"" **tous les endpoints acceptent n'importe quel nom de base** en paramètre. Quelqu'un peut simplement taper dans son navigateur `/count?base=prospects.db` ou `/patient?base=prospects.db&id=1` sans même toucher au JS.

Le filtre côté client n'est qu'un confort d'affichage, pas une sécurité."

## Instructions IA

- Respecter strictement les règles, pas de validations inutiles
- Résultats exploitables immédiatement. Qualité avant tout
- Résumé systématique à chaque étape
- TDD : penser aux tests dès la conception
- **Ne rien inventer** : si un fichier est cité comme fourni, il doit être fourni ou demandé
- **Pas de cow-boy** : en cas d'incertitude, demander des précisions
- Document de synthèse `conv_[nom].md` mis à jour à chaque échange (date/heure + Q/R synthétiques). Demander le nom si non fourni via `nc=[nom]`
- Prompts `.md` nommés `Prompt_xxx`. Ne jamais changer nom/signature d'un `.py` sans demande explicite
- Fournir systématiquement les prompts complets pour recréer tous les `.py` avec PJ nécessaires
- Commandes copiables à l'aveugle : pas de `# commentaire` dans les pip, pas de USERNAME à remplacer
- Commentaires : `[COMMENTAIRE]…[FIN COMMENTAIRE]` et `REM` ignorés. HTML : `/* */`

📦 **Annexe disponible** : `Prompt_contexte_annexe.md` contient les détails sur le versionning, SemVer, pipeline cerbere/horodateur, affichage web/chatbot, architecture SQL/FTS5, schéma BDD, index, et checklist de livraison. À consulter quand ces sujets sont abordés.
