"""
Management command to validate all Django templates for syntax errors.
"""
from django.core.management.base import BaseCommand
from django.template import engines
from django.template.loader import get_template
from django.apps import apps
import os
import glob


class Command(BaseCommand):
    help = 'Validate all Django templates for syntax errors'

    def handle(self, *args, **options):
        """Validate all templates in the project."""
        template_dirs = []
        
        # Get template directories from settings
        engine = engines['django']
        template_dirs.extend(engine.engine.dirs)
        
        # Get app template directories
        for app_config in apps.get_app_configs():
            app_template_dir = os.path.join(app_config.path, 'templates')
            if os.path.exists(app_template_dir):
                template_dirs.append(app_template_dir)
        
        errors = []
        validated_count = 0
        
        for template_dir in template_dirs:
            for template_file in glob.glob(os.path.join(template_dir, '**/*.html'), recursive=True):
                # Get template name relative to template dir
                template_name = os.path.relpath(template_file, template_dir)
                
                try:
                    # Try to compile the template
                    get_template(template_name)
                    validated_count += 1
                    self.stdout.write(f'✓ {template_name}')
                except Exception as e:
                    errors.append(f'✗ {template_name}: {str(e)}')
                    self.stdout.write(
                        self.style.ERROR(f'✗ {template_name}: {str(e)}')
                    )
        
        self.stdout.write(f'\nValidated {validated_count} templates')
        
        if errors:
            self.stdout.write(
                self.style.ERROR(f'\n{len(errors)} template errors found:')
            )
            for error in errors:
                self.stdout.write(self.style.ERROR(f'  {error}'))
            exit(1)
        else:
            self.stdout.write(
                self.style.SUCCESS('All templates validated successfully!')
            )