# Prompt_server31_patch.md — Modifications server.py pour photofit31

## 1. Modifier les imports photofit (ligne ~237)

**Remplacer :**
```python
    from photofit_upload import (
        extraire_features as photofit_extraire_features,
        rechercher_par_image as photofit_rechercher,
        enrichir_avec_patients as photofit_enrichir,
        sauver_prospect as photofit_sauver_prospect,
        lister_prospects as photofit_lister_prospects,
        get_stats_prospects as photofit_stats_prospects,
        creer_base_prospects,
        lire_config as photofit_lire_config,
```

**Par :**
```python
    from photofit_upload import (
        extraire_features as photofit_extraire_features,
        rechercher_par_image as photofit_rechercher,
        enrichir_avec_patients as photofit_enrichir,
        sauver_prospect as photofit_sauver_prospect,
        supprimer_prospect as photofit_supprimer_prospect,
        lister_prospects as photofit_lister_prospects,
        get_stats_prospects as photofit_stats_prospects,
        get_prospect_by_id as photofit_get_prospect_by_id,
        creer_base_prospects,
        lire_config as photofit_lire_config,
```

---

## 2. Ajouter au dictionnaire des endpoints (ligne ~949)

Ajouter dans le bloc `"photofit"` :

```python
            "/photofit/prospects/{id}": "Supprimer un prospect (DELETE)",
            "/photofit/search-by-prospect-id": "Recherche par prospect existant (POST)",
```

---

## 3. Ajouter 2 nouveaux endpoints APRÈS `photofit_get_prospects` (~ligne 3513)

Coller ce code **juste après** le endpoint `GET /photofit/prospects` et **avant** le bloc `POINT D'ENTRÉE` :

```python
@app.delete("/photofit/prospects/{prospect_id}")
async def photofit_delete_prospect_endpoint(prospect_id: int):
    """
    Supprime un prospect par son ID (base + photo sur disque).

    Retourne : {"success": true, "id": int, "photo_deleted": bool}
    """
    if not PHOTOFIT_UPLOAD_DISPONIBLE:
        raise HTTPException(status_code=503,
                            detail="Module photofit_upload non disponible")

    result = photofit_supprimer_prospect(
        prospect_id, verbose=False, debug=False
    )

    if not result['success']:
        raise HTTPException(status_code=404,
                            detail=result.get('error', 'Erreur suppression'))

    logger.info(f"DELETE /photofit/prospects/{prospect_id} - OK "
                f"(photo_deleted={result['photo_deleted']})")

    return result


@app.post("/photofit/search-by-prospect-id")
async def photofit_search_by_prospect_id_endpoint(
    prospect_id: int = Form(...),
    base: str = Form("base1964.db"),
    score_min: int = Form(None),
    max_results: int = Form(None),
):
    """
    Recherche de portraits similaires à partir d'un prospect existant.

    Utilise les embeddings déjà stockés dans prospects.db → pas d'appel API Photofit.

    Paramètres (multipart/form-data) :
    - prospect_id : ID du prospect source
    - base : Nom de la base patients active
    - score_min : Score minimum (override, optionnel)
    - max_results : Nombre max de résultats (override, optionnel)

    Retourne le même format que /photofit/search-by-image + infos du prospect source.
    """
    if not PHOTOFIT_UPLOAD_DISPONIBLE:
        raise HTTPException(status_code=503,
                            detail="Module photofit_upload non disponible")

    # Récupérer le prospect avec ses embeddings
    prospect = photofit_get_prospect_by_id(prospect_id)
    if not prospect:
        raise HTTPException(status_code=404,
                            detail=f"Prospect #{prospect_id} introuvable")

    if not prospect['hair_embedding']:
        raise HTTPException(status_code=400,
                            detail=f"Prospect #{prospect_id} sans embeddings")

    start_time = datetime.now()

    logger.info(f"POST /photofit/search-by-prospect-id - "
                f"prospect #{prospect_id} ({prospect['prenom']} {prospect['nom']}), "
                f"base={base}")

    # Config avec overrides éventuels
    config_override = None
    if score_min is not None or max_results is not None:
        config_override = photofit_lire_config(debug=False).copy()
        if score_min is not None:
            config_override['score_min'] = score_min
        if max_results is not None:
            config_override['max_results'] = max_results

    # Rechercher les similaires (pas d'appel API Photofit)
    resultats = photofit_rechercher(
        hair_embedding=prospect['hair_embedding'],
        face_embedding=prospect['face_embedding'],
        config=config_override,
        verbose=False, debug=False
    )

    # Enrichir avec les infos patients
    db_path = BASES_DIR / base if BASES_DIR else Path(base)
    if not db_path.exists():
        logger.warning(f"  ⚠️  Base {base} introuvable, enrichissement limité")

    resultats = photofit_enrichir(
        resultats=resultats,
        base_path=db_path,
        portraits_cache=PORTRAITS_CACHE,
        debug=False
    )

    elapsed_total = int((datetime.now() - start_time).total_seconds() * 1000)

    nb_photofit = sum(1 for r in resultats if r['source'] == 'photofit')
    nb_prospects = sum(1 for r in resultats if r['source'] == 'prospect')
    logger.info(f"  ✓ {len(resultats)} résultat(s) en {elapsed_total}ms "
                f"({nb_photofit} patients, {nb_prospects} prospects)")

    return {
        "resultats": resultats,
        "nb_resultats": len(resultats),
        "temps_ms": elapsed_total,
        "temps_api_ms": 0,
        "prospect_source": {
            "id": prospect['id'],
            "prenom": prospect['prenom'],
            "nom": prospect['nom'],
            "photo_url": prospect['photo_url'],
        },
        "hair_embedding": prospect['hair_embedding'],
        "face_embedding": prospect['face_embedding'],
        "attributes": prospect['attributes'],
    }
```

---

## Résumé des modifications

| Action | Détail |
|---|---|
| Import | +2 fonctions : `supprimer_prospect`, `get_prospect_by_id` |
| Endpoint | `DELETE /photofit/prospects/{id}` — supprime prospect + photo |
| Endpoint | `POST /photofit/search-by-prospect-id` — recherche via prospect existant (0ms API) |
| Dict endpoints | +2 entrées documentation |
