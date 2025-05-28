#!/usr/bin/env python3
"""
Format Django templates to improve readability using simple Python rules.
"""
import os
import re
import sys
from pathlib import Path

def format_template(content):
    """Format Django template content for better readability."""
    # Fix spacing around template tags
    content = re.sub(r'({%\s*)', r'\n\1', content)  # Add newline before {%
    content = re.sub(r'(\s*%})', r'\1\n', content)  # Add newline after %}

    # Fix spacing around variable tags
    content = re.sub(r'({{\s*)', r'\1', content)  # Clean space after {{
    content = re.sub(r'(\s*}})', r'\1', content)  # Clean space before }}

    # Remove consecutive blank lines
    content = re.sub(r'\n{3,}', r'\n\n', content)

    # Fix indentation of template tags
    lines = content.split('\n')
    indentation = 0
    formatted_lines = []

    for i, line in enumerate(lines):
        stripped = line.strip()

        # Check for block opening tags
        if re.search(r'{%\s*block|{%\s*for|{%\s*if|{%\s*with|{%\s*comment', stripped) and not re.search(r'end', stripped):
            formatted_lines.append(' ' * indentation + stripped)
            indentation += 2
        # Check for block closing tags
        elif re.search(r'{%\s*end', stripped):
            indentation = max(0, indentation - 2)
            formatted_lines.append(' ' * indentation + stripped)
        # Handle normal lines
        else:
            formatted_lines.append(' ' * indentation + stripped if stripped else '')

    return '\n'.join(formatted_lines)

def process_django_templates(root_dir):
    """Process all Django HTML templates in the project."""
    template_dirs = [
        os.path.join(root_dir, "templates"),
    ]

    formatted_count = 0

    for template_dir in template_dirs:
        for root, _, files in os.walk(template_dir):
            for file in files:
                if file.endswith(".html"):
                    file_path = os.path.join(root, file)
                    print(f"Formatting {file_path}...")

                    try:
                        # Read the file
                        with open(file_path, 'r') as f:
                            content = f.read()

                        # Format the content
                        formatted_content = format_template(content)

                        # Write back to the file
                        with open(file_path, 'w') as f:
                            f.write(formatted_content)

                        formatted_count += 1
                    except Exception as e:
                        print(f"Error formatting {file_path}: {e}")

    print(f"\nFormatted {formatted_count} template files.")
    return formatted_count

if __name__ == "__main__":
    root_directory = Path(__file__).parent
    process_django_templates(root_directory)
