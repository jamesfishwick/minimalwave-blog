from django.test import TestCase, override_settings
from django.utils import timezone
from django.contrib.auth.models import User
from unittest.mock import patch, Mock, MagicMock
from datetime import timedelta
import json

from .models import (
    Entry, LinkedInCredentials, LinkedInPost, LinkedInSettings, Tag
)
from .linkedin_service import LinkedInService, LinkedInAPIException
from .signals import entry_published


class LinkedInModelsTestCase(TestCase):
    """Test LinkedIn-related models"""
    
    def setUp(self):
        self.user = User.objects.create_user('testuser', 'test@example.com', 'password')
        self.tag = Tag.objects.create(name='Test Tag', slug='test-tag')
        
    def test_linkedin_credentials_singleton(self):
        """Test that LinkedInCredentials behaves as singleton"""
        creds1 = LinkedInCredentials.objects.create(
            client_id='test_id',
            client_secret='test_secret',
            access_token='test_token',
            authorized_user='Test User',
            token_expires_at=timezone.now() + timedelta(days=30)
        )
        
        # Get credentials should return the first instance
        retrieved = LinkedInCredentials.get_credentials()
        self.assertEqual(retrieved.id, creds1.id)
        
    def test_linkedin_credentials_token_validity(self):
        """Test token validity checking"""
        # Valid token
        creds = LinkedInCredentials.objects.create(
            client_id='test_id',
            client_secret='test_secret',
            access_token='test_token',
            authorized_user='Test User',
            token_expires_at=timezone.now() + timedelta(days=30)
        )
        self.assertTrue(creds.is_token_valid)
        
        # Expired token
        creds.token_expires_at = timezone.now() - timedelta(days=1)
        creds.save()
        self.assertFalse(creds.is_token_valid)
        
    def test_entry_linkedin_fields(self):
        """Test Entry model LinkedIn fields"""
        entry = Entry.objects.create(
            title='Test Entry',
            slug='test-entry',
            summary='Test summary',
            body='Test body',
            status='published',
            linkedin_enabled=True,
            linkedin_custom_text='Custom LinkedIn text'
        )
        
        self.assertTrue(entry.linkedin_enabled)
        self.assertEqual(entry.linkedin_post_text, 'Custom LinkedIn text')
        self.assertFalse(entry.linkedin_posted)
        
        # Test fallback to summary_text
        entry.linkedin_custom_text = ''
        entry.save()
        self.assertEqual(entry.linkedin_post_text, entry.summary_text)
        
    def test_linkedin_post_tracking(self):
        """Test LinkedIn post tracking model"""
        entry = Entry.objects.create(
            title='Test Entry',
            slug='test-entry',
            summary='Test summary',
            body='Test body',
            status='published'
        )
        
        linkedin_post = LinkedInPost.objects.create(
            entry=entry,
            linkedin_post_id='urn:li:share:123456',
            post_url='https://linkedin.com/feed/update/123456',
            post_text='Test post text',
            status='posted'
        )
        
        self.assertEqual(str(linkedin_post), 'LinkedIn post for: Test Entry')
        self.assertEqual(linkedin_post.status, 'posted')
        
    def test_linkedin_settings_singleton(self):
        """Test LinkedIn settings singleton behavior"""
        settings = LinkedInSettings.get_settings()
        self.assertTrue(settings.enabled)
        self.assertTrue(settings.auto_post_entries)
        self.assertFalse(settings.auto_post_blogmarks)
        
        # Should return same instance
        settings2 = LinkedInSettings.get_settings()
        self.assertEqual(settings.id, settings2.id)


