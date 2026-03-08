#*TO*#
__pgm__ = "gen_variantes.py"
__version__ = "0.0.0"
__date__ = "01/01/1970 00:00"

import argparse
import hashlib
import os
import random
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont
from tqdm import tqdm

# ═══════════════════════════════════════════════════════════════════
#  CONSTANTES
# ═══════════════════════════════════════════════════════════════════

EXTENSIONS_IMAGES = {".jpg", ".jpeg", ".png", ".bmp", ".webp", ".tiff", ".tif"}
NUMERO_DEPART = 1000
PAS = 10
NB_VARIANTES = 9

# ═══════════════════════════════════════════════════════════════════
#  TRANSFORMATIONS
#  Chaque fonction prend (image_PIL, intensity 0.0→1.0, rng) et
#  retourne une image PIL transformée.
# ═══════════════════════════════════════════════════════════════════


def t_brightness(img, intensity, rng):
    """Ajuste la luminosité (+/-)."""
    direction = rng.choice([-1, 1])
    factor = 1.0 + intensity * 0.55 * direction
    return ImageEnhance.Brightness(img).enhance(max(factor, 0.15))


def t_contrast(img, intensity, rng):
    """Ajuste le contraste (+/-)."""
    direction = rng.choice([-1, 1])
    factor = 1.0 + intensity * 0.50 * direction
    return ImageEnhance.Contrast(img).enhance(max(factor, 0.15))


def t_saturation(img, intensity, rng):
    """Ajuste la saturation des couleurs (+/-)."""
    direction = rng.choice([-1, 1])
    factor = 1.0 + intensity * 0.65 * direction
    return ImageEnhance.Color(img).enhance(max(factor, 0.0))


def t_blur(img, intensity, rng):
    """Applique un flou gaussien progressif."""
    radius = intensity * 3.5
    return img.filter(ImageFilter.GaussianBlur(radius=radius))


def t_noise(img, intensity, rng):
    """Ajoute du bruit gaussien."""
    arr = np.array(img, dtype=np.float32)
    sigma = intensity * 35
    noise = rng.normal(0, sigma, arr.shape)
    arr = np.clip(arr + noise, 0, 255).astype(np.uint8)
    return Image.fromarray(arr)


def t_hue_shift(img, intensity, rng):
    """Décale la teinte (hue) dans l'espace HSV."""
    hsv = img.convert("HSV")
    arr = np.array(hsv)
    shift = int(intensity * 25 * rng.choice([-1, 1]))
    arr[:, :, 0] = ((arr[:, :, 0].astype(np.int16) + shift) % 256).astype(np.uint8)
    return Image.fromarray(arr, "HSV").convert("RGB")


def t_color_temperature(img, intensity, rng):
    """Décale la température de couleur (chaud/froid)."""
    arr = np.array(img, dtype=np.float32)
    shift = intensity * 30
    if rng.random() > 0.5:
        # Chaud
        arr[:, :, 0] = np.clip(arr[:, :, 0] + shift, 0, 255)
        arr[:, :, 2] = np.clip(arr[:, :, 2] - shift * 0.5, 0, 255)
    else:
        # Froid
        arr[:, :, 2] = np.clip(arr[:, :, 2] + shift, 0, 255)
        arr[:, :, 0] = np.clip(arr[:, :, 0] - shift * 0.5, 0, 255)
    return Image.fromarray(arr.astype(np.uint8))


def t_rotation(img, intensity, rng):
    """Rotation légère."""
    angle = intensity * 7 * rng.choice([-1, 1])
    return img.rotate(angle, resample=Image.BICUBIC, expand=False, fillcolor=(128, 128, 128))


