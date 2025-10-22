# Generated manually for image field support

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('blog', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='entry',
            name='image',
            field=models.ImageField(blank=True, help_text='Upload an image for this entry (replaces card_image URL)', null=True, upload_to='blog/images/%Y/%m/'),
        ),
        migrations.AddField(
            model_name='entry',
            name='image_alt',
            field=models.CharField(blank=True, help_text='Alt text for the image (for accessibility)', max_length=255, null=True),
        ),
        migrations.AddField(
            model_name='blogmark',
            name='image',
            field=models.ImageField(blank=True, help_text='Upload an image for this blogmark', null=True, upload_to='blog/blogmarks/%Y/%m/'),
        ),
        migrations.AddField(
            model_name='blogmark',
            name='image_alt',
            field=models.CharField(blank=True, help_text='Alt text for the image (for accessibility)', max_length=255, null=True),
        ),
        migrations.AlterField(
            model_name='entry',
            name='card_image',
            field=models.URLField(blank=True, help_text='URL to image for social media cards (deprecated: use image field)', null=True),
        ),
    ]
