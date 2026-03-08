# md2reveal.py V1.0.0 - 21/01/2026 19:56:58
__pgm__ = "md2reveal.py"
__version__ = "1.0.0"
__date__ = "21/01/2026 19:56:58"

"""
╔════════════════════════════════════════════════════════════════════════════════
║ md2reveal.py - Convertisseur Markdown → Reveal.js
║
║ Convertit un fichier Markdown avec métadonnées de slides (format 
║ Prompt_MD_to_Slides_Ready.md) en présentation HTML Reveal.js.
║
║ MÉTADONNÉES SUPPORTÉES :
║   - PRESENTATION_META : En-tête de présentation (titre, durée, audience...)
║   - SLIDE : Définition d'une slide (id, titre, template, emoji, timing)
║   - KEY : Message clé (affiché en speaker notes)
║   - QUESTION : Question pour l'audience
║   - DIAGRAM : Encadre un schéma ASCII
║   - CODE : Encadre un bloc de code
║   - TABLE : Encadre un tableau
║   - SUBSLIDE : Slide verticale
║   - NO_SLIDE : Section à exclure des slides
║
║ TEMPLATES SUPPORTÉS :
║   - titre-section : Grande slide de transition
║   - schema : Fond sombre pour diagrammes
║   - 2colonnes : Deux colonnes côte à côte
║   - tableau : Mise en forme tableau
║   - code : Fond sombre pour code
║   - synthese : Slide de conclusion
║   - stats : Chiffres clés
║   - quote : Citation
║
║ USAGE :
║   python md2reveal.py input.md [output.html] [--theme=black|white|moon|...]
║   python md2reveal.py detection.md
║   python md2reveal.py detection.md presentation.html --theme=moon
║
║ DÉPENDANCES :
║   - Python 3.13+ (standard library uniquement)
║   - Reveal.js chargé via CDN (pas d'installation requise)
║
╚════════════════════════════════════════════════════════════════════════════════
"""

import re
import sys
import argparse
from pathlib import Path
from datetime import datetime
import html


# ═══════════════════════════════════════════════════════════════════════════════
# CONFIGURATION
# ═══════════════════════════════════════════════════════════════════════════════

REVEAL_CDN = "https://cdn.jsdelivr.net/npm/reveal.js@5.1.0"

THEMES_DISPONIBLES = [
    "black", "white", "league", "beige", "sky", 
    "night", "serif", "simple", "solarized", "moon", "dracula"
]

# Templates CSS personnalisés par type de slide
TEMPLATE_STYLES = {
    "titre-section": "background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);",
    "schema": "background: #1e1e1e;",
    "code": "background: #1e1e1e;",
    "2colonnes": "",
    "tableau": "",
    "synthese": "background: linear-gradient(135deg, #0f3460 0%, #16213e 100%);",
    "stats": "background: linear-gradient(135deg, #e94560 0%, #0f3460 100%);",
    "quote": "background: #2d3436;",
    "timeline": "",
    "exercice": "background: #00b894;",
}


# ═══════════════════════════════════════════════════════════════════════════════
# PARSEUR DE MÉTADONNÉES
# ═══════════════════════════════════════════════════════════════════════════════

def parse_meta_block(content: str) -> dict:
    """
    Parse un bloc de métadonnées YAML-like dans un commentaire HTML.
    
    Exemple:
        titre: "Mon titre"
        emoji: "🔍"
    
    Returns:
        dict avec les clés/valeurs
    """
    meta = {}
    for line in content.strip().split('\n'):
        line = line.strip()
        if ':' in line:
            key, value = line.split(':', 1)
            key = key.strip()
            value = value.strip().strip('"').strip("'")
            meta[key] = value
    return meta


def extract_presentation_meta(md_content: str) -> dict:
    """
    Extrait le bloc PRESENTATION_META du document.
    """
    pattern = r'<!--\s*PRESENTATION_META\s*(.*?)\s*-->'
    match = re.search(pattern, md_content, re.DOTALL)
    if match:
        return parse_meta_block(match.group(1))
    return {}


