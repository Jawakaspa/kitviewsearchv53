#*TO*#
__pgm__ = "synchro_render.py"
__version__ = "0.0.0"
__date__ = "07/03/2026 00:00"

"""
synchro_render.py — Synchronisation C:\\cx → D:\\kitviewsearchvNN + push Render

Usage :
  python synchro_render.py                         # Affiche l'aide
  python synchro_render.py --copy                  # Diff + copie (chemins par défaut)
  python synchro_render.py --render                # Diff + copie + git push
  python synchro_render.py --src C:/cx --dst D:/v53 --copy   # Chemins personnalisés
  python synchro_render.py --branch main           # Branche git cible (défaut: main)
  python synchro_render.py --copy -d               # Mode debug (détail fichier par fichier)
"""

import sys
import os
import shutil
import hashlib
import subprocess
from pathlib import Path
from datetime import datetime

# ─────────────────────────────────────────────
# CONFIGURATION PAR DÉFAUT (modifiable en argument)
# ─────────────────────────────────────────────
DEFAULT_SRC = Path(r"C:\cx")
DEFAULT_DST = Path(r"D:\kitviewsearchv53")

# Dossiers et fichiers à ignorer dans la comparaison
IGNORE_DIRS  = {".git", "__pycache__", ".pytest_cache", "node_modules",
                "prospects_photos", "logs"}
IGNORE_FILES = {".gitignore", "*.pyc", "*.log", "env-local.js"}

# Extensions à comparer (None = tout comparer)
EXTENSIONS   = None   # ou {".py", ".html", ".js", ".css", ".json", ".md"}

# ─────────────────────────────────────────────
# UTILITAIRES
# ─────────────────────────────────────────────
DEBUG = "-d" in sys.argv or "--debug" in sys.argv

def log(msg):
    print(msg)

def dbg(msg):
    if DEBUG:
        print(f"[DEBUG] {msg}")

def md5(path: Path) -> str:
    h = hashlib.md5()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()

def should_ignore(path: Path) -> bool:
    for part in path.parts:
        if part in IGNORE_DIRS:
            return True
    name = path.name
    for pat in IGNORE_FILES:
        if pat.startswith("*"):
            if name.endswith(pat[1:]):
                return True
        elif name == pat:
            return True
    if EXTENSIONS and path.suffix.lower() not in EXTENSIONS:
        return True
    return False

def human_size(size: int) -> str:
    for unit in ("o", "Ko", "Mo", "Go"):
        if size < 1024:
            return f"{size:.0f} {unit}"
        size /= 1024
    return f"{size:.1f} To"

# ─────────────────────────────────────────────
# COMPARAISON
# ─────────────────────────────────────────────
def compare_trees(src: Path, dst: Path) -> dict:
    """
    Retourne un dict avec :
      - modified : fichiers présents dans src et dst mais différents
      - src_only : fichiers présents dans src mais pas dans dst (nouveaux)
      - dst_only : fichiers présents dans dst mais pas dans src (supprimés côté src)
    """
    result = {"modified": [], "src_only": [], "dst_only": []}

    # Index des fichiers src
    src_files = {}
    for f in src.rglob("*"):
        if f.is_file():
            rel = f.relative_to(src)
            if not should_ignore(rel):
                src_files[rel] = f

    # Index des fichiers dst
    dst_files = {}
    for f in dst.rglob("*"):
        if f.is_file():
            rel = f.relative_to(dst)
            if not should_ignore(rel):
                dst_files[rel] = f

    # Comparaison
    all_keys = set(src_files) | set(dst_files)
    for rel in sorted(all_keys):
        if rel in src_files and rel not in dst_files:
            result["src_only"].append(rel)
            dbg(f"NOUVEAU   : {rel}")
        elif rel in dst_files and rel not in src_files:
            result["dst_only"].append(rel)
            dbg(f"src ABSENT: {rel}")
        else:
            s, d = src_files[rel], dst_files[rel]
            if s.stat().st_size != d.stat().st_size or md5(s) != md5(d):
                result["modified"].append(rel)
                dbg(f"MODIFIÉ   : {rel}")
            else:
                dbg(f"IDENTIQUE : {rel}")

    return result

