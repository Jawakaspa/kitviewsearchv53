# extract_texts_for_translation.py V1.0.0 - 22/01/2026 15:09:00
#!/usr/bin/env python3
__pgm__ = "extract_texts_for_translation.py"
__version__ = "1.0.0"
__date__ = "22/01/2026 15:09:00"

"""
Extrait les textes traduisibles d'un fichier HTML Kitview vers un CSV.
Le CSV peut ensuite être édité pour réviser les traductions.

Usage:
    python extract_texts_for_translation.py kitviewmanuals.html translations_fr_en.csv
"""

import re
import csv
import sys
from pathlib import Path
from html.parser import HTMLParser

class TextExtractor(HTMLParser):
    """Extracteur de textes depuis HTML."""
    
    # Tags dont on veut extraire le contenu textuel
    EXTRACTABLE_TAGS = {'p', 'li', 'h1', 'h2', 'h3', 'h4', 'strong', 'em', 'span', 'td', 'th'}
    
    # Tags à ignorer complètement
    SKIP_TAGS = {'script', 'style', 'noscript', 'code', 'pre'}
    
    # Classes à ignorer (éléments techniques)
    SKIP_CLASSES = {'notranslate', 'search-icon', 'dropdown-arrow', 'chip-flag'}
    
    def __init__(self):
        super().__init__()
        self.texts = []
        self.current_section = ""
        self.current_id = ""
        self.skip_depth = 0
        self.tag_stack = []
        self.current_text = ""
        self.text_id_counter = 0
        
    def handle_starttag(self, tag, attrs):
        attrs_dict = dict(attrs)
        
        # Vérifier si on doit ignorer ce tag
        if tag in self.SKIP_TAGS:
            self.skip_depth += 1
            return
            
        # Vérifier les classes à ignorer
        classes = attrs_dict.get('class', '').split()
        if any(c in self.SKIP_CLASSES for c in classes):
            self.skip_depth += 1
            return
        
        # Détecter les sections
        if tag == 'section':
            self.current_section = attrs_dict.get('id', '')
            
        # Détecter les IDs
        if 'id' in attrs_dict:
            self.current_id = attrs_dict['id']
            
        self.tag_stack.append(tag)
        
    def handle_endtag(self, tag):
        if tag in self.SKIP_TAGS or self.skip_depth > 0:
            if tag in self.SKIP_TAGS:
                self.skip_depth -= 1
            return
            
        if self.tag_stack and self.tag_stack[-1] == tag:
            self.tag_stack.pop()
            
        # Sauvegarder le texte accumulé pour certains tags
        if tag in {'p', 'li', 'h1', 'h2', 'h3', 'h4', 'td', 'th'} and self.current_text.strip():
            self._save_text(tag)
            
    def handle_data(self, data):
        if self.skip_depth > 0:
            return
            
        text = data.strip()
        if text and len(text) > 1:  # Ignorer les textes trop courts
            self.current_text += " " + text
            
    def _save_text(self, tag):
        text = self.current_text.strip()
        text = re.sub(r'\s+', ' ', text)  # Normaliser les espaces
        
        if text and len(text) > 2:
            self.text_id_counter += 1
            self.texts.append({
                'id': f"txt_{self.text_id_counter:04d}",
                'section': self.current_section,
                'element_id': self.current_id,
                'tag': tag,
                'fr': text,
                'en': '',  # À remplir par traduction
                'status': 'TODO'
            })
        self.current_text = ""


