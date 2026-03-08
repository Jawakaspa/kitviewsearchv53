#*TO*#
__pgm__ = "resize_portraits.py"
__version__ = "0.0.0"
__date__ = "01/01/1970 00:00"

"""
Redimensionnement batch des portraits pour hébergement GitHub.

Ce script redimensionne les photos d'un répertoire en vignettes JPEG
optimisées pour l'affichage web (200px côté le plus long).

ENTRÉE :
    Dossier source contenant les photos (tout format image accepté)

SORTIE :
    Dossier destination contenant les vignettes JPEG optimisées

Usage CLI :
    python resize_portraits.py                                              # → Affiche l'aide
    python resize_portraits.py C:\\PortraitsPhotofit\\1964N                   # → Redimensionne tout
    python resize_portraits.py C:\\PortraitsPhotofit\\1964N -o thumbs         # → Sortie dans thumbs/
    python resize_portraits.py C:\\PortraitsPhotofit\\1964N -s 150            # → Vignettes 150px
    python resize_portraits.py C:\\PortraitsPhotofit\\1964N -v                # → Mode verbose
    python resize_portraits.py C:\\PortraitsPhotofit\\1964N -d                # → Mode debug
"""

import sys
import os
import argparse
import time
from pathlib import Path

try:
    from PIL import Image
except ImportError:
    print("[ERREUR] Pillow requis : pip install Pillow")
    sys.exit(1)

try:
    from tqdm import tqdm
except ImportError:
    print("[ERREUR] tqdm requis : pip install tqdm")
    sys.exit(1)


def redimensionner_photo(
    chemin_source: Path,
    chemin_dest: Path,
    taille_max: int = 200,
    qualite: int = 75,
    verbose: bool = False,
    debug: bool = False
) -> dict:
    """
    Redimensionne une photo en vignette JPEG.

    Args:
        chemin_source: Chemin vers la photo originale
        chemin_dest: Chemin vers la vignette de sortie
        taille_max: Taille maximale du côté le plus long (pixels)
        qualite: Qualité JPEG (1-100)
        verbose: Mode verbose
        debug: Mode debug

    Returns:
        dict: {
            "ok": bool,
            "source": str,
            "dest": str,
            "taille_avant": int,    # Octets
            "taille_apres": int,    # Octets
            "dimensions_avant": (w, h),
            "dimensions_apres": (w, h),
            "erreur": str ou None
        }
    """
    resultat = {
        "ok": False,
        "source": str(chemin_source),
        "dest": str(chemin_dest),
        "taille_avant": 0,
        "taille_apres": 0,
        "dimensions_avant": (0, 0),
        "dimensions_apres": (0, 0),
        "erreur": None
    }

    try:
        taille_avant = chemin_source.stat().st_size
        resultat["taille_avant"] = taille_avant

        with Image.open(chemin_source) as img:
            resultat["dimensions_avant"] = img.size

            # Convertir en RGB si nécessaire (PNG avec alpha, etc.)
            if img.mode in ('RGBA', 'P', 'LA'):
                img = img.convert('RGB')
            elif img.mode != 'RGB':
                img = img.convert('RGB')

            # Redimensionner en conservant le ratio
            img.thumbnail((taille_max, taille_max), Image.LANCZOS)
            resultat["dimensions_apres"] = img.size

            # Sauvegarder en JPEG optimisé
            img.save(chemin_dest, 'JPEG', quality=qualite, optimize=True)

        resultat["taille_apres"] = chemin_dest.stat().st_size
        resultat["ok"] = True

        if debug:
            ratio = resultat["taille_apres"] / resultat["taille_avant"] * 100 if resultat["taille_avant"] > 0 else 0
            print(f"[DEBUG] {chemin_source.name}: {resultat['dimensions_avant']} → {resultat['dimensions_apres']}, "
                  f"{taille_avant:,} → {resultat['taille_apres']:,} octets ({ratio:.1f}%)")

    except Exception as e:
        resultat["erreur"] = str(e)
        if verbose or debug:
            print(f"[ERREUR] {chemin_source.name}: {e}")

    return resultat


EXTENSIONS_IMAGES = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}


def traiter_dossier(
    dossier_source: Path,
    dossier_dest: Path,
    taille_max: int = 200,
    qualite: int = 75,
    verbose: bool = False,
    debug: bool = False
) -> dict:
    """
    Redimensionne toutes les photos d'un dossier.

    Args:
        dossier_source: Dossier contenant les photos originales
        dossier_dest: Dossier de sortie pour les vignettes
        taille_max: Taille maximale du côté le plus long
        qualite: Qualité JPEG
        verbose: Mode verbose
        debug: Mode debug

    Returns:
        dict: Statistiques globales
    """
    # Lister dynamiquement toutes les images du répertoire
    fichiers = sorted([
        f for f in dossier_source.iterdir()
        if f.is_file() and f.suffix.lower() in EXTENSIONS_IMAGES
    ])

    if not fichiers:
        print(f"[ERREUR] Aucune photo trouvée dans {dossier_source.resolve()}")
        print(f"         Extensions acceptées : {', '.join(sorted(EXTENSIONS_IMAGES))}")
        return {"nb_total": 0, "nb_ok": 0, "nb_erreur": 0}

    print(f"Photos trouvées  : {len(fichiers)}")
    print(f"Source           : {dossier_source.resolve()}")
    print(f"Destination      : {dossier_dest.resolve()}")
    print(f"Taille max       : {taille_max}px")
    print(f"Qualité JPEG     : {qualite}")
    print()

    # Créer le dossier de sortie
    dossier_dest.mkdir(parents=True, exist_ok=True)

    # Traitement batch avec barre de progression
    stats = {
        "nb_total": len(fichiers),
        "nb_ok": 0,
        "nb_erreur": 0,
        "taille_avant_total": 0,
        "taille_apres_total": 0,
        "erreurs": []
    }

    start_time = time.perf_counter()

    for chemin_source in tqdm(fichiers, desc="Redimensionnement", unit="photo",
                               bar_format="{l_bar}{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}]"):
        chemin_dest = dossier_dest / (chemin_source.stem + ".jpg")

        resultat = redimensionner_photo(
            chemin_source, chemin_dest,
            taille_max=taille_max,
            qualite=qualite,
            verbose=verbose,
            debug=debug
        )

        if resultat["ok"]:
            stats["nb_ok"] += 1
            stats["taille_avant_total"] += resultat["taille_avant"]
            stats["taille_apres_total"] += resultat["taille_apres"]
        else:
            stats["nb_erreur"] += 1
            stats["erreurs"].append(f"{chemin_source.name}: {resultat['erreur']}")

    elapsed = time.perf_counter() - start_time
    stats["temps_s"] = round(elapsed, 2)

    return stats


