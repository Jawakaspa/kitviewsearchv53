# generate_translated_html.py V1.0.0 - 22/01/2026 15:09:00
#!/usr/bin/env python3
__pgm__ = "generate_translated_html.py"
__version__ = "1.0.0"
__date__ = "22/01/2026 15:09:00"

"""
Génère une version traduite d'un fichier HTML Kitview à partir d'un CSV de traductions.

Usage:
    python generate_translated_html.py kitviewmanuals.html translations.csv kitviewmanuals_en.html
"""

import re
import csv
import sys
from pathlib import Path

def load_translations(csv_file):
    """Charge les traductions depuis un fichier CSV."""
    translations = {}
    
    with open(csv_file, 'r', encoding='utf-8-sig') as f:
        # Filtrer les lignes de commentaires
        lines = [line for line in f if not line.strip().startswith('#')]
        
    # Réouvrir avec les lignes filtrées
    import io
    reader = csv.DictReader(io.StringIO(''.join(lines)), delimiter=';')
    
    for row in reader:
        if 'fr' not in row or 'en' not in row:
            continue
            
        fr_text = row['fr'].strip().strip('"')
        en_text = row['en'].strip().strip('"')
        
        # Nettoyer le préfixe [AUTO] si présent et non révisé
        if en_text.startswith('[AUTO] '):
            en_text = en_text[7:]  # Garder le texte auto pour la démo
        
        if fr_text and en_text:
            # Normaliser pour la comparaison
            fr_normalized = normalize_text(fr_text)
            translations[fr_normalized] = {
                'fr': fr_text,
                'en': en_text,
                'status': row.get('status', 'TODO')
            }
    
    return translations


def normalize_text(text):
    """Normalise le texte pour faciliter la correspondance."""
    # Supprimer les espaces multiples
    text = re.sub(r'\s+', ' ', text)
    # Supprimer les marqueurs markdown
    text = text.replace('**', '').replace('*', '')
    return text.strip().lower()


def replace_text_in_html(html_content, translations, lang='en'):
    """Remplace les textes français par leur traduction dans le HTML."""
    
    replaced_count = 0
    not_found = []
    
    # Pour chaque traduction, chercher et remplacer dans le HTML
    for fr_norm, trans in translations.items():
        fr_text = trans['fr']
        en_text = trans['en']
        
        # Créer un pattern qui gère les variations d'espaces et de balises
        # On cherche le texte français tel quel
        if fr_text in html_content:
            html_content = html_content.replace(fr_text, en_text)
            replaced_count += 1
        else:
            # Essayer avec une recherche moins stricte
            pattern = re.escape(fr_text).replace(r'\ ', r'\s+')
            if re.search(pattern, html_content):
                html_content = re.sub(pattern, en_text.replace('\\', '\\\\'), html_content)
                replaced_count += 1
    
    return html_content, replaced_count


def update_html_metadata(html_content, lang='en'):
    """Met à jour les métadonnées HTML pour la nouvelle langue."""
    
    # Changer l'attribut lang
    html_content = re.sub(r'<html lang="[^"]*">', f'<html lang="{lang}">', html_content)
    
    # Mettre à jour le titre
    html_content = re.sub(
        r'<title>Kitview - Manuel d\'utilisation[^<]*</title>',
        '<title>Kitview - User Manual (Standard)</title>',
        html_content
    )
    
    # Mettre à jour le commentaire de version
    html_content = re.sub(
        r'Manuel d\'utilisation Kitview - Version Standard',
        'Kitview User Manual - Standard Version',
        html_content
    )
    
    # Mettre à jour le footer
    html_content = re.sub(
        r"Manuel d'utilisation v[\d.]+ \(Standard\)",
        "User Manual v1.5 (Standard)",
        html_content
    )
    
    # Mettre à jour les textes d'interface fixes
    ui_translations = {
        'Rechercher dans le manuel...': 'Search in manual...',
        '📑 Toutes les sections': '📑 All sections',
        'Sommaire': 'Table of Contents',
        'Changer le thème': 'Toggle theme',
        'Retour': 'Back',
        'résultat': 'result',
        'résultats': 'results',
        'Préc.': 'Prev.',
        'Suiv.': 'Next',
        'Fermer': 'Close',
        'Effacer': 'Clear',
        'Précédent': 'Previous',
        'Suivant': 'Next',
        'Langue du manuel': 'Manual language',
        'Sélectionnez une langue': 'Select a language',
        'Standard': 'Standard',
        'Débutant': 'Beginner',
        'Intermédiaire': 'Intermediate',
        'Inter.': 'Inter.',
        'Expert': 'Expert',
        'Version Standard': 'Standard Version',
        'Version Débutant': 'Beginner Version',
        'Version Intermédiaire': 'Intermediate Version',
        'Version Expert': 'Expert Version',
    }
    
    for fr, en in ui_translations.items():
        html_content = html_content.replace(fr, en)
    
    # Mettre à jour les noms de fichiers pour les liens
    html_content = html_content.replace('kitviewmanuals.html', 'kitviewmanuals_en.html')
    html_content = html_content.replace('kitviewmanuald.html', 'kitviewmanuald_en.html')
    html_content = html_content.replace('kitviewmanuali.html', 'kitviewmanuali_en.html')
    html_content = html_content.replace('kitviewmanuale.html', 'kitviewmanuale_en.html')
    
    return html_content


