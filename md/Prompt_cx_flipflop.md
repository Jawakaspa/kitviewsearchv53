# Prompt pour projet cx : Architecture Flip-Flop A/B KitviewSearch

## Contexte

Je développe KitviewSearch, une application de recherche multilingue pour un cabinet d'orthodontie (25 000+ patients, 12 langues supportées). L'application est déployée sur Render avec GitHub auto-deploy.

**Situation actuelle :**
- Version en production : `D:\KitviewSearchV210` (déployée sur Render)
- Nouvelle version à risque : `D:\KitviewSearchV300` (détection totalement revue)

**Besoin :**
Mettre en place une architecture **flip-flop A/B** permettant :
1. Deux versions cohabitant sur le même serveur (slot A et slot B)
2. Bascule instantanée entre les versions via interface admin
3. Rollback immédiat en cas de problème
4. Test de la nouvelle version en production avant bascule

---

## Architecture cible

```
C:\KitviewSearchV201\          ← Repo GitHub connecté à Render
├── main.py                    ← Point d'entrée FastAPI, routeur A/B
├── config.json                ← Configuration : {"active": "A", ...}
├── requirements.txt           ← Dépendances Python
├── slot_a/                    ← Version A (ex: V210 stable)
│   ├── cherche.py
│   ├── suche.py
│   ├── traduire.py
│   ├── refs/
│   │   ├── pathoori.csv
│   │   ├── pathosyn.csv
│   │   └── messages.csv
│   └── web/
│       ├── index.html
│       └── web1.html
├── slot_b/                    ← Version B (ex: V300 nouvelle)
│   └── (même structure)
└── static/
    └── admin.html             ← Interface admin (roue dentée)
```

---

## Spécifications techniques

### 1. Fichier `config.json`

```json
{
    "active": "A",
    "version_a": "2.1.0",
    "version_b": "3.0.0",
    "last_switch": "2025-12-15T14:30:00Z",
    "switch_history": [
        {
            "from": "B",
            "to": "A", 
            "date": "2025-12-15T14:30:00Z",
            "reason": "Rollback bug détection"
        }
    ]
}
```

### 2. Fichier `main.py` - Routeur principal

Doit implémenter :
- Lecture de `config.json` pour déterminer le slot actif
- Import dynamique des modules du slot actif (`slot_a/` ou `slot_b/`)
- Routes API existantes (`/api/search`, `/api/pathologies`, etc.)
- **Nouvelles routes admin** :
  - `GET /api/admin/status` : Retourne slot actif et versions
  - `POST /api/admin/switch` : Bascule vers l'autre slot (protégé par mot de passe)
  - `GET /api/admin/test/{slot}` : Teste un slot spécifique sans basculer
- Servir les fichiers statiques du slot actif
- Route `/admin` pour l'interface d'administration

**Sécurité :**
- Mot de passe admin via variable d'environnement `ADMIN_PASSWORD`
- Historique des bascules conservé dans `config.json`

### 3. Interface admin `admin.html`

Accessible via bouton ⚙️ (roue dentée) dans l'interface principale.

**Fonctionnalités :**
- Afficher le slot actif (A ou B) avec indicateur visuel
- Afficher les versions de chaque slot
- Afficher la date de dernière bascule
- Formulaire de bascule :
  - Champ mot de passe
  - Champ raison (optionnel)
  - Bouton "Basculer vers [autre slot]"
- Historique des 10 dernières bascules
- Lien pour tester le slot inactif (ouvre dans nouvel onglet)

**Design :**
- Modal ou page dédiée
- Style cohérent avec l'interface KitviewSearch existante
- Responsive (PC, tablette, mobile)

### 4. Modification de `index.html` et `web1.html`

Ajouter dans chaque interface :
- Bouton ⚙️ (roue dentée) en haut à droite, près des autres contrôles
- Ce bouton ouvre l'interface admin
- Visible uniquement (ou mis en évidence) pour les admins ? (optionnel)

