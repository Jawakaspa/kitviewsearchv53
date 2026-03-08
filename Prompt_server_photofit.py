# ╔════════════════════════════════════════════════════════════════
# ║ Prompt_server_photofit.py
# ║ Ajouts à server.py pour le service Photofit Upload
# ║
# ║ Ce fichier contient les blocs de code à insérer dans server.py
# ║ pour ajouter les 3 nouveaux endpoints Photofit :
# ║   POST /photofit/search-by-image  - Recherche par image uploadée
# ║   POST /photofit/save-prospect    - Sauvegarder un prospect
# ║   GET  /photofit/prospects        - Lister les prospects
# ║   GET  /photofit/prospects/photos/{filename} - Servir photo prospect
# ║
# ║ INSTRUCTIONS D'INTÉGRATION :
# ║   1. IMPORT : Ajouter après les imports existants (ligne ~170)
# ║   2. CACHE PROSPECTS : Ajouter après SEARCH_CACHE (ligne ~286)
# ║   3. LIFESPAN : Ajouter dans lifespan() avant le yield
# ║   4. MODÈLES PYDANTIC : Ajouter après RatingRequest (ligne ~810)
# ║   5. ENDPOINTS : Ajouter avant le bloc "POINT D'ENTRÉE" (ligne ~3198)
# ║   6. STATIC FILES : Ajouter après le mount /ihm (ligne ~786)
# ╚════════════════════════════════════════════════════════════════


# ═══════════════════════════════════════════════════════════════
# BLOC 1 : IMPORT (après ligne ~170, après "import json")
# ═══════════════════════════════════════════════════════════════

# Import du module photofit_upload
try:
    from photofit_upload import (
        extraire_features as photofit_extraire_features,
        rechercher_par_image as photofit_rechercher,
        enrichir_avec_patients as photofit_enrichir,
        sauver_prospect as photofit_sauver_prospect,
        lister_prospects as photofit_lister_prospects,
        get_stats_prospects as photofit_stats_prospects,
        creer_base_prospects,
        lire_config as photofit_lire_config,
    )
    PHOTOFIT_UPLOAD_DISPONIBLE = True
except ImportError as e:
    PHOTOFIT_UPLOAD_DISPONIBLE = False
    logging.warning(f"Module photofit_upload.py non importable: {e}")


# ═══════════════════════════════════════════════════════════════
# BLOC 2 : VARIABLE GLOBALE (après SEARCH_CACHE, ligne ~286)
# ═══════════════════════════════════════════════════════════════

# Répertoire des photos de prospects
PROSPECTS_PHOTOS_DIR = None


# ═══════════════════════════════════════════════════════════════
# BLOC 3 : LIFESPAN (dans la fonction lifespan(), avant le yield)
# Ajouter après le dernier logger.info("") avant yield
# ═══════════════════════════════════════════════════════════════

    # ═══════════════════════════════════════════════════════════════
    # ÉTAPE N : INITIALISATION PHOTOFIT UPLOAD & PROSPECTS
    # ═══════════════════════════════════════════════════════════════

    logger.info("ÉTAPE N : Initialisation Photofit Upload & Prospects")

    if PHOTOFIT_UPLOAD_DISPONIBLE:
        # Créer la base prospects.db et le répertoire photos si nécessaires
        try:
            prospects_db = BASES_DIR / "prospects.db"
            creer_base_prospects(prospects_db, verbose=False)

            global PROSPECTS_PHOTOS_DIR
            PROSPECTS_PHOTOS_DIR = BASES_DIR / "prospects"
            PROSPECTS_PHOTOS_DIR.mkdir(parents=True, exist_ok=True)

            stats = photofit_stats_prospects(prospects_db)
            logger.info(f"  ✓ prospects.db : {stats['total']} prospect(s)")
            logger.info(f"  ✓ Photos prospects : {PROSPECTS_PHOTOS_DIR}")

            # Lire la config Photofit
            config = photofit_lire_config(debug=False)
            logger.info(f"  ✓ Config Photofit : max={config['max_results']}, "
                        f"score_min={config['score_min']}, "
                        f"weights=hair:{config['weight_hair']}/face:{config['weight_face']}")

        except Exception as e:
            logger.error(f"  ❌ Erreur init Photofit Upload : {e}")
    else:
        logger.warning("  ⚠️  Module photofit_upload.py non disponible")

    logger.info("")