def main():
    """Point d'entrée CLI."""
    print(f"╔════════════════════════════════════════════════════════════════")
    print(f"║ {__pgm__} V{__version__} - {__date__}")
    print(f"║ Redimensionnement batch des portraits pour GitHub")
    print(f"╚════════════════════════════════════════════════════════════════")
    print()

    if len(sys.argv) < 2:
        print("Usage :")
        print(f"  python {__pgm__} <dossier_source> [options]")
        print()
        print("Arguments :")
        print("  dossier_source       Dossier contenant les photos")
        print()
        print("Options :")
        print("  -o, --output DIR     Dossier de sortie (défaut: <source>/thumbs)")
        print("  -s, --size N         Taille max en pixels (défaut: 200)")
        print("  -q, --quality N      Qualité JPEG 1-100 (défaut: 75)")
        print("  -v                   Affichage modéré")
        print("  -d                   Affichage complet")
        print()
        print("Exemples :")
        print(f"  python {__pgm__} C:\\PortraitsPhotofit\\1964N")
        print(f"  python {__pgm__} C:\\PortraitsPhotofit\\1964N -o C:\\cx\\data\\thumbs -s 150")
        print(f"  python {__pgm__} C:\\PortraitsPhotofit\\1964N -v")
        return 0

    parser = argparse.ArgumentParser(description="Redimensionnement batch des portraits")
    parser.add_argument('source', help='Dossier contenant les photos originales')
    parser.add_argument('-o', '--output', default=None, help='Dossier de sortie')
    parser.add_argument('-s', '--size', type=int, default=200, help='Taille max pixels')
    parser.add_argument('-q', '--quality', type=int, default=75, help='Qualité JPEG')
    parser.add_argument('-v', '--verbose', action='store_true', help='Affichage modéré')
    parser.add_argument('-d', '--debug', action='store_true', help='Affichage complet')

    args = parser.parse_args()

    dossier_source = Path(args.source)
    if not dossier_source.exists():
        print(f"[ERREUR] Dossier introuvable : {dossier_source.resolve()}")
        return 1

    if args.output:
        dossier_dest = Path(args.output)
    else:
        dossier_dest = dossier_source / "thumbs"

    stats = traiter_dossier(
        dossier_source=dossier_source,
        dossier_dest=dossier_dest,
        taille_max=args.size,
        qualite=args.quality,
        verbose=args.verbose,
        debug=args.debug
    )

    # Afficher le résumé
    print()
    print("═" * 70)
    print("RÉSUMÉ")
    print("═" * 70)

    if stats["nb_total"] == 0:
        print("Aucune photo traitée.")
        return 1

    print(f"Photos traitées  : {stats['nb_ok']}/{stats['nb_total']}")
    if stats["nb_erreur"] > 0:
        print(f"Erreurs          : {stats['nb_erreur']}")

    taille_avant_mo = stats["taille_avant_total"] / (1024 * 1024)
    taille_apres_mo = stats["taille_apres_total"] / (1024 * 1024)
    ratio = (1 - stats["taille_apres_total"] / stats["taille_avant_total"]) * 100 if stats["taille_avant_total"] > 0 else 0

    print(f"Taille avant     : {taille_avant_mo:.1f} Mo")
    print(f"Taille après     : {taille_apres_mo:.1f} Mo")
    print(f"Réduction        : {ratio:.1f}%")
    print(f"Taille moyenne   : {stats['taille_apres_total'] / max(stats['nb_ok'], 1) / 1024:.1f} Ko/photo")
    print(f"Temps            : {stats.get('temps_s', 0):.1f}s")
    print(f"Sortie           : {dossier_dest.resolve()}")

    if stats.get("erreurs"):
        print()
        print("Erreurs détaillées :")
        for err in stats["erreurs"][:20]:
            print(f"  ✗ {err}")
        if len(stats["erreurs"]) > 20:
            print(f"  ... et {len(stats['erreurs']) - 20} autres")

    print()
    print("✓ Prêt pour upload GitHub !")
    print(f"  Dossier à uploader : {dossier_dest.resolve()}")

    return 0 if stats["nb_erreur"] == 0 else 1


if __name__ == '__main__':
    sys.exit(main())
