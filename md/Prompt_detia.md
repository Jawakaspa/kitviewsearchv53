# Prompt de recréation de detia.py

**Version cible** : V1.0.31
**Date** : 02/02/2026

---

## Fichiers PJ nécessaires

1. `Prompt_contexte1301.md` — Règles du projet
2. `detia.py` V1.0.30 — Version précédente (base de travail)
3. `detmeme.py` — Module de détection des similarités
4. `Prompt_detia_systeme.md` — Prompt système IA (extrait de la V1.0.30)
5. `ia.csv` — Configuration des moteurs IA (fichier de référence)

---

## Prompt

```
Contexte : Projet KITVIEW Search (voir Prompt_contexte1301.md en PJ)

Objectif : Mettre à jour detia.py V1.0.30 vers V1.0.31 pour migrer les modèles GPT dépréciés.

Table de correspondance des modèles :

| Ancien nom court | Ancien complet   | Nouveau nom court | Nouveau complet     |
|------------------|------------------|-------------------|---------------------|
| gpt4o            | gpt-4o           | gpt52             | gpt-5.2             |
| gpt41mini        | gpt-4.1-mini     | gpt52instant      | gpt-5.2-instant     |
| gpt4omini        | gpt-4o-mini      | gpt52instant      | gpt-5.2-instant     |

Modifications à appliquer :

1. SIGNATURE : Version 1.0.31, format #*TO*# standard

2. DOCSTRING : 
   - Ajouter changelog V1.0.31 décrivant la migration
   - Mettre à jour les exemples CLI (gpt51mini → gpt52instant, gpt4o → gpt52)

3. DEFAULT_MODEL : "gpt41mini" → "gpt52instant"

4. MODEL_SIMPLE_NAMES : remplacer les clés/valeurs
   - "gpt-4o": "gpt-4o" → "gpt-5.2": "gpt-5.2"
   - "gpt-4o-mini": "gpt-4o-mini" → "gpt-5.2-instant": "gpt-5.2-instant"
   - Garder claude-sonnet-3.7 inchangé

5. SUPPORTED_MODELS : remplacer les clés/valeurs
   - "gpt-4o": "openai/gpt-4o" → "gpt-5.2": "openai/gpt-5.2"
   - "gpt-4o-mini": "openai/gpt-4o-mini" → "gpt-5.2-instant": "openai/gpt-5.2-instant"
   - Garder claude-sonnet inchangé

6. default_config (fallback dans charger_modeles_ia) :
   - 'gpt41mini': complet 'gpt-4.1-mini' → 'gpt52instant': complet 'gpt-5.2-instant'
   - 'gpt4o': complet 'gpt-4o' → 'gpt52': complet 'gpt-5.2'
   - Garder sonnet inchangé

7. Banner main() : mettre à jour la ligne de version

Contraintes :
- NE PAS modifier la logique de détection, le pipeline detmeme → IA, 
  ni le prompt système
- NE PAS modifier la signature de la fonction (nom, paramètres)
- Le test `model_name.startswith('gpt-')` ligne 237 reste valide (gpt-5.2 commence par gpt-)
- Conserver les fins de ligne du fichier source
- Respecter le format de cartouche #*TO*# du projet

Génère detia.py V1.0.31 complet.
```

---

## Vérification post-génération

```bash
# Aucune trace des anciens modèles (sauf dans le changelog) :
grep -n "gpt-4o\|gpt-4.1\|gpt4o\|gpt41\|gpt51" detia.py

# Test CLI :
python detia.py -l
python detia.py "bruxisme sévère" gpt52instant -v
```
