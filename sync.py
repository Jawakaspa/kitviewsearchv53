# sync.py V1.0.3 - 12/01/2026 15:03:57
__pgm__ = "sync.py"
__version__ = "1.0.3"
__date__ = "12/01/2026 15:03:57"

"""
sync.py - Comparaison et synchronisation récursive de deux répertoires

Usage:
    python sync.py [repa] [repb] [ok]

Arguments:
    repa    Répertoire A (défaut: c:\\cx)
    repb    Répertoire B (défaut: c:\\kitviewsearchv5)
    ok      Si présent, effectue la synchronisation

Exclusions automatiques:
    - Fichiers: *.tmp
    - Répertoires: .git, __pycache__, .tmp.driveupload, + contenant "old" ou "convs"

Exemples:
    python sync.py                           # Compare avec valeurs par défaut
    python sync.py c:\\cx c:\\projet         # Compare deux répertoires
    python sync.py c:\\cx c:\\projet ok      # Compare ET synchronise
"""

import os
import sys
import shutil
from datetime import datetime
from pathlib import Path

# Valeurs par défaut
DEFAULT_REPA = r"c:\cx"
DEFAULT_REPB = r"c:\kitviewsearchv5"

# Patterns d'exclusion
EXCLUDED_EXTENSIONS = {".tmp"}  # Extensions de fichiers à ignorer

# Répertoires à ignorer :
# - Noms exacts : .git, __pycache__, .tmp.driveupload
# - Noms contenant : old, convs (donc oldies, myold, conversations, etc.)
EXCLUDED_DIR_EXACT = {".git", "__pycache__", ".tmp.driveupload"}
EXCLUDED_DIR_CONTAINS = {"old", "convs"}


def should_exclude_path(path: Path, base_dir: Path) -> bool:
    """
    Vérifie si un chemin doit être exclu.
    
    Exclusions:
    - Fichiers avec extensions dans EXCLUDED_EXTENSIONS
    - Répertoires avec noms exacts dans EXCLUDED_DIR_EXACT
    - Répertoires dont le nom contient un pattern de EXCLUDED_DIR_CONTAINS
    """
    # Vérifier l'extension du fichier
    if path.is_file() and path.suffix.lower() in EXCLUDED_EXTENSIONS:
        return True
    
    # Vérifier si un des répertoires parents doit être exclu
    try:
        relative = path.relative_to(base_dir)
        for part in relative.parts:
            part_lower = part.lower()
            
            # Exclusion par nom exact (ex: .git, __pycache__)
            if part_lower in EXCLUDED_DIR_EXACT:
                return True
            
            # Exclusion par pattern contenu (ex: old dans oldies)
            for pattern in EXCLUDED_DIR_CONTAINS:
                if pattern in part_lower:
                    return True
    except ValueError:
        pass
    
    return False


def get_all_files(directory: Path) -> dict[str, Path]:
    """
    Récupère tous les fichiers d'un répertoire récursivement.
    Retourne un dict {chemin_relatif: chemin_absolu}
    Exclut les fichiers et répertoires selon les patterns définis.
    """
    files = {}
    excluded_count = 0
    
    if not directory.exists():
        print(f"[ERREUR] Le répertoire n'existe pas: {directory}")
        return files
    
    for file_path in directory.rglob("*"):
        if file_path.is_file():
            if should_exclude_path(file_path, directory):
                excluded_count += 1
                continue
            # Chemin relatif par rapport au répertoire racine
            relative = file_path.relative_to(directory)
            files[str(relative)] = file_path
    
    if excluded_count > 0:
        print(f"       → {excluded_count} fichier(s) exclu(s) par les filtres")
    
    return files


