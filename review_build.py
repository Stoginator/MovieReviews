#!/usr/bin/env python3
"""
build.py - Convert Markdown movie reviews to HTML for Tanish's Movie Reviews.

Usage:
    python build.py review.md                     # single file
    python build.py review.md -o output/          # single file, custom output dir
    python build.py reviews/ -o output/           # batch: all .md files in a directory

Markdown Format:
    # Movie Title
    
    Date Seen - Timestamp - Location/Format
    
    (Release Year) - Spoilers Ahead       <- "Spoilers Ahead" is optional
    
    *Review subtitle here.*
    
    > Quote from the film.
    
    Body paragraphs, with special blocks:
    
    _Film Title_ -> <cite>Film Title</cite>
    *emphasis*   -> <em>emphasis</em>
    **bold**     -> <b>bold</b>
    [text](url)  -> <a href="url">text</a>
    <q>text</q>  -> passed through as-is
    
    ![](filename.webp)                -> inline photo
    
    :::carousel
    ![](photo1.webp)
    ![](photo2.webp)
    :::
    
    :::spoilers:::                    -> spoiler divider
    
    :::dialogue
    CHARACTER
    Line of dialogue.
    
    CHARACTER2
    Another line.
    :::
    
    :::smash-cut
    SMASH CUT TO:
    :::
    
    ---
    
    directed_by: Steven Spielberg
    written_by: Scott Frank, Jon Cohen
    music_by: John Williams
    selected_tracks: Track One, Track Two
    release_date: June 21, 2002
    budget: $102 million
    box_office: $358.4 million
    production_company: Company A, Company B
    distribution_company: Company C
    poster: filename.jpg
    card_image: filename.webp
"""

import re
import sys
import argparse
from datetime import datetime
from pathlib import Path


# --- Constants ----------------------------------------------------------------

BASE_URL = "https://stoginator.github.io/MovieReviews"


# --- Inline Formatting -------------------------------------------------------

def format_inline(text):
    """Convert inline Markdown formatting to HTML.
    
    Order matters:
    1. Protect links and raw HTML from other replacements
    2. Bold **text**
    3. Cite _text_ (work titles)
    4. Emphasis *text*
    5. Restore protected content
    """
    # Protect links: [text](url) -> placeholder
    # Process inline formatting within link text first
    links = []
    def save_link(m):
        link_text = m.group(1)
        # Apply emphasis/cite inside link text before protecting
        link_text = re.sub(r'(?<!\w)_(?!_)(.+?)_(?!\w)', r'<em>\1</em>', link_text)
        link_text = re.sub(r'(?<!\*)\*(?!\*)(.+?)\*(?!\*)', r'<cite>\1</cite>', link_text)
        links.append(f'<a href="{m.group(2)}">{link_text}</a>')
        return f'\x00LINK{len(links)-1}\x00'
    text = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', save_link, text)
    
    # Protect raw HTML tags from interference
    html_tags = []
    def save_html(m):
        html_tags.append(m.group(0))
        return f'\x00HTML{len(html_tags)-1}\x00'
    text = re.sub(r'<[^>]+>', save_html, text)
    
    # Bold: **text** -> <b><em>text</em></b>
    text = re.sub(r'\*\*(.+?)\*\*', r'<b><em>\1</em></b>', text)
    
    # Cite: *text* -> <cite>text</cite> (film/work titles)
    text = re.sub(r'(?<!\*)\*(?!\*)(.+?)\*(?!\*)', r'<cite>\1</cite>', text)
    
    # Emphasis: _text_ -> <em>text</em> (word boundaries to avoid URLs)
    text = re.sub(r'(?<!\w)_(?!_)(.+?)_(?!\w)', r'<em>\1</em>', text)
    
    # Restore HTML tags
    for i, tag in enumerate(html_tags):
        text = text.replace(f'\x00HTML{i}\x00', tag)
    
    # Restore links
    for i, link in enumerate(links):
        text = text.replace(f'\x00LINK{i}\x00', link)
    
    return text


# --- Parsing ------------------------------------------------------------------

