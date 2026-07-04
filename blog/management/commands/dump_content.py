"""
Export blog content (markdown fields) to files for skill-based editing.

Writes each selected markdown field to
    <output-dir>/<type>-<slug>-<field>.md
with a YAML front-matter header identifying the row (type/pk/slug/field), so
load_content can write the edited text back through the ORM.

Examples:
    python manage.py dump_content --type entry --slug my-post
    python manage.py dump_content --type til
    python manage.py dump_content --all
"""

import os

import yaml
from django.core.management.base import BaseCommand

from ._content_registry import CONTENT_TYPES, resolve_types


class Command(BaseCommand):
    help = "Export blog content markdown fields to files for editing"

    def add_arguments(self, parser):
        parser.add_argument(
            "--type",
            choices=sorted(CONTENT_TYPES),
            help="Content type to dump (omit when using --all)",
        )
        parser.add_argument("--slug", help="Only dump the object with this slug")
        parser.add_argument("--all", action="store_true", help="Dump all content types")
        parser.add_argument(
            "--output-dir",
            default="content",
            help="Directory to write files into (default: content/)",
        )

    def handle(self, *args, **options):
        types = resolve_types(options)
        out = options["output_dir"]
        os.makedirs(out, exist_ok=True)
        slug = options["slug"]

        written = 0
        for tname in types:
            spec = CONTENT_TYPES[tname]
            qs = spec["model"].objects.all()
            if slug:
                qs = qs.filter(slug=slug)
            for obj in qs:
                for field in spec["fields"]:
                    content = getattr(obj, field) or ""
                    meta = {
                        "type": tname,
                        "pk": obj.pk,
                        "slug": obj.slug,
                        "field": field,
                        "title": obj.title,
                    }
                    # Include pk: BaseEntry.slug is unique_for_date (not global),
                    # so two same-slug posts on different dates would otherwise
                    # write to the same file and silently overwrite each other.
                    path = os.path.join(out, f"{tname}-{obj.pk}-{obj.slug}-{field}.md")
                    with open(path, "w", encoding="utf-8") as fh:
                        fh.write("---\n")
                        fh.write(
                            yaml.safe_dump(meta, sort_keys=False, allow_unicode=True)
                        )
                        fh.write("---\n")
                        fh.write(content.rstrip("\n") + "\n")
                    written += 1
                    self.stdout.write(f"wrote {path}")

        if written == 0:
            self.stdout.write(
                self.style.WARNING("No content matched the given filters.")
            )
        else:
            self.stdout.write(self.style.SUCCESS(f"Dumped {written} file(s) to {out}/"))
