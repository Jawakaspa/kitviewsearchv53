# discriminants.py V1.0.0 - 10/12/2025 12:42:43
__pgm__ = "discriminants.py"
__version__ = "1.0.0"
__date__ = "10/12/2025 12:42:43"

"""
discriminants.py - Génère discriminants.csv avec les mots-clés et caractères discriminants par langue

Ce programme crée ou met à jour le fichier discriminants.csv contenant :
- vocabulaire : mots courants discriminants par langue (langues latines uniquement)
- accent : caractères accentués/spéciaux discriminants par langue (langues latines uniquement)

Pour les langues non-latines (th, ar, cn), les colonnes restent vides car la détection
se fait par plages Unicode dans le programme de détection de langue.

Si discriminants.csv existe déjà :
- Les lignes existantes sont préservées
- Seules les nouvelles lignes type sont ajoutées
- Les nouvelles colonnes langues sont ajoutées si nécessaire
"""

import csv
import os
import sys
from pathlib import Path

# ============================================================================
# DONNÉES DISCRIMINANTES PAR LANGUE
# ============================================================================

# Mots courants discriminants (uniquement langues à alphabet latin)
VOCABULAIRE = {
    "fr": "avec,sans,les,des,qui,ont,dans,pour,que,est,une,sur,pas,mais,aux,cette,tout,être,faire,comme",
    "en": "with,without,the,who,have,has,this,that,from,are,was,were,been,being,which,their,would,could,should,about",
    "de": "mit,ohne,die,der,das,haben,ist,sind,und,ein,eine,nicht,auch,sich,auf,für,werden,kann,nach,bei",
    "es": "con,sin,los,las,que,tienen,está,son,una,para,por,como,pero,más,este,esta,todo,puede,hace,sobre",
    "it": "con,senza,gli,che,hanno,sono,una,per,come,più,questo,questa,tutto,può,fare,essere,anche,della,nella,sulla",
    "pt": "com,sem,os,as,que,têm,está,são,uma,para,por,como,mais,este,esta,todo,pode,fazer,também,sobre",
    "pl": "z,bez,który,która,które,mają,jest,są,dla,jak,ale,też,przez,przy,nad,pod,można,będzie,bardzo,tylko",
    "ro": "cu,fără,care,sunt,este,pentru,dar,mai,acest,această,tot,poate,face,fiind,prin,asupra,într,dintre,după,când",
    "th": "",  # Détection par Unicode
    "ar": "",  # Détection par Unicode
    "cn": "",  # Détection par Unicode
}

# Caractères accentués/spéciaux discriminants (uniquement langues à alphabet latin)
ACCENTS = {
    "fr": "é,è,ê,ë,à,â,ù,û,ô,î,ï,ç,œ,æ,É,È,Ê,Ë,À,Â,Ù,Û,Ô,Î,Ï,Ç,Œ,Æ",
    "en": "",  # Pas de caractères accentués spécifiques
    "de": "ä,ö,ü,ß,Ä,Ö,Ü,ẞ",
    "es": "á,é,í,ó,ú,ñ,ü,¿,¡,Á,É,Í,Ó,Ú,Ñ,Ü",
    "it": "à,è,é,ì,ò,ù,À,È,É,Ì,Ò,Ù",
    "pt": "á,â,ã,à,é,ê,í,ó,ô,õ,ú,ç,Á,Â,Ã,À,É,Ê,Í,Ó,Ô,Õ,Ú,Ç",
    "pl": "ą,ć,ę,ł,ń,ó,ś,ź,ż,Ą,Ć,Ę,Ł,Ń,Ó,Ś,Ź,Ż",
    "ro": "ă,â,î,ș,ț,Ă,Â,Î,Ș,Ț",
    "th": "",  # Détection par Unicode
    "ar": "",  # Détection par Unicode
    "cn": "",  # Détection par Unicode
}


def lire_langues_cibles(chemin_commun: str) -> list[str]:
    """
    Lit les langues cibles depuis commun.csv (colonne languescibles).
    
    Args:
        chemin_commun: Chemin vers commun.csv
        
    Returns:
        Liste des codes langues uniques
    """
    langues = []
    
    with open(chemin_commun, "r", encoding="utf-8-sig", newline="") as f:
        # Lire toutes les lignes et filtrer les commentaires
        lignes = [ligne for ligne in f if not ligne.strip().startswith("#")]
    
    # Parser le CSV à partir des lignes filtrées
    reader = csv.DictReader(lignes, delimiter=";")
    
    if not reader.fieldnames or "languescibles" not in reader.fieldnames:
        print(f"[ERREUR] Colonne 'languescibles' non trouvée dans {chemin_commun}")
        print(f"[DEBUG] Colonnes trouvées : {reader.fieldnames}")
        sys.exit(1)
    
    for row in reader:
        langue = row.get("languescibles", "").strip()
        if langue and langue not in langues:
            langues.append(langue)
    
    print(f"[INFO] Langues cibles détectées : {', '.join(langues)}")
    return langues