def parse_markdown(filepath):
    """Parse a Markdown review file into structured data.
    
    Structure:
        [header + body]
        ---
        [metadata key: value pairs]
        <!-- end -->        ← optional, everything below is ignored
        [scratch notes]     ← never appears in HTML output
    """
    text = Path(filepath).read_text(encoding='utf-8')
    lines = text.split('\n')
    
    # Find the --- separator (body/metadata boundary)
    separator_idx = None
    for i, line in enumerate(lines):
        if line.strip() == '---':
            separator_idx = i
            break
    
    if separator_idx is None:
        raise ValueError(f"No metadata separator (---) found in {filepath}")
    
    header_and_body_lines = lines[:separator_idx]
    metadata_lines = lines[separator_idx + 1:]
    
    # If <!-- end --> appears, discard everything from that point onward
    end_idx = None
    for i, line in enumerate(metadata_lines):
        if line.strip() == '<!-- end -->':
            end_idx = i
            break
    
    if end_idx is not None:
        metadata_lines = metadata_lines[:end_idx]
    
    data = parse_header(header_and_body_lines)
    data['metadata'] = parse_metadata(metadata_lines)
    
    # Build filename from title + review year: "Blade Runner 2049" (2026) → blade_runner_2049_2026.html
    title_slug = re.sub(r'[^a-z0-9]+', '_', data['title'].lower()).strip('_')
    review_year = data.get('review_year', '')
    data['html_filename'] = f"{title_slug}_{review_year}.html"
    
    return data


def parse_header(lines):
    """Parse the header block and body from the review lines."""
    data = {}
    idx = 0
    
    # Skip leading blank lines
    while idx < len(lines) and not lines[idx].strip():
        idx += 1
    
    # Title: "# Movie Title" or just "Movie Title" (Obsidian inline title)
    if idx < len(lines):
        title_line = lines[idx].strip()
        if title_line.startswith('# '):
            data['title'] = title_line[2:].strip()
        else:
            data['title'] = title_line
        idx += 1
    else:
        raise ValueError("Expected title as first line")
    
    # Skip blanks
    while idx < len(lines) and not lines[idx].strip():
        idx += 1
    
    # Date line: Date - Timestamp - Location
    if idx < len(lines):
        date_line = lines[idx].strip()
        parts = date_line.split(' - ', 2)
        if len(parts) >= 3:
            data['date_seen'] = parts[0].strip()
            data['timestamp'] = parts[1].strip()
            data['location'] = parts[2].strip()
        elif len(parts) == 2:
            data['date_seen'] = parts[0].strip()
            data['timestamp'] = parts[1].strip()
            data['location'] = ''
        else:
            data['date_seen'] = date_line
            data['timestamp'] = ''
            data['location'] = ''
        idx += 1
    
    # Parse datetime for the <time> tag
    try:
        dt = datetime.strptime(
            f"{data['date_seen']} {data['timestamp']}",
            "%B %d, %Y %I:%M %p"
        )
        data['datetime'] = dt.strftime("%Y-%m-%d %H:%M")
        data['review_year'] = dt.year
    except ValueError:
        data['datetime'] = ''
        data['review_year'] = ''
    
    # Skip blanks
    while idx < len(lines) and not lines[idx].strip():
        idx += 1
    
    # Year line: (2002) or (2002) - Spoilers Ahead or (2002) - **Spoilers Ahead**
    if idx < len(lines):
        year_line = lines[idx].strip()
        # Strip any markdown bold markers for matching
        year_clean = year_line.replace('**', '')
        year_match = re.match(r'\((\d{4})\)(?:\s*-\s*Spoilers Ahead)?', year_clean)
        if year_match:
            data['release_year'] = int(year_match.group(1))
            data['has_spoilers'] = 'Spoilers Ahead' in year_clean
            idx += 1
        else:
            data['release_year'] = ''
            data['has_spoilers'] = False
    
    # Skip blanks
    while idx < len(lines) and not lines[idx].strip():
        idx += 1
    
    # Review subtitle: *Subtitle text here.* or _Subtitle text here._
    data['review_title'] = ''
    if idx < len(lines):
        subtitle_line = lines[idx].strip()
        subtitle_match = re.match(r'^[*_](.+)[*_]$', subtitle_line)
        if subtitle_match:
            data['review_title'] = subtitle_match.group(1)
            idx += 1
    
    # Skip blanks
    while idx < len(lines) and not lines[idx].strip():
        idx += 1
    
    # Quote: > Quote text here.
    data['quote'] = ''
    if idx < len(lines):
        quote_line = lines[idx].strip()
        if quote_line.startswith('> '):
            data['quote'] = quote_line[2:].strip()
            idx += 1
    
    # Skip blanks
    while idx < len(lines) and not lines[idx].strip():
        idx += 1
    
    # Everything remaining is the body
    data['body'] = parse_body(lines[idx:])
    
    return data


