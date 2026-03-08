# conv_republicationbases — Synthèse de conversation

## 13/02/2026 — Échange 1 : Republication des bases .db sur Render

### Question
Thierry a modifié des bases .db dans `D:\kitviewsearchV52\bases` et veut toutes les republier pour kitviewsearchV52 sur Render.

### Clarifications
- Déploiement : via `git push` dans un repo GitHub lié à Render (auto-deploy)
- Repo local : `D:\kitviewsearchV52`
- Bases : toutes les `.db` du répertoire `/bases`, déjà en place dans le repo
- Source des bases : directement dans `D:\kitviewsearchV52\bases`

### Procédure fournie
```
cd /d D:\kitviewsearchV52
git add bases\*.db
git commit -m "MAJ bases .db"
git push
```

### Points de vigilance signalés
- `.gitignore` pourrait exclure les `.db` → vérifier si `git add` les prend
- GitHub limite à 100 Mo par fichier → si bases volumineuses, Git LFS nécessaire

---

## 13/02/2026 — Échange 2 : Diagnostic du problème

### Problème
Les `git add` + `git commit` ne détectaient aucun changement, et le push (4 commits en attente) était bloqué/très lent (15 KB/s, interrompu à 62%).

### Cause racine
Les fichiers ont été **renommés** (zéros supprimés) :
- GitHub : `base01600.db`, `base01964.db`, `base03200.db`, `base03564.db`
- Local : `base1600.db`, `base1964.db`, `base3200.db`, `base3564.db`

`git add bases\*.db` ajoutait les nouveaux noms mais ne supprimait pas les anciens. Git ne voyait donc rien de nouveau à committer.

### Solution appliquée
```
cd /d D:\KitviewSearchV52
git reset origin/main
git add -A bases/
git add -A data/
git commit -m "MAJ bases .db et CSV patients"
git push
```
- `git reset origin/main` : annule les 4 commits locaux ratés (contenu disque inchangé)
- `git add -A bases/` : supprime les anciens noms (base0XXXX) + ajoute les nouveaux (baseXXXX)
- `git add -A data/` : inclut les 5 pats*.csv modifiés
- Résultat attendu sur GitHub : exactement les 6 fichiers .db sans zéros + photofit.db
