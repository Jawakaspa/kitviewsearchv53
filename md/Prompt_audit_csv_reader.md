# Prompt d'audit : Lecture des fichiers CSV avec commentaires

## Contexte

Dans le projet, les fichiers CSV peuvent contenir des lignes de commentaires commençant par `#`. Ces commentaires peuvent apparaître :
- En début de fichier (avant la ligne d'en-tête)
- Après la ligne d'en-tête
- N'importe où dans le fichier

## Problème identifié

Quand on utilise `csv.DictReader` directement sur un fichier contenant des commentaires en première ligne, Python interprète cette ligne de commentaire comme la ligne d'en-tête, ce qui corrompt la lecture de toutes les colonnes.

### Exemple de code problématique :
```python
with open(fichier, 'r', encoding='utf-8-sig') as f:
    reader = csv.DictReader(f, delimiter=';')
    for row in reader:
        # BUG: Si la 1ère ligne est un commentaire, les colonnes sont fausses
        valeur = row.get('ma_colonne', '')
```

### Solution correcte :
```python
with open(fichier, 'r', encoding='utf-8-sig') as f:
    # Filtrer les lignes de commentaires AVANT DictReader
    lignes = []
    for ligne in f:
        ligne_strip = ligne.strip()
        if ligne_strip and not ligne_strip.startswith('#'):
            lignes.append(ligne)
    
    if not lignes:
        # Gérer le cas fichier vide
        return
    
    import io
    contenu_filtre = io.StringIO(''.join(lignes))
    reader = csv.DictReader(contenu_filtre, delimiter=';')
    
    for row in reader:
        # Maintenant les colonnes sont correctes
        valeur = row.get('ma_colonne', '')
```

## Demande d'audit

Auditer tous les fichiers `.py` du répertoire courant pour identifier ceux qui :

1. Utilisent `csv.DictReader` ou `csv.reader`
2. Lisent des fichiers CSV qui pourraient contenir des commentaires
3. Ne filtrent PAS les lignes de commentaires avant la création du reader

### Format de sortie attendu

Pour chaque fichier problématique, indiquer :
- Nom du fichier
- Numéro(s) de ligne concerné(s)
- Fonction/contexte
- Sévérité (CRITIQUE si le fichier CSV lu contient des commentaires en 1ère ligne)

### Fichiers CSV connus avec commentaires en 1ère ligne

Ces fichiers de référence ont des commentaires AVANT l'en-tête :
- `refs/commun.csv`
- `refs/glossaire.csv`
- `refs/syntags.csv`
- `refs/synadjs.csv`
- `refs/tagsadjs.csv`
- Tous les fichiers `refs/*.csv` potentiellement

## Commande à exécuter

```bash
# Lister tous les .py utilisant csv.DictReader ou csv.reader
grep -l "csv\.\(DictReader\|reader\)" *.py

# Pour chaque fichier, vérifier s'il filtre les commentaires
grep -n "csv\.\(DictReader\|reader\)" *.py
```

## Exemple de rapport

```
=== AUDIT CSV READER - [date] ===

FICHIER: exemple.py
  Ligne 45: csv.DictReader utilisé dans fonction charger_donnees()
  Risque: CRITIQUE - lit refs/commun.csv qui a des commentaires en L1
  Action: Appliquer le pattern de filtrage des commentaires

FICHIER: autre.py  
  Ligne 123: csv.DictReader utilisé dans fonction lire_config()
  Risque: FAIBLE - lit un fichier généré sans commentaires
  Action: Aucune (mais recommandé de sécuriser)

=== FIN AUDIT ===
```