def _extract_image_src(text):
    """Extract image filename from either ![alt](file) or ![[file]] syntax."""
    m = re.match(r'^!\[([^\]]*)\]\(([^)]+)\)$', text.strip())
    if m:
        return m.group(2)
    m = re.match(r'^!\[\[([^\]]+)\]\]$', text.strip())
    if m:
        return m.group(1)
    return None


def _extract_all_images(text):
    """Extract all image filenames from a line (handles multiple ![[file]] on one line)."""
    images = []
    # Standard markdown: ![alt](file)
    for m in re.finditer(r'!\[([^\]]*)\]\(([^)]+)\)', text):
        images.append(m.group(2))
    # Obsidian: ![[file]]
    for m in re.finditer(r'!\[\[([^\]]+)\]\]', text):
        images.append(m.group(1))
    return images


def _is_image_line(line):
    """Check if a line is a standalone image (either syntax)."""
    s = line.strip()
    return bool(re.match(r'^!\[([^\]]*)\]\(([^)]+)\)$', s) or re.match(r'^!\[\[([^\]]+)\]\]$', s))


def parse_body(lines):
    """Parse the body into a sequence of content blocks.
    
    Block types: paragraph, dialogue, carousel, figure, spoilers, smash_cut
    """
    blocks = []
    idx = 0
    
    while idx < len(lines):
        line = lines[idx].strip()
        
        if not line:
            idx += 1
            continue
        
        # :::spoilers:::
        if line == ':::spoilers:::':
            blocks.append({'type': 'spoilers'})
            idx += 1
            continue
        
        # :::dialogue ... :::
        if line == ':::dialogue':
            idx += 1
            dialogue_lines = []
            while idx < len(lines) and lines[idx].strip() != ':::':
                dialogue_lines.append(lines[idx])
                idx += 1
            if idx < len(lines):
                idx += 1  # skip closing :::
            blocks.append({
                'type': 'dialogue',
                'exchanges': parse_dialogue(dialogue_lines)
            })
            continue
        
        # :::carousel ... ::: (flexible: images can be on same line, multiple per line)
        if line.startswith(':::carousel'):
            images = []
            # Check for images on the same line as :::carousel
            rest = line[len(':::carousel'):]
            # Check if closing ::: is on this same line
            if rest.rstrip().endswith(':::'):
                rest = rest.rstrip()[:-3]
                images.extend(_extract_all_images(rest))
                idx += 1
            else:
                images.extend(_extract_all_images(rest))
                idx += 1
                while idx < len(lines):
                    l = lines[idx].strip()
                    # Check if this line ends with ::: (closing fence)
                    if l == ':::':
                        idx += 1
                        break
                    if l.endswith(':::'):
                        images.extend(_extract_all_images(l[:-3]))
                        idx += 1
                        break
                    images.extend(_extract_all_images(l))
                    idx += 1
            blocks.append({'type': 'carousel', 'images': [{'src': img} for img in images]})
            continue
        
        # :::smash-cut ... :::
        if line == ':::smash-cut':
            idx += 1
            smash_text = ''
            while idx < len(lines) and lines[idx].strip() != ':::':
                if lines[idx].strip():
                    smash_text = lines[idx].strip()
                idx += 1
            if idx < len(lines):
                idx += 1  # skip closing :::
            blocks.append({'type': 'smash_cut', 'text': smash_text})
            continue
        
        # Inline photo on its own line: ![alt](file) or ![[file]]
        if _is_image_line(line):
            src = _extract_image_src(line)
            if src:
                blocks.append({'type': 'figure', 'alt': '', 'src': src})
            idx += 1
            continue
        
        # Regular paragraph: collect lines until blank or special block
        para_lines = []
        while idx < len(lines):
            l = lines[idx].strip()
            if not l:
                break
            if l in (':::spoilers:::', ':::dialogue', ':::smash-cut'):
                break
            if l.startswith(':::carousel'):
                break
            if _is_image_line(l):
                break
            para_lines.append(l)
            idx += 1
        
        if para_lines:
            blocks.append({
                'type': 'paragraph',
                'text': ' '.join(para_lines)
            })
    
    return blocks


