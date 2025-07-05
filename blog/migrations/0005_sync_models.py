# Empty migration to sync model state

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('blog', '0004_linkedin_models'),
    ]

    operations = [
        # Empty migration to sync current model state
        # This resolves "Your models have changes not reflected in migration" 
    ]