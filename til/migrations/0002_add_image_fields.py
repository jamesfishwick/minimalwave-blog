# Generated manually for image field support

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('til', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='til',
            name='image',
            field=models.ImageField(blank=True, help_text='Upload an image for this TIL', null=True, upload_to='til/images/%Y/%m/'),
        ),
        migrations.AddField(
            model_name='til',
            name='image_alt',
            field=models.CharField(blank=True, help_text='Alt text for the image (for accessibility)', max_length=255, null=True),
        ),
        migrations.AlterField(
            model_name='til',
            name='card_image',
            field=models.URLField(blank=True, help_text='URL to image for social media cards (deprecated: use image field)', null=True),
        ),
    ]
