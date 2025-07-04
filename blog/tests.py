from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from blog.models import Entry, Tag, Blogmark
from til.models import TIL
from django.utils import timezone

class BlogTestCase(TestCase):
    def setUp(self):
        # Create a test user
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpassword'
        )
        
        # Create test tags
        self.tag1 = Tag.objects.create(name='Django', slug='django')
        self.tag2 = Tag.objects.create(name='Python', slug='python')
        
        # Create test blog entry
        self.entry = Entry.objects.create(
            title='Test Blog Post',
            slug='test-blog-post',
            summary='This is a test blog post summary.',
            body='This is the full content of the test blog post.',
            created=timezone.now(),
            status='published'
        )
        self.entry.tags.add(self.tag1, self.tag2)
        
        # Create test blogmark
        self.blogmark = Blogmark.objects.create(
            title='Test Link',
            slug='test-link',
            url='https://example.com',
            commentary='This is a test link commentary.',
            created=timezone.now(),
            status='published'
        )
        self.blogmark.tags.add(self.tag1)
        
        # Create test TIL
        self.til = TIL.objects.create(
            title='Test TIL',
            slug='test-til',
            body='This is a test TIL content.',
            created=timezone.now(),
            is_draft=False,
            author=self.user
        )
        self.til.tags.add(self.tag2)
        
        # Create a test client
        self.client = Client()

    def test_blog_index(self):
        """Test the blog index page loads correctly"""
        response = self.client.get(reverse('blog:index'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Test Blog Post')
        self.assertContains(response, 'Test Link')
        
    def test_blog_entry(self):
        """Test the blog entry detail page loads correctly"""
        created = self.entry.created
        response = self.client.get(reverse('blog:entry', kwargs={
            'year': created.year,
            'month': created.strftime('%b').lower(),
            'day': created.day,
            'slug': self.entry.slug
        }))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Test Blog Post')
        self.assertContains(response, 'This is the full content of the test blog post.')
        
    def test_blogmark(self):
        """Test the blogmark detail page loads correctly"""
        created = self.blogmark.created
        response = self.client.get(reverse('blog:blogmark', kwargs={
            'year': created.year,
            'month': created.strftime('%b').lower(),
            'day': created.day,
            'slug': self.blogmark.slug
        }))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Test Link')
        self.assertContains(response, 'https://example.com')
        
    def test_tag_page(self):
        """Test the tag page loads correctly"""
        response = self.client.get(reverse('blog:tag', kwargs={'slug': 'django'}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Test Blog Post')
        self.assertContains(response, 'Test Link')
        
    def test_search(self):
        """Test the search functionality"""
        response = self.client.get(reverse('blog:search'), {'q': 'test'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Test Blog Post')
        self.assertContains(response, 'Test Link')
        
    def test_til_index(self):
        """Test the TIL index page loads correctly"""
        response = self.client.get(reverse('til:index'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Test TIL')
        
    def test_til_detail(self):
        """Test the TIL detail page loads correctly"""
        created = self.til.created
        response = self.client.get(reverse('til:detail', kwargs={
            'year': created.year,
            'month': created.strftime('%b').lower(),
            'day': created.day,
            'slug': self.til.slug
        }))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Test TIL')
        self.assertContains(response, 'This is a test TIL content.')
        
    def test_til_tag(self):
        """Test the TIL tag page loads correctly"""
        response = self.client.get(reverse('til:tag', kwargs={'slug': 'python'}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Test TIL')
        
    def test_til_search(self):
        """Test the TIL search functionality"""
        response = self.client.get(reverse('til:search'), {'q': 'test'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Test TIL')
