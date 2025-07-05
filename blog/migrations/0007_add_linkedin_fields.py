# Add missing LinkedIn fields to Entry model

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('blog', '0006_create_default_site'),
    ]

    operations = [
        migrations.AddField(
            model_name='entry',
            name='linkedin_enabled',
            field=models.BooleanField(default=True, help_text='Automatically post to LinkedIn when published'),
        ),
        migrations.AddField(
            model_name='entry',
            name='linkedin_custom_text',
            field=models.TextField(blank=True, help_text='Custom text for LinkedIn post (optional)', null=True),
        ),
    ]