# Rename linkedin_post_url to post_url in LinkedInPost model

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('blog', '0008_add_linkedin_posted'),
    ]

    operations = [
        migrations.RenameField(
            model_name='linkedinpost',
            old_name='linkedin_post_url',
            new_name='post_url',
        ),
        migrations.RenameField(
            model_name='linkedinpost',
            old_name='post_content',
            new_name='post_text',
        ),
        migrations.RemoveField(
            model_name='linkedinpost',
            name='is_successful',
        ),
        migrations.RemoveField(
            model_name='linkedinpost',
            name='visibility',
        ),
        migrations.RemoveField(
            model_name='linkedinpost',
            name='engagement_stats',
        ),
        migrations.AddField(
            model_name='linkedinpost',
            name='status',
            field=models.CharField(
                choices=[
                    ('pending', 'Pending'),
                    ('posted', 'Posted'),
                    ('failed', 'Failed'),
                ],
                default='pending',
                max_length=20
            ),
        ),
        migrations.AlterField(
            model_name='linkedinpost',
            name='linkedin_post_id',
            field=models.CharField(
                help_text='LinkedIn post URN',
                max_length=255,
                unique=True
            ),
        ),
        migrations.AlterField(
            model_name='linkedinpost',
            name='posted_at',
            field=models.DateTimeField(auto_now_add=True),
        ),
    ]