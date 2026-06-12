# Replaces AlterField (unsupported for M2M) with SeparateDatabaseAndState:
# drops the old EnhancedTag join tables via raw SQL, updates Django state to TaggableManager.

import taggit.managers
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("blog", "0004_remove_linkedin"),
        (
            "taggit",
            "0006_rename_taggeditem_content_type_object_id_taggit_tagg_content_8fc721_idx",
        ),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            database_operations=[
                migrations.RunSQL("DROP TABLE IF EXISTS blog_blogmark_tags;"),
                migrations.RunSQL("DROP TABLE IF EXISTS blog_entry_tags;"),
            ],
            state_operations=[
                migrations.AlterField(
                    model_name="blogmark",
                    name="tags",
                    field=taggit.managers.TaggableManager(
                        blank=True,
                        help_text="A comma-separated list of tags.",
                        through="taggit.TaggedItem",
                        to="taggit.Tag",
                        verbose_name="Tags",
                    ),
                ),
                migrations.AlterField(
                    model_name="entry",
                    name="tags",
                    field=taggit.managers.TaggableManager(
                        blank=True,
                        help_text="A comma-separated list of tags.",
                        through="taggit.TaggedItem",
                        to="taggit.Tag",
                        verbose_name="Tags",
                    ),
                ),
            ],
        ),
    ]
