# Add missing linkedin_posted field

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('blog', '0007_add_linkedin_fields'),
    ]

    operations = [
        migrations.AddField(
            model_name='entry',
            name='linkedin_posted',
            field=models.BooleanField(default=False, help_text='Whether this entry has been posted to LinkedIn'),
        ),
    ]