def parse_dialogue(lines):
    """Parse dialogue lines into (character, dialogue) pairs.
    
    Input format:
        CHARACTER NAME
        Line of dialogue.
        
        ANOTHER CHARACTER
        Their dialogue.
    """
    exchanges = []
    idx = 0
    
    while idx < len(lines):
        line = lines[idx].rstrip()
        
        if not line.strip():
            idx += 1
            continue
        
        # Character name: all-uppercase line (optionally wrapped in ** bold **)
        clean_line = re.sub(r'^\*\*(.+?)\*\*$', r'\1', line.strip())
        if re.match(r'^[A-Z][A-Z\s.\'\-]*$', clean_line):
            character = clean_line
            idx += 1
            dialogue_parts = []
            while idx < len(lines):
                dline = lines[idx].rstrip()
                if not dline.strip():
                    break
                clean_dline = re.sub(r'^\*\*(.+?)\*\*$', r'\1', dline.strip())
                if re.match(r'^[A-Z][A-Z\s.\'\-]*$', clean_dline):
                    break
                dialogue_parts.append(dline.strip())
                idx += 1
            dialogue = ' '.join(dialogue_parts)
            exchanges.append((character, dialogue))
        else:
            idx += 1
    
    return exchanges


def parse_metadata(lines):
    """Parse key: value metadata from lines below the --- separator."""
    metadata = {}
    
    for line in lines:
        line = line.strip()
        if not line or ':' not in line:
            continue
        
        key, _, value = line.partition(':')
        key = key.strip().lower().replace(' ', '_')
        value = value.strip()
        
        # These fields support comma-separated lists
        multi_fields = [
            'written_by', 'story_by', 'selected_tracks',
            'production_company', 'distribution_company'
        ]
        
        if key in multi_fields:
            metadata[key] = [v.strip() for v in value.split(',') if v.strip()]
        else:
            metadata[key] = value
    
    return metadata


# --- HTML Rendering -----------------------------------------------------------