def extract_slides(md_content: str) -> list:
    """
    Extrait toutes les slides du document Markdown.
    
    Returns:
        Liste de dicts avec structure:
        {
            'meta': dict des métadonnées SLIDE,
            'content': contenu markdown de la slide,
            'key': message clé (optionnel),
            'question': question audience (optionnel),
            'subslides': liste de sous-slides
        }
    """
    slides = []
    
    # Supprimer les blocs NO_SLIDE
    md_content = re.sub(
        r'<!--\s*NO_SLIDE\s*-->.*?<!--\s*/NO_SLIDE\s*-->',
        '',
        md_content,
        flags=re.DOTALL
    )
    
    # Pattern pour détecter les slides (## titre précédé de <!-- SLIDE -->)
    slide_pattern = r'<!--\s*SLIDE\s*(.*?)\s*-->\s*\n\s*(##\s+[^\n]+)'
    
    # Trouver toutes les positions de slides
    matches = list(re.finditer(slide_pattern, md_content, re.DOTALL))
    
    for i, match in enumerate(matches):
        meta = parse_meta_block(match.group(1))
        title_line = match.group(2)
        
        # Extraire le titre (sans le ##)
        title = re.sub(r'^##\s+', '', title_line).strip()
        meta['title_raw'] = title
        
        # Déterminer la fin du contenu de cette slide
        start_pos = match.end()
        if i + 1 < len(matches):
            end_pos = matches[i + 1].start()
        else:
            end_pos = len(md_content)
        
        content = md_content[start_pos:end_pos].strip()
        
        # Extraire KEY
        key_match = re.search(r'<!--\s*KEY:\s*(.*?)\s*-->', content)
        key = key_match.group(1).strip() if key_match else None
        
        # Extraire QUESTION
        question_match = re.search(r'<!--\s*QUESTION:\s*(.*?)\s*-->', content)
        question = question_match.group(1).strip() if question_match else None
        
        # Extraire les SUBSLIDES
        subslides = extract_subslides(content)
        
        # Nettoyer le contenu des métadonnées
        content = re.sub(r'<!--\s*KEY:.*?-->', '', content)
        content = re.sub(r'<!--\s*QUESTION:.*?-->', '', content)
        content = re.sub(r'<!--\s*SUBSLIDE.*?-->.*?<!--\s*/SUBSLIDE\s*-->', '', content, flags=re.DOTALL)
        content = re.sub(r'<!--\s*/?(?:DIAGRAM|CODE|TABLE).*?-->', '', content)
        
        slides.append({
            'meta': meta,
            'content': content.strip(),
            'key': key,
            'question': question,
            'subslides': subslides
        })
    
    return slides


def extract_subslides(content: str) -> list:
    """
    Extrait les SUBSLIDE d'un contenu de slide.
    """
    subslides = []
    pattern = r'<!--\s*SUBSLIDE\s*(.*?)\s*-->\s*(.*?)\s*<!--\s*/SUBSLIDE\s*-->'
    
    for match in re.finditer(pattern, content, re.DOTALL):
        meta = parse_meta_block(match.group(1))
        sub_content = match.group(2).strip()
        subslides.append({
            'meta': meta,
            'content': sub_content
        })
    
    return subslides


# ═══════════════════════════════════════════════════════════════════════════════
# CONVERTISSEUR MARKDOWN → HTML
# ═══════════════════════════════════════════════════════════════════════════════

def markdown_to_html(md_text: str) -> str:
    """
    Convertit du Markdown basique en HTML.
    Gère : titres, listes, code, tableaux, gras, italique, liens.
    """
    lines = md_text.split('\n')
    html_lines = []
    in_code_block = False
    code_lang = ""
    code_content = []
    in_list = False
    in_table = False
    table_rows = []
    
    for line in lines:
        # Blocs de code
        if line.startswith('```'):
            if not in_code_block:
                in_code_block = True
                code_lang = line[3:].strip()
                code_content = []
            else:
                in_code_block = False
                lang_class = f' class="language-{code_lang}"' if code_lang else ''
                escaped_code = html.escape('\n'.join(code_content))
                html_lines.append(f'<pre><code{lang_class}>{escaped_code}</code></pre>')
            continue
        
        if in_code_block:
            code_content.append(line)
            continue
        
        # Tableaux
        if '|' in line and line.strip().startswith('|'):
            if not in_table:
                in_table = True
                table_rows = []
            
            # Ignorer les lignes de séparation (|---|---|)
            if re.match(r'^\s*\|[\s\-:|]+\|\s*$', line):
                continue
            
            cells = [c.strip() for c in line.strip().strip('|').split('|')]
            table_rows.append(cells)
            continue
        elif in_table:
            # Fin du tableau
            in_table = False
            html_lines.append(render_table(table_rows))
            table_rows = []
        
        # Listes à puces
        if re.match(r'^\s*[-*]\s+', line):
            if not in_list:
                in_list = True
                html_lines.append('<ul>')
            item = re.sub(r'^\s*[-*]\s+', '', line)
            item = apply_inline_formatting(item)
            html_lines.append(f'<li>{item}</li>')
            continue
        elif in_list and line.strip() == '':
            continue
        elif in_list:
            in_list = False
            html_lines.append('</ul>')
        
        # Titres
        if line.startswith('####'):
            text = apply_inline_formatting(line[4:].strip())
            html_lines.append(f'<h4>{text}</h4>')
            continue
        elif line.startswith('###'):
            text = apply_inline_formatting(line[3:].strip())
            html_lines.append(f'<h3>{text}</h3>')
            continue
        elif line.startswith('##'):
            text = apply_inline_formatting(line[2:].strip())
            html_lines.append(f'<h2>{text}</h2>')
            continue
        
        # Ligne vide
        if line.strip() == '':
            html_lines.append('')
            continue
        
        # Ligne horizontale
        if re.match(r'^---+$', line.strip()):
            html_lines.append('<hr>')
            continue
        
        # Paragraphe normal
        text = apply_inline_formatting(line)
        html_lines.append(f'<p>{text}</p>')
    
    # Fermer les éléments ouverts
    if in_list:
        html_lines.append('</ul>')
    if in_table:
        html_lines.append(render_table(table_rows))
    
    return '\n'.join(html_lines)


