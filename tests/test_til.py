from django.test import TestCase
from django.urls import reverse
from blog.models import Tag
from .models import TIL
from django.contrib.auth.models import User
from django.utils import timezone

class TILTestCase(TestCase):
    def setUp(self):
        # Create a test user
        self.user = User.objects.create_user(
            username='tiluser',
            email='til@example.com',
            password='tilpassword'
        )
        
        # Create test tags
        self.tag1 = Tag.objects.create(name='Django', slug='django')
        self.tag2 = Tag.objects.create(name='Python', slug='python')
        
        # Create test TILs
        self.til1 = TIL.objects.create(
            title='First Test TIL',
            slug='first-test-til',
            body='This is the first test TIL content.',
            created=timezone.now(),
            is_draft=False,
            author=self.user
        )
        self.til1.tags.add(self.tag1)
        
        self.til2 = TIL.objects.create(
            title='Second Test TIL',
            slug='second-test-til',
            body='This is the second test TIL content with Python code.',
            created=timezone.now(),
            is_draft=False,
            author=self.user
        )
        self.til2.tags.add(self.tag2)
        
        # Create a draft TIL
        self.draft_til = TIL.objects.create(
            title='Draft TIL',
            slug='draft-til',
            body='This is a draft TIL that should not appear in listings.',
            created=timezone.now(),
            is_draft=True,
            author=self.user
        )
        
    def test_til_index(self):
        """Test the TIL index page loads correctly and shows only published TILs"""
        response = self.client.get(reverse('til:index'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'First Test TIL')
        self.assertContains(response, 'Second Test TIL')
        self.assertNotContains(response, 'Draft TIL')
        
    def test_til_detail(self):
        """Test the TIL detail page loads correctly"""
        created = self.til1.created
        response = self.client.get(reverse('til:detail', kwargs={
            'year': created.year,
            'month': created.strftime('%b').lower(),
            'day': created.day,
            'slug': self.til1.slug
        }))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'First Test TIL')
        self.assertContains(response, 'This is the first test TIL content.')
        
    def test_til_tag(self):
        """Test the TIL tag filtering works correctly"""
        # Test Django tag
        response = self.client.get(reverse('til:tag', kwargs={'slug': 'django'}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'First Test TIL')
        self.assertNotContains(response, 'Second Test TIL')
        
        # Test Python tag
        response = self.client.get(reverse('til:tag', kwargs={'slug': 'python'}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Second Test TIL')
        self.assertNotContains(response, 'First Test TIL')
        
    def test_til_search(self):
        """Test the TIL search functionality"""
        # Search for 'first'
        response = self.client.get(reverse('til:search'), {'q': 'first'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'First Test TIL')
        self.assertNotContains(response, 'Second Test TIL')
        
        # Search for 'Python'
        response = self.client.get(reverse('til:search'), {'q': 'Python'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Second Test TIL')
        self.assertNotContains(response, 'First Test TIL')
        
        # Search for 'draft' should not return draft TILs
        response = self.client.get(reverse('til:search'), {'q': 'draft'})
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, 'Draft TIL')
        
    def test_draft_til_direct_access(self):
        """Test that draft TILs can be accessed directly if you know the URL"""
        created = self.draft_til.created
        response = self.client.get(reverse('til:detail', kwargs={
            'year': created.year,
            'month': created.strftime('%b').lower(),
            'day': created.day,
            'slug': self.draft_til.slug
        }))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Draft TIL')
