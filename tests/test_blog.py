import glob
import os

from django.apps import apps
from django.contrib.auth.models import User
from django.template import engines
from django.template.loader import get_template
from django.test import Client, TestCase
from django.urls import reverse
from django.utils import timezone

from blog.models import Blogmark, Entry


class BlogTestCase(TestCase):
    def setUp(self):
        # Create a test user
        self.user = User.objects.create_user(
            username="testuser", email="test@example.com", password="testpassword"
        )

        # Create test blog entry
        self.entry = Entry.objects.create(
            title="Test Blog Post",
            slug="test-blog-post",
            summary="This is a test blog post summary.",
            body="This is the full content of the test blog post.",
            created=timezone.now(),
            status="published",
            publish_date=None,
        )
        self.entry.tags.add("django", "python")

        # Create test blogmark
        self.blogmark = Blogmark.objects.create(
            title="Test Link",
            slug="test-link",
            url="https://example.com",
            commentary="This is a test link commentary.",
            created=timezone.now(),
            status="published",
            publish_date=None,
        )
        self.blogmark.tags.add("django")

        # Create a test client
        self.client = Client()

    def test_blog_index(self):
        """Test the homepage bio page loads correctly"""
        response = self.client.get(reverse("blog:index"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "home-bio")

    def test_blog_posts(self):
        """Test the posts listing page loads correctly"""
        response = self.client.get(reverse("blog:posts"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Test Blog Post")
        self.assertContains(response, "Test Link")

    def test_blog_entry(self):
        """Test the blog entry detail page loads correctly"""
        created = self.entry.created
        response = self.client.get(
            reverse(
                "blog:entry",
                kwargs={
                    "year": created.year,
                    "month": created.strftime("%b").lower(),
                    "day": created.day,
                    "slug": self.entry.slug,
                },
            )
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Test Blog Post")
        self.assertContains(response, "This is the full content of the test blog post.")

    def test_draft_entry_404s_at_canonical_url(self):
        """A draft entry must 404 at its public URL rather than leak. Reviewing
        drafts happens through the login-gated entry_preview view."""
        draft = Entry.objects.create(
            title="Secret Draft",
            slug="secret-draft",
            summary="s",
            body="hidden body",
            status="draft",
        )
        c = draft.created
        url = reverse(
            "blog:entry",
            kwargs={
                "year": c.year,
                "month": c.strftime("%b").lower(),
                "day": c.day,
                "slug": draft.slug,
            },
        )
        self.assertEqual(self.client.get(url).status_code, 404)

    def test_blogmark(self):
        """Test the blogmark detail page loads correctly"""
        created = self.blogmark.created
        response = self.client.get(
            reverse(
                "blog:blogmark",
                kwargs={
                    "year": created.year,
                    "month": created.strftime("%b").lower(),
                    "day": created.day,
                    "slug": self.blogmark.slug,
                },
            )
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Test Link")
        self.assertContains(response, "https://example.com")

    def test_tag_page(self):
        """Test the tag page loads correctly"""
        response = self.client.get(reverse("blog:tag", kwargs={"slug": "django"}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Test Blog Post")
        self.assertContains(response, "Test Link")

    def test_search(self):
        """Test the search functionality"""
        response = self.client.get(reverse("blog:search"), {"q": "test"})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Test Blog Post")
        self.assertContains(response, "Test Link")

    def test_archive_lists_all_entries_unpaginated(self):
        """The archive is a full chronological index: an old entry that would
        fall past the first paginator page must still appear. Guards against
        re-paginating the archive and stranding older posts (e.g. migrated
        TILs) on an unreachable page."""
        from datetime import timedelta

        base = timezone.now()
        for i in range(15):
            Entry.objects.create(
                title=f"Archive Entry {i}",
                slug=f"archive-entry-{i}",
                summary="s",
                body="b",
                status="published",
                created=base - timedelta(days=i + 1),
            )
        response = self.client.get(reverse("blog:archive"))
        self.assertEqual(response.status_code, 200)
        # The oldest would sit on page 2 under a 10-per-page paginator.
        self.assertContains(response, "Archive Entry 14")
        self.assertContains(response, "Archive Entry 0")

    def test_year_archive_returns_200(self):
        """Year archive renders. Regression guard: it previously 500'd
        (TemplateDoesNotExist) because blog/year.html did not exist."""
        response = self.client.get(
            reverse("blog:year", kwargs={"year": self.entry.created.year})
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Test Blog Post")

    def test_month_archive_returns_200(self):
        """Month archive renders. Regression guard for the same 500, and for
        the month-slug resolution (numeric months resolve to January)."""
        created = self.entry.created
        response = self.client.get(
            reverse(
                "blog:month",
                kwargs={"year": created.year, "month": created.strftime("%b").lower()},
            )
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Test Blog Post")

    def test_site_name_renders_from_context_processor(self):
        """site_name (common_context) reaches the page. Regression guard: the
        processor's registration was dropped and re-added during development
        with nothing to catch the resulting blank titles in production."""
        from blog.models import SiteSettings

        settings_row = SiteSettings.get_settings()
        settings_row.site_title = "Distinctive Site Title QZX"
        settings_row.save()
        response = self.client.get(reverse("blog:posts"))
        # Rendered site-wide via the <title> and the WebSite/Organization
        # JSON-LD; absent entirely if the context processor is unregistered.
        self.assertContains(response, "Distinctive Site Title QZX")


class TemplateValidationTests(TestCase):
    """Test that all templates can be compiled without syntax errors."""

    def test_all_templates_compile(self):
        """Test that all templates in the project compile without errors."""
        template_dirs = []

        # Get template directories from settings
        engine = engines["django"]
        template_dirs.extend(engine.engine.dirs)

        # Get app template directories
        for app_config in apps.get_app_configs():
            app_template_dir = os.path.join(app_config.path, "templates")
            if os.path.exists(app_template_dir):
                template_dirs.append(app_template_dir)

        errors = []

        for template_dir in template_dirs:
            for template_file in glob.glob(
                os.path.join(template_dir, "**/*.html"), recursive=True
            ):
                # Get template name relative to template dir
                template_name = os.path.relpath(template_file, template_dir)

                try:
                    # Try to compile the template
                    get_template(template_name)
                except Exception as e:
                    errors.append(f"{template_name}: {str(e)}")

        if errors:
            self.fail("Template compilation errors found:\n" + "\n".join(errors))

    def test_extends_tag_placement(self):
        """Test that extends tags are properly placed as first tags."""
        template_dirs = []

        # Get template directories from settings
        engine = engines["django"]
        template_dirs.extend(engine.engine.dirs)

        # Get app template directories
        for app_config in apps.get_app_configs():
            app_template_dir = os.path.join(app_config.path, "templates")
            if os.path.exists(app_template_dir):
                template_dirs.append(app_template_dir)

        errors = []

        for template_dir in template_dirs:
            for template_file in glob.glob(
                os.path.join(template_dir, "**/*.html"), recursive=True
            ):
                template_name = os.path.relpath(template_file, template_dir)

                try:
                    with open(template_file, "r") as f:
                        content = f.read()

                    # Check if file contains extends tag
                    if "{% extends" in content:
                        lines = content.split("\n")
                        extends_line = None
                        first_non_empty_line = None

                        for i, line in enumerate(lines):
                            stripped = line.strip()
                            if stripped and not stripped.startswith("<!--"):
                                if first_non_empty_line is None:
                                    first_non_empty_line = i
                                if "{% extends" in line:
                                    extends_line = i
                                    break

                        if (
                            extends_line is not None
                            and first_non_empty_line is not None
                        ):
                            if extends_line != first_non_empty_line:
                                errors.append(
                                    f"{template_name}: extends tag is not the first non-comment tag"
                                )

                except Exception as e:
                    errors.append(f"{template_name}: Error reading file: {str(e)}")

        if errors:
            self.fail(
                "Template extends tag placement errors found:\n" + "\n".join(errors)
            )
