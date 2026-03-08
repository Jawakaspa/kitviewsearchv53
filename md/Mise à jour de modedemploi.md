Création de meme.md

Contexte : Projet KITVIEW - Interface de recherche patients orthodontie

Fichiers à joindre en PJ :

- modedemploi.html (version actuelle)
- Prompt_contexte1301.md
- Prompt_MD_to_Slides_v2_meta.md 

Demande :
Mettre à jour modedemploi.html pour ajouter une section expliquant la fonctionnalité "Recherche par similarité" (même X que Patient).

Ne touche surtout pas à la structure technique qui a nécessité un certain nombre d'itérations pour pouvoir utiliser google translate.

Applique les règles de rajout de meta définies dans Prompt_MD_to_Slides_v2_meta pour pouvoir convertir le document en slides si souhaité.

Contenu à ajouter :

### Fonctionnalité "Même X que Patient"

Cette fonctionnalité permet de trouver des patients similaires à un patient de référence.

**Comment l'utiliser :**

1. **Recherche initiale** : Faites une recherche normale (ex: "patients avec bruxisme")

2. **Sélection du patient de référence** : Cliquez sur n'importe quel élément cliquable d'une fiche patient :
   
   - Portrait → "même portrait"
   - Prénom → "même prénom"  
   - Nom → "même nom"
   - Sexe (♂/♀) → "même sexe"
   - Âge → "même âge" (±3 ans)
   - Tag (ex: Béance) → "même béance"
   - Pathologie complète → "même béance antérieure gauche modérée"

3. **Patient sélectionné** : La fiche du patient de référence s'affiche avec un fond jaune

4. **Ajouter des critères** : Cliquez sur d'autres éléments du même patient pour combiner les critères (ex: "même portrait et même âge que Guillaume Moulin")

5. **Retirer un critère** : Re-cliquez sur un élément actif (bordure rouge) pour le retirer

6. **Changer de patient de référence** : Cliquez sur n'importe quel élément d'un autre patient

7. **Revenir à la recherche initiale** : Retirez tous les critères actifs

**Syntaxe directe dans la barre de recherche :**

- "même portrait que Guillaume Moulin"
- "même âge et même sexe que Hélène Joly"
- "mêmes portrait, prénom et âge que Jean Dupont"
- "même béance antérieure que id 123"

**Affichage des pathologies :**

- Tags (1 mot) : fond sombre, texte blanc (ex: Béance)
- Pathologies complètes : fond clair, texte noir (ex: Béance Antérieure Gauche Modérée)
- Les pathologies sont groupées par tag

Intégrer cette section de manière cohérente avec le style existant de modedemploi.html.
