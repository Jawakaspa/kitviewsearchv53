# conv_fakenom.md

## Synthèse de conversation : fakenom

---

### 2025-02-16 ~14:00 — Création de fakenom.py

**Question** : Créer `fakenom.py` pour anonymiser nom et prénom d'un CSV patients avec Faker, en respectant la cohérence sexe/prénom.

**Usage** : `python fakenom.py pats01964.csv toto.csv [-d] [-v]`

**Réponse** : Programme créé et testé avec succès.

- Source et résultat dans `/data`
- Faker locale `fr_FR`, seed fixe (42) pour reproductibilité
- Prénom masculin si sexe=M, féminin si sexe=F
- Mapping stable : même couple (prénom, nom) original → même couple fake (ex: Francesco Delanna → Guillaume Moulin sur les lignes 10001 et 10002)
- 1964 lignes traitées, 1814 identités uniques anonymisées
- Encodage UTF-8-SIG, séparateur `;`, conventions projet respectées
- Sans arguments → affichage de l'aide
- Options `-d`/`-v` pour le debug (échantillon des mappings)

**Fichiers livrés** : `fakenom.py`, `toto.csv` (résultat d'exemple)
