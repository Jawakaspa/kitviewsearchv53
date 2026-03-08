# Prompt_commente.md

## Objectif
Créer le programme `commente.py` qui remplit automatiquement la colonne `commentaire` du fichier `commentaires.csv` en interrogeant une IA.

## Pièces jointes requises
- `Prompt_contexte2312.md` (contexte général du projet)
- `detia.py` (référence pour la structure d'appel aux IA)
- `ia.csv` (configuration des moteurs IA)
- `commentaires.csv` (fichier à compléter, optionnel pour les tests)

## Spécifications

### Usage
```bash
python commente.py [nomdelia] [-t pattern] [-l] [-v]
```

**Arguments :**
- `nomdelia` : Nom du moteur IA (gpt4o, sonnet, haiku, etc.). Défaut : `gpt4o`
- `-t pattern` : Filtre sur le premier mot de l'oripathologie. Si absent, traite toutes les lignes
- `-l` : Liste les moteurs disponibles
- `-v` : Mode verbeux

**Exemples :**
```bash
python commente.py                        # Toutes les lignes, IA par défaut
python commente.py sonnet                 # Toutes les lignes, avec Sonnet
python commente.py -t béance              # Seulement "béance ...", IA par défaut
python commente.py gpt4omini -t bruxisme  # Seulement "bruxisme ...", GPT-4o-mini
python commente.py -l                     # Liste les moteurs
```

### Fichiers d'entrée/sortie
- **Entrée/Sortie** : `refs/commentaires.csv` (lecture et écriture)
- **Configuration** : `refs/ia.csv`

### Logique de traitement

1. Charger `commentaires.csv`
2. Filtrer les lignes :
   - Sans commentaire (colonne vide)
   - Correspondant au pattern si `-t` spécifié (premier mot)
3. Pour chaque ligne à traiter :
   - Appeler l'IA avec un prompt demandant un commentaire orthodontique
   - Stocker le commentaire généré
   - Sauvegarder toutes les 10 lignes (sauvegarde intermédiaire)
4. Sauvegarde finale

### Prompt IA

**Prompt système :**
```
Tu es un assistant spécialisé en orthodontie.
Tu dois fournir un commentaire court et utile pour un praticien orthodontiste.

RÈGLES STRICTES :
1. Le commentaire doit faire entre 40 et 120 caractères
2. Pas de guillemets autour du commentaire
3. Pas de préfixe comme "Commentaire:" ou "Définition:"
4. Utilise un vocabulaire technique approprié
5. Sois concis et informatif
6. Réponds UNIQUEMENT avec le commentaire, rien d'autre
```

**Prompt utilisateur :**
```
Donne un commentaire orthodontique pour : "{oripathologie}"

Rappel : entre 40 et 120 caractères, vocabulaire technique, utile au praticien.
```

### Appel aux IA

Le programme doit supporter deux modes d'appel (comme `detia.py`) :

1. **OpenAI direct** (`via: openai` dans ia.csv)
   - URL : `https://api.openai.com/v1/chat/completions`
   - Clé API : variable d'environnement `OPENAI_API_KEY`

2. **Eden AI** (`via: eden` dans ia.csv)
   - URL : `https://api.edenai.run/v2/text/chat`
   - Clé API : variable d'environnement `EDENAI_API_KEY`

### Nettoyage du commentaire

Après réception de la réponse IA :
1. Supprimer les guillemets englobants (`"..."` ou `'...'`)
2. Supprimer les préfixes courants (Commentaire:, Définition:, etc.)
3. Tronquer à 130 caractères si nécessaire (avec `...`)

### Affichage

```
commente.py V0.0.0 - 01/01/1970 00:00

[INFO] Racine du projet : /chemin/vers/projet
[INFO] Fichier : /chemin/vers/refs/commentaires.csv
[INFO] Moteur IA : gpt4o (gpt-4o via openai)
[INFO] Filtre : premier mot = 'béance'  # Si -t spécifié

[INFO] 179 lignes chargées
[INFO] 42 lignes à commenter

Génération des commentaires...
----------------------------------------------------------------------
Progression: 100%|██████████████████████| 42/42 [01:23<00:00, 1.98s/ligne]
----------------------------------------------------------------------

======================================================================
RÉSUMÉ
======================================================================
  Lignes traitées    : 42
  Erreurs            : 0
  Latence totale     : 83000 ms
  Latence moyenne    : 1976 ms/ligne
  Fichier mis à jour : /chemin/vers/refs/commentaires.csv
======================================================================
```

### Contraintes techniques

- Python 3.13+
- Dépendance : `tqdm` pour la barre de progression
- Encodage UTF-8-BOM pour les CSV
- Séparateur `;` pour les CSV
- Sauvegarde intermédiaire toutes les 10 lignes (résilience)
- Détection automatique de la racine du projet
- Cartouche de version au début du fichier

### Gestion des erreurs

- Vérifier l'existence du moteur dans ia.csv
- Vérifier la présence des clés API selon le mode (openai/eden)
- Capturer les erreurs d'appel API et continuer le traitement
- Afficher le nombre d'erreurs dans le résumé