def compare_directories(repa: Path, repb: Path) -> tuple[list, list, list, list]:
    """
    Compare deux répertoires récursivement.
    
    Retourne:
        - newer_in_a: fichiers plus récents dans repa
        - newer_in_b: fichiers plus récents dans repb
        - only_in_a: fichiers uniquement dans repa
        - only_in_b: fichiers uniquement dans repb
    """
    print(f"\n[INFO] Scan de {repa}...")
    files_a = get_all_files(repa)
    print(f"       → {len(files_a)} fichier(s) retenu(s)")
    
    print(f"[INFO] Scan de {repb}...")
    files_b = get_all_files(repb)
    print(f"       → {len(files_b)} fichier(s) retenu(s)")
    
    all_relatives = set(files_a.keys()) | set(files_b.keys())
    
    newer_in_a = []  # (chemin_relatif, date_a, date_b)
    newer_in_b = []
    only_in_a = []
    only_in_b = []
    identical = 0
    
    for rel_path in sorted(all_relatives):
        in_a = rel_path in files_a
        in_b = rel_path in files_b
        
        if in_a and in_b:
            # Fichier présent dans les deux → comparer les dates
            mtime_a = files_a[rel_path].stat().st_mtime
            mtime_b = files_b[rel_path].stat().st_mtime
            
            # Tolérance de 2 secondes pour les différences de système de fichiers
            if abs(mtime_a - mtime_b) < 2:
                identical += 1
            elif mtime_a > mtime_b:
                newer_in_a.append((rel_path, mtime_a, mtime_b, files_a[rel_path], files_b[rel_path]))
            else:
                newer_in_b.append((rel_path, mtime_a, mtime_b, files_a[rel_path], files_b[rel_path]))
        
        elif in_a:
            only_in_a.append((rel_path, files_a[rel_path]))
        
        else:
            only_in_b.append((rel_path, files_b[rel_path]))
    
    print(f"\n[INFO] Fichiers identiques (même date): {identical}")
    
    return newer_in_a, newer_in_b, only_in_a, only_in_b


def format_date(timestamp: float) -> str:
    """Formate un timestamp en date lisible."""
    return datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d %H:%M:%S")


def display_results(repa: Path, repb: Path, newer_in_a: list, newer_in_b: list, 
                   only_in_a: list, only_in_b: list):
    """Affiche les résultats de la comparaison."""
    
    print("\n" + "=" * 80)
    print(f"RÉSULTATS DE LA COMPARAISON")
    print("=" * 80)
    
    # Fichiers plus récents dans A
    print(f"\n📁 [{repa.name}] Fichiers plus RÉCENTS dans A ({len(newer_in_a)}):")
    print("-" * 60)
    if newer_in_a:
        for rel_path, mtime_a, mtime_b, _, _ in newer_in_a:
            print(f"  {rel_path}")
            print(f"      A: {format_date(mtime_a)}  |  B: {format_date(mtime_b)}")
    else:
        print("  (aucun)")
    
    # Fichiers plus récents dans B
    print(f"\n📁 [{repb.name}] Fichiers plus RÉCENTS dans B ({len(newer_in_b)}):")
    print("-" * 60)
    if newer_in_b:
        for rel_path, mtime_a, mtime_b, _, _ in newer_in_b:
            print(f"  {rel_path}")
            print(f"      A: {format_date(mtime_a)}  |  B: {format_date(mtime_b)}")
    else:
        print("  (aucun)")
    
    # Fichiers uniquement dans A
    print(f"\n📄 Fichiers UNIQUEMENT dans A ({len(only_in_a)}):")
    print("-" * 60)
    if only_in_a:
        for rel_path, _ in only_in_a:
            print(f"  {rel_path}")
    else:
        print("  (aucun)")
    
    # Fichiers uniquement dans B
    print(f"\n📄 Fichiers UNIQUEMENT dans B ({len(only_in_b)}):")
    print("-" * 60)
    if only_in_b:
        for rel_path, _ in only_in_b:
            print(f"  {rel_path}")
    else:
        print("  (aucun)")
    
    print("\n" + "=" * 80)