def extract_structured_texts(html_content):
    """Extrait les textes de manière structurée en analysant le HTML."""
    texts = []
    text_id = 0
    
    # Patterns pour extraire les différents éléments
    patterns = [
        # Titres de sections
        (r'<h2[^>]*>([^<]+(?:<[^>]+>[^<]*</[^>]+>)?[^<]*)</h2>', 'h2', 'titre'),
        # Sous-titres
        (r'<h3[^>]*id="([^"]*)"[^>]*>([^<]+)</h3>', 'h3', 'sous-titre'),
        (r'<h4[^>]*>([^<]+)</h4>', 'h4', 'sous-sous-titre'),
        # Paragraphes
        (r'<p(?:\s+class="([^"]*)")?[^>]*>([^<]+(?:<(?:strong|em)[^>]*>[^<]*</(?:strong|em)>)?[^<]*)</p>', 'p', 'paragraphe'),
        # Éléments de liste
        (r'<li[^>]*>([^<]+(?:<[^>]+>[^<]*</[^>]+>)*[^<]*)</li>', 'li', 'liste'),
        # Légendes d'images
        (r'<p class="img-caption">([^<]+)</p>', 'caption', 'légende'),
        # Notes (tip, warning, info)
        (r'<div class="note-box[^"]*">\s*<strong>([^<]+)</strong>\s*([^<]+(?:<[^>]+>[^<]*</[^>]+>)*[^<]*)\s*</div>', 'note', 'note'),
    ]
    
    # Trouver toutes les sections
    section_pattern = r'<section class="help-section" id="([^"]+)">(.*?)</section>'
    sections = re.findall(section_pattern, html_content, re.DOTALL)
    
    for section_id, section_content in sections:
        # Extraire le titre de section
        h2_match = re.search(r'<h2>([^<]+)</h2>', section_content)
        if h2_match:
            text_id += 1
            texts.append({
                'id': f"txt_{text_id:04d}",
                'section': section_id,
                'tag': 'h2',
                'context': 'titre_section',
                'fr': clean_html(h2_match.group(1)),
                'en': '',
                'status': 'TODO'
            })
        
        # Extraire les sous-titres h3
        for h3_match in re.finditer(r'<h3[^>]*>([^<]+)</h3>', section_content):
            text_id += 1
            texts.append({
                'id': f"txt_{text_id:04d}",
                'section': section_id,
                'tag': 'h3',
                'context': 'sous_titre',
                'fr': clean_html(h3_match.group(1)),
                'en': '',
                'status': 'TODO'
            })
        
        # Extraire les paragraphes (hors légendes et notes)
        for p_match in re.finditer(r'<p(?!\s+class="img-caption")(?:\s+class="[^"]*")?[^>]*>(.+?)</p>', section_content, re.DOTALL):
            text = clean_html(p_match.group(1))
            if text and len(text) > 5:
                text_id += 1
                texts.append({
                    'id': f"txt_{text_id:04d}",
                    'section': section_id,
                    'tag': 'p',
                    'context': 'paragraphe',
                    'fr': text,
                    'en': '',
                    'status': 'TODO'
                })
        
        # Extraire les légendes d'images
        for cap_match in re.finditer(r'<p class="img-caption">([^<]+)</p>', section_content):
            text_id += 1
            texts.append({
                'id': f"txt_{text_id:04d}",
                'section': section_id,
                'tag': 'caption',
                'context': 'légende_image',
                'fr': clean_html(cap_match.group(1)),
                'en': '',
                'status': 'TODO'
            })
        
        # Extraire les éléments de liste
        for li_match in re.finditer(r'<li[^>]*>(.+?)</li>', section_content, re.DOTALL):
            text = clean_html(li_match.group(1))
            if text and len(text) > 3:
                text_id += 1
                texts.append({
                    'id': f"txt_{text_id:04d}",
                    'section': section_id,
                    'tag': 'li',
                    'context': 'liste',
                    'fr': text,
                    'en': '',
                    'status': 'TODO'
                })
        
        # Extraire les notes (tip, warning, info)
        for note_match in re.finditer(r'<div class="note-box\s+(\w+)">\s*<strong>([^<]+)</strong>\s*(.+?)\s*</div>', section_content, re.DOTALL):
            note_type = note_match.group(1)
            note_title = clean_html(note_match.group(2))
            note_content = clean_html(note_match.group(3))
            
            text_id += 1
            texts.append({
                'id': f"txt_{text_id:04d}",
                'section': section_id,
                'tag': 'note',
                'context': f'note_{note_type}',
                'fr': f"{note_title} | {note_content}",
                'en': '',
                'status': 'TODO'
            })
    
    return texts