def apply_inline_formatting(text: str) -> str:
    """
    Applique le formatage inline : **gras**, *italique*, `code`, [lien](url)
    """
    # Code inline
    text = re.sub(r'`([^`]+)`', r'<code>\1</code>', text)
    # Gras
    text = re.sub(r'\*\*([^*]+)\*\*', r'<strong>\1</strong>', text)
    # Italique
    text = re.sub(r'\*([^*]+)\*', r'<em>\1</em>', text)
    # Liens
    text = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', r'<a href="\2">\1</a>', text)
    
    return text


def render_table(rows: list) -> str:
    """
    Génère le HTML d'un tableau à partir des lignes.
    """
    if not rows:
        return ''
    
    html_parts = ['<table>']
    
    # Première ligne = en-tête
    html_parts.append('<thead><tr>')
    for cell in rows[0]:
        cell_html = apply_inline_formatting(cell)
        html_parts.append(f'<th>{cell_html}</th>')
    html_parts.append('</tr></thead>')
    
    # Reste = corps
    if len(rows) > 1:
        html_parts.append('<tbody>')
        for row in rows[1:]:
            html_parts.append('<tr>')
            for cell in row:
                cell_html = apply_inline_formatting(cell)
                html_parts.append(f'<td>{cell_html}</td>')
            html_parts.append('</tr>')
        html_parts.append('</tbody>')
    
    html_parts.append('</table>')
    return '\n'.join(html_parts)


# ═══════════════════════════════════════════════════════════════════════════════
# GÉNÉRATEUR HTML REVEAL.JS
# ═══════════════════════════════════════════════════════════════════════════════

def generate_slide_html(slide: dict) -> str:
    """
    Génère le HTML d'une slide Reveal.js.
    """
    meta = slide['meta']
    template = meta.get('template', '')
    emoji = meta.get('emoji', '')
    titre = meta.get('titre', meta.get('title_raw', ''))
    slide_id = meta.get('id', '')
    
    # Style selon le template
    style = TEMPLATE_STYLES.get(template, '')
    style_attr = f' data-background-color="inherit" style="{style}"' if style else ''
    id_attr = f' id="{slide_id}"' if slide_id else ''
    
    # Contenu de la slide
    content_html = markdown_to_html(slide['content'])
    
    # Titre avec emoji
    title_html = f"{emoji} {titre}" if emoji else titre
    
    # Construction de la slide
    parts = [f'<section{id_attr}{style_attr}>']
    
    # Template spécifique : titre-section
    if template == 'titre-section':
        parts.append(f'<h1>{title_html}</h1>')
    else:
        if titre and '##' not in slide['content'][:50]:
            parts.append(f'<h2>{title_html}</h2>')
    
    # Question pour l'audience
    if slide.get('question'):
        parts.append(f'<blockquote class="question">💬 {html.escape(slide["question"])}</blockquote>')
    
    # Contenu principal
    parts.append(content_html)
    
    # Speaker notes (KEY)
    if slide.get('key'):
        parts.append(f'<aside class="notes">')
        parts.append(f'<strong>🔑 Message clé :</strong> {html.escape(slide["key"])}')
        if meta.get('timing'):
            parts.append(f'<br><strong>⏱️ Timing :</strong> {meta["timing"]}')
        parts.append('</aside>')
    
    parts.append('</section>')
    
    # Sous-slides verticales
    if slide.get('subslides'):
        # Wrapper pour slides verticales
        wrapper_parts = [f'<section{id_attr}>']
        wrapper_parts.append('\n'.join(parts[1:-1]))  # Contenu de la slide principale sans <section>
        wrapper_parts.append('</section>')
        
        for subslide in slide['subslides']:
            sub_meta = subslide['meta']
            sub_titre = sub_meta.get('titre', '')
            sub_content = markdown_to_html(subslide['content'])
            
            wrapper_parts.append('<section>')
            if sub_titre:
                wrapper_parts.append(f'<h3>{sub_titre}</h3>')
            wrapper_parts.append(sub_content)
            wrapper_parts.append('</section>')
        
        return '\n'.join(['<section>'] + wrapper_parts + ['</section>'])
    
    return '\n'.join(parts)


