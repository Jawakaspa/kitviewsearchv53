# Prompt web5 - Suite du développement

## Fichiers à joindre en PJ :
1. `web4.html` (version actuelle)
2. `server.py` (version 4.1.0)
3. `commun.csv` (configuration langues)
4. `portraits.csv` (mapping id → URL portraits)
5. `Prompt_contexte2312.md` (règles du projet)

---

## Demandes

Créer web5.html à partir de web4.html avec les modifications suivantes :

### 1. Correction bug portraits

Les portraits patients ne s'affichent plus depuis qu'on a remplacé l'URL complète par un ID dans la base de données. 

Actuellement la base contient un champ `portrait` avec juste l'ID (ex: "12345").
Le fichier `portraits.csv` contient le mapping : id;url

Il faut :
- Soit côté serveur (server.py) : charger portraits.csv au démarrage et remplacer l'ID par l'URL complète avant de renvoyer les résultats
- Soit côté client (web5.html) : charger portraits.csv et faire la résolution ID→URL à l'affichage

Proposer la solution la plus performante.

### 2. Refonte page paramètres (roue dentée)

Remplacer la page paramètres actuelle par une structure en tableau 3 colonnes :

| Actif | Bandeau | Valeur |
|-------|---------|--------|
| ☑️    | ☐       | Jour/Nuit (toggle existant) |
| ☑️    | ☐       | Thème : classique / IOS |
| ☑️    | ☐       | Fonds d'écran (sélecteur existant) |
| ☑️    | ☐       | Filigrane (slider 0-100%) |
| ☑️    | ☐       | Nom d'utilisateur (input texte) |
| ☑️    | ☑️       | Bases (dropdown existant) |
| ☑️    | ☑️       | Internationalisation (popup langues) |
| ☑️    | ☐       | Panel gauche : ☑️ Historique ☑️ Exemples |
| ☑️    | ☐       | Durée cycle démo (input nombre) |
| ☑️    | ☐       | Limite résultats (input nombre) |
| ☑️    | ☐       | Nombre par page (input nombre) |

Colonnes :
- **Actif** : Checkbox pour activer/désactiver la fonctionnalité
- **Bandeau** : Checkbox pour afficher l'élément dans la toolbar (header)
- **Valeur** : Le contrôle lui-même (toggle, input, dropdown, slider...)

Design :
- Style propre et esthétique (pas un tableau Excel)
- Cohérent avec le thème de l'application (clair/sombre)
- La page paramètres reste toujours en français

### 3. Comportement changement de base

Quand on change de base depuis les paramètres :
- Fermer la modale paramètres
- Revenir à l'écran d'accueil (comme "Nouvelle recherche")
- Rejouer l'animation Search (Rouge → Orange → Vert)

### 4. Fractionnement toolbar selon paramètres "Bandeau"

Les éléments cochés dans la colonne "Bandeau" apparaissent dans la toolbar du header.
Les éléments non cochés restent uniquement accessibles dans les paramètres.

Éléments pouvant aller dans le bandeau :
- Bases (dropdown)
- Internationalisation (bouton langue)
- Jour/Nuit (toggle)

### 5. Panel gauche configurable

Dans les paramètres, "Panel gauche" a 2 sous-checkboxes :
- ☑️ Historique : affiche/masque la section "Conversations récentes"
- ☑️ Exemples : affiche/masque la section "Exemples"

Ces états sont sauvegardés dans localStorage.