# ═══════════════════════════════════════════════════════════════
# BLOC 4 : MODÈLE PYDANTIC (après RatingRequest, ligne ~810)
# ═══════════════════════════════════════════════════════════════

class ProspectSaveRequest(BaseModel):
    """Modèle pour la sauvegarde d'un prospect."""
    prenom: str
    nom: str
    sexe: Optional[str] = ""
    age: Optional[float] = None
    tags: Optional[str] = "prospect"
    # Les embeddings sont passés pour éviter de rappeler l'API
    hair_embedding: List[float]
    face_embedding: List[float] = []
    attributes: List[float] = []


# ═══════════════════════════════════════════════════════════════
# BLOC 5 : STATIC FILES MOUNT (après le mount /ihm, ligne ~786)
# ═══════════════════════════════════════════════════════════════

# Servir les photos des prospects
# NOTE : Ce mount est conditionnel, il sera effectif si le dossier existe
_prospects_photos = SCRIPT_DIR / "bases" / "prospects"
if _prospects_photos.exists():
    app.mount("/photofit/prospects/photos",
              StaticFiles(directory=str(_prospects_photos)),
              name="prospects_photos")


# ═══════════════════════════════════════════════════════════════
# BLOC 6 : ENDPOINTS PHOTOFIT (avant "POINT D'ENTRÉE", ligne ~3198)
# ═══════════════════════════════════════════════════════════════

# ═══════════════════════════════════════════════════════════════
# ENDPOINTS PHOTOFIT UPLOAD - Recherche par image
# ═══════════════════════════════════════════════════════════════

from fastapi import File, UploadFile, Form


@app.post("/photofit/search-by-image")
async def photofit_search_by_image(
    img: UploadFile = File(...),
    base: str = Form("base1000.db"),
):
    """
    Recherche de portraits similaires à partir d'une image uploadée.

    1. Envoie l'image à l'API Photofit pour extraire les embeddings
    2. Recherche dans photofit.db + prospects.db
    3. Enrichit avec les infos patients depuis baseN.db
    4. Retourne les résultats triés par score

    Paramètres (multipart/form-data) :
    - img : Fichier image (jpg, png, webp, bmp)
    - base : Nom de la base patients active (défaut: base1000.db)

    Retourne :
    {
        "resultats": [...],
        "nb_resultats": int,
        "temps_ms": int,
        "hair_embedding": [...],   // Pour save-prospect sans rappeler l'API
        "face_embedding": [...],
        "attributes": [...]
    }
    """
    if not PHOTOFIT_UPLOAD_DISPONIBLE:
        raise HTTPException(status_code=503,
                            detail="Module photofit_upload non disponible")

    # Vérifier l'extension
    ext = Path(img.filename).suffix.lower()
    if ext not in {'.jpg', '.jpeg', '.png', '.bmp', '.webp'}:
        raise HTTPException(status_code=400,
                            detail=f"Format non supporté : {ext}. "
                                   f"Acceptés : jpg, png, webp, bmp")

    # Lire le contenu
    image_bytes = await img.read()
    if len(image_bytes) == 0:
        raise HTTPException(status_code=400, detail="Fichier image vide")

    if len(image_bytes) > 10 * 1024 * 1024:  # 10 Mo max
        raise HTTPException(status_code=400,
                            detail="Image trop volumineuse (max 10 Mo)")

    logger.info(f"POST /photofit/search-by-image - {img.filename} "
                f"({len(image_bytes)} bytes), base={base}")

    start_time = datetime.now()

    # Étape 1 : Extraire les features via API Photofit
    features, error = photofit_extraire_features(
        image_bytes, img.filename, verbose=False, debug=False
    )

    if error:
        logger.error(f"  ❌ Erreur API Photofit : {error}")
        raise HTTPException(status_code=502,
                            detail=f"Erreur API Photofit : {error}")

    elapsed_api = int((datetime.now() - start_time).total_seconds() * 1000)
    logger.info(f"  ✓ Features extraites en {elapsed_api}ms "
                f"(hair={len(features['hair_embedding'])}, "
                f"face={len(features.get('face_embedding', []))})")

    # Étape 2 : Rechercher les similaires
    resultats = photofit_rechercher(
        hair_embedding=features['hair_embedding'],
        face_embedding=features.get('face_embedding', []),
        verbose=False, debug=False
    )

    # Étape 3 : Enrichir avec les infos patients
    db_path = BASES_DIR / base if BASES_DIR else Path(base)
    if not db_path.exists():
        logger.warning(f"  ⚠️  Base {base} introuvable, enrichissement désactivé")

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
        "temps_api_ms": elapsed_api,
        # Renvoyer les embeddings pour un éventuel save-prospect
        "hair_embedding": features['hair_embedding'],
        "face_embedding": features.get('face_embedding', []),
        "attributes": features.get('attributes', []),
    }


