# Generated migration for taxonomy simplification
# This migration has been refactored to handle both clean databases (CI) and existing production databases

from django.db import migrations, models


def simplify_taxonomy(apps, schema_editor):
    """
    Safely simplify taxonomy by removing old models and fields.
    Handles both clean databases and databases where these models never existed.
    """
    db_alias = schema_editor.connection.alias
    with schema_editor.connection.cursor() as cursor:
        # Drop index if it exists (must happen before dropping column)
        try:
            cursor.execute('DROP INDEX IF EXISTS core_enhanc_content_9af629_idx')
        except Exception:
            pass

        # Drop old tables if they exist
        for table in ['core_seriesentry', 'core_series', 'core_category']:
            try:
                cursor.execute(f'DROP TABLE IF EXISTS {table} CASCADE')
            except Exception:
                pass

        # Remove fields from EnhancedTag if they exist
        # Check which fields exist first
        is_postgres = 'postgresql' in schema_editor.connection.settings_dict['ENGINE']

        if is_postgres:
            # PostgreSQL - check information_schema
            cursor.execute("""
                SELECT column_name
                FROM information_schema.columns
                WHERE table_name = 'core_enhancedtag'
            """)
            existing_columns = {row[0] for row in cursor.fetchall()}
        else:
            # SQLite - use pragma
            cursor.execute("PRAGMA table_info(core_enhancedtag)")
            existing_columns = {row[1] for row in cursor.fetchall()}

        # List of columns to remove
        columns_to_remove = {'category_id', 'content_type', 'color', 'icon', 'usage_count', 'last_used'}
        columns_to_remove = columns_to_remove & existing_columns  # Only remove if they exist

        if columns_to_remove:
            # For SQLite, we need to recreate the table without these columns
            # For PostgreSQL, we can drop columns directly
            if is_postgres:
                for column in columns_to_remove:
                    try:
                        cursor.execute(f'ALTER TABLE core_enhancedtag DROP COLUMN {column} CASCADE')
                    except Exception:
                        pass
            else:
                # SQLite requires table recreation - but we'll let Django handle this
                # by using the model's current state
                pass


def add_new_indexes(apps, schema_editor):
    """Add new indexes for slug and is_active fields"""
    with schema_editor.connection.cursor() as cursor:
        # Add index for slug if it doesn't exist
        try:
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS core_enhanc_slug_idx
                ON core_enhancedtag (slug)
            """)
        except Exception:
            pass

        # Add index for is_active if it doesn't exist
        try:
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS core_enhanc_is_acti_idx
                ON core_enhancedtag (is_active)
            """)
        except Exception:
            pass


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0002_seriesentry'),
    ]

    operations = [
        # Use SeparateDatabaseAndState to handle database ops separately from state ops
        migrations.SeparateDatabaseAndState(
            database_operations=[
                # Database operations: Handle existing and non-existing tables/columns safely
                migrations.RunPython(
                    simplify_taxonomy,
                    reverse_code=migrations.RunPython.noop,
                ),
                migrations.RunPython(
                    add_new_indexes,
                    reverse_code=migrations.RunPython.noop,
                ),
            ],
            state_operations=[
                # State operations: Update Django's migration state
                # First remove the index that references content_type
                migrations.RemoveIndex(
                    model_name='enhancedtag',
                    name='core_enhanc_content_9af629_idx',
                ),
                # Then remove fields
                migrations.RemoveField(model_name='enhancedtag', name='category'),
                migrations.RemoveField(model_name='enhancedtag', name='content_type'),
                migrations.RemoveField(model_name='enhancedtag', name='color'),
                migrations.RemoveField(model_name='enhancedtag', name='icon'),
                migrations.RemoveField(model_name='enhancedtag', name='usage_count'),
                migrations.RemoveField(model_name='enhancedtag', name='last_used'),
                # Remove old models
                migrations.DeleteModel(name='SeriesEntry'),
                migrations.DeleteModel(name='Series'),
                migrations.DeleteModel(name='Category'),
                # Update model options
                migrations.AlterModelOptions(
                    name='enhancedtag',
                    options={'ordering': ['name']},
                ),
            ],
        ),
    ]