# ─────────────────────────────────────────────
# AFFICHAGE DU RAPPORT
# ─────────────────────────────────────────────
def print_report(diff: dict, src: Path = None, dst: Path = None):
    if src is None: src = DEFAULT_SRC
    if dst is None: dst = DEFAULT_DST
    total = len(diff["modified"]) + len(diff["src_only"]) + len(diff["dst_only"])

    if total == 0:
        log("\n✅ Les deux dossiers sont identiques — rien à synchroniser.")
        return

    if diff["modified"]:
        log(f"\n📝 MODIFIÉS ({len(diff['modified'])} fichier(s)) :")
        for rel in diff["modified"]:
            src_f = src / rel
            dst_f = dst / rel
            src_sz = human_size(src_f.stat().st_size)
            dst_sz = human_size(dst_f.stat().st_size)
            src_dt = datetime.fromtimestamp(src_f.stat().st_mtime).strftime("%d/%m %H:%M")
            dst_dt = datetime.fromtimestamp(dst_f.stat().st_mtime).strftime("%d/%m %H:%M")
            log(f"   ✏️  {rel}")
            log(f"       CX  : {src_sz:>8}  {src_dt}")
            log(f"       dst : {dst_sz:>8}  {dst_dt}")

    if diff["src_only"]:
        log(f"\n🆕 NOUVEAUX dans CX ({len(diff['src_only'])} fichier(s)) :")
        for rel in diff["src_only"]:
            sz = human_size((src / rel).stat().st_size)
            log(f"   ➕ {rel}  ({sz})")

    if diff["dst_only"]:
        log(f"\n🗑️  ABSENTS DE CX ({len(diff['dst_only'])} fichier(s)) :")
        log("   (présents dans dst mais supprimés côté CX — non touchés)")
        for rel in diff["dst_only"]:
            log(f"   ❓ {rel}")

    log(f"\n{'─'*60}")
    log(f"   Total à copier : {len(diff['modified']) + len(diff['src_only'])} fichier(s)")

# ─────────────────────────────────────────────
# COPIE
# ─────────────────────────────────────────────
def copy_files(diff: dict, src: Path = None, dst: Path = None) -> int:
    if src is None: src = DEFAULT_SRC
    if dst is None: dst = DEFAULT_DST
    to_copy = diff["modified"] + diff["src_only"]
    if not to_copy:
        log("  Rien à copier.")
        return 0

    ok = 0
    for rel in to_copy:
        src_f = src / rel
        dst_f = dst / rel
        try:
            dst_f.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src_f, dst_f)
            log(f"   ✅ {rel}")
            ok += 1
        except Exception as e:
            log(f"   ❌ {rel} → {e}")

    return ok