@app.post("/photofit/save-prospect")
async def photofit_save_prospect(
    img: UploadFile = File(...),
    prenom: str = Form(...),
    nom: str = Form(...),
    sexe: str = Form(""),
    age: float = Form(None),
    tags: str = Form("prospect"),
    hair_embedding: str = Form(...),     # JSON array stringifié
    face_embedding: str = Form("[]"),    # JSON array stringifié
    attributes: str = Form("[]"),        # JSON array stringifié
):
    """
    Sauvegarde un prospect dans prospects.db avec sa photo.

    Les embeddings sont passés en JSON stringifié pour éviter de
    rappeler l'API Photofit (ils ont déjà été calculés par search-by-image).

    Paramètres (multipart/form-data) :
    - img : Fichier image
    - prenom, nom : Obligatoires
    - sexe, age, tags : Optionnels
    - hair_embedding, face_embedding, attributes : JSON arrays (de search-by-image)
    """
    if not PHOTOFIT_UPLOAD_DISPONIBLE:
        raise HTTPException(status_code=503,
                            detail="Module photofit_upload non disponible")

    # Valider les champs obligatoires
    if not prenom or not prenom.strip():
        raise HTTPException(status_code=400, detail="Prénom obligatoire")
    if not nom or not nom.strip():
        raise HTTPException(status_code=400, detail="Nom obligatoire")

    # Parser les embeddings JSON
    try:
        hair_emb = json.loads(hair_embedding)
        face_emb = json.loads(face_embedding)
        attrs = json.loads(attributes)
    except json.JSONDecodeError as e:
        raise HTTPException(status_code=400,
                            detail=f"Embeddings JSON invalides : {e}")

    if not hair_emb:
        raise HTTPException(status_code=400,
                            detail="hair_embedding requis (appeler search-by-image d'abord)")

    # Lire la photo
    image_bytes = await img.read()
    if len(image_bytes) == 0:
        raise HTTPException(status_code=400, detail="Fichier image vide")

    logger.info(f"POST /photofit/save-prospect - {prenom} {nom}, "
                f"{img.filename} ({len(image_bytes)} bytes)")

    # Construire le dict features
    features = {
        'attributes': attrs,
        'hair_embedding': hair_emb,
        'face_embedding': face_emb,
    }

    # Sauvegarder
    try:
        result = photofit_sauver_prospect(
            prenom=prenom.strip(),
            nom=nom.strip(),
            photo_bytes=image_bytes,
            photo_filename=img.filename,
            features=features,
            sexe=sexe.strip(),
            age=age,
            tags=tags.strip() if tags else "prospect",
            verbose=False, debug=False
        )

        logger.info(f"  ✓ Prospect #{result['id']} sauvegardé : "
                    f"{result['prenom']} {result['nom']}")

        return {
            "success": True,
            "prospect": result,
        }

    except Exception as e:
        logger.error(f"  ❌ Erreur sauvegarde prospect : {e}")
        raise HTTPException(status_code=500,
                            detail=f"Erreur sauvegarde : {str(e)}")


@app.get("/photofit/prospects")
async def photofit_get_prospects():
    """
    Retourne la liste des prospects enregistrés.
    """
    if not PHOTOFIT_UPLOAD_DISPONIBLE:
        raise HTTPException(status_code=503,
                            detail="Module photofit_upload non disponible")

    prospects = photofit_lister_prospects(verbose=False)
    stats = photofit_stats_prospects()

    logger.info(f"GET /photofit/prospects - {len(prospects)} prospect(s)")

    return {
        "prospects": prospects,
        "total": stats.get('total', 0),
    }
