# Generated by Django 5.2 on 2025-05-26 23:37

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("blog", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="blogmark",
            name="publish_date",
            field=models.DateTimeField(
                blank=True,
                help_text="Schedule this content to be published at a future date and time",
                null=True,
            ),
        ),
        migrations.AddField(
            model_name="blogmark",
            name="status",
            field=models.CharField(
                choices=[
                    ("draft", "Draft"),
                    ("review", "In Review"),
                    ("published", "Published"),
                ],
                default="draft",
                help_text="Draft entries are only visible to logged-in users with the preview link",
                max_length=10,
            ),
        ),
        migrations.AddField(
            model_name="entry",
            name="publish_date",
            field=models.DateTimeField(
                blank=True,
                help_text="Schedule this content to be published at a future date and time",
                null=True,
            ),
        ),
        migrations.AddField(
            model_name="entry",
            name="status",
            field=models.CharField(
                choices=[
                    ("draft", "Draft"),
                    ("review", "In Review"),
                    ("published", "Published"),
                ],
                default="draft",
                help_text="Draft entries are only visible to logged-in users with the preview link",
                max_length=10,
            ),
        ),
        migrations.AlterField(
            model_name="blogmark",
            name="is_draft",
            field=models.BooleanField(
                default=False, help_text="Legacy field. Use 'status' instead."
            ),
        ),
        migrations.AlterField(
            model_name="entry",
            name="is_draft",
            field=models.BooleanField(
                default=False, help_text="Legacy field. Use 'status' instead."
            ),
        ),
    ]
