# Sync LinkedIn models with current state

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('blog', '0009_rename_linkedin_post_url_field'),
    ]

    operations = [
        # LinkedInCredentials changes
        migrations.RemoveField(
            model_name='linkedincredentials',
            name='redirect_uri',
        ),
        migrations.AddField(
            model_name='linkedincredentials',
            name='state',
            field=models.CharField(blank=True, max_length=128, null=True, help_text='OAuth state for CSRF protection'),
        ),
        migrations.AddField(
            model_name='linkedincredentials',
            name='authorized_user',
            field=models.CharField(default='pending', max_length=255, help_text='LinkedIn user who authorized the app'),
        ),
        
        # LinkedInSettings model changes
        migrations.RemoveField(
            model_name='linkedinsettings',
            name='auto_post_delay_minutes',
        ),
        migrations.RemoveField(
            model_name='linkedinsettings',
            name='auto_post_enabled',
        ),
        migrations.RemoveField(
            model_name='linkedinsettings',
            name='created_at',
        ),
        migrations.RemoveField(
            model_name='linkedinsettings',
            name='custom_hashtags',
        ),
        migrations.RemoveField(
            model_name='linkedinsettings',
            name='include_tags',
        ),
        migrations.RemoveField(
            model_name='linkedinsettings',
            name='max_tags',
        ),
        migrations.RemoveField(
            model_name='linkedinsettings',
            name='post_template',
        ),
        migrations.RemoveField(
            model_name='linkedinsettings',
            name='updated_at',
        ),
        migrations.AddField(
            model_name='linkedinsettings',
            name='auto_post_blogmarks',
            field=models.BooleanField(default=False, help_text='Automatically post blogmarks to LinkedIn'),
        ),
        migrations.AddField(
            model_name='linkedinsettings',
            name='auto_post_entries',
            field=models.BooleanField(default=True, help_text='Automatically post blog entries to LinkedIn'),
        ),
        migrations.AddField(
            model_name='linkedinsettings',
            name='include_url',
            field=models.BooleanField(default=True, help_text='Include blog post URL in LinkedIn posts'),
        ),
        migrations.AddField(
            model_name='linkedinsettings',
            name='url_template',
            field=models.CharField(default='Read more: {url}', max_length=255, help_text='Template for including URL in posts'),
        ),
        
        # Entry model changes
        migrations.AlterField(
            model_name='entry',
            name='linkedin_custom_text',
            field=models.TextField(blank=True, null=True, help_text='Custom text for LinkedIn post (leave blank to use summary)'),
        ),
    ]