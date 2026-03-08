# Prompt conv_KITVIEW_API_KEY V1.0.0 - 13/01/2026 14:59:26

# Synthèse conversation : KITVIEW_API_KEY

## Métadonnées
- **Date de création** : 13/01/2026
- **Dernière mise à jour** : 13/01/2026 14:45 UTC
- **Fichiers analysés** : server.py (v1.0.50), search.py (v1.0.28)

---

## Échange 1 — 13/01/2026 14:32 UTC

### Question
Étude de l'opportunité d'exposer la recherche sous forme d'API avec clé d'authentification (type EDENAI_API_KEY ou DEEPL_API_KEY).
- Intérêt
- Complexité de la chaîne complète (distribution, maintenance des clés, logging)
- Que retourner : IDs, SQL complets, pagination ?

### Analyse Claude

#### 1. Intérêt
| POUR | CONTRE |
|------|--------|
| Monétisation (SaaS B2B) | Complexité infrastructure |
| Contrôle d'accès | Pas de besoin immédiat (usage interne) |
| Rate limiting | Coûts IA en passthrough difficiles à tarifer |
| Analytics par client | Conformité RGPD si données patients exposées |
| Intégration partenaires | |

**Verdict** : Intérêt modéré court terme, fort si commercialisation envisagée.

#### 2. Complexité estimée
| Composant | Temps |
|-----------|-------|
| Middleware validation | 2h |
| Table apikeys.csv | 1h |
| CRUD /api/keys | 4h |
| Quotas/rate limiting | 4h |
| Dashboard admin | 6h |
| Tests | 3h |
| **TOTAL** | **~20h** |

#### 3. Proposition de niveaux de retour
- **ids** : `{nb_patients, patient_ids[], temps_ms}` → léger
- **summary** : `{nb_patients, patients[{id,nom,prenom,age,sexe}]}` → affichage liste
- **full** : Retour actuel complet → debug/intégration complète

### Recommandation
1. **Court terme** : Pas de changement (usage interne)
2. **Moyen terme (commercialisation)** : v1 minimaliste avec apikeys.csv + middleware + 3 niveaux de retour

### Actions décidées
- *Aucune pour l'instant — en attente de décision*

---

## Échange 2 — 13/01/2026 14:45 UTC

### Question
Est-il possible ou souhaitable que tout le monde ait besoin d'une clé API sauf la page de recherche interne ?

### Réponse Claude

**OUI**, c'est un pattern standard appelé **"first-party vs third-party access"**.

#### Principe
| Source | Endpoint | Clé requise |
|--------|----------|-------------|
| Page web interne (index.html) | `/search` | ❌ Non |
| Application externe (partenaires) | `/api/v1/search` | ✅ Oui |

#### Solution recommandée : Endpoint séparé

```python
# INTERNE (page web) - pas de clé
@app.post("/search")
async def search_internal(request: SearchRequest):
    return await _do_search(request)

# EXTERNE (API publique) - clé obligatoire
@app.post("/api/v1/search")
async def search_api(request: SearchRequest, x_api_key: str = Header(...)):
    if not _validate_api_key(x_api_key):
        raise HTTPException(401, "Clé API invalide")
    return await _do_search(request, api_key=x_api_key)
```

#### Avantages
1. Zéro friction pour utilisateurs web actuels
2. Séparation claire (documentation API distincte)
3. Évolutif (versioning /api/v2/search possible)
4. Rate limiting différencié (illimité interne, quotas externe)
5. Pas de régression du code actuel

#### Exemples du marché
- DeepL : interface web sans clé, API avec clé
- OpenAI : playground web sans clé visible, API avec clé
- Stripe : dashboard sans clé, API avec clé

### Décision
- **Maintenant** : Ne rien changer
- **Plus tard (si commercialisation)** : Créer `/api/v1/search` avec clé, garder `/search` libre

---

## Fichiers créés/modifiés

| Fichier | Action | Description |
|---------|--------|-------------|
| conv_KITVIEW_API_KEY.md | Créé | Ce fichier de synthèse |

---

## Prompts pour recréer les fichiers

*Aucun fichier .py créé dans cette conversation.*

---

## Notes et questions ouvertes

1. Y a-t-il des clients externes potentiels ?
2. Veux-tu limiter l'accès à certaines bases selon la clé ?
3. Modèle de facturation : à l'usage ou au forfait ?
