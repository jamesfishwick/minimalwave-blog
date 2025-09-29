"""
Management command to configure the site for local development.
"""

from django.core.management.base import BaseCommand
from django.contrib.sites.models import Site
from django.conf import settings


class Command(BaseCommand):
    help = 'Configure site domain for local development'

    def handle(self, *args, **options):
        try:
            site = Site.objects.get(id=settings.SITE_ID)

            # Update for local development
            site.domain = 'localhost:8000'
            site.name = 'Minimal Wave Blog (Development)'
            site.save()

            self.stdout.write(
                self.style.SUCCESS(
                    f'✅ Site configured for development:\n'
                    f'   Domain: {site.domain}\n'
                    f'   Name: {site.name}'
                )
            )

        except Site.DoesNotExist:
            # Create new site if it doesn't exist
            site = Site.objects.create(
                id=settings.SITE_ID,
                domain='localhost:8000',
                name='Minimal Wave Blog (Development)'
            )

            self.stdout.write(
                self.style.SUCCESS(
                    f'✅ Development site created:\n'
                    f'   Domain: {site.domain}\n'
                    f'   Name: {site.name}'
                )
            )