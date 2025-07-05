# Create default Site object

from django.db import migrations


def create_default_site(apps, schema_editor):
    Site = apps.get_model('sites', 'Site')
    if not Site.objects.filter(pk=1).exists():
        Site.objects.create(
            pk=1,
            domain='jamesfishwick.com',
            name='Minimal Wave Blog'
        )


def reverse_default_site(apps, schema_editor):
    Site = apps.get_model('sites', 'Site')
    Site.objects.filter(pk=1).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('blog', '0005_sync_models'),
        ('sites', '0002_alter_domain_unique'),
    ]

    operations = [
        migrations.RunPython(create_default_site, reverse_default_site),
    ]