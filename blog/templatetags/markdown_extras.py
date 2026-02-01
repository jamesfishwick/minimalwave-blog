"""
Markdown preprocessing functions for enhanced image handling.

This module provides custom shortcode syntax for images that compiles to
semantic HTML with <figure> and <figcaption> tags for better accessibility.

Syntax: {{img:path|position|width|optional_caption}}
- path: Smart detection (https://... or relative to /media/)
- position: left, right, center, full
- width: Pixel width (200, 300, 400, 500, 800)
- caption: Optional caption text (wrapped in <figcaption>)

Example:
    {{img:uploads/photo.jpg|right|300|A beautiful sunset}}

    Becomes:
    <figure class="markdown-image float-right" style="max-width: 300px;">
        <img src="/media/uploads/photo.jpg" alt="A beautiful sunset" loading="lazy">
        <figcaption>A beautiful sunset</figcaption>
    </figure>
"""

import re
from html import escape


def preprocess_image_shortcodes(text):
    """
    Convert {{img:...}} syntax to semantic HTML with <figure>/<figcaption>.

    Args:
        text (str): Markdown text containing shortcode syntax

    Returns:
        str: Text with shortcodes replaced by HTML figure elements

    Syntax:
        {{img:path|position|width|optional_caption}}

    Parameters:
        path: Image path (absolute URLs pass through, relative prepend /media/)
        position: left, right, center, full
        width: Pixel width (200, 300, 400, 500, 800)
        caption: Optional caption (becomes both figcaption and alt text)
    """
    # Regex pattern to match {{img:path|position|width|caption}}
    # Caption is optional (group 4)
    pattern = r'\{\{img:([^|]+)\|([^|]+)\|(\d+)(?:\|([^}]*))?\}\}'

    def replace_shortcode(match):
        path, position, width, caption = match.groups()
        caption = caption.strip() if caption else ''

        # Escape caption for HTML safety
        caption_escaped = escape(caption) if caption else ''

        # Smart path handling: absolute URLs pass through, relative prepend /media/
        if not (path.startswith('http://') or path.startswith('https://')):
            # Remove leading slash if present, then prepend /media/
            path = f'/media/{path.lstrip("/")}'

        # Escape path for HTML safety
        path_escaped = escape(path)

        # Map position to CSS class
        position_class_map = {
            'left': 'float-left',
            'right': 'float-right',
            'center': 'center',
            'full': 'full'
        }
        position_class = position_class_map.get(position, 'center')

        # Build semantic HTML with <figure> and <figcaption>
        if caption_escaped:
            html = f'''<figure class="markdown-image {position_class}" style="max-width: {width}px;">
    <img src="{path_escaped}" alt="{caption_escaped}" loading="lazy">
    <figcaption>{caption_escaped}</figcaption>
</figure>'''
        else:
            # No caption: use empty alt (decorative image)
            html = f'<figure class="markdown-image {position_class}" style="max-width: {width}px;"><img src="{path_escaped}" alt="" loading="lazy"></figure>'

        return html

    # Replace all shortcodes in the text
    return re.sub(pattern, replace_shortcode, text)
