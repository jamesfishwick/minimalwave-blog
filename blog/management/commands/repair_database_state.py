"""
Emergency database repair command for production deployment.
This fixes the mismatch between migration records and actual database tables.
"""

from django.core.management.base import BaseCommand
from django.db import connection, transaction


class Command(BaseCommand):
    help = 'Repair database state by ensuring tables match migration records'

    def handle(self, *args, **options):
        with connection.cursor() as cursor:
            # Check what migration records exist
            cursor.execute("SELECT app, name FROM django_migrations WHERE app IN ('core', 'blog') ORDER BY app, name")
            migrations = cursor.fetchall()

            self.stdout.write("Current migration records:")
            for app, name in migrations:
                self.stdout.write(f"  {app}.{name}")

            # Check which core tables actually exist
            cursor.execute("""
                SELECT table_name FROM information_schema.tables
                WHERE table_schema = 'public' AND table_name LIKE 'core_%'
                ORDER BY table_name
            """)
            core_tables = [row[0] for row in cursor.fetchall()]

            self.stdout.write(f"\\nExisting core tables: {core_tables}")

            # Expected core tables based on migrations
            expected_tables = ['core_enhancedtag', 'core_series', 'core_taxonomy']
            missing_tables = [table for table in expected_tables if table not in core_tables]

            if missing_tables:
                self.stdout.write(f"\\nMissing tables: {missing_tables}")
                self.stdout.write("Creating missing tables...")

                try:
                    with transaction.atomic():
                        # Create missing tables
                        if 'core_enhancedtag' in missing_tables:
                            cursor.execute("""
                                CREATE TABLE core_enhancedtag (
                                    id BIGSERIAL PRIMARY KEY,
                                    name VARCHAR(100) NOT NULL UNIQUE,
                                    slug VARCHAR(100) NOT NULL UNIQUE,
                                    category VARCHAR(50),
                                    description TEXT,
                                    parent_id BIGINT,
                                    is_primary BOOLEAN DEFAULT FALSE,
                                    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                                    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                                )
                            """)
                            cursor.execute("CREATE INDEX IF NOT EXISTS idx_enhancedtag_slug ON core_enhancedtag(slug)")
                            cursor.execute("CREATE INDEX IF NOT EXISTS idx_enhancedtag_category ON core_enhancedtag(category)")
                            cursor.execute("ALTER TABLE core_enhancedtag ADD CONSTRAINT core_enhancedtag_parent_id_fkey FOREIGN KEY (parent_id) REFERENCES core_enhancedtag(id) DEFERRABLE INITIALLY DEFERRED")
                            self.stdout.write("✓ Created core_enhancedtag")

                        if 'core_series' in missing_tables:
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
                            cursor.execute("CREATE INDEX IF NOT EXISTS idx_series_slug ON core_series(slug)")
                            cursor.execute("CREATE INDEX IF NOT EXISTS idx_series_status ON core_series(status)")
                            self.stdout.write("✓ Created core_series")

                        if 'core_taxonomy' in missing_tables:
                            cursor.execute("""
                                CREATE TABLE core_taxonomy (
                                    id BIGSERIAL PRIMARY KEY,
                                    name VARCHAR(100) NOT NULL UNIQUE,
                                    slug VARCHAR(100) NOT NULL UNIQUE,
                                    taxonomy_type VARCHAR(50),
                                    description TEXT,
                                    parent_id BIGINT,
                                    metadata JSONB
                                )
                            """)
                            cursor.execute("CREATE INDEX IF NOT EXISTS idx_taxonomy_slug ON core_taxonomy(slug)")
                            cursor.execute("CREATE INDEX IF NOT EXISTS idx_taxonomy_type ON core_taxonomy(taxonomy_type)")
                            cursor.execute("ALTER TABLE core_taxonomy ADD CONSTRAINT core_taxonomy_parent_id_fkey FOREIGN KEY (parent_id) REFERENCES core_taxonomy(id) DEFERRABLE INITIALLY DEFERRED")
                            self.stdout.write("✓ Created core_taxonomy")

                        self.stdout.write(f"\\n✅ Successfully created {len(missing_tables)} missing tables")

                except Exception as e:
                    self.stdout.write(f"❌ Error creating tables: {e}")
                    # Don't raise - let migrations continue and potentially fix themselves

            else:
                self.stdout.write("\\n✅ All expected core tables exist")

            # Verify table creation
            cursor.execute("""
                SELECT table_name FROM information_schema.tables
                WHERE table_schema = 'public' AND table_name LIKE 'core_%'
                ORDER BY table_name
            """)
            final_tables = [row[0] for row in cursor.fetchall()]
            self.stdout.write(f"\\nFinal core tables: {final_tables}")

            # Check if we can proceed with migrations
            all_exist = all(table in final_tables for table in expected_tables)
            if all_exist:
                self.stdout.write("\\n✅ Database state repaired - migrations should proceed normally")
            else:
                self.stdout.write("\\n⚠️  Some tables still missing - migrations may fail")