def t_crop_resize(img, intensity, rng):
    """Recadrage léger puis remise à la taille d'origine."""
    w, h = img.size
    crop_pct = intensity * 0.08
    left = int(w * crop_pct * rng.random())
    top = int(h * crop_pct * rng.random())
    right = w - int(w * crop_pct * rng.random())
    bottom = h - int(h * crop_pct * rng.random())
    # Sécurité : au moins 50% de l'image
    right = max(right, left + w // 2)
    bottom = max(bottom, top + h // 2)
    return img.crop((left, top, right, bottom)).resize((w, h), Image.LANCZOS)


def t_gamma(img, intensity, rng):
    """Correction gamma."""
    direction = rng.choice([-1, 1])
    gamma = 1.0 + intensity * 0.7 * direction
    gamma = max(0.3, gamma)
    arr = np.array(img, dtype=np.float32) / 255.0
    arr = np.power(arr, 1.0 / gamma)
    return Image.fromarray((arr * 255).astype(np.uint8))


def t_channel_mix(img, intensity, rng):
    """Mélange partiel des canaux RGB."""
    arr = np.array(img, dtype=np.float32)
    mix = intensity * 0.25
    r, g, b = arr[:, :, 0].copy(), arr[:, :, 1].copy(), arr[:, :, 2].copy()
    # Rotation partielle des canaux
    arr[:, :, 0] = np.clip(r * (1 - mix) + g * mix, 0, 255)
    arr[:, :, 1] = np.clip(g * (1 - mix) + b * mix, 0, 255)
    arr[:, :, 2] = np.clip(b * (1 - mix) + r * mix, 0, 255)
    return Image.fromarray(arr.astype(np.uint8))


def t_sharpness(img, intensity, rng):
    """Sur-accentuation ou adoucissement."""
    if rng.random() > 0.5:
        factor = 1.0 + intensity * 2.5
    else:
        factor = 1.0 - intensity * 0.7
    return ImageEnhance.Sharpness(img).enhance(max(factor, 0.1))


# Pool complet des transformations
TRANSFORMS_POOL = [
    t_brightness,
    t_contrast,
    t_saturation,
    t_blur,
    t_noise,
    t_hue_shift,
    t_color_temperature,
    t_rotation,
    t_crop_resize,
    t_gamma,
    t_channel_mix,
    t_sharpness,
]


# ═══════════════════════════════════════════════════════════════════
#  FONCTIONS UTILITAIRES
# ═══════════════════════════════════════════════════════════════════


def image_hash_seed(filepath: Path) -> int:
    """Calcule un seed déterministe à partir du contenu du fichier image."""
    h = hashlib.md5(filepath.read_bytes()).hexdigest()
    return int(h[:8], 16)


def etiqueter_image(img: Image.Image, numero: int) -> Image.Image:
    """Inscrit un chiffre rouge (1-9) en bas à droite de l'image."""
    img_copy = img.copy()
    draw = ImageDraw.Draw(img_copy)
    w, h = img_copy.size

    # Taille de police proportionnelle à l'image (environ 5% de la hauteur, min 16px)
    font_size = max(16, int(h * 0.05))

    # Essayer de trouver une police système
    font = None
    font_paths = [
        "arial.ttf",
        "Arial.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
        "C:/Windows/Fonts/arial.ttf",
        "C:/Windows/Fonts/arialbd.ttf",
    ]
    for fp in font_paths:
        try:
            font = ImageFont.truetype(fp, font_size)
            break
        except (OSError, IOError):
            continue

    if font is None:
        # Fallback : police par défaut de Pillow
        try:
            font = ImageFont.load_default(size=font_size)
        except TypeError:
            font = ImageFont.load_default()

    texte = str(numero)

    # Mesurer le texte
    bbox = draw.textbbox((0, 0), texte, font=font)
    tw = bbox[2] - bbox[0]
    th = bbox[3] - bbox[1]

    # Position : bas-droite avec marge
    marge = max(4, int(min(w, h) * 0.02))
    x = w - tw - marge
    y = h - th - marge

    # Fond semi-transparent pour lisibilité
    padding = 3
    draw.rectangle(
        [x - padding, y - padding, x + tw + padding, y + th + padding],
        fill=(0, 0, 0, 180) if img_copy.mode == "RGBA" else (0, 0, 0),
    )

    # Texte rouge vif
    draw.text((x, y), texte, fill=(255, 0, 0), font=font)

    return img_copy


def generer_variantes(img: Image.Image, seed: int, verbose: bool = False) -> list:
    """
    Génère 9 variantes d'une image avec dégradation progressive.

    Retourne une liste de 9 images PIL (variante 1 à 9).
    Les transformations appliquées dépendent du seed (hash de l'image source)
    pour que chaque photo ait un profil de dégradation différent.
    """
    rng = np.random.RandomState(seed)

    # Mélanger le pool de transformations de manière déterministe pour cette image
    indices = list(range(len(TRANSFORMS_POOL)))
    rng.shuffle(indices)
    transforms_ordre = [TRANSFORMS_POOL[i] for i in indices]

    variantes = []

    for niveau in range(1, NB_VARIANTES + 1):
        # Intensité progressive : de 0.08 (niveau 1) à 1.0 (niveau 9)
        intensity = niveau / NB_VARIANTES

        # Nombre de transformations appliquées : croissant avec le niveau
        #   niveau 1 → 2 transforms, niveau 9 → 7-8 transforms
        nb_transforms = min(2 + (niveau * 2) // 3, len(transforms_ordre))

        # Sélectionner les premières nb_transforms du pool mélangé
        # (le mélange est propre à chaque image source)
        transforms_actives = transforms_ordre[:nb_transforms]

        if verbose:
            noms = [t.__name__ for t in transforms_actives]
            print(f"    [DEBUG] Variante {niveau}: intensity={intensity:.2f}, "
                  f"transforms({nb_transforms})={noms}")

        # Appliquer séquentiellement
        result = img.copy()
        if result.mode != "RGB":
            result = result.convert("RGB")

        for transform_fn in transforms_actives:
            try:
                # Chaque transform reçoit son propre RNG dérivé
                t_seed = seed + niveau * 100 + hash(transform_fn.__name__) % 10000
                t_rng = np.random.RandomState(t_seed & 0x7FFFFFFF)
                result = transform_fn(result, intensity, t_rng)
            except Exception as e:
                if verbose:
                    print(f"    [DEBUG] WARN: {transform_fn.__name__} échouée: {e}")

        # Étiqueter avec le numéro de variante
        result = etiqueter_image(result, niveau)
        variantes.append(result)

    return variantes


def lister_images(repertoire: Path) -> list:
    """Liste toutes les images du répertoire (non récursif)."""
    images = []
    for f in sorted(repertoire.iterdir()):
        if f.is_file() and f.suffix.lower() in EXTENSIONS_IMAGES:
            images.append(f)
    return images


# ═══════════════════════════════════════════════════════════════════
#  PROGRAMME PRINCIPAL
# ═══════════════════════════════════════════════════════════════════


def afficher_aide():
    """Affiche l'aide CLI."""
    print("=" * 60)
    print("Génère 9 variantes de portrait par photo avec dégradation")
    print("progressive pour tester la recherche par ressemblance.")
    print()
    print("Usage :")
    print(f"  python {__pgm__} <répertoire_source> [options]")
    print()
    print("Arguments :")
    print("  répertoire_source  Répertoire contenant les photos d'origine")
    print()
    print("Options :")
    print("  -o, --output DIR   Répertoire de sortie (défaut: source/variantes)")
    print("  -v, --verbose      Mode verbeux (détail des transformations)")
    print("  -d, --debug        Mode debug (équivalent à -v)")
    print("  --dry-run          Simule sans créer de fichiers")
    print("  --format EXT       Format de sortie: jpg, png (défaut: jpg)")
    print("  --quality N        Qualité JPEG 1-100 (défaut: 92)")
    print()
    print("Numérotation :")
    print("  Photo 1 → 1000.jpg (original), 1001-1009 (variantes)")
    print("  Photo 2 → 1010.jpg (original), 1011-1019 (variantes)")
    print("  Photo N → (1000+N*10).jpg, +1 à +9 pour variantes")
    print()
    print("Exemples :")
    print(f"  python {__pgm__} ./photos")
    print(f"  python {__pgm__} ./photos -o ./sortie -v")
    print(f"  python {__pgm__} ./photos --dry-run")
    print(f"  python {__pgm__} ./photos --format png --quality 95 -d")


def main():
    print(f"{__pgm__} V{__version__} - {__date__}")

    if len(sys.argv) < 2 or sys.argv[1] in ("-h", "--help"):
        afficher_aide()
        sys.exit(0)

    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("source", type=str, help="Répertoire source")
    parser.add_argument("-o", "--output", type=str, default=None)
    parser.add_argument("-v", "--verbose", action="store_true")
    parser.add_argument("-d", "--debug", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--format", type=str, default="jpg", choices=["jpg", "png"])
    parser.add_argument("--quality", type=int, default=92)

    args = parser.parse_args()
    verbose = args.verbose or args.debug

    # ── Vérification du répertoire source ──
    source_dir = Path(args.source).resolve()
    if not source_dir.is_dir():
        print(f"ERREUR : Le répertoire '{source_dir}' n'existe pas.")
        sys.exit(1)

    # ── Répertoire de sortie ──
    if args.output:
        output_dir = Path(args.output).resolve()
    else:
        output_dir = source_dir / "variantes"

    if not args.dry_run:
        output_dir.mkdir(parents=True, exist_ok=True)
    print(f"Source  : {source_dir}")
    print(f"Sortie  : {output_dir}")

    # ── Lister les images ──
    images = lister_images(source_dir)
    nb_images = len(images)

    if nb_images == 0:
        print(f"ERREUR : Aucune image trouvée dans '{source_dir}'")
        print(f"  Extensions acceptées : {', '.join(sorted(EXTENSIONS_IMAGES))}")
        sys.exit(1)

    print(f"Images trouvées : {nb_images}")
    print(f"Fichiers à produire : {nb_images} originaux + {nb_images * NB_VARIANTES} variantes "
          f"= {nb_images * (1 + NB_VARIANTES)} fichiers")

    # Vérifier que la numérotation ne dépasse pas
    dernier_numero = NUMERO_DEPART + (nb_images - 1) * PAS + NB_VARIANTES
    print(f"Numérotation : {NUMERO_DEPART} → {dernier_numero}")

    if args.dry_run:
        print("\n── MODE DRY-RUN : aucun fichier ne sera créé ──")

    ext = f".{args.format}"

    # ── Mapping original → nouveau nom pour traçabilité ──
    mapping_lines = ["# Mapping original → nouveau numéro"]
    mapping_lines.append("# original;numero;fichier_sortie")

    # ── Traitement ──
    print()
    for idx, img_path in enumerate(tqdm(images, desc="Traitement", unit="photo")):
        numero_base = NUMERO_DEPART + idx * PAS

        if verbose:
            print(f"\n  [{idx+1}/{nb_images}] {img_path.name} → {numero_base}")

        # Charger l'image
        try:
            img = Image.open(img_path)
            if img.mode not in ("RGB", "RGBA"):
                img = img.convert("RGB")
        except Exception as e:
            print(f"  ERREUR lecture '{img_path}': {e}")
            continue

        seed = image_hash_seed(img_path)

        if verbose:
            print(f"    Taille: {img.size[0]}x{img.size[1]}, seed: {seed}")

        # ── Sauvegarder l'original (sans étiquette) ──
        nom_original = f"{numero_base}{ext}"
        chemin_original = output_dir / nom_original
        mapping_lines.append(f"{img_path.name};{numero_base};{nom_original}")

        if not args.dry_run:
            img_rgb = img.convert("RGB") if img.mode != "RGB" else img
            if ext == ".jpg":
                img_rgb.save(chemin_original, "JPEG", quality=args.quality)
            else:
                img_rgb.save(chemin_original, "PNG")

        if verbose:
            print(f"    Original → {chemin_original}")

        # ── Générer les 9 variantes ──
        variantes = generer_variantes(img, seed, verbose=verbose)

        for v_idx, v_img in enumerate(variantes, start=1):
            numero_variante = numero_base + v_idx
            nom_variante = f"{numero_variante}{ext}"
            chemin_variante = output_dir / nom_variante

            if not args.dry_run:
                if ext == ".jpg":
                    v_img.save(chemin_variante, "JPEG", quality=args.quality)
                else:
                    v_img.save(chemin_variante, "PNG")

            if verbose:
                print(f"    Variante {v_idx} → {chemin_variante}")

    # ── Sauvegarder le mapping ──
    if not args.dry_run:
        mapping_path = output_dir / "mapping_originaux.csv"
        with open(mapping_path, "w", encoding="utf-8-sig") as f:
            f.write("\n".join(mapping_lines))
        print(f"\nMapping sauvegardé : {mapping_path}")

    # ── Résumé final ──
    print("\n" + "=" * 60)
    print("RÉSUMÉ")
    print("=" * 60)
    print(f"  Photos traitées  : {nb_images}")
    print(f"  Fichiers créés   : {nb_images * (1 + NB_VARIANTES)}")
    print(f"  Répertoire       : {output_dir}")
    print(f"  Numérotation     : {NUMERO_DEPART} → {dernier_numero}")
    print(f"  Format           : {args.format.upper()}, qualité={args.quality}")
    if args.dry_run:
        print("  ⚠ MODE DRY-RUN : aucun fichier n'a été créé")
    print()


if __name__ == "__main__":
    main()
