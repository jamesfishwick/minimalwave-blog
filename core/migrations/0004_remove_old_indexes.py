# Migration to remove all custom indexes from EnhancedTag model
# After this migration, only the automatic index on slug (from unique=True) remains

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0003_simplify_taxonomy"),
    ]

    operations = [
        # Remove any remaining custom indexes
        # These operations are safe even if the indexes don't exist
        migrations.RemoveIndex(
            model_name="enhancedtag",
            name="core_enhanc_slug_836ce2_idx",
        ),
    ]
