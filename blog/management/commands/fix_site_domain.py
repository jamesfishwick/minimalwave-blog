"""
Management command to fix the Django Site domain for LinkedIn OAuth.
"""
from django.core.management.base import BaseCommand
from django.contrib.sites.models import Site

class Command(BaseCommand):
    help = 'Fix Django Site domain for LinkedIn OAuth'

    def handle(self, *args, **options):
        # Get the current site (should be pk=1 by default)
        try:
            site = Site.objects.get(pk=1)
            old_domain = site.domain
            old_name = site.name
            
            # Update to correct domain
            site.domain = 'jamesfishwick.com'
            site.name = 'James Fishwick Blog'
            site.save()
            
            self.stdout.write(
                self.style.SUCCESS(
                    f'Site updated: {old_domain} -> {site.domain}, {old_name} -> {site.name}'
                )
            )
            
        except Site.DoesNotExist:
            # Create the site if it doesn't exist
            site = Site.objects.create(
                pk=1,
                domain='jamesfishwick.com',
                name='James Fishwick Blog'
            )
            self.stdout.write(
                self.style.SUCCESS(f'Site created: {site.domain}')
            )
            
        # Verify the change
        current_site = Site.objects.get_current()
        self.stdout.write(f'Current site domain: {current_site.domain}')