def lire_discriminants_existant(chemin_discriminants: str) -> tuple[list[str], dict[str, dict[str, str]]]:
    """
    Lit le fichier discriminants.csv existant.
    
    Args:
        chemin_discriminants: Chemin vers discriminants.csv
        
    Returns:
        Tuple (liste des colonnes, dictionnaire {type: {langue: valeur}})
    """
    if not os.path.exists(chemin_discriminants):
        return [], {}
    
    colonnes = []
    donnees = {}
    
    with open(chemin_discriminants, "r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f, delimiter=";")
        colonnes = list(reader.fieldnames) if reader.fieldnames else []
        
        for row in reader:
            type_ligne = row.get("type", "").strip()
            if type_ligne:
                donnees[type_ligne] = {k: v for k, v in row.items() if k != "type"}
    
    print(f"[INFO] Fichier existant lu : {len(donnees)} ligne(s), colonnes : {colonnes}")
    return colonnes, donnees


def generer_discriminants(chemin_commun: str, chemin_discriminants: str) -> None:
    """
    Génère ou met à jour discriminants.csv.
    
    Args:
        chemin_commun: Chemin vers commun.csv (source des langues)
        chemin_discriminants: Chemin vers discriminants.csv (sortie)
    """
    print(f"{__pgm__} V{__version__} - {__date__}")
    print(f"[INFO] Lecture de {os.path.abspath(chemin_commun)}")
    
    # Lire les langues cibles
    langues = lire_langues_cibles(chemin_commun)
    
    if not langues:
        print("[ERREUR] Aucune langue cible trouvée dans commun.csv")
        sys.exit(1)
    
    # Lire le fichier existant s'il existe
    colonnes_existantes, donnees_existantes = lire_discriminants_existant(chemin_discriminants)
    
    # Construire la liste des colonnes finale
    colonnes_finales = ["type"] + langues
    
    # Vérifier s'il y a de nouvelles langues
    langues_existantes = [c for c in colonnes_existantes if c != "type"]
    nouvelles_langues = [l for l in langues if l not in langues_existantes]
    if nouvelles_langues:
        print(f"[INFO] Nouvelles langues à ajouter : {', '.join(nouvelles_langues)}")
    
    # Types de lignes à générer
    types_requis = ["vocabulaire", "accent"]
    
    # Données finales
    donnees_finales = {}
    
    for type_ligne in types_requis:
        if type_ligne in donnees_existantes:
            # Ligne existante : conserver et compléter si nouvelles langues
            donnees_finales[type_ligne] = donnees_existantes[type_ligne].copy()
            for langue in nouvelles_langues:
                if type_ligne == "vocabulaire":
                    donnees_finales[type_ligne][langue] = VOCABULAIRE.get(langue, "")
                elif type_ligne == "accent":
                    donnees_finales[type_ligne][langue] = ACCENTS.get(langue, "")
            print(f"[INFO] Ligne '{type_ligne}' : conservée (complétée si nouvelles langues)")
        else:
            # Nouvelle ligne : créer avec toutes les langues
            donnees_finales[type_ligne] = {}
            for langue in langues:
                if type_ligne == "vocabulaire":
                    donnees_finales[type_ligne][langue] = VOCABULAIRE.get(langue, "")
                elif type_ligne == "accent":
                    donnees_finales[type_ligne][langue] = ACCENTS.get(langue, "")
            print(f"[INFO] Ligne '{type_ligne}' : créée")
    
    # Conserver les autres lignes existantes (types personnalisés)
    for type_ligne, valeurs in donnees_existantes.items():
        if type_ligne not in types_requis:
            donnees_finales[type_ligne] = valeurs
            # Compléter avec les nouvelles langues (vide)
            for langue in nouvelles_langues:
                if langue not in donnees_finales[type_ligne]:
                    donnees_finales[type_ligne][langue] = ""
            print(f"[INFO] Ligne personnalisée '{type_ligne}' : conservée")
    
    # Écrire le fichier
    chemin_absolu = os.path.abspath(chemin_discriminants)
    print(f"[INFO] Écriture de {chemin_absolu}")
    
    with open(chemin_discriminants, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=colonnes_finales, delimiter=";")
        writer.writeheader()
        
        # Écrire d'abord vocabulaire, puis accent, puis les autres
        ordre = ["vocabulaire", "accent"] + [t for t in donnees_finales.keys() if t not in ["vocabulaire", "accent"]]
        
        for type_ligne in ordre:
            if type_ligne in donnees_finales:
                row = {"type": type_ligne}
                for langue in langues:
                    row[langue] = donnees_finales[type_ligne].get(langue, "")
                writer.writerow(row)
    
    print(f"[OK] Fichier généré : {chemin_absolu}")
    print(f"[OK] {len(donnees_finales)} ligne(s), {len(langues)} langue(s)")


def main():
    """Point d'entrée principal."""
    # Chemins par défaut (même répertoire que le script)
    script_dir = Path(__file__).parent
    chemin_commun = script_dir / "commun.csv"
    chemin_discriminants = script_dir / "discriminants.csv"
    
    # Possibilité de passer les chemins en arguments
    if len(sys.argv) >= 2:
        chemin_commun = Path(sys.argv[1])
    if len(sys.argv) >= 3:
        chemin_discriminants = Path(sys.argv[2])
    
    # Vérifier que commun.csv existe
    if not chemin_commun.exists():
        print(f"[ERREUR] Fichier non trouvé : {chemin_commun.absolute()}")
        sys.exit(1)
    
    generer_discriminants(str(chemin_commun), str(chemin_discriminants))


if __name__ == "__main__":
    main()
