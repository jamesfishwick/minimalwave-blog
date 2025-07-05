# Generated manually for LinkedIn integration

from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('blog', '0003_sitesettings'),
    ]

    operations = [
        migrations.CreateModel(
            name='LinkedInCredentials',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('client_id', models.CharField(help_text='LinkedIn App Client ID', max_length=255)),
                ('client_secret', models.CharField(help_text='LinkedIn App Client Secret', max_length=255)),
                ('redirect_uri', models.URLField(help_text='OAuth redirect URI')),
                ('access_token', models.TextField(blank=True, help_text='OAuth access token', null=True)),
                ('token_expires_at', models.DateTimeField(blank=True, help_text='When the access token expires', null=True)),
                ('refresh_token', models.TextField(blank=True, help_text='OAuth refresh token', null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'verbose_name': 'LinkedIn Credentials',
                'verbose_name_plural': 'LinkedIn Credentials',
            },
        ),
        migrations.CreateModel(
            name='LinkedInSettings',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('enabled', models.BooleanField(default=True, help_text='Enable LinkedIn integration globally')),
                ('auto_post_enabled', models.BooleanField(default=False, help_text='Automatically post new blog entries to LinkedIn')),
                ('auto_post_delay_minutes', models.PositiveIntegerField(default=5, help_text='Minutes to wait before auto-posting')),
                ('include_tags', models.BooleanField(default=True, help_text='Include blog post tags as hashtags')),
                ('max_tags', models.PositiveIntegerField(default=5, help_text='Maximum number of hashtags to include')),
                ('custom_hashtags', models.CharField(blank=True, help_text='Additional hashtags to always include (comma-separated)', max_length=500)),
                ('post_template', models.TextField(default='New blog post: {title}\n\n{summary}\n\nRead more: {url}', help_text='Template for LinkedIn posts. Available variables: {title}, {summary}, {url}, {tags}')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'verbose_name': 'LinkedIn Settings',
                'verbose_name_plural': 'LinkedIn Settings',
            },
        ),
        migrations.CreateModel(
            name='LinkedInPost',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('linkedin_post_id', models.CharField(blank=True, help_text='LinkedIn post ID', max_length=255, null=True)),
                ('linkedin_post_url', models.URLField(blank=True, help_text='URL to the LinkedIn post', null=True)),
                ('post_content', models.TextField(help_text='Content that was posted to LinkedIn')),
                ('posted_at', models.DateTimeField(default=django.utils.timezone.now)),
                ('is_successful', models.BooleanField(default=True, help_text='Whether the post was successful')),
                ('error_message', models.TextField(blank=True, help_text='Error message if posting failed', null=True)),
                ('visibility', models.CharField(choices=[('PUBLIC', 'Public'), ('CONNECTIONS', 'Connections only')], default='PUBLIC', max_length=20)),
                ('engagement_stats', models.JSONField(blank=True, default=dict, help_text='Engagement statistics from LinkedIn')),
                ('entry', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='linkedin_posts', to='blog.entry')),
            ],
            options={
                'verbose_name': 'LinkedIn Post',
                'verbose_name_plural': 'LinkedIn Posts',
                'ordering': ['-posted_at'],
            },
        ),
    ]