def clean_html(text):
    """Nettoie le texte HTML en gardant le contenu."""
    if not text:
        return ""
    
    # Supprimer les tags HTML mais garder le contenu
    text = re.sub(r'<strong>([^<]*)</strong>', r'**\1**', text)
    text = re.sub(r'<em>([^<]*)</em>', r'*\1*', text)
    text = re.sub(r'<[^>]+>', ' ', text)
    
    # Nettoyer les espaces
    text = re.sub(r'\s+', ' ', text)
    text = text.strip()
    
    return text


def simulate_translation(text_fr, glossary=None):
    """
    Simule une traduction automatique.
    En production, utiliser Google Translate API ou DeepL.
    """
    # Glossaire de base pour la démo
    default_glossary = {
        'Kitview': 'Kitview',
        'patient': 'patient',
        'patients': 'patients',
        'photo': 'photo',
        'photos': 'photos',
        'orthodontie': 'orthodontics',
        'cabinet': 'practice',
        'téléradiographie': 'cephalometric radiograph',
        'panoramique': 'panoramic X-ray',
        'radios': 'X-rays',
        'médiathèque': 'media library',
        'vignettes': 'thumbnails',
        'clic droit': 'right-click',
        'Paramètres': 'Settings',
        'Administration': 'Administration',
        'Valider': 'Confirm',
        'Supprimer': 'Delete',
        'Créer': 'Create',
        'Présentation générale': 'General Overview',
        'Gestion des patients': 'Patient Management',
        'Personnalisation': 'Customization',
        'Import/Export': 'Import/Export',
        'Séances photos': 'Photo Sessions',
        'Gabarits': 'Templates',
        'Viewers': 'Viewers',
        'Modification de photos': 'Photo Editing',
        'Diaporama': 'Slideshow',
        'Comparateur': 'Comparator',
        'Courrier': 'Mail',
        'Portfolio': 'Portfolio',
        'Formulaires': 'Forms',
    }
    
    glossary = glossary or default_glossary
    
    # Placeholder - en production, appeler l'API de traduction ici
    # Pour la démo, on marque juste [EN] devant
    return f"[AUTO] {text_fr}"


def main():
    print(f"{__pgm__} V{__version__} - {__date__}")
    
    if len(sys.argv) < 2:
        print("Usage: python extract_texts_for_translation.py <fichier.html> [output.csv]")
        print("Exemple: python extract_texts_for_translation.py kitviewmanuals.html translations.csv")
        sys.exit(1)
    
    input_file = Path(sys.argv[1])
    output_file = Path(sys.argv[2]) if len(sys.argv) > 2 else input_file.with_suffix('.csv')
    
    if not input_file.exists():
        print(f"❌ Erreur: fichier '{input_file}' non trouvé")
        sys.exit(1)
    
    print(f"📄 Lecture de {input_file}...")
    html_content = input_file.read_text(encoding='utf-8')
    
    print("🔍 Extraction des textes...")
    texts = extract_structured_texts(html_content)
    
    print(f"✅ {len(texts)} textes extraits")
    
    # Ajouter les traductions simulées
    print("🌐 Pré-remplissage des traductions (simulation)...")
    for text in texts:
        text['en'] = simulate_translation(text['fr'])
    
    # Écrire le CSV
    print(f"💾 Écriture de {output_file}...")
    with open(output_file, 'w', encoding='utf-8-sig', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['id', 'section', 'tag', 'context', 'fr', 'en', 'status'], 
                                delimiter=';', quoting=csv.QUOTE_ALL)
        writer.writeheader()
        writer.writerows(texts)
    
    print(f"✅ Terminé ! {len(texts)} textes exportés vers {output_file}")
    print("\n📝 Prochaines étapes:")
    print("   1. Ouvrir le CSV dans Excel/LibreOffice")
    print("   2. Réviser la colonne 'en' (traductions)")
    print("   3. Mettre 'status' à 'OK' pour les lignes validées")
    print("   4. Exécuter generate_translated_html.py pour générer la version EN")


if __name__ == '__main__':
    main()
