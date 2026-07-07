"""Drop the til_til table.

TIL content was folded into blog Entry by blog.0006_migrate_til_to_entry.
The dependency on that migration is load-bearing: it forces the data copy to
complete before this drops the source table, on a fresh database and on prod
alike. Media under til/images/ is NOT touched — migrated entries still point
at those files.
"""

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("til", "0005_alter_til_tags"),
        ("blog", "0006_migrate_til_to_entry"),
    ]

    operations = [
        migrations.DeleteModel(
            name="TIL",
        ),
    ]