def synchronize(repa: Path, repb: Path, newer_in_a: list, newer_in_b: list,
                only_in_a: list, only_in_b: list):
    """
    Synchronise les deux répertoires:
    - Copie les fichiers plus récents vers l'autre répertoire
    - Copie les fichiers uniques vers l'autre répertoire
    """
    print("\n🔄 SYNCHRONISATION EN COURS...")
    print("-" * 60)
    
    copied = 0
    errors = 0
    
    # Copier les fichiers plus récents de A vers B
    for rel_path, _, _, src_path, dst_path in newer_in_a:
        try:
            dst_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src_path, dst_path)
            print(f"  [A→B] {rel_path}")
            copied += 1
        except Exception as e:
            print(f"  [ERREUR] {rel_path}: {e}")
            errors += 1
    
    # Copier les fichiers plus récents de B vers A
    for rel_path, _, _, dst_path, src_path in newer_in_b:
        try:
            dst_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src_path, dst_path)
            print(f"  [B→A] {rel_path}")
            copied += 1
        except Exception as e:
            print(f"  [ERREUR] {rel_path}: {e}")
            errors += 1
    
    # Copier les fichiers uniques de A vers B
    for rel_path, src_path in only_in_a:
        try:
            dst_path = repb / rel_path
            dst_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src_path, dst_path)
            print(f"  [A→B] {rel_path} (nouveau)")
            copied += 1
        except Exception as e:
            print(f"  [ERREUR] {rel_path}: {e}")
            errors += 1
    
    # Copier les fichiers uniques de B vers A
    for rel_path, src_path in only_in_b:
        try:
            dst_path = repa / rel_path
            dst_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src_path, dst_path)
            print(f"  [B→A] {rel_path} (nouveau)")
            copied += 1
        except Exception as e:
            print(f"  [ERREUR] {rel_path}: {e}")
            errors += 1
    
    print("-" * 60)
    print(f"✅ Synchronisation terminée: {copied} fichier(s) copié(s), {errors} erreur(s)")


def main():
    """Point d'entrée principal."""
    print(f"{__pgm__} V{__version__} - {__date__}")
    print(f"Heure de début: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Afficher les exclusions actives
    print(f"[CONFIG] Extensions exclues: {', '.join(sorted(EXCLUDED_EXTENSIONS))}")
    print(f"[CONFIG] Répertoires exclus (exact): {', '.join(sorted(EXCLUDED_DIR_EXACT))}")
    print(f"[CONFIG] Répertoires exclus (contenant): {', '.join(sorted(EXCLUDED_DIR_CONTAINS))}")
    
    # Parsing des arguments
    args = sys.argv[1:]
    
    # Déterminer repa, repb et mode sync
    repa = Path(DEFAULT_REPA)
    repb = Path(DEFAULT_REPB)
    do_sync = False
    
    # Filtrer "ok" des arguments
    if "ok" in [a.lower() for a in args]:
        do_sync = True
        args = [a for a in args if a.lower() != "ok"]
    
    # Assigner les répertoires
    if len(args) >= 1:
        repa = Path(args[0])
    if len(args) >= 2:
        repb = Path(args[1])
    
    # Afficher la configuration
    print(f"\nRépertoire A: {repa.absolute()}")
    print(f"Répertoire B: {repb.absolute()}")
    print(f"Mode: {'SYNCHRONISATION' if do_sync else 'COMPARAISON SEULE'}")
    
    # Vérifier l'existence des répertoires
    if not repa.exists():
        print(f"\n[ERREUR] Le répertoire A n'existe pas: {repa.absolute()}")
        sys.exit(1)
    if not repb.exists():
        print(f"\n[ERREUR] Le répertoire B n'existe pas: {repb.absolute()}")
        sys.exit(1)
    
    # Comparer
    newer_in_a, newer_in_b, only_in_a, only_in_b = compare_directories(repa, repb)
    
    # Afficher les résultats
    display_results(repa, repb, newer_in_a, newer_in_b, only_in_a, only_in_b)
    
    # Synchroniser si demandé
    if do_sync:
        if newer_in_a or newer_in_b or only_in_a or only_in_b:
            synchronize(repa, repb, newer_in_a, newer_in_b, only_in_a, only_in_b)
        else:
            print("\n✅ Les répertoires sont déjà synchronisés, rien à faire.")
    else:
        total_diff = len(newer_in_a) + len(newer_in_b) + len(only_in_a) + len(only_in_b)
        if total_diff > 0:
            print(f"\n💡 Pour synchroniser, relancer avec 'ok': python {__pgm__} {repa} {repb} ok")
    
    print(f"\nHeure de fin: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")


if __name__ == "__main__":
    main()
