import datetime

from django.db import IntegrityError, transaction
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from projects.models import Project


class ProjectSiteTests(TestCase):
    def setUp(self):
        self.published = Project.objects.create(
            title="Published Project",
            slug="published-project",
            summary="A shipped thing.",
            body="Body text.",
            tech_stack="Django, PostgreSQL",
            project_status="active",
            start_date=datetime.date(2024, 1, 1),
            featured=True,
            status="published",
        )
        self.published.tags.add("web")
        self.draft = Project.objects.create(
            title="Draft Project",
            slug="draft-project",
            summary="secret draft",
            start_date=datetime.date(2024, 2, 1),
            status="draft",
        )
        self.future = Project.objects.create(
            title="Future Project",
            slug="future-project",
            summary="scheduled",
            start_date=datetime.date(2024, 3, 1),
            status="published",
            publish_date=timezone.now() + datetime.timedelta(days=7),
        )

    def test_index_shows_published_only(self):
        r = self.client.get(reverse("projects:index"))
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, "Published Project")
        self.assertNotContains(r, "Draft Project")
        self.assertNotContains(r, "Future Project")

    def test_detail_published_returns_200(self):
        r = self.client.get(
            reverse("projects:detail", kwargs={"slug": "published-project"})
        )
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, "Published Project")

    def test_detail_draft_returns_404(self):
        r = self.client.get(
            reverse("projects:detail", kwargs={"slug": "draft-project"})
        )
        self.assertEqual(r.status_code, 404)

    def test_detail_future_scheduled_returns_404(self):
        r = self.client.get(
            reverse("projects:detail", kwargs={"slug": "future-project"})
        )
        self.assertEqual(r.status_code, 404)

    def test_static_subpaths_resolve_before_slug_catchall(self):
        # feed/ and tag/<slug>/ must not be swallowed by the <slug:slug> catch-all.
        self.assertEqual(self.client.get(reverse("projects:feed")).status_code, 200)
        r = self.client.get(reverse("projects:tag", kwargs={"slug": "web"}))
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, "Published Project")

    def test_sitemap_excludes_unpublished(self):
        r = self.client.get("/sitemap.xml")
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, "/projects/published-project/")
        self.assertNotContains(r, "/projects/draft-project/")
        self.assertNotContains(r, "/projects/future-project/")


class ProjectModelTests(TestCase):
    def test_slug_is_globally_unique(self):
        Project.objects.create(
            title="A", slug="dup", summary="x", start_date=datetime.date(2024, 1, 1)
        )
        with self.assertRaises(IntegrityError), transaction.atomic():
            Project.objects.create(
                title="B", slug="dup", summary="y", start_date=datetime.date(2024, 2, 1)
            )

    def test_is_draft_synced_with_status(self):
        p = Project.objects.create(
            title="P",
            slug="p",
            summary="x",
            start_date=datetime.date(2024, 1, 1),
            status="published",
        )
        self.assertFalse(p.is_draft)
        p.status = "draft"
        p.save()
        self.assertTrue(p.is_draft)

    def test_tech_stack_list_parsing(self):
        p = Project(tech_stack="Django, PostgreSQL ,HTMX,")
        self.assertEqual(p.tech_stack_list, ["Django", "PostgreSQL", "HTMX"])
        self.assertEqual(Project(tech_stack="").tech_stack_list, [])

    def test_get_absolute_url_is_flat(self):
        self.assertEqual(
            Project(slug="my-proj").get_absolute_url(), "/projects/my-proj/"
        )

    def test_end_date_before_start_is_rejected(self):
        with self.assertRaises(IntegrityError), transaction.atomic():
            Project.objects.create(
                title="Bad",
                slug="bad",
                summary="x",
                start_date=datetime.date(2024, 5, 1),
                end_date=datetime.date(2024, 1, 1),
            )

    def test_published_manager_scope(self):
        Project.objects.create(
            title="Pub",
            slug="pub",
            summary="x",
            start_date=datetime.date(2024, 1, 1),
            status="published",
        )
        Project.objects.create(
            title="Drf",
            slug="drf",
            summary="x",
            start_date=datetime.date(2024, 1, 1),
            status="draft",
        )
        slugs = set(Project.objects.published().values_list("slug", flat=True))
        self.assertEqual(slugs, {"pub"})
