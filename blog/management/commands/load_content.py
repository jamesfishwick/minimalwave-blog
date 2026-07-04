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
    """Split a dumped file into (metadata dict, body string).

    Raises CommandError (never a raw traceback) for every malformed-input case
    so the caller can report it against the file and continue the batch.
    """
    with open(path, encoding="utf-8") as fh:
        text = fh.read()
    if not text.startswith("---\n"):
        raise CommandError(f"{path}: missing YAML front-matter")
    # Front-matter is the first block delimited by a leading '---\n' and a
    # following '\n---\n'. Split only once so '---' inside the body is safe.
    head, sep, body = text[len("---\n") :].partition("\n---\n")
    if not sep:
        raise CommandError(f"{path}: malformed front-matter (no closing '---')")
    try:
        meta = yaml.safe_load(head)
    except yaml.YAMLError as exc:
        raise CommandError(f"{path}: invalid front-matter YAML: {exc}")
    if not isinstance(meta, dict):
        raise CommandError(f"{path}: front-matter is not a mapping")
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
        tally = {"changed": 0, "unchanged": 0, "skipped": 0}

        for path in options["files"]:
            # Isolate each file: a parse/lookup/save failure on one file must
            # not strand the batch mid-write or suppress the final summary.
            try:
                result = self._process_file(path, dry)
            except Exception as exc:
                self.stderr.write(self.style.ERROR(f"{path}: {exc}"))
                result = "skipped"
            tally[result] += 1

        verb = "would change" if dry else "changed"
        self.stdout.write(
            self.style.SUCCESS(
                f"{verb} {tally['changed']}, unchanged {tally['unchanged']}, "
                f"skipped {tally['skipped']}"
            )
        )

    def _process_file(self, path, dry):
        """Process one file; return 'changed' | 'unchanged' | 'skipped'."""
        meta, body = parse_file(path)
        tname, pk = meta.get("type"), meta.get("pk")
        field, slug = meta.get("field"), meta.get("slug")

        spec = CONTENT_TYPES.get(tname)
        if not spec:
            self.stderr.write(self.style.ERROR(f"{path}: unknown type '{tname}'"))
            return "skipped"
        if field not in spec["fields"]:
            self.stderr.write(
                self.style.ERROR(
                    f"{path}: field '{field}' is not editable for '{tname}'"
                )
            )
            return "skipped"
        try:
            obj = spec["model"].objects.get(pk=pk)
        except spec["model"].DoesNotExist:
            self.stderr.write(
                self.style.ERROR(f"{path}: {tname} pk={pk} not found (wrong database?)")
            )
            return "skipped"
        # Guard against stale files / wrong DB: the pk's slug must still match.
        if slug and obj.slug != slug:
            self.stderr.write(
                self.style.ERROR(
                    f"{path}: slug mismatch (file '{slug}' != db '{obj.slug}') — stale file? skipping"
                )
            )
            return "skipped"

        # strip leading/trailing blank lines so a markdown formatter adding a
        # blank line after the front-matter doesn't create spurious diffs.
        current = (getattr(obj, field) or "").strip("\n")
        new = body.strip("\n")
        if current == new:
            self.stdout.write(f"unchanged: {tname} '{obj.slug}' [{field}]")
            return "unchanged"

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
        return "changed"