def render_html(data):
    """Render the complete HTML page from parsed review data."""
    meta = data.get('metadata', {})
    title = data['title']
    release_year = data.get('release_year', '')
    html_filename = data['html_filename']
    review_title = data.get('review_title', '')
    card_image = meta.get('card_image', '')
    poster = meta.get('poster', '')
    poster_alt = f"Photo of {title} Poster"
    
    title_tag = f"{title} ({release_year}) | Tanish's Movie Reviews" if release_year else f"{title} | Tanish's Movie Reviews"
    review_url = f"{BASE_URL}/reviews/{html_filename}"
    card_url = f"{BASE_URL}/assets/cards/{card_image}" if card_image else ''
    
    # Build date display
    date_seen = data.get('date_seen', '')
    timestamp = data.get('timestamp', '')
    location = data.get('location', '')
    datetime_attr = data.get('datetime', '')
    
    time_display = f"{date_seen} - {timestamp}" if date_seen and timestamp else date_seen
    subtitle_line = f'<time datetime="{datetime_attr}">{time_display}</time> - {location}' if location else f'<time datetime="{datetime_attr}">{time_display}</time>'
    
    # Render body and details
    article_html = render_article_body(data['body'])
    details_html = render_details_table(meta)
    
    html = f'''<!DOCTYPE html>
<html lang="en">
    <head>
        <meta charset="UTF-8">
        <title>{title_tag}</title>
        <meta name="viewport" content="width=device-width, initial-scale=1.0" />
        <link rel="stylesheet" href="../styles/style.css" />
        <link rel="shortcut icon" href="../favicon.ico" />
        <link rel="apple-touch-icon" sizes="180x180" href="../assets/images/apple-touch-icon.png" />
        <link rel="icon" type="image/png" sizes="32x32" href="../assets/images/favicon-32x32.png" />
        <link rel="icon" type="image/png" sizes="16x16" href="../assets/images/favicon-16x16.png" />
        <link rel="mask-icon" href="../safari-pinned-tab.svg" color="#5bbad5" />
        <meta name="msapplication-TileColor" content="#2b5797" />
        <meta name="theme-color" media="(prefers-color-scheme: light)" content="#FD7F22" />
        <meta name="theme-color" media="(prefers-color-scheme: dark)" content="#DA5D00" />

        <!---------- Embed Meta Tags ---------->
        <meta name="title" content="{title_tag}" />
        <meta name="description" content="{review_title}" />
        <meta name="author" content="Tanish Rastogi">
        <meta property="og:type" content="Movie Review" />
        <meta property="og:url" content="{review_url}" />
        
        <meta property="og:title" content="{title_tag}" />
        <meta property="og:description" content="{review_title}" />
        <meta property="og:image" content="{card_url}" />
        
        <meta property="twitter:card" content="summary_large_image" />
        <meta property="twitter:url" content="{review_url}" />
        <meta property="twitter:title" content="{title_tag}" />
        <meta property="twitter:description" content="{review_title}" />
        <meta property="twitter:image" content="{card_url}" /> 
        <!------------------------------>

        <link rel="manifest" href="../site.webmanifest">
        <script type="text/javascript" src="../js/script.js"></script>
    </head>
    <body>
        <div class="content">
           <nav id="sidebar" class="sidebar-hidden" role="navigation">
                <header class="sidebar-header">
                    <p class="sidebar-title">TMR</p>
                    <input type="image" class="sidebar-exit" title="Exit Site Navigation" aria-label="Exit Site Navigation" aria-controls="sidebar" src="../assets/icons/close.svg" onclick="controlNav()"></input>
                </header>
                <section class="roboto">
                    <span><a href="../index.html">Home Page</a></span>
                    <span><a href="../pages/fav_films.html">Favorite Films</a></span>
                    <span><a href="../pages/watched.html">Watched List</a></span>
                    <span><a href="../pages/about_me.html">About Me</a></span>
                    <span><a href="../pages/review_list.html">Plain Review List</a></span>
                    <span><button id="toggle-btn" class="theme-toggle" onclick="themeToggle()">Toggle Dark Mode</button></span>
                </section>
            </nav>
            <header class="site-header">
                <input type="image" class="sidebar-toggle" title="Toggle Site Navigation" aria-label="Toggle Site Navigation" aria-controls="sidebar" src="../assets/icons/menu.svg" onclick="controlNav()"></input>
                <p class="site-title"><a href="../index.html">Tanish's Movie Reviews</a></p>
                <a href="https://github.com/Stoginator" title="Visit Owner's GitHub"><img class="memoji" src="../assets/icons/memoji.png" alt="Animated picture of website owner"></img></a>
            </header>
            <hr class="rounded">
            <article class="review">
    			<h1 class="review-title"><cite>{title}</cite></h1>
    			<p class="review-subtitle">{subtitle_line}</p>
                <p class="review-subtitle"><i>{review_title}</i></p>
                <q class="review-subtitle">{data.get('quote', '')}</q>
{article_html}
            </article>
{details_html}
			<section class="poster">
				<img 
                    src="../assets/posters/{poster}" 
                    alt="{poster_alt}" />
			</section>
        </div>
        <footer class="site-footer roboto">
            Roboto designed by Christian Robertson; licensed through Google Fonts.<br>
            All trademarks are the property of the respective trademark owners.<br>
            &copy; {datetime.now().year} <a href="https://github.com/Stoginator">Tanish Rastogi</a>. All Rights Reserved.
        </footer>
	</body>
</html>'''
    
    return html


def render_article_body(blocks):
    """Render body blocks into HTML.
    
    Groups consecutive text-type blocks (paragraph, dialogue, smash_cut)
    into <section class="review-text"> wrappers. Figures, carousels, and
    spoiler dividers break the section.
    """
    output_parts = []
    current_section = []
    
    def flush_section():
        if not current_section:
            return
        inner = '\n'.join(current_section)
        output_parts.append(
            f'                <section class="review-text">\n'
            f'{inner}\n'
            f'                </section>'
        )
        current_section.clear()
    
    for block in blocks:
        btype = block['type']
        
        if btype == 'paragraph':
            html_text = format_inline(block['text'])
            current_section.append(f'                    <p>{html_text}</p>')
        
        elif btype == 'dialogue':
            current_section.append(render_dialogue(block['exchanges']))
        
        elif btype == 'smash_cut':
            text = block['text']
            current_section.append(
                f'                    <blockquote class="section-quote smash-cut">'
                f'<b><em>{text}</em></b></blockquote>'
            )
        
        elif btype == 'figure':
            flush_section()
            src = block['src']
            output_parts.append(
                f'                <figure class="inline-photo">\n'
                f'                    <img src="../assets/review_photos/{src}">\n'
                f'                </figure>'
            )
        
        elif btype == 'carousel':
            flush_section()
            slides = '\n'.join(
                f'                    <div class="carousel-slide">'
                f'<img src="../assets/review_photos/{img["src"]}" loading="lazy" alt>'
                f'</div>'
                for img in block['images']
            )
            output_parts.append(
                f'                <div class="carousel-container">\n'
                f'                  <div class="carousel-slides">\n'
                f'{slides}\n'
                f'                  </div>\n'
                f'                  <div class="carousel-arrow carousel-left">&#10094;</div>\n'
                f'                  <div class="carousel-arrow carousel-right">&#10095;</div>\n'
                f'                  <div class="carousel-dots"></div>\n'
                f'                </div>'
            )
        
        elif btype == 'spoilers':
            flush_section()
            output_parts.append(
                f'                <div class="spoilers">\n'
                f'                    <hr />\n'
                f'                    <p>Spoilers Ahead</p>\n'
                f'                    <hr />\n'
                f'                </div>'
            )
    
    flush_section()
    return '\n'.join(output_parts)