def translate_section_names(html_content):
    """Traduit les noms de sections dans le select et le sommaire."""
    
    section_translations = {
        '1. Présentation': '1. Overview',
        '2. Gestion patients': '2. Patient Management',
        '3. Personnalisation': '3. Customization',
        '4. Import/Export': '4. Import/Export',
        '5. Séances photos': '5. Photo Sessions',
        '6. Gabarits': '6. Templates',
        '7. Viewers': '7. Viewers',
        '8. Modification photos': '8. Photo Editing',
        '9. Présentations fixes': '9. Fixed Presentations',
        '10. Docking': '10. Docking',
        '11. Créer présentation': '11. Create Presentation',
        '12. Diaporama': '12. Slideshow',
        '13. Comparateur': '13. Comparator',
        '14. Courrier': '14. Mail Templates',
        '15. Portfolio': '15. Portfolio',
        '16. Filtre population': '16. Population Filter',
        '17. Recherche date': '17. Date Search',
        '18. Formulaires': '18. Forms',
        '19. Support formation': '19. Training Support',
        
        # TOC entries
        'Présentation générale': 'General Overview',
        'Gestion des patients': 'Patient Management',
        'Créer un patient': 'Create a Patient',
        'Supprimer un patient': 'Delete a Patient',
        "Photo d'identité": 'ID Photo',
        'Personnalisation': 'Customization',
        'Onglets et style': 'Tabs and Style',
        'Couleurs du bureau': 'Desktop Colors',
        'Taille des vignettes': 'Thumbnail Size',
        'Import / Export': 'Import / Export',
        'Importer des photos': 'Import Photos',
        'Exporter des photos': 'Export Photos',
        'Glisser-déposer': 'Drag and Drop',
        'Séances photos': 'Photo Sessions',
        'Protocole': 'Protocol',
        'WiFi': 'WiFi',
        'Gabarits et mots-clés': 'Templates and Keywords',
        'Créer un mot-clé': 'Create a Keyword',
        'Créer un gabarit': 'Create a Template',
        'Créer un filtre': 'Create a Filter',
        'Viewers': 'Viewers',
        'Présentation': 'Presentation',
        'Personnaliser': 'Customize',
        'Ajouter des viewers': 'Add Viewers',
        'Modification de photos': 'Photo Editing',
        'Recadrer': 'Crop',
        'Luminosité': 'Brightness',
        'Annotations': 'Annotations',
        'Présentations fixes': 'Fixed Presentations',
        'Utilisation': 'Usage',
        'Configuration': 'Configuration',
        'Le Docking': 'Docking',
        'Principe': 'Principle',
        'Créer une présentation': 'Create Presentation',
        'Diaporama': 'Slideshow',
        'Comparer des photos': 'Compare Photos',
        'Modèles de courrier': 'Mail Templates',
        'Portfolio / PowerPoint': 'Portfolio / PowerPoint',
        'Filtre de population': 'Population Filter',
        'Recherche par date': 'Date Search',
        'Formulaires': 'Forms',
        'Support de formation': 'Training Support',
    }
    
    for fr, en in section_translations.items():
        html_content = html_content.replace(fr, en)
    
    return html_content


def main():
    print(f"{__pgm__} V{__version__} - {__date__}")
    
    if len(sys.argv) < 3:
        print("Usage: python generate_translated_html.py <source.html> <translations.csv> [output.html]")
        print("Exemple: python generate_translated_html.py kitviewmanuals.html translations.csv kitviewmanuals_en.html")
        sys.exit(1)
    
    source_file = Path(sys.argv[1])
    translations_file = Path(sys.argv[2])
    output_file = Path(sys.argv[3]) if len(sys.argv) > 3 else source_file.with_stem(source_file.stem + '_en')
    
    if not source_file.exists():
        print(f"❌ Erreur: fichier source '{source_file}' non trouvé")
        sys.exit(1)
    
    if not translations_file.exists():
        print(f"❌ Erreur: fichier de traductions '{translations_file}' non trouvé")
        sys.exit(1)
    
    print(f"📄 Chargement de {source_file}...")
    html_content = source_file.read_text(encoding='utf-8')
    
    print(f"🌐 Chargement des traductions depuis {translations_file}...")
    translations = load_translations(translations_file)
    print(f"   {len(translations)} traductions chargées")
    
    print("🔄 Application des traductions...")
    html_content, replaced_count = replace_text_in_html(html_content, translations)
    print(f"   {replaced_count} remplacements effectués")
    
    print("📝 Mise à jour des métadonnées...")
    html_content = update_html_metadata(html_content)
    
    print("📑 Traduction des noms de sections...")
    html_content = translate_section_names(html_content)
    
    print(f"💾 Écriture de {output_file}...")
    output_file.write_text(html_content, encoding='utf-8')
    
    print(f"✅ Terminé ! Version anglaise générée : {output_file}")


if __name__ == '__main__':
    main()
