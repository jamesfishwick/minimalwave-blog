# Generated by Django 5.2 on 2025-05-27 00:28

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("blog", "0002_blogmark_publish_date_blogmark_status_and_more"),
    ]

    operations = [
        migrations.CreateModel(
            name="SiteSettings",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "site_title",
                    models.CharField(
                        default="Minimal Wave Blog",
                        help_text="The title of your blog",
                        max_length=100,
                    ),
                ),
                (
                    "site_description",
                    models.TextField(
                        default="A personal blog with minimal wave aesthetics",
                        help_text="The description of your blog",
                    ),
                ),
                (
                    "header_logo",
                    models.ImageField(
                        blank=True,
                        help_text="Logo to display in the header (optional)",
                        null=True,
                        upload_to="site_settings/",
                    ),
                ),
                (
                    "favicon",
                    models.ImageField(
                        blank=True,
                        help_text="Site favicon (optional)",
                        null=True,
                        upload_to="site_settings/",
                    ),
                ),
            ],
            options={
                "verbose_name": "Site Settings",
                "verbose_name_plural": "Site Settings",
            },
        ),
    ]