def render_dialogue(exchanges):
    """Render dialogue exchanges as <ul class="script-list">."""
    items = []
    for i, (character, dialogue) in enumerate(exchanges):
        if i > 0:
            items.append('                        <li><br></li>')
        items.append(f'                        <li class="character-name">{character}</li> ')
        items.append(f'                        <li class="dialogue">{format_inline(dialogue)}</li>')
    
    inner = '\n'.join(items)
    return (
        f'                    <ul class="script-list">\n'
        f'{inner}\n'
        f'                    </ul>'
    )


def render_details_table(meta):
    """Render the Key Details section with table."""
    rows = []
    
    def add_row(label, value):
        if isinstance(value, list):
            cell = '<br>'.join(value)
        else:
            cell = value
        rows.append(
            f'                    <tr>\n'
            f'                        <td><b>{label}</b></td>\n'
            f'                        <td>{cell}</td>\n'
            f'                    </tr>'
        )
    
    # Fields in display order
    if meta.get('directed_by'):
        add_row('Directed By', meta['directed_by'])
    if meta.get('written_by'):
        add_row('Written By', meta['written_by'])
    if meta.get('story_by'):
        add_row('Story By', meta['story_by'])
    if meta.get('music_by'):
        add_row('Music By', meta['music_by'])
    
    # Selected tracks get <cite> wrapping
    if meta.get('selected_tracks'):
        tracks = meta['selected_tracks']
        if isinstance(tracks, list):
            cell_lines = '\n'.join(
                f'                            <cite>{t}</cite><br>' for t in tracks
            )
            rows.append(
                f'                    <tr>\n'
                f'                        <td><b>Selected Tracks</b></td>\n'
                f'                        <td>\n{cell_lines}\n'
                f'                        </td>\n'
                f'                    </tr>'
            )
    
    if meta.get('release_date'):
        add_row('Release Date', meta['release_date'])
    if meta.get('budget'):
        add_row('Budget', meta['budget'])
    if meta.get('box_office'):
        add_row('Box Office', meta['box_office'])
    if meta.get('production_company'):
        add_row('Production Company', meta['production_company'])
    if meta.get('distribution_company'):
        add_row('Distribution Company', meta['distribution_company'])
    
    rows_html = '\n'.join(rows)
    
    return (
        f'            <section class="details">\n'
        f'                <header class="details-header">\n'
        f'                    <hr />\n'
        f'                    <p>Key Details</p>\n'
        f'                    <hr />\n'
        f'                </header>\n'
        f'                <table class="details-table">\n'
        f'{rows_html}\n'
        f'                </table>\n'
        f'            </section>'
    )


# --- Main ---------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Convert Markdown movie reviews to HTML."
    )
    parser.add_argument(
        'input',
        help='Markdown file or directory of .md files'
    )
    parser.add_argument(
        '-o', '--output',
        default='.',
        help='Output directory (default: current directory)'
    )
    
    args = parser.parse_args()
    input_path = Path(args.input)
    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    if input_path.is_dir():
        md_files = sorted(input_path.glob('*.md'))
        if not md_files:
            print(f"No .md files found in {input_path}")
            sys.exit(1)
    elif input_path.is_file():
        md_files = [input_path]
    else:
        print(f"Input not found: {input_path}")
        sys.exit(1)
    
    for md_file in md_files:
        print(f"Building: {md_file.name}")
        try:
            data = parse_markdown(md_file)
            html = render_html(data)
            
            out_file = output_dir / data['html_filename']
            out_file.write_text(html, encoding='utf-8')
            print(f"  -> {out_file}")
        except Exception as e:
            print(f"  ERROR: {e}")
            raise
    
    print(f"\nDone. {len(md_files)} file(s) built.")


if __name__ == '__main__':
    main()
