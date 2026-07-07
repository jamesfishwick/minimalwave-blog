"""Delete orphaned rows from the django_migrations table.

Production's migration history carries records for migrations whose files were
removed long ago: an old pre-squash blog chain (0002-0011, heavy on the
retired linkedin feature), the deleted linkedin app's initial, and a
superseded til migration. Django ignores these (they are not in the graph
built from the on-disk files), but they are confusing cruft. This removes
exactly those records and nothing else.

Safe by construction:
- Only the hardcoded (app, name) pairs below are deleted. Every one was
  confirmed absent from disk yet present in the applied set
  (MigrationLoader: applied - disk) against a production copy.
- Idempotent: a second run deletes nothing. On a fresh database (tests, CI)
  none of these rows exist, so it is a no-op.
- Never touches a record that has a migration file, so the live graph and
  every deploy's `migrate` remain unaffected.
"""

from django.db import migrations

# (app_label, migration_name) records with no corresponding file on disk.
LEGACY_RECORDS = [
    ("blog", "0002_blogmark_publish_date_blogmark_status_and_more"),
    ("blog", "0003_sitesettings"),
    ("blog", "0004_linkedin_models"),
    ("blog", "0005_sync_models"),
    ("blog", "0006_create_default_site"),
    ("blog", "0007_add_linkedin_fields"),
    ("blog", "0008_add_linkedin_posted"),
    ("blog", "0009_rename_linkedin_post_url_field"),
    ("blog", "0010_sync_linkedin_models"),
    ("blog", "0011_alter_entry_linkedin_enabled_and_more"),
    ("linkedin", "0001_initial"),
    ("til", "0002_add_card_image_and_linkedin_fields"),
]


def prune_legacy_records(apps, schema_editor):
    with schema_editor.connection.cursor() as cursor:
        cursor.executemany(
            "DELETE FROM django_migrations WHERE app = %s AND name = %s",
            LEGACY_RECORDS,
        )


class Migration(migrations.Migration):
    dependencies = [
        ("blog", "0006_migrate_til_to_entry"),
    ]

    operations = [
        # Reverse is a no-op: deleted history records cannot be meaningfully
        # recreated, and they were dead weight to begin with.
        migrations.RunPython(prune_legacy_records, migrations.RunPython.noop),
    ]
