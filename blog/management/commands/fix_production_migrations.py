"""
Emergency management command to fix production database migration state.
This handles the complex case where:
1. blog.0001_initial is already applied but now depends on core.0001_initial
2. core.0001_initial needs to be applied but might conflict with existing tables
"""

from django.core.management.base import BaseCommand
from django.db import connection, transaction


class Command(BaseCommand):
    help = 'Fix migration state for production deployment'

    def handle(self, *args, **options):
        with connection.cursor() as cursor:
            # Check current state
            cursor.execute(
                "SELECT * FROM django_migrations WHERE app='blog' AND name='0001_initial'"
            )
            blog_migration = cursor.fetchone()

            cursor.execute(
                "SELECT * FROM django_migrations WHERE app='core' AND name='0001_initial'"
            )
            core_migration = cursor.fetchone()

            if blog_migration and not core_migration:
                self.stdout.write(
                    self.style.WARNING(
                        'Blog migration exists but core migration does not. '
                        'Applying emergency fix...'
                    )
                )

                try:
                    with transaction.atomic():
                        # First, mark core.0001_initial as applied
                        cursor.execute(
                            "INSERT INTO django_migrations (app, name, applied) "
                            "VALUES ('core', '0001_initial', NOW())"
                        )
                        self.stdout.write('Marked core.0001_initial as applied')

                        # Create the core tables that don't exist yet
                        # Check if tables already exist before creating
                        tables_to_create = []

                        # Check for EnhancedTag
                        cursor.execute(
                            "SELECT EXISTS (SELECT 1 FROM information_schema.tables "
                            "WHERE table_schema = 'public' AND table_name = 'core_enhancedtag')"
                        )
                        if not cursor.fetchone()[0]:
                            tables_to_create.append('core_enhancedtag')
                            cursor.execute("""
                                CREATE TABLE core_enhancedtag (
                                    id BIGSERIAL PRIMARY KEY,
                                    name VARCHAR(100) NOT NULL UNIQUE,
                                    slug VARCHAR(100) NOT NULL UNIQUE,
                                    category VARCHAR(50),
                                    description TEXT,
                                    parent_id BIGINT REFERENCES core_enhancedtag(id),
                                    is_primary BOOLEAN DEFAULT FALSE,
                                    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                                    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                                )
                            """)
                            self.stdout.write('Created core_enhancedtag table')

                        # Check for Series
                        cursor.execute(
                            "SELECT EXISTS (SELECT 1 FROM information_schema.tables "
                            "WHERE table_schema = 'public' AND table_name = 'core_series')"
                        )
                        if not cursor.fetchone()[0]:
                            tables_to_create.append('core_series')
                            cursor.execute("""
                                CREATE TABLE core_series (
                                    id BIGSERIAL PRIMARY KEY,
                                    title VARCHAR(200) NOT NULL,
                                    slug VARCHAR(200) NOT NULL UNIQUE,
                                    description TEXT,
                                    status VARCHAR(20) DEFAULT 'active',
                                    order_type VARCHAR(20) DEFAULT 'chronological',
                                    cover_image VARCHAR(500),
                                    created TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                                    updated TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                                )
                            """)
                            self.stdout.write('Created core_series table')

                        # Check for Taxonomy
                        cursor.execute(
                            "SELECT EXISTS (SELECT 1 FROM information_schema.tables "
                            "WHERE table_schema = 'public' AND table_name = 'core_taxonomy')"
                        )
                        if not cursor.fetchone()[0]:
                            tables_to_create.append('core_taxonomy')
                            cursor.execute("""
                                CREATE TABLE core_taxonomy (
                                    id BIGSERIAL PRIMARY KEY,
                                    name VARCHAR(100) NOT NULL UNIQUE,
                                    slug VARCHAR(100) NOT NULL UNIQUE,
                                    taxonomy_type VARCHAR(50),
                                    description TEXT,
                                    parent_id BIGINT REFERENCES core_taxonomy(id),
                                    metadata JSONB
                                )
                            """)
                            self.stdout.write('Created core_taxonomy table')

                        # Create indexes
                        if 'core_enhancedtag' in tables_to_create:
                            cursor.execute("CREATE INDEX IF NOT EXISTS idx_enhancedtag_slug ON core_enhancedtag(slug)")
                            cursor.execute("CREATE INDEX IF NOT EXISTS idx_enhancedtag_category ON core_enhancedtag(category)")

                        if 'core_series' in tables_to_create:
                            cursor.execute("CREATE INDEX IF NOT EXISTS idx_series_slug ON core_series(slug)")
                            cursor.execute("CREATE INDEX IF NOT EXISTS idx_series_status ON core_series(status)")

                        if 'core_taxonomy' in tables_to_create:
                            cursor.execute("CREATE INDEX IF NOT EXISTS idx_taxonomy_slug ON core_taxonomy(slug)")
                            cursor.execute("CREATE INDEX IF NOT EXISTS idx_taxonomy_type ON core_taxonomy(taxonomy_type)")

                        self.stdout.write(
                            self.style.SUCCESS(
                                f'Successfully created {len(tables_to_create)} core tables'
                            )
                        )

                except Exception as e:
                    self.stdout.write(
                        self.style.ERROR(f'Failed to apply fix: {e}')
                    )
                    raise

            else:
                self.stdout.write(
                    self.style.SUCCESS('Migration state looks correct.')
                )