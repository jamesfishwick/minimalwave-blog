"""
Management command to fix migration dependencies in production.
This handles the case where blog.0001_initial is already applied
but depends on core.0001_initial which doesn't exist yet.
"""

from django.core.management.base import BaseCommand
from django.db import connection


class Command(BaseCommand):
    help = 'Fix migration dependencies for production deployment'

    def handle(self, *args, **options):
        with connection.cursor() as cursor:
            # Check if blog.0001_initial is already applied
            cursor.execute(
                "SELECT * FROM django_migrations WHERE app='blog' AND name='0001_initial'"
            )
            blog_migration = cursor.fetchone()

            # Check if core.0001_initial exists
            cursor.execute(
                "SELECT * FROM django_migrations WHERE app='core' AND name='0001_initial'"
            )
            core_migration = cursor.fetchone()

            if blog_migration and not core_migration:
                self.stdout.write(
                    self.style.WARNING(
                        'Blog migration exists but core migration does not. '
                        'Marking core.0001_initial as applied...'
                    )
                )

                # Insert core.0001_initial as already applied
                cursor.execute(
                    "INSERT INTO django_migrations (app, name, applied) "
                    "VALUES ('core', '0001_initial', NOW())"
                )

                self.stdout.write(
                    self.style.SUCCESS('Successfully marked core.0001_initial as applied')
                )
            elif core_migration:
                self.stdout.write(
                    self.style.SUCCESS('Core migration already exists. No action needed.')
                )
            else:
                self.stdout.write(
                    self.style.WARNING(
                        'Blog migration not found. Regular migrations should work.'
                    )
                )