def generate_title_slide(pres_meta: dict) -> str:
    """
    Génère la slide de titre.
    """
    titre = pres_meta.get('titre_court', 'Présentation')
    sous_titre = pres_meta.get('sous_titre', '')
    emoji = pres_meta.get('emoji_principal', '')
    duree = pres_meta.get('duree_estimee', '')
    audience = pres_meta.get('audience', '')
    
    title_html = f"{emoji} {titre}" if emoji else titre
    
    parts = ['<section data-background-color="#1a1a2e">']
    parts.append(f'<h1>{title_html}</h1>')
    if sous_titre:
        parts.append(f'<h3>{sous_titre}</h3>')
    
    if duree or audience:
        parts.append('<p style="margin-top: 2em; font-size: 0.8em; opacity: 0.8;">')
        if duree:
            parts.append(f'⏱️ Durée : {duree}')
        if duree and audience:
            parts.append(' | ')
        if audience:
            parts.append(f'👥 {audience}')
        parts.append('</p>')
    
    parts.append('</section>')
    return '\n'.join(parts)


def generate_reveal_html(pres_meta: dict, slides: list, theme: str = "black") -> str:
    """
    Génère le document HTML complet avec Reveal.js.
    """
    titre = pres_meta.get('titre_court', 'Présentation')
    
    # CSS personnalisé
    custom_css = """
    <style>
        .reveal h1, .reveal h2, .reveal h3 {
            text-transform: none;
        }
        .reveal pre {
            width: 100%;
            font-size: 0.55em;
        }
        .reveal pre code {
            max-height: 500px;
            padding: 15px;
        }
        .reveal table {
            font-size: 0.7em;
            margin: 20px auto;
        }
        .reveal table th {
            background: rgba(255,255,255,0.1);
            font-weight: bold;
        }
        .reveal table td, .reveal table th {
            padding: 8px 15px;
            border: 1px solid rgba(255,255,255,0.2);
        }
        .reveal blockquote.question {
            background: rgba(255,193,7,0.15);
            border-left: 4px solid #ffc107;
            padding: 15px 20px;
            font-style: normal;
            font-size: 0.9em;
            margin: 20px 0;
        }
        .reveal ul, .reveal ol {
            display: block;
            text-align: left;
            margin-left: 1em;
        }
        .reveal li {
            margin: 0.5em 0;
        }
        .reveal code {
            background: rgba(255,255,255,0.1);
            padding: 2px 6px;
            border-radius: 3px;
        }
        .reveal .slides section {
            height: 100%;
        }
        /* Template 2 colonnes */
        .two-columns {
            display: flex;
            gap: 40px;
        }
        .two-columns > div {
            flex: 1;
        }
        /* Notes de l'orateur */
        .reveal .notes {
            font-size: 1.2em;
        }
    </style>
    """
    
    # Générer les slides
    slides_html = []
    
    # Slide de titre
    slides_html.append(generate_title_slide(pres_meta))
    
    # Slides de contenu
    for slide in slides:
        slides_html.append(generate_slide_html(slide))
    
    # Document HTML complet
    html_doc = f"""<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{html.escape(titre)}</title>
    <link rel="stylesheet" href="{REVEAL_CDN}/dist/reset.css">
    <link rel="stylesheet" href="{REVEAL_CDN}/dist/reveal.css">
    <link rel="stylesheet" href="{REVEAL_CDN}/dist/theme/{theme}.css">
    <link rel="stylesheet" href="{REVEAL_CDN}/plugin/highlight/monokai.css">
    {custom_css}
</head>
<body>
    <div class="reveal">
        <div class="slides">
{chr(10).join(slides_html)}
        </div>
    </div>

    <script src="{REVEAL_CDN}/dist/reveal.js"></script>
    <script src="{REVEAL_CDN}/plugin/notes/notes.js"></script>
    <script src="{REVEAL_CDN}/plugin/markdown/markdown.js"></script>
    <script src="{REVEAL_CDN}/plugin/highlight/highlight.js"></script>
    <script>
        Reveal.initialize({{
            hash: true,
            slideNumber: true,
            showNotes: false,
            transition: 'slide',
            plugins: [ RevealNotes, RevealHighlight ]
        }});
    </script>
</body>
</html>
"""
    return html_doc


