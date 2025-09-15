"""
Management command to show and optionally fix Django Site information.
"""
from django.core.management.base import BaseCommand
from django.contrib.sites.models import Site

class Command(BaseCommand):
    help = 'Show current Django Site information'

    def add_arguments(self, parser):
        parser.add_argument(
            '--fix',
            action='store_true',
            help='Fix the site domain to jamesfishwick.com',
        )

    def handle(self, *args, **options):
        try:
            # Get all sites
            sites = Site.objects.all()
            
            self.stdout.write("=== Django Sites Information ===")
            for site in sites:
                self.stdout.write(f"Site ID: {site.id}")
                self.stdout.write(f"Domain: {site.domain}")
                self.stdout.write(f"Name: {site.name}")
                self.stdout.write("---")
            
            # Get current site
            current_site = Site.objects.get_current()
            self.stdout.write(f"Current site: {current_site.domain}")
            
            if options['fix']:
                if current_site.domain != 'jamesfishwick.com':
                    old_domain = current_site.domain
                    current_site.domain = 'jamesfishwick.com'
                    current_site.name = 'James Fishwick Blog'
                    current_site.save()
                    
                    self.stdout.write(
                        self.style.SUCCESS(
                            f'✅ Site domain updated: {old_domain} → {current_site.domain}'
                        )
                    )
                else:
                    self.stdout.write(
                        self.style.SUCCESS('✅ Site domain is already correct')
                    )
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Error: {str(e)}')
            )