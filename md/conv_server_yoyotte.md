# conv_server_yoyotte

## Synthèse de la conversation

---

### 17/02/2026 10:20 — Messages d'info doublés au démarrage de server.py

**Question** : Tous les messages `logger.info(...)` apparaissent en double dans la console au lancement de `server.py`.

**Diagnostic initial** : `propagate=True` par défaut → propagation vers le root logger uvicorn.

**Correction v1** : Ajout de `logger.propagate = False` — **n'a pas suffi**.

---

### 17/02/2026 10:50 — Correction v2

**Vrai diagnostic** : Le doublement vient du double import du module. Quand on lance `python server.py` :
1. Python charge le module comme `__main__` → code module-level exécuté → handler #1 ajouté
2. `uvicorn.run("server:app", reload=True)` importe le module `server` → code module-level ré-exécuté → handler #2 ajouté au **même** objet logger

**Correction** : Guard `if not logger.handlers:` avant d'ajouter le handler + `propagate = False`.

---

### 17/02/2026 ~10:55 — Répercussion sur version mise à jour

Thierry a modifié server.py en parallèle (3548 lignes vs 3245). Fix appliqué à l'identique sur la nouvelle version.

---

### 17/02/2026 ~11:00 — Téléchargement fichiers sur iPad

**Constat** : L'app Claude sur iPad ne propose pas de bouton de téléchargement pour les fichiers générés. Seule solution : passer par **Safari → claude.ai** où le lien de téléchargement fonctionne.