# ═══════════════════════════════════════════════════════════════════════════════
# FONCTION PRINCIPALE
# ═══════════════════════════════════════════════════════════════════════════════

def convert_md_to_reveal(input_path: Path, output_path: Path, theme: str = "black", verbose: bool = True) -> dict:
    """
    Convertit un fichier Markdown en présentation Reveal.js.
    
    Args:
        input_path: Chemin du fichier .md source
        output_path: Chemin du fichier .html de sortie
        theme: Thème Reveal.js (black, white, moon, etc.)
        verbose: Afficher les détails
    
    Returns:
        dict avec statistiques de conversion
    """
    # Lecture du fichier source
    if verbose:
        print(f"📖 Lecture de {input_path.resolve()}...")
    
    with open(input_path, 'r', encoding='utf-8') as f:
        md_content = f.read()
    
    # Extraction des métadonnées
    if verbose:
        print("🔍 Extraction des métadonnées...")
    
    pres_meta = extract_presentation_meta(md_content)
    slides = extract_slides(md_content)
    
    if verbose:
        print(f"   ✓ Métadonnées de présentation : {len(pres_meta)} champs")
        print(f"   ✓ Slides détectées : {len(slides)}")
        
        # Compter les sous-slides
        total_subslides = sum(len(s.get('subslides', [])) for s in slides)
        if total_subslides > 0:
            print(f"   ✓ Sous-slides : {total_subslides}")
    
    # Génération HTML
    if verbose:
        print(f"🎨 Génération HTML (thème: {theme})...")
    
    html_content = generate_reveal_html(pres_meta, slides, theme)
    
    # Écriture du fichier
    if verbose:
        print(f"💾 Écriture de {output_path.resolve()}...")
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    stats = {
        'input': str(input_path.resolve()),
        'output': str(output_path.resolve()),
        'theme': theme,
        'slides': len(slides),
        'subslides': sum(len(s.get('subslides', [])) for s in slides),
        'total_slides': len(slides) + sum(len(s.get('subslides', [])) for s in slides) + 1,  # +1 pour titre
        'keys': sum(1 for s in slides if s.get('key')),
        'questions': sum(1 for s in slides if s.get('question')),
    }
    
    if verbose:
        print()
        print("═" * 60)
        print(f"✅ Conversion terminée !")
        print(f"   📊 {stats['total_slides']} slides générées ({stats['slides']} principales + {stats['subslides']} sous-slides + 1 titre)")
        print(f"   🔑 {stats['keys']} messages clés (speaker notes)")
        print(f"   💬 {stats['questions']} questions audience")
        print()
        print(f"   👉 Ouvrir dans un navigateur : file://{output_path.resolve()}")
        print(f"   👉 Touche 'S' pour les notes du présentateur")
        print("═" * 60)
    
    return stats


def main():
    """Point d'entrée principal."""
    print(f"{__pgm__} V{__version__} - {__date__}")
    print()
    
    parser = argparse.ArgumentParser(
        description="Convertit un fichier Markdown avec métadonnées en présentation Reveal.js",
        epilog=f"Thèmes disponibles : {', '.join(THEMES_DISPONIBLES)}"
    )
    parser.add_argument('input', type=str, help="Fichier Markdown source (.md)")
    parser.add_argument('output', type=str, nargs='?', help="Fichier HTML de sortie (optionnel)")
    parser.add_argument('--theme', '-t', type=str, default='black',
                        choices=THEMES_DISPONIBLES,
                        help="Thème Reveal.js (défaut: black)")
    parser.add_argument('--quiet', '-q', action='store_true',
                        help="Mode silencieux")
    
    args = parser.parse_args()
    
    # Chemins
    input_path = Path(args.input)
    
    if not input_path.exists():
        print(f"❌ Erreur : Le fichier '{input_path}' n'existe pas.")
        sys.exit(1)
    
    if not input_path.suffix.lower() == '.md':
        print(f"⚠️  Attention : Le fichier n'a pas l'extension .md")
    
    # Fichier de sortie
    if args.output:
        output_path = Path(args.output)
    else:
        output_path = input_path.with_suffix('.html')
    
    # Conversion
    try:
        stats = convert_md_to_reveal(
            input_path, 
            output_path, 
            theme=args.theme,
            verbose=not args.quiet
        )
    except Exception as e:
        print(f"❌ Erreur lors de la conversion : {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
