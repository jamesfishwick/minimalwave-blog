from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0005_remove_enhancedtag_core_enhanc_content_9af629_idx_and_more"),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            database_operations=[
                migrations.RunSQL(
                    sql="DROP TABLE IF EXISTS core_contentlinkedin CASCADE",
                    reverse_sql="",
                ),
            ],
            state_operations=[
                migrations.DeleteModel(name="ContentLinkedIn"),
            ],
        ),
    ]
