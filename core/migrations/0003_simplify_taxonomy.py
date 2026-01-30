# Generated migration for taxonomy simplification

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0002_seriesentry'),
    ]

    operations = [
        # FIRST: Remove the index on content_type before removing the field
        # This prevents SQLite errors when dropping the column
        migrations.RemoveIndex(
            model_name='enhancedtag',
            name='core_enhanc_content_9af629_idx',
        ),

        # Remove SeriesEntry model (depends on Series)
        migrations.DeleteModel(
            name='SeriesEntry',
        ),

        # Remove Series model (depends on Category)
        migrations.DeleteModel(
            name='Series',
        ),

        # Remove Category model
        migrations.DeleteModel(
            name='Category',
        ),

        # Remove fields from EnhancedTag (index already removed above)
        migrations.RemoveField(
            model_name='enhancedtag',
            name='category',
        ),
        migrations.RemoveField(
            model_name='enhancedtag',
            name='content_type',
        ),
        migrations.RemoveField(
            model_name='enhancedtag',
            name='color',
        ),
        migrations.RemoveField(
            model_name='enhancedtag',
            name='icon',
        ),
        migrations.RemoveField(
            model_name='enhancedtag',
            name='usage_count',
        ),
        migrations.RemoveField(
            model_name='enhancedtag',
            name='last_used',
        ),

        # Remove old indexes
        migrations.AlterIndexTogether(
            name='enhancedtag',
            index_together=set(),
        ),

        # Update Meta for EnhancedTag
        migrations.AlterModelOptions(
            name='enhancedtag',
            options={'ordering': ['name']},
        ),

        # Add new indexes
        migrations.AddIndex(
            model_name='enhancedtag',
            index=models.Index(fields=['slug'], name='core_enhanc_slug_idx'),
        ),
        migrations.AddIndex(
            model_name='enhancedtag',
            index=models.Index(fields=['is_active'], name='core_enhanc_is_acti_idx'),
        ),
    ]
