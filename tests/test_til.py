"""Tests for the retired TIL section.

TIL content was folded into blog Entries (blog migration
0006_migrate_til_to_entry) and the TIL model was dropped
(til migration 0006_delete_til). The app now exists only to 301-redirect
the old /til/ URLs to their new blog homes. The one-shot data migration was
verified against production data before the model was removed; only the
redirect behavior remains testable through the ORM.
"""

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from blog.models import Entry


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

    def test_search_redirect_encodes_special_characters(self):
        response = self.client.get(reverse("til:search"), {"q": "foo & bar"})
        self.assertEqual(response.status_code, 301)
        # Spaces and ampersands must be percent-encoded, not passed raw.
        self.assertEqual(
            response["Location"], reverse("blog:search") + "?q=foo+%26+bar"
        )

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

    def _til_detail_url(self, created, slug):
        return reverse(
            "til:detail",
            kwargs={
                "year": created.year,
                "month": created.strftime("%b").lower(),
                "day": created.day,
                "slug": slug,
            },
        )

    def test_detail_falls_back_to_suffixed_slug(self):
        # A collided TIL is migrated as "<slug>-til"; the old URL uses "<slug>".
        entry = Entry.objects.create(
            title="Collided",
            slug="collided-til",
            summary="s",
            body="b",
            status="published",
            created=timezone.now(),
        )
        response = self.client.get(self._til_detail_url(entry.created, "collided"))
        self.assertRedirects(
            response, entry.get_absolute_url(), status_code=301, target_status_code=200
        )

    def test_detail_404s_for_draft_entry(self):
        draft = Entry.objects.create(
            title="Draft",
            slug="draft-entry",
            summary="s",
            body="b",
            status="draft",
            created=timezone.now(),
        )
        response = self.client.get(self._til_detail_url(draft.created, "draft-entry"))
        self.assertEqual(response.status_code, 404)

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
