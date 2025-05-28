#!/usr/bin/env python3
"""
Format Django templates using VS Code's formatting capabilities.
This script helps to format all Django HTML templates in the project.
"""
import os
import subprocess
import sys
from pathlib import Path

def format_django_templates(root_dir):
    """Format all Django HTML templates in the project."""
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

                    # Use VS Code's formatting command
                    try:
                        subprocess.run(
                            ["code", "--wait", "--goto", file_path,
                             "--command", "editor.action.formatDocument"],
                            check=True,
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE
                        )
                        formatted_count += 1
                    except subprocess.CalledProcessError as e:
                        print(f"Error formatting {file_path}: {e}")

    print(f"\nFormatted {formatted_count} template files.")
    return formatted_count

if __name__ == "__main__":
    root_directory = Path(__file__).parent
    format_django_templates(root_directory)
