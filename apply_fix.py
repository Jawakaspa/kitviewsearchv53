"""
Applique les corrections -v/-d aux 4 modules.
Usage : copier dans c:/g/ et exécuter : python apply_fix.py
"""
import re, os

files_fixes = {
    "detcount.py": [
        ("add_argument('--verbose'", "add_argument('-v', '--verbose'"),
        ("add_argument('--debug'", "add_argument('-d', '--debug'"),
    ],
    "detage.py": [
        ("add_argument('--verbose'", "add_argument('-v', '--verbose'"),
        ("add_argument('--debug'", "add_argument('-d', '--debug'"),
    ],
    "detangles.py": [
        ("add_argument('--verbose'", "add_argument('-v', '--verbose'"),
        ("add_argument('--debug'", "add_argument('-d', '--debug'"),
    ],
    "detmeme.py": [
        ("add_argument('--verbose'", "add_argument('-v', '--verbose'"),
        ("add_argument('--debug'", "add_argument('-d', '--debug'"),
    ],
}

for filename, replacements in files_fixes.items():
    filepath = filename
    if not os.path.exists(filepath):
        print(f"  ✗ {filename} introuvable")
        continue
    
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    modified = False
    for old, new in replacements:
        if old in content and new not in content:
            content = content.replace(old, new, 1)
            modified = True
    
    if modified:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"  ✓ {filename} corrigé (ajout -v/-d)")
    else:
        print(f"  ○ {filename} déjà corrigé ou pattern non trouvé")

print()
print("Terminé. Relancez detfull.py pour vérifier.")
