import datetime
import shutil
import tempfile
from io import StringIO
from pathlib import Path

from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase

from blog.management.commands.load_content import parse_file
from projects.models import Project


class ParseFileTests(TestCase):
    """Unit tests for the front-matter parser (no DB needed)."""

    def _write(self, text):
        d = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, d, ignore_errors=True)
        path = Path(d) / "f.md"
        path.write_text(text, encoding="utf-8")
        return str(path)

    def test_preserves_horizontal_rule_in_body(self):
        # A markdown '---' rule inside the body must survive (partition on first).
        path = self._write(
            "---\ntype: entry\npk: 1\nfield: body\nslug: x\n---\n"
            "Intro\n\n---\n\nAfter the rule.\n"
        )
        meta, body = parse_file(path)
        self.assertEqual(meta["type"], "entry")
        self.assertIn("\n---\n", body)
        self.assertIn("After the rule.", body)

    def test_missing_frontmatter_raises_commanderror(self):
        with self.assertRaises(CommandError):
            parse_file(self._write("no front matter here\n"))

    def test_unterminated_frontmatter_raises_commanderror(self):
        with self.assertRaises(CommandError):
            parse_file(self._write("---\ntype: entry\nbody follows but no close\n"))

    def test_malformed_yaml_raises_commanderror(self):
        with self.assertRaises(CommandError):
            parse_file(self._write("---\n: : bad: yaml:\n---\nbody\n"))

    def test_non_mapping_frontmatter_raises_commanderror(self):
        with self.assertRaises(CommandError):
            parse_file(self._write("---\njust a scalar string\n---\nbody\n"))


class LoadContentTests(TestCase):
    def setUp(self):
        self.project = Project.objects.create(
            title="Round Trip",
            slug="round-trip",
            summary="Summary.",
            body="# Body\n\nOriginal content.",
            start_date=datetime.date(2024, 1, 1),
            status="published",
        )
        self.dir = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.dir, ignore_errors=True)

    def _dump(self):
        call_command(
            "dump_content",
            "--type",
            "project",
            "--slug",
            "round-trip",
            "--output-dir",
            self.dir,
        )
        return Path(self.dir) / f"project-{self.project.pk}-round-trip-body.md"

    def test_roundtrip_no_edit_reports_unchanged(self):
        body_file = self._dump()
        out = StringIO()
        call_command("load_content", str(body_file), stdout=out)
        self.assertIn("unchanged", out.getvalue())

    def test_dry_run_writes_nothing(self):
        body_file = self._dump()
        body_file.write_text(
            body_file.read_text(encoding="utf-8").replace(
                "Original content.", "EDITED."
            ),
            encoding="utf-8",
        )
        out = StringIO()
        call_command("load_content", str(body_file), "--dry-run", stdout=out)
        self.assertIn("[dry-run]", out.getvalue())
        self.project.refresh_from_db()
        self.assertIn("Original content.", self.project.body)
        self.assertNotIn("EDITED.", self.project.body)

    def test_load_applies_change(self):
        body_file = self._dump()
        body_file.write_text(
            body_file.read_text(encoding="utf-8").replace(
                "Original content.", "EDITED."
            ),
            encoding="utf-8",
        )
        call_command("load_content", str(body_file), stdout=StringIO())
        self.project.refresh_from_db()
        self.assertIn("EDITED.", self.project.body)

    def test_slug_mismatch_is_skipped_not_written(self):
        body_file = self._dump()
        text = body_file.read_text(encoding="utf-8")
        text = text.replace("slug: round-trip", "slug: wrong-slug").replace(
            "Original content.", "SHOULD NOT LAND."
        )
        body_file.write_text(text, encoding="utf-8")
        err = StringIO()
        call_command("load_content", str(body_file), stderr=err)
        self.assertIn("slug mismatch", err.getvalue())
        self.project.refresh_from_db()
        self.assertNotIn("SHOULD NOT LAND.", self.project.body)

    def test_bad_file_does_not_abort_batch(self):
        # A malformed file must be skipped, and a valid later file still applied,
        # with a summary printed (the Critical resilience fix).
        good = self._dump()
        good.write_text(
            good.read_text(encoding="utf-8").replace("Original content.", "GOOD EDIT."),
            encoding="utf-8",
        )
        bad = Path(self.dir) / "bad.md"
        bad.write_text("not a valid dumped file\n", encoding="utf-8")
        out, err = StringIO(), StringIO()
        call_command("load_content", str(bad), str(good), stdout=out, stderr=err)
        self.assertIn("skipped 1", out.getvalue())  # summary still printed
        self.project.refresh_from_db()
        self.assertIn("GOOD EDIT.", self.project.body)  # good file still applied
