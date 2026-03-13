## Sécurité filtrage serveur

J'ai un petit problème qui existe également en local. Quand je rajoute basegg007.db elle ne s'affiche pas dans la liste des bases alors que si je rajoute base007.db c'est ok. Voici server que je soupçonne même si je n'ai pas trouvé le code qui bloque.

18:31

Identifié un problème de filtrage regex affectant l'affichage des bases

Identifié un problème de filtrage regex affectant l'affichage des bases

Ce n'est pas dans server.py, c'est dans `simple30_search.js` ligne 204 que j'ai déjà vu plus tôt :

javascript

```javascript
const bases = allBases.filter(base => {
    return /^base\d+\.db$/i.test(base);
});
```

Le regex exige : `base` + **uniquement des chiffres** + `.db`. Donc `base007.db` passe, mais `basegg007.db` est rejeté à cause des lettres `gg`.

Il faut élargir le pattern pour accepter des caractères alphanumériques après `base` :

javascript

```javascript
// AVANT : /^base\d+\.db$/i  → uniquement base + chiffres
// APRÈS : /^base.+\.db$/i   → base + n'importe quoi
const bases = allBases.filter(base => {
    return /^base.+\.db$/i.test(base);
});
```

C'est la seule modification nécessaire, dans `simple30_search.js` (et `simple31_search.js` si tu l'as aussi). Le serveur retourne bien toutes les `.db` du répertoire — c'est le filtre côté client qui est trop restrictif.

Jamais je n'y aurais pensé car c'est du n'importe quoi au niveau sécurité. Ca veut dire que n'importe qui peut modifier une page client et bricoler la liste des bases proposées non ?

18:34

Identifié faille sécurité client-side, proposé solution serveur

Identifié faille sécurité client-side, proposé solution serveur

Tu as tout à fait raison, et la remarque va plus loin que le filtre d'affichage. Le vrai problème c'est que **tous les endpoints acceptent n'importe quel nom de base** en paramètre. Quelqu'un peut simplement taper dans son navigateur `/count?base=prospects.db` ou `/patient?base=prospects.db&id=1` sans même toucher au JS.

Le filtre côté client n'est qu'un confort d'affichage, pas une sécurité. La protection doit être côté serveur, à deux endroits :

**1. Filtrer dans GET /bases** (ne retourner que les bases autorisées) :

python

```python
# Dans server.py, endpoint /bases — remplacer le listage brut
@app.get("/bases")
async def list_bases():
    bases = []
    for db_file in sorted(BASES_DIR.glob("*.db")):
        name = db_file.name
        # Seules les bases commençant par "base" sont exposées
        if name.lower().startswith("base"):
            bases.append(name)
    return {"bases": bases}
```

**2. Valider dans chaque endpoint qui reçoit un paramètre `base`** :

python

```python
def validate_base_name(base: str):
    """Vérifie qu'un nom de base est autorisé."""
    if not base.lower().startswith("base") or not base.endswith(".db"):
        raise HTTPException(status_code=403, detail=f"Base non autorisée : {base}")
    # Empêcher le path traversal (../../etc/passwd.db)
    if ".." in base or "/" in base or "\\" in base:
        raise HTTPException(status_code=403, detail="Nom de base invalide")
```

Ceci dit, pour ta V53 en développement, ça n'est pas critique — tes utilisateurs sont de confiance et le serveur n'est pas exposé publiquement sans authentification. Mais c'est clairement à mettre sur la liste avant une mise en production. Tu veux que je fasse le patch server.py maintenant ou tu préfères le garder pour plus tard ?

Oui fais le patch car c'est typiquement le truc auquel je n'ai aucune chance de penser lors de la mise en production. Je vais rajouter dans ton contexte global que tu dois éviter ce genre de choses. Et moi je vais quand même faire le patch du côté client car 2 précautions valent mieux qu'une.
