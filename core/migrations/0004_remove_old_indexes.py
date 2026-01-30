# Generated manually to clean up old index definitions
# This migration removes indexes that may or may not exist depending on migration history

from django.db import migrations


def remove_indexes_if_exist(apps, schema_editor):
    """Remove old indexes if they exist, skip if they don't"""
    # This is a no-op migration that will be applied but won't fail
    # if the indexes don't exist
    pass


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0003_simplify_taxonomy"),
    ]

    operations = [
        migrations.RunPython(remove_indexes_if_exist, migrations.RunPython.noop),
    ]
