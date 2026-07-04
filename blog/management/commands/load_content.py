"""
Write edited content files back into the database through the ORM.

Reads files produced by dump_content. For each file whose text differs from the
current DB value, prints a unified diff and (unless --dry-run) saves the change
via Model.save() so save() logic (status/is_draft sync) and signals (auto-tag)
fire correctly.

Use --dry-run as the review/accept gate: it shows the exact diff that would be
written, with the live DB row as the baseline.

Examples:
    python manage.py load_content content/entry-my-post-body.md --dry-run
    python manage.py load_content content/entry-my-post-body.md
"""

import difflib

import yaml
from django.core.management.base import BaseCommand, CommandError

from ._content_registry import CONTENT_TYPES


def parse_file(path):
    """Split a dumped file into (metadata dict, body string)."""
    with open(path, encoding="utf-8") as fh:
        text = fh.read()
    if not text.startswith("---\n"):
        raise CommandError(f"{path}: missing YAML front-matter")
    # Front-matter is the first block delimited by a leading '---\n' and a
    # following '\n---\n'. Split only once so '---' inside the body is safe.
    head, sep, body = text[len("---\n") :].partition("\n---\n")
    if not sep:
        raise CommandError(f"{path}: malformed front-matter (no closing '---')")
    meta = yaml.safe_load(head) or {}
    return meta, body


class Command(BaseCommand):
    help = "Write edited content files back to the database via the ORM"

    def add_arguments(self, parser):
        parser.add_argument("files", nargs="+", help="Content files to load")
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Show diffs without saving (the accept gate)",
        )

    def handle(self, *args, **options):
        dry = options["dry_run"]
        changed = unchanged = skipped = 0

        for path in options["files"]:
            meta, body = parse_file(path)
            tname, pk = meta.get("type"), meta.get("pk")
            field, slug = meta.get("field"), meta.get("slug")

            spec = CONTENT_TYPES.get(tname)
            if not spec:
                self.stderr.write(self.style.ERROR(f"{path}: unknown type '{tname}'"))
                skipped += 1
                continue
            if field not in spec["fields"]:
                self.stderr.write(
                    self.style.ERROR(
                        f"{path}: field '{field}' is not editable for '{tname}'"
                    )
                )
                skipped += 1
                continue
            try:
                obj = spec["model"].objects.get(pk=pk)
            except spec["model"].DoesNotExist:
                self.stderr.write(
                    self.style.ERROR(
                        f"{path}: {tname} pk={pk} not found (wrong database?)"
                    )
                )
                skipped += 1
                continue
            # Guard against stale files / wrong DB: the pk's slug must still match.
            if slug and obj.slug != slug:
                self.stderr.write(
                    self.style.ERROR(
                        f"{path}: slug mismatch (file '{slug}' != db '{obj.slug}') — stale file? skipping"
                    )
                )
                skipped += 1
                continue

            # strip leading/trailing blank lines so a markdown formatter adding a
            # blank line after the front-matter doesn't create spurious diffs.
            current = (getattr(obj, field) or "").strip("\n")
            new = body.strip("\n")
            if current == new:
                unchanged += 1
                self.stdout.write(f"unchanged: {tname} '{obj.slug}' [{field}]")
                continue

            diff = difflib.unified_diff(
                current.splitlines(),
                new.splitlines(),
                fromfile=f"db:{tname}/{obj.slug}/{field}",
                tofile=f"file:{path}",
                lineterm="",
            )
            self.stdout.write("\n".join(diff))

            if dry:
                self.stdout.write(
                    self.style.WARNING(
                        f"[dry-run] would update {tname} '{obj.slug}' [{field}]"
                    )
                )
            else:
                setattr(obj, field, new)
                obj.save()
                self.stdout.write(
                    self.style.SUCCESS(f"updated {tname} '{obj.slug}' [{field}]")
                )
            changed += 1

        verb = "would change" if dry else "changed"
        self.stdout.write(
            self.style.SUCCESS(
                f"{verb} {changed}, unchanged {unchanged}, skipped {skipped}"
            )
        )