### 5. Scripts de déploiement

#### `deploy_to_slot.cmd`
```
Usage : deploy_to_slot.cmd [A|B] [source_path]
Exemple : deploy_to_slot.cmd B D:\KitviewSearchV300
```

Fonctionnement :
1. Vérifie que le slot cible n'est PAS le slot actif (sécurité)
2. Nettoie le slot cible
3. Copie les fichiers source vers le slot
4. Met à jour la version dans `config.json`
5. Commit et push (sans basculer)

#### `switch_slot.cmd`
```
Usage : switch_slot.cmd [mot_de_passe] [raison]
```

Fonctionnement :
1. Appelle l'API `/api/admin/switch`
2. Affiche le résultat

---

## Workflow de mise à jour

### Déploiement initial (migration vers A/B)

1. Créer la structure `slot_a/` et `slot_b/`
2. Copier V210 dans `slot_a/`
3. Copier V210 également dans `slot_b/` (identique au départ)
4. Créer `main.py`, `config.json`, `admin.html`
5. Modifier les imports dans `main.py` pour utiliser les slots
6. Tester localement
7. Déployer sur Render

### Mise à jour normale (flip-flop)

```
1. Vérifier le slot actif
   → curl https://kitviewsearch.onrender.com/api/admin/status
   → {"active": "A", ...}

2. Déployer vers le slot INACTIF (B)
   → deploy_to_slot.cmd B D:\KitviewSearchV300

3. Tester le slot B (sans impacter les utilisateurs)
   → https://kitviewsearch.onrender.com/api/admin/test/B?q=bruxisme
   → Ou via l'interface : /slot_b/web/index.html

4. Si OK, basculer via l'admin
   → Clic sur ⚙️ → Mot de passe → "Basculer vers B"

5. Si problème après bascule
   → Re-clic sur ⚙️ → "Basculer vers A" (rollback instantané)
```

---

## Contraintes techniques

- **Python 3.13+** uniquement
- **FastAPI** pour l'API
- **Encodage** : UTF-8-SIG pour CSV, UTF-8 pour le reste
- **Pas de base de données externe** : tout en fichiers (SQLite, CSV, JSON)
- **Render** : Auto-deploy depuis GitHub, une seule instance
- **Performance** : Bascule instantanée (lecture config.json)

---

## Livrables attendus

1. **`main.py`** : Routeur FastAPI complet avec gestion A/B
2. **`config.json`** : Fichier de configuration initial
3. **`static/admin.html`** : Interface d'administration
4. **`deploy_to_slot.cmd`** : Script de déploiement vers un slot
5. **`switch_slot.cmd`** : Script de bascule en ligne de commande
6. **Modifications de `index.html`** : Ajout du bouton ⚙️
7. **Documentation** : README ou guide de mise en place

---

## Questions préalables

Avant de commencer, peux-tu confirmer :

1. Le fichier `main.py` actuel existe-t-il déjà ? Si oui, peux-tu me le fournir pour que j'adapte ?
2. Quelles sont les routes API actuelles à conserver ?
3. Y a-t-il d'autres fichiers à la racine du projet (requirements.txt, Procfile, etc.) ?
4. Le mot de passe admin doit-il être configurable via l'interface ou seulement via variable d'environnement ?
5. Veux-tu un mode "maintenance" qui affiche un message pendant une bascule ?

---

## Fichiers à fournir

Pour que je puisse travailler efficacement, merci de joindre :

- [ ] `main.py` actuel (ou équivalent point d'entrée)
- [ ] `requirements.txt`
- [ ] `index.html` (pour voir où placer le bouton ⚙️)
- [ ] Structure actuelle du projet (sortie de `tree` ou `dir /s`)
- [ ] Tout fichier de configuration Render (render.yaml si existant)

---

*Ce prompt est prévu pour le projet cx. L'objectif est de migrer de la V210 stable vers la V300 risquée avec possibilité de rollback instantané.*
