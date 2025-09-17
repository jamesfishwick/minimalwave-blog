from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from blog.models import Entry, Blogmark
from core.models import EnhancedTag
from til.models import TIL
from django.utils import timezone
from django.template import engines
from django.template.loader import get_template
from django.apps import apps
import os
import glob

class BlogTestCase(TestCase):
    def setUp(self):
        # Create a test user
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpassword'
        )
        
        # Create test tags
        self.tag1 = EnhancedTag.objects.create(name='Django', slug='django')
        self.tag2 = EnhancedTag.objects.create(name='Python', slug='python')
        
        # Create test blog entry
        self.entry = Entry.objects.create(
            title='Test Blog Post',
            slug='test-blog-post',
            summary='This is a test blog post summary.',
            body='This is the full content of the test blog post.',
            created=timezone.now(),
            status='published',
            publish_date=None  # Explicitly set to None so it shows immediately
        )
        self.entry.tags.add(self.tag1, self.tag2)
        
        # Create test blogmark
        self.blogmark = Blogmark.objects.create(
            title='Test Link',
            slug='test-link',
            url='https://example.com',
            commentary='This is a test link commentary.',
            created=timezone.now(),
            status='published',
            publish_date=None  # Explicitly set to None so it shows immediately
        )
        self.blogmark.tags.add(self.tag1)
        
        # Create test TIL
        self.til = TIL.objects.create(
            title='Test TIL',
            slug='test-til',
            body='This is a test TIL content.',
            created=timezone.now(),
            is_draft=False,  # Published TIL
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


class TemplateValidationTests(TestCase):
    """Test that all templates can be compiled without syntax errors."""
    
    def test_all_templates_compile(self):
        """Test that all templates in the project compile without errors."""
        template_dirs = []
        
        # Get template directories from settings
        engine = engines['django']
        template_dirs.extend(engine.engine.dirs)
        
        # Get app template directories
        for app_config in apps.get_app_configs():
            app_template_dir = os.path.join(app_config.path, 'templates')
            if os.path.exists(app_template_dir):
                template_dirs.append(app_template_dir)
        
        errors = []
        
        for template_dir in template_dirs:
            for template_file in glob.glob(os.path.join(template_dir, '**/*.html'), recursive=True):
                # Get template name relative to template dir
                template_name = os.path.relpath(template_file, template_dir)
                
                try:
                    # Try to compile the template
                    get_template(template_name)
                except Exception as e:
                    errors.append(f'{template_name}: {str(e)}')
        
        if errors:
            self.fail(f'Template compilation errors found:\n' + '\n'.join(errors))
    
    def test_extends_tag_placement(self):
        """Test that extends tags are properly placed as first tags."""
        template_dirs = []
        
        # Get template directories from settings
        engine = engines['django']
        template_dirs.extend(engine.engine.dirs)
        
        # Get app template directories
        for app_config in apps.get_app_configs():
            app_template_dir = os.path.join(app_config.path, 'templates')
            if os.path.exists(app_template_dir):
                template_dirs.append(app_template_dir)
        
        errors = []
        
        for template_dir in template_dirs:
            for template_file in glob.glob(os.path.join(template_dir, '**/*.html'), recursive=True):
                template_name = os.path.relpath(template_file, template_dir)
                
                try:
                    with open(template_file, 'r') as f:
                        content = f.read()
                    
                    # Check if file contains extends tag
                    if '{% extends' in content:
                        lines = content.split('\n')
                        extends_line = None
                        first_non_empty_line = None
                        
                        for i, line in enumerate(lines):
                            stripped = line.strip()
                            if stripped and not stripped.startswith('<!--'):
                                if first_non_empty_line is None:
                                    first_non_empty_line = i
                                if '{% extends' in line:
                                    extends_line = i
                                    break
                        
                        if extends_line is not None and first_non_empty_line is not None:
                            if extends_line != first_non_empty_line:
                                errors.append(f'{template_name}: extends tag is not the first non-comment tag')
                
                except Exception as e:
                    errors.append(f'{template_name}: Error reading file: {str(e)}')
        
        if errors:
            self.fail(f'Template extends tag placement errors found:\n' + '\n'.join(errors))