# ─────────────────────────────────────────────
# GIT PUSH → RENDER
# ─────────────────────────────────────────────
def git_push(diff: dict, dst: Path = None, branch: str = "main") -> bool:
    if dst is None: dst = DEFAULT_DST
    changed = diff["modified"] + diff["src_only"]

    log(f"\n{'═'*60}")
    log("🚀 DÉPLOIEMENT SUR RENDER (git)")
    log(f"{'═'*60}")
    log(f"  Dossier git : {dst}")
    log(f"  Branche     : {branch}")

    # Vérifier que c'est un repo git
    git_dir = dst / ".git"
    if not git_dir.exists():
        log(f"\n❌ {dst} n'est pas un dépôt git !")
        log("   Initialisez d'abord avec : git init && git remote add origin <url>")
        return False

    # git add des fichiers modifiés seulement
    files_to_add = [str(dst / rel) for rel in changed]
    if not files_to_add:
        log("\n  Rien à commiter.")
        return True

    # git add
    log(f"\n  📋 git add ({len(files_to_add)} fichier(s))...")
    r = subprocess.run(["git", "-C", str(dst), "add"] + files_to_add,
                       capture_output=True, text=True)
    # Ignorer les warnings LF/CRLF (returncode=0 même avec warnings sur stderr)
    real_errors = [l for l in r.stderr.splitlines()
                   if l.strip() and not l.startswith("warning:") and not l.startswith("hint:")]
    if r.returncode != 0 and real_errors:
        log(f"  ❌ git add échoué :\n" + "\n".join(real_errors))
        return False
    if r.stderr.strip():
        log(f"  ℹ️  git add warnings (ignorés) : {len(r.stderr.splitlines())} ligne(s)")
    log("  ✅ git add OK")

    # git commit
    nb = len(changed)
    # Déduire le label depuis le nom du dossier destination (ex: kitviewsearchv53 → KVS53)
    import re
    version_match = re.search(r'v(\d+)', dst.name, re.IGNORECASE)
    label = f"KVS{version_match.group(1)}" if version_match else "KVS"
    msg = f"{label} sync {datetime.now().strftime('%d/%m/%Y %H:%M')} — {nb} fichier(s) mis à jour"
    log(f"\n  📝 git commit : {msg}")
    r = subprocess.run(["git", "-C", str(dst), "commit", "-m", msg],
                       capture_output=True, text=True)
    if r.returncode != 0:
        log(f"  ❌ git commit échoué :\n{r.stderr}")
        return False
    log("  ✅ git commit OK")

    # git push
    log("\n  ⬆️  git push origin main...")
    r = subprocess.run(["git", "-C", str(dst), "push", "origin", branch],
                       capture_output=True, text=True)
    if r.returncode != 0:
        log(f"  ❌ git push échoué :\n{r.stderr}")
        return False
    log("  ✅ git push OK → Render va redéployer automatiquement")
    return True

# ─────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────
def parse_args():
    """Parse les arguments --src, --dst, --branch, --copy, --render, -d."""
    args = sys.argv[1:]
    src  = DEFAULT_SRC
    dst  = DEFAULT_DST
    branch = "main"
    do_copy = do_render = False

    i = 0
    while i < len(args):
        a = args[i]
        if a == "--src" and i + 1 < len(args):
            src = Path(args[i+1]); i += 2
        elif a == "--dst" and i + 1 < len(args):
            dst = Path(args[i+1]); i += 2
        elif a == "--branch" and i + 1 < len(args):
            branch = args[i+1]; i += 2
        elif a == "--copy":
            do_copy = True; i += 1
        elif a == "--render":
            do_render = True; i += 1
        else:
            i += 1
    return src, dst, branch, do_copy, do_render


def main():
    print(f"{__pgm__} V{__version__} - {__date__}")

    src, dst, branch, do_copy, do_render = parse_args()

    if not (do_copy or do_render):
        print(__doc__)
        return

    # Vérifications
    if not src.exists():
        log(f"\n❌ Dossier source introuvable : {src}")
        sys.exit(1)
    if not dst.exists():
        log(f"\n❌ Dossier destination introuvable : {dst}")
        log(f"   Créez-le d'abord ou vérifiez le chemin.")
        sys.exit(1)

    # ── Analyse ──
    log(f"\n{'═'*60}")
    log(f"  ANALYSE DES DIFFÉRENCES")
    log(f"{'═'*60}")
    log(f"  Source      : {src}")
    log(f"  Destination : {dst}")
    log(f"  Branche git : {branch}")
    log(f"  Date        : {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
    log(f"{'─'*60}")
    log("  Comparaison en cours...")

    diff = compare_trees(src, dst)
    print_report(diff, src, dst)

    total_to_copy = len(diff["modified"]) + len(diff["src_only"])

    if total_to_copy == 0 and not do_render:
        return

    # ── Copie ──
    if do_copy or do_render:
        log(f"\n{'═'*60}")
        log(f"📂 COPIE {src} → {dst}")
        log(f"{'═'*60}")
        nb = copy_files(diff, src, dst)
        log(f"\n  ✅ {nb} fichier(s) copié(s) avec succès")
    elif total_to_copy > 0:
        log(f"\n  💡 Pour copier, relancer avec --copy ou --render")

    # ── Push Render ──
    if do_render:
        git_push(diff, dst, branch)


if __name__ == "__main__":
    main()
