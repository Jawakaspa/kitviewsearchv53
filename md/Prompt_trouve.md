# Prompt de recréation de trouve.py

**Version cible** : V1.0.21
**Date** : 02/02/2026

---

## Fichiers PJ nécessaires

1. `Prompt_contexte1301.md` — Règles du projet
2. `trouve.py` V1.0.20 — Version précédente (base de travail)
3. `ia.csv` — Configuration des moteurs IA (fichier de référence)

---

## Prompt

```
Contexte : Projet KITVIEW Search (voir Prompt_contexte1301.md en PJ)

Objectif : Mettre à jour trouve.py V1.0.20 vers V1.0.21 pour migrer 
les modèles GPT dépréciés dans le fallback par défaut.

Table de correspondance des modèles :

| Ancien nom court | Ancien complet   | Nouveau nom court | Nouveau complet     |
|------------------|------------------|-------------------|---------------------|
| gpt4omini        | gpt-4o-mini      | gpt52instant      | gpt-5.2-instant     |

Modifications à appliquer :

1. SIGNATURE : Version 1.0.21, format #*TO*# standard

2. DOCSTRING : Ajouter changelog V1.0.21 décrivant la migration

3. default_config (fallback dans charger_modeles_ia quand ia.csv absent) :
   - 'gpt4omini': complet 'gpt-4o-mini' → 'gpt52instant': complet 'gpt-5.2-instant'
   - Garder 'standard' et 'sonnet' inchangés

Contraintes :
- NE PAS modifier la logique du pipeline, les imports, 
  ni aucune autre partie du code
- NE PAS modifier la signature des fonctions (nom, paramètres)
- Le fallback dans get_modele_defaut() retourne 'sonnet', 
  c'est correct et ne change pas
- Respecter le format de cartouche #*TO*# du projet

Génère trouve.py V1.0.21 complet.
```

---

## Vérification post-génération

```bash
# Aucune trace des anciens modèles (sauf dans le changelog) :
grep -n "gpt-4o\|gpt-4.1\|gpt4o\|gpt41" trouve.py
```
