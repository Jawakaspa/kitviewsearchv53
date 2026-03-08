# main.py V1.0.0 - 20/12/2025 16:23:33
__pgm__ = "main.py"
__version__ = "1.0.0"
__date__ = "20/12/2025 16:23:33"

"""
Étape 3 : API FastAPI pour les parkings Strasbourg
- Endpoint /parkings : liste tous les parkings avec données fusionnées
- Endpoint /parkings/{id} : détail d'un parking
- Endpoint /health : vérification que l'API fonctionne
"""

import urllib.request
import json
from datetime import datetime
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

# URLs des APIs Strasbourg
URL_PARKINGS = "https://data.strasbourg.eu/api/explore/v2.1/catalog/datasets/parkings/records?limit=100"
URL_OCCUPATION = "https://data.strasbourg.eu/api/explore/v2.1/catalog/datasets/occupation-parkings-temps-reel/records?limit=100"

app = FastAPI(
    title="ParkStras API",
    description="API pour les parkings de Strasbourg - Données temps réel",
    version=__version__
)

# CORS : autoriser les appels depuis n'importe quel frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def fetch_json(url: str) -> dict | None:
    """Récupère et parse le JSON depuis une URL."""
    try:
        with urllib.request.urlopen(url, timeout=10) as response:
            return json.loads(response.read().decode("utf-8"))
    except Exception:
        return None


def fusionner_donnees(parkings: dict, occupation: dict) -> list[dict]:
    """Fusionne les données descriptives et temps réel."""
    # Indexer l'occupation par idsurfs
    occupation_par_id = {}
    for record in occupation.get("results", []):
        idsurfs = record.get("idsurfs")
        if idsurfs:
            occupation_par_id[idsurfs] = record
    
    resultats = []
    
    for record in parkings.get("results", []):
        idsurfs = record.get("idsurfs")
        if not idsurfs:
            continue
        
        # Données descriptives
        parking = {
            "id": idsurfs,
            "nom": record.get("name", "Sans nom"),
            "adresse": record.get("address", ""),
            "description": record.get("description", ""),
            "telephone": record.get("phone", ""),
            "url": record.get("websiteurl", ""),
            "position": record.get("position"),
        }
        
        # Données temps réel
        occup = occupation_par_id.get(idsurfs)
        if occup:
            total = occup.get("total", 0) or 0
            libre = occup.get("libre", 0) or 0
            pct = round((libre / total * 100), 1) if total > 0 else 0
            
            parking["total"] = total
            parking["libre"] = libre
            parking["pct_disponible"] = pct
            parking["etat"] = occup.get("etat")
            parking["etat_desc"] = occup.get("etat_descriptif", "")
            parking["couleur"] = occup.get("couleur_occup", "")
            parking["a_donnees_temps_reel"] = True
        else:
            parking["total"] = None
            parking["libre"] = None
            parking["pct_disponible"] = None
            parking["etat"] = None
            parking["etat_desc"] = ""
            parking["couleur"] = ""
            parking["a_donnees_temps_reel"] = False
        
        resultats.append(parking)
    
    # Trier par places libres (décroissant)
    resultats.sort(key=lambda p: (not p["a_donnees_temps_reel"], -(p["libre"] or 0)))
    
    return resultats


@app.get("/")
def root():
    """Redirection vers la documentation."""
    return {
        "message": "ParkStras API",
        "version": __version__,
        "docs": "/docs"
    }


@app.get("/health")
def health():
    """Vérification que l'API fonctionne."""
    return {
        "status": "ok",
        "timestamp": datetime.now().isoformat()
    }


@app.get("/parkings")
def get_parkings():
    """Retourne tous les parkings avec données fusionnées."""
    # Récupérer les données
    data_parkings = fetch_json(URL_PARKINGS)
    if not data_parkings:
        raise HTTPException(status_code=502, detail="Impossible de récupérer les données descriptives")
    
    data_occupation = fetch_json(URL_OCCUPATION)
    if not data_occupation:
        raise HTTPException(status_code=502, detail="Impossible de récupérer les données temps réel")
    
    # Fusionner
    parkings = fusionner_donnees(data_parkings, data_occupation)
    
    return {
        "timestamp": datetime.now().isoformat(),
        "count": len(parkings),
        "parkings": parkings
    }


@app.get("/parkings/{parking_id}")
def get_parking(parking_id: str):
    """Retourne un parking spécifique par son ID."""
    # Récupérer tous les parkings (pas optimisé mais simple)
    data_parkings = fetch_json(URL_PARKINGS)
    if not data_parkings:
        raise HTTPException(status_code=502, detail="Impossible de récupérer les données descriptives")
    
    data_occupation = fetch_json(URL_OCCUPATION)
    if not data_occupation:
        raise HTTPException(status_code=502, detail="Impossible de récupérer les données temps réel")
    
    parkings = fusionner_donnees(data_parkings, data_occupation)
    
    # Chercher le parking demandé
    for p in parkings:
        if p["id"] == parking_id:
            return {
                "timestamp": datetime.now().isoformat(),
                "parking": p
            }
    
    raise HTTPException(status_code=404, detail=f"Parking non trouvé: {parking_id}")


# Pour exécution locale avec: python main.py
if __name__ == "__main__":
    import uvicorn
    print(f"{__pgm__} V{__version__} - {__date__}")
    print("Démarrage du serveur FastAPI...")
    print("Documentation: http://127.0.0.1:8000/docs")
    uvicorn.run(app, host="127.0.0.1", port=8000)
