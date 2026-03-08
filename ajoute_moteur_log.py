# ajoute_moteur_log.py V1.0.0 - 05/01/2026 12:47:28
__pgm__ = "ajoute_moteur_log.py"
__version__ = "1.0.0"
__date__ = "05/01/2026 12:47:28"

"""
Script pour ajouter la colonne 'moteur' au fichier logrecherche.csv.

- Ajoute la colonne 'moteur' après la colonne 'mode'
- Pour les lignes avec mode='ia', met un moteur aléatoire parmi ceux de ia.csv
- Pour les autres modes, laisse vide

Usage:
    python ajoute_moteur_log.py logrecherche.csv ia.csv
"""

import csv
import sys
import random
from pathlib import Path


def charger_moteurs_ia(ia_path: str) -> list:
    """Charge les noms courts des moteurs IA depuis ia.csv (sauf 'standard')."""
    moteurs = []
    
    with open(ia_path, 'r', encoding='utf-8-sig') as f:
        lignes = [line for line in f if not line.strip().startswith('#')]
    
    if not lignes:
        return ['sonnet', 'gpt4omini', 'deepseekr1']  # Fallback
    
    reader = csv.DictReader(lignes, delimiter=';')
    
    for row in reader:
        moteur = row.get('moteur', '').strip()
        # Exclure 'standard' qui n'est pas un vrai moteur IA
        if moteur and moteur != 'standard':
            moteurs.append(moteur)
    
    print(f"Moteurs IA chargés ({len(moteurs)}) : {', '.join(moteurs)}")
    return moteurs


def ajouter_colonne_moteur(log_path: str, ia_path: str, output_path: str = None):
    """
    Ajoute la colonne 'moteur' au fichier de logs.
    
    Args:
        log_path: Chemin vers logrecherche.csv
        ia_path: Chemin vers ia.csv
        output_path: Chemin de sortie (par défaut remplace le fichier original)
    """
    if output_path is None:
        output_path = log_path
    
    # Charger les moteurs disponibles
    moteurs = charger_moteurs_ia(ia_path)
    if not moteurs:
        print("ERREUR: Aucun moteur trouvé dans ia.csv")
        return False
    
    # Lire le fichier original
    lignes_output = []
    nb_ia = 0
    nb_total = 0
    
    with open(log_path, 'r', encoding='utf-8-sig') as f:
        for i, line in enumerate(f):
            # Ligne de commentaire - conserver telle quelle mais ajouter des ; vides si nécessaire
            if line.strip().startswith('#'):
                lignes_output.append(line)
                continue
            
            # Ligne d'entête
            if 'module;timestamp;' in line.lower() or 'module;timestamp' in line:
                # Trouver la position de 'mode' et insérer 'moteur' juste après
                parts = line.rstrip('\n\r').split(';')
                
                # Chercher l'index de 'mode'
                mode_idx = -1
                for idx, col in enumerate(parts):
                    if col.strip().lower() == 'mode':
                        mode_idx = idx
                        break
                
                if mode_idx >= 0 and 'moteur' not in [p.strip().lower() for p in parts]:
                    # Insérer 'moteur' après 'mode'
                    parts.insert(mode_idx + 1, 'moteur')
                    line = ';'.join(parts) + '\n'
                    print(f"Entête modifiée : 'moteur' ajouté après 'mode' (position {mode_idx + 1})")
                elif 'moteur' in [p.strip().lower() for p in parts]:
                    print("La colonne 'moteur' existe déjà dans l'entête")
                    return False
                
                lignes_output.append(line)
                continue
            
            # Ligne de données
            nb_total += 1
            parts = line.rstrip('\n\r').split(';')
            
            # Trouver l'index de 'mode' (colonne 12, index 12 en 0-based selon l'entête)
            # L'entête est : module;timestamp;temps_ms;languesaisie;langueutilisee;modulelangue;questionoriginale;question;filtres;sql;tri;base;mode;...
            # mode est donc à l'index 12
            mode_idx = 12
            
            if len(parts) > mode_idx:
                mode_val = parts[mode_idx].strip().lower()
                
                # Choisir le moteur
                if mode_val == 'ia':
                    moteur = random.choice(moteurs)
                    nb_ia += 1
                else:
                    moteur = ''
                
                # Insérer le moteur après mode (position 13)
                parts.insert(mode_idx + 1, moteur)
            else:
                # Ligne trop courte, ajouter une colonne vide
                parts.insert(mode_idx + 1, '')
            
            line = ';'.join(parts) + '\n'
            lignes_output.append(line)
    
    # Écrire le fichier de sortie
    with open(output_path, 'w', encoding='utf-8-sig', newline='') as f:
        f.writelines(lignes_output)
    
    print(f"\nRésultat :")
    print(f"  - Lignes traitées : {nb_total}")
    print(f"  - Lignes mode=ia avec moteur aléatoire : {nb_ia}")
    print(f"  - Fichier sauvegardé : {output_path}")
    
    return True


def main():
    print(f"{__pgm__} V{__version__} - {__date__}")
    print()
    
    if len(sys.argv) < 3:
        print(f"Usage: python {__pgm__} <logrecherche.csv> <ia.csv> [output.csv]")
        print()
        print("Arguments :")
        print("  logrecherche.csv : Fichier de logs à modifier")
        print("  ia.csv           : Fichier des moteurs IA")
        print("  output.csv       : Fichier de sortie (optionnel, remplace l'original si absent)")
        return 1
    
    log_path = sys.argv[1]
    ia_path = sys.argv[2]
    output_path = sys.argv[3] if len(sys.argv) > 3 else None
    
    if not Path(log_path).exists():
        print(f"ERREUR: Fichier non trouvé : {log_path}")
        return 1
    
    if not Path(ia_path).exists():
        print(f"ERREUR: Fichier non trouvé : {ia_path}")
        return 1
    
    success = ajouter_colonne_moteur(log_path, ia_path, output_path)
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
