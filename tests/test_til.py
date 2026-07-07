"""Tests for the retired TIL section.

TIL content was folded into blog Entries (blog migration
0006_migrate_til_to_entry). Two things must keep working:
  1. the data migration copies each TIL into an Entry faithfully, and
  2. the old /til/ URLs 301-redirect to their new blog homes.
"""

from importlib import import_module

from django.apps import apps as global_apps
from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from blog.models import Entry
from til.models import TIL

# Migration module name starts with a digit, so import it by string.
_migration = import_module("blog.migrations.0006_migrate_til_to_entry")


class TILMigrationTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="tiluser", email="til@example.com", password="tilpassword"
        )
        self.published = TIL.objects.create(
            title="First Test TIL",
            slug="first-test-til",
            body="First paragraph body.\n\nSecond paragraph is ignored in summary.",
            created=timezone.now(),
            is_draft=False,
            author=self.user,
        )
        self.published.tags.add("django")

        self.draft = TIL.objects.create(
            title="Draft TIL",
            slug="draft-til",
            body="Draft body.",
            created=timezone.now(),
            is_draft=True,
            author=self.user,
        )

    def _run_migration(self):
        # The migration function uses apps.get_model / taggit / contenttypes,
        # all of which resolve against the live app registry in tests.
        _migration.migrate_tils_to_entries(global_apps, None)

    def test_creates_one_entry_per_til(self):
        self._run_migration()
        self.assertEqual(Entry.objects.count(), 2)

    def test_status_maps_from_is_draft(self):
        self._run_migration()
        published = Entry.objects.get(slug="first-test-til")
        draft = Entry.objects.get(slug="draft-til")
        self.assertEqual(published.status, "published")
        self.assertFalse(published.is_draft)
        self.assertEqual(draft.status, "draft")
        self.assertTrue(draft.is_draft)

    def test_body_and_summary_copied(self):
        self._run_migration()
        entry = Entry.objects.get(slug="first-test-til")
        self.assertEqual(entry.body, self.published.body)
        # Summary is the first paragraph of the body.
        self.assertEqual(entry.summary, "First paragraph body.")

    def test_original_tags_preserved_and_til_tag_added(self):
        self._run_migration()
        entry = Entry.objects.get(slug="first-test-til")
        tag_slugs = set(entry.tags.values_list("slug", flat=True))
        self.assertIn("django", tag_slugs)
        self.assertIn("til", tag_slugs)

    def test_til_tag_added_even_without_original_tags(self):
        self._run_migration()
        entry = Entry.objects.get(slug="draft-til")
        self.assertIn("til", entry.tags.values_list("slug", flat=True))

    def test_authorship_carried_over(self):
        self._run_migration()
        entry = Entry.objects.get(slug="first-test-til")
        self.assertIn(self.user, entry.authors.all())

    def test_slug_collision_is_suffixed(self):
        # An existing Entry already owns the slug on the same day.
        Entry.objects.create(
            title="Existing",
            slug="first-test-til",
            summary="s",
            body="b",
            status="published",
            created=self.published.created,
        )
        self._run_migration()
        # The migrated TIL must not clobber the existing entry's slug+date.
        migrated = Entry.objects.filter(title="First Test TIL")
        self.assertEqual(migrated.count(), 1)
        self.assertNotEqual(migrated.first().slug, "first-test-til")


class TILRedirectTests(TestCase):
    def test_index_redirects_to_blog_posts(self):
        response = self.client.get(reverse("til:index"))
        self.assertRedirects(
            response, reverse("blog:posts"), status_code=301, target_status_code=200
        )

    def test_tag_redirects_to_blog_tag(self):
        response = self.client.get(reverse("til:tag", kwargs={"slug": "python"}))
        self.assertEqual(response.status_code, 301)
        self.assertEqual(
            response["Location"], reverse("blog:tag", kwargs={"slug": "python"})
        )

    def test_search_redirect_preserves_query(self):
        response = self.client.get(reverse("til:search"), {"q": "django"})
        self.assertEqual(response.status_code, 301)
        self.assertEqual(response["Location"], reverse("blog:search") + "?q=django")

    def test_feed_redirects_to_blog_feed(self):
        response = self.client.get(reverse("til:feed"))
        self.assertEqual(response.status_code, 301)
        self.assertEqual(response["Location"], reverse("blog:feed"))

    def test_detail_redirects_to_matching_entry(self):
        entry = Entry.objects.create(
            title="Migrated TIL",
            slug="migrated-til",
            summary="s",
            body="b",
            status="published",
            created=timezone.now(),
        )
        c = entry.created
        response = self.client.get(
            reverse(
                "til:detail",
                kwargs={
                    "year": c.year,
                    "month": c.strftime("%b").lower(),
                    "day": c.day,
                    "slug": entry.slug,
                },
            )
        )
        self.assertRedirects(
            response, entry.get_absolute_url(), status_code=301, target_status_code=200
        )

    def test_detail_404s_when_no_matching_entry(self):
        response = self.client.get(
            reverse(
                "til:detail",
                kwargs={
                    "year": 2020,
                    "month": "jan",
                    "day": 1,
                    "slug": "does-not-exist",
                },
            )
        )
        self.assertEqual(response.status_code, 404)