class LinkedInServiceTestCase(TestCase):
    """Test LinkedIn service functionality"""
    
    def setUp(self):
        self.credentials = LinkedInCredentials.objects.create(
            client_id='test_client_id',
            client_secret='test_client_secret',
            access_token='test_access_token',
            authorized_user='Test User',
            token_expires_at=timezone.now() + timedelta(days=30)
        )
        self.service = LinkedInService()
        
    def test_service_initialization(self):
        """Test service initialization with credentials"""
        self.assertIsNotNone(self.service.credentials)
        self.assertEqual(self.service.credentials.client_id, 'test_client_id')
        
    def test_authentication_check(self):
        """Test authentication status checking"""
        self.assertTrue(self.service.is_authenticated())
        
        # Test with expired token
        self.credentials.token_expires_at = timezone.now() - timedelta(days=1)
        self.credentials.save()
        self.service = LinkedInService()  # Reinitialize
        self.assertFalse(self.service.is_authenticated())
        
    def test_auth_url_generation(self):
        """Test OAuth URL generation"""
        redirect_uri = 'https://example.com/callback'
        auth_url, state = self.service.generate_auth_url(redirect_uri)
        
        self.assertIn('linkedin.com/oauth/v2/authorization', auth_url)
        self.assertIn('test_client_id', auth_url)
        self.assertIn('response_type=code', auth_url)
        self.assertIsNotNone(state)
        
        # Verify state is saved
        self.credentials.refresh_from_db()
        self.assertEqual(self.credentials.state, state)
        
    @patch('blog.linkedin_service.requests.post')
    def test_token_exchange_success(self, mock_post):
        """Test successful token exchange"""
        # Mock successful token response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'access_token': 'new_access_token',
            'refresh_token': 'new_refresh_token',
            'expires_in': 5184000
        }
        mock_post.return_value = mock_response
        
        # Set up state for verification
        self.credentials.state = 'test_state'
        self.credentials.save()
        
        with patch.object(self.service, '_get_user_info', return_value={'name': 'Test User'}):
            token_data = self.service.exchange_code_for_token(
                'test_code', 'https://example.com/callback', 'test_state'
            )
        
        self.assertEqual(token_data['access_token'], 'new_access_token')
        self.credentials.refresh_from_db()
        self.assertEqual(self.credentials.access_token, 'new_access_token')
        
    @patch('blog.linkedin_service.requests.post')
    def test_token_exchange_failure(self, mock_post):
        """Test failed token exchange"""
        mock_response = Mock()
        mock_response.status_code = 400
        mock_response.text = 'Invalid request'
        mock_post.return_value = mock_response
        
        self.credentials.state = 'test_state'
        self.credentials.save()
        
        with self.assertRaises(LinkedInAPIException):
            self.service.exchange_code_for_token(
                'invalid_code', 'https://example.com/callback', 'test_state'
            )
            
    def test_state_verification(self):
        """Test CSRF state verification"""
        self.credentials.state = 'correct_state'
        self.credentials.save()
        
        # Wrong state should raise exception
        with self.assertRaises(LinkedInAPIException):
            self.service.exchange_code_for_token(
                'test_code', 'https://example.com/callback', 'wrong_state'
            )


class LinkedInPostingTestCase(TestCase):
    """Test LinkedIn posting functionality"""
    
    def setUp(self):
        self.user = User.objects.create_user('testuser', 'test@example.com', 'password')
        self.credentials = LinkedInCredentials.objects.create(
            client_id='test_client_id',
            client_secret='test_client_secret',
            access_token='test_access_token',
            authorized_user='Test User',
            token_expires_at=timezone.now() + timedelta(days=30)
        )
        self.service = LinkedInService()
        
        self.entry = Entry.objects.create(
            title='Test Entry',
            slug='test-entry',
            summary='Test summary for LinkedIn posting',
            body='Test body content',
            status='published',
            linkedin_enabled=True
        )
        
    @patch('blog.linkedin_service.requests.post')
    @patch.object(LinkedInService, '_get_user_id', return_value='test_user_id')
    def test_successful_post_creation(self, mock_get_user_id, mock_post):
        """Test successful LinkedIn post creation"""
        mock_response = Mock()
        mock_response.status_code = 201
        mock_response.json.return_value = {
            'id': 'urn:li:share:123456789'
        }
        mock_post.return_value = mock_response
        
        response = self.service.post_entry_to_linkedin(self.entry)
        
        self.assertEqual(response['id'], 'urn:li:share:123456789')
        
        # Verify LinkedIn post record was created
        linkedin_post = LinkedInPost.objects.get(entry=self.entry)
        self.assertEqual(linkedin_post.status, 'posted')
        self.assertEqual(linkedin_post.linkedin_post_id, 'urn:li:share:123456789')
        
    @patch('blog.linkedin_service.requests.post')
    def test_failed_post_creation(self, mock_post):
        """Test failed LinkedIn post creation"""
        mock_response = Mock()
        mock_response.status_code = 400
        mock_response.text = 'Bad Request'
        mock_post.return_value = mock_response
        
        with self.assertRaises(LinkedInAPIException):
            self.service.post_entry_to_linkedin(self.entry)
        
        # Verify failed post record was created
        linkedin_post = LinkedInPost.objects.get(entry=self.entry)
        self.assertEqual(linkedin_post.status, 'failed')
        self.assertIn('Bad Request', linkedin_post.error_message)
        
    def test_post_without_authentication(self):
        """Test posting without authentication"""
        # Clear credentials
        self.credentials.access_token = ''
        self.credentials.save()
        
        service = LinkedInService()
        
        with self.assertRaises(LinkedInAPIException):
            service.post_entry_to_linkedin(self.entry)


