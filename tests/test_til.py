from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from til.models import TIL


class TILTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="tiluser", email="til@example.com", password="tilpassword"
        )

        self.til1 = TIL.objects.create(
            title="First Test TIL",
            slug="first-test-til",
            body="This is the first test TIL content.",
            created=timezone.now(),
            is_draft=False,
            author=self.user,
        )
        self.til1.tags.add("django")

        self.til2 = TIL.objects.create(
            title="Second Test TIL",
            slug="second-test-til",
            body="This is the second test TIL content with Python code.",
            created=timezone.now(),
            is_draft=False,
            author=self.user,
        )
        self.til2.tags.add("python")

        self.draft_til = TIL.objects.create(
            title="Draft TIL",
            slug="draft-til",
            body="This is a draft TIL that should not appear in listings.",
            created=timezone.now(),
            is_draft=True,
            author=self.user,
        )

    def test_til_index(self):
        """Test the TIL index page loads correctly and shows only published TILs"""
        response = self.client.get(reverse("til:index"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "First Test TIL")
        self.assertContains(response, "Second Test TIL")
        self.assertNotContains(response, "Draft TIL")

    def test_til_detail(self):
        """Test the TIL detail page loads correctly"""
        created = self.til1.created
        response = self.client.get(
            reverse(
                "til:detail",
                kwargs={
                    "year": created.year,
                    "month": created.strftime("%b").lower(),
                    "day": created.day,
                    "slug": self.til1.slug,
                },
            )
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "First Test TIL")
        self.assertContains(response, "This is the first test TIL content.")

    def test_til_tag(self):
        """Test the TIL tag filtering works correctly"""
        response = self.client.get(reverse("til:tag", kwargs={"slug": "django"}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "First Test TIL")
        self.assertNotContains(response, "Second Test TIL")

        response = self.client.get(reverse("til:tag", kwargs={"slug": "python"}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Second Test TIL")
        self.assertNotContains(response, "First Test TIL")

    def test_til_search(self):
        """Test the TIL search functionality"""
        response = self.client.get(reverse("til:search"), {"q": "first"})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "First Test TIL")
        self.assertNotContains(response, "Second Test TIL")

        response = self.client.get(reverse("til:search"), {"q": "Python"})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Second Test TIL")
        self.assertNotContains(response, "First Test TIL")

        response = self.client.get(reverse("til:search"), {"q": "draft"})
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "Draft TIL")

    def test_draft_til_direct_access(self):
        """Test that draft TILs can be accessed directly"""
        created = self.draft_til.created
        response = self.client.get(
            reverse(
                "til:detail",
                kwargs={
                    "year": created.year,
                    "month": created.strftime("%b").lower(),
                    "day": created.day,
                    "slug": self.draft_til.slug,
                },
            )
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Draft TIL")
