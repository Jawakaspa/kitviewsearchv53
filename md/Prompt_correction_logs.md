# Prompt de recréation : Correction des logs de recherche

## Objectif
Corriger l'incohérence des chemins de logs entre `server.py` et `search.py` qui empêche l'enregistrement des logs de recherche.

---

## FICHIERS CORRIGÉS DISPONIBLES

Les fichiers suivants sont prêts à l'emploi :
- `search.py` (V1.0.13) - Module de recherche avec logs corrigés
- `server.py` (V1.0.23) - Serveur API avec chemin de logs corrigé

**Ces fichiers peuvent être déployés directement sur Render.**

---

## Contexte
Les logs de recherche ne s'enregistrent plus depuis le 30/12/2025. Le problème vient d'une incohérence de chemins :
- `search.py` écrit dans `logs/logrecherche.csv`
- `server.py` cherchait `logrecherche.csv` à la racine

---

## Pièces jointes nécessaires (si recréation depuis zéro)
1. `server.py` - Version originale (V1.0.22) à corriger
2. `search.py` - Version originale (V1.0.12) à corriger
3. `Prompt_contexte2312.md` - Contexte du projet

---

## Instructions

### 1. Correction de server.py

Dans la fonction `lifespan()` (section "ÉTAPE 1 : CONFIGURATION DES CHEMINS"), remplacer :

```python
LOG_RECHERCHE_PATH = SCRIPT_DIR / "logrecherche.csv"

logger.info(f"  Fichier log recherches : {LOG_RECHERCHE_PATH}")
```

Par :

```python
# CORRECTION : Le fichier de log est dans le sous-répertoire logs/
LOG_RECHERCHE_PATH = SCRIPT_DIR / "logs" / "logrecherche.csv"

logger.info(f"  Fichier log recherches : {LOG_RECHERCHE_PATH}")

# S'assurer que le répertoire logs existe
logs_dir = SCRIPT_DIR / "logs"
if not logs_dir.exists():
    try:
        logs_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"  ✓ Répertoire logs/ créé")
    except Exception as e:
        logger.error(f"  ❌ Impossible de créer le répertoire logs/: {e}")
else:
    logger.info(f"  ✓ Répertoire logs/ trouvé")
```

### 2. Correction de search.py

#### 2.1 Améliorer `_init_log_file()` (lignes ~734-746)

```python
def _init_log_file():
    """Initialise le fichier de logs s'il n'existe pas avec le nouvel en-tête."""
    try:
        if not os.path.exists(LOGS_DIR):
            os.makedirs(LOGS_DIR, exist_ok=True)
            print(f"[INFO] Répertoire logs créé : {LOGS_DIR}")
        
        if not os.path.exists(LOG_FILE):
            timestamp = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
            with open(LOG_FILE, 'w', encoding='utf-8-sig', newline='') as f:
                f.write(f"# logrecherche.csv V1.1.0 - {timestamp}\n")
                writer = csv.writer(f, delimiter=';')
                writer.writerow(LOG_HEADER)
            print(f"[INFO] Fichier log créé : {LOG_FILE}")
        else:
            _migrate_log_file_if_needed()
    except Exception as e:
        print(f"[ERREUR] Impossible d'initialiser le fichier de logs: {e}")
        print(f"[DEBUG] LOGS_DIR={LOGS_DIR}, LOG_FILE={LOG_FILE}")
        # Propager l'erreur pour diagnostic
        raise
```

#### 2.2 Améliorer `_log_recherche()` - section try/except (lignes ~795-824)

Remplacer le bloc except générique par :

```python
    except PermissionError as e:
        print(f"[ERREUR] Permission refusée pour écrire dans {LOG_FILE}: {e}")
    except FileNotFoundError as e:
        print(f"[ERREUR] Fichier log introuvable {LOG_FILE}: {e}")
        # Tenter de recréer le fichier
        try:
            _init_log_file()
            with open(LOG_FILE, 'a', encoding='utf-8-sig', newline='') as f:
                writer = csv.writer(f, delimiter=';')
                writer.writerow([
                    __pgm__, timestamp, temps_ms, languesaisie, langueutilisee,
                    modulelangue, question_originale, question_fr, filtres_json,
                    sql, '', base, mode, nb_patients, pathologies_str, ages_str,
                    residu, erreur, session_id, ip_utilisateur, '', '', ''
                ])
        except Exception as retry_error:
            print(f"[ERREUR] Échec de récupération: {retry_error}")
    except Exception as e:
        print(f"[ERREUR] Erreur inattendue écriture log: {type(e).__name__}: {e}")
```

---

## Tests recommandés après correction

1. Redéployer sur Render
2. Vérifier dans les logs Render que le message "✓ Répertoire logs/ créé" ou "✓ Répertoire logs/ trouvé" apparaît
3. Effectuer une recherche sur l'interface web
4. Vérifier que le log est bien enregistré via `/api/export-logs`

---

## Résumé des modifications

| Fichier | Localisation | Modification |
|---------|--------------|--------------|
| server.py | Ligne ~339 | Chemin vers `logs/logrecherche.csv` |
| server.py | Après ligne ~343 | Création du répertoire `logs/` au démarrage |
| search.py | Lignes ~734-746 | Meilleure gestion d'erreur dans `_init_log_file()` |
| search.py | Lignes ~795-824 | Gestion d'erreur détaillée dans `_log_recherche()` |

---

*Prompt créé le 31/12/2024*