class LinkedInSignalsTestCase(TestCase):
    """Test LinkedIn integration signals"""
    
    def setUp(self):
        self.user = User.objects.create_user('testuser', 'test@example.com', 'password')
        self.credentials = LinkedInCredentials.objects.create(
            client_id='test_client_id',
            client_secret='test_client_secret',
            access_token='test_access_token',
            authorized_user='Test User',
            token_expires_at=timezone.now() + timedelta(days=30)
        )
        
    @patch('blog.signals.LinkedInService')
    def test_entry_published_signal_enabled(self, mock_service_class):
        """Test signal fires when entry is published with LinkedIn enabled"""
        mock_service = Mock()
        mock_service_class.return_value = mock_service
        
        entry = Entry.objects.create(
            title='Test Entry',
            slug='test-entry',
            summary='Test summary',
            body='Test body',
            status='published',
            linkedin_enabled=True
        )
        
        mock_service.post_entry_to_linkedin.assert_called_once_with(entry)
        
    @patch('blog.signals.LinkedInService')
    def test_entry_published_signal_disabled(self, mock_service_class):
        """Test signal doesn't fire when LinkedIn is disabled"""
        mock_service = Mock()
        mock_service_class.return_value = mock_service
        
        Entry.objects.create(
            title='Test Entry',
            slug='test-entry',
            summary='Test summary',
            body='Test body',
            status='published',
            linkedin_enabled=False
        )
        
        mock_service.post_entry_to_linkedin.assert_not_called()
        
    @patch('blog.signals.LinkedInService')
    def test_status_change_triggers_signal(self, mock_service_class):
        """Test changing status to published triggers signal"""
        mock_service = Mock()
        mock_service_class.return_value = mock_service
        
        # Create draft entry
        entry = Entry.objects.create(
            title='Test Entry',
            slug='test-entry',
            summary='Test summary',
            body='Test body',
            status='draft',
            linkedin_enabled=True
        )
        
        # Publish it
        entry.status = 'published'
        entry.save()
        
        mock_service.post_entry_to_linkedin.assert_called_once_with(entry)


@override_settings(
    LINKEDIN_CLIENT_ID='test_client_id',
    LINKEDIN_CLIENT_SECRET='test_client_secret'
)
class LinkedInViewsTestCase(TestCase):
    """Test LinkedIn integration views"""
    
    def setUp(self):
        self.admin_user = User.objects.create_superuser(
            'admin', 'admin@example.com', 'password'
        )
        self.client.login(username='admin', password='password')
        
    def test_auth_start_view(self):
        """Test LinkedIn auth start view"""
        response = self.client.get('/admin/linkedin/auth/start/')
        self.assertEqual(response.status_code, 302)  # Redirect to LinkedIn
        
    def test_status_view(self):
        """Test LinkedIn status view"""
        response = self.client.get('/admin/linkedin/status/')
        self.assertEqual(response.status_code, 200)
        
        data = response.json()
        self.assertIn('is_authenticated', data)
        self.assertIn('client_id_configured', data)