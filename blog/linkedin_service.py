import requests
import json
import logging
import time
from datetime import datetime, timedelta
from django.utils import timezone
from django.conf import settings
from django.urls import reverse
from django.contrib.sites.models import Site
from urllib.parse import urlencode, quote
import secrets
import string

logger = logging.getLogger(__name__)


class LinkedInAPIException(Exception):
    """Exception for LinkedIn API errors"""
    pass


class LinkedInService:
    """
    Service class for LinkedIn API interactions.
    Handles OAuth flow, token management, and posting content.
    """
    
    # LinkedIn API endpoints
    LINKEDIN_AUTH_URL = "https://www.linkedin.com/oauth/v2/authorization"
    LINKEDIN_TOKEN_URL = "https://www.linkedin.com/oauth/v2/accessToken"
    LINKEDIN_POSTS_URL = "https://api.linkedin.com/rest/posts"
    LINKEDIN_USERINFO_URL = "https://api.linkedin.com/v2/userinfo"
    
    def __init__(self):
        self.credentials = self._get_credentials()
    
    def _get_credentials(self):
        """Get LinkedIn credentials from database"""
        try:
            # Import here to avoid circular imports
            from .models import LinkedInCredentials
            return LinkedInCredentials.get_credentials()
        except Exception as e:
            logger.error(f"Failed to get LinkedIn credentials: {str(e)}")
            return None
    
    def _get_settings(self):
        """Get LinkedIn settings from database"""
        try:
            # Import here to avoid circular imports
            from .models import LinkedInSettings
            return LinkedInSettings.get_settings()
        except Exception as e:
            logger.error(f"Failed to get LinkedIn settings: {str(e)}")
            return None
    
    def generate_auth_url(self, redirect_uri):
        """
        Generate LinkedIn OAuth authorization URL.
        
        Args:
            redirect_uri: The callback URL for OAuth flow
            
        Returns:
            tuple: (auth_url, state) where state is used for CSRF protection
        """
        if not self.credentials:
            raise LinkedInAPIException("LinkedIn credentials not configured")
        
        # Generate random state for CSRF protection
        state = ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(32))
        
        # Save state to credentials for verification
        self.credentials.state = state
        self.credentials.save()
        
        params = {
            'response_type': 'code',
            'client_id': self.credentials.client_id,
            'redirect_uri': redirect_uri,
            'scope': 'w_member_social profile email',
            'state': state
        }
        
        auth_url = f"{self.LINKEDIN_AUTH_URL}?{urlencode(params)}"
        return auth_url, state
    
    def exchange_code_for_token(self, code, redirect_uri, state):
        """
        Exchange authorization code for access token.
        
        Args:
            code: Authorization code from LinkedIn
            redirect_uri: The callback URL used in auth request
            state: State parameter for CSRF protection
            
        Returns:
            dict: Token response from LinkedIn
        """
        if not self.credentials:
            raise LinkedInAPIException("LinkedIn credentials not configured")
        
        # Verify state parameter
        if not self.credentials.state or self.credentials.state != state:
            raise LinkedInAPIException("Invalid state parameter - possible CSRF attack")
        
        data = {
            'grant_type': 'authorization_code',
            'code': code,
            'redirect_uri': redirect_uri,
            'client_id': self.credentials.client_id,
            'client_secret': self.credentials.client_secret
        }
        
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded'
        }
        
        response = requests.post(self.LINKEDIN_TOKEN_URL, data=data, headers=headers)
        
        if response.status_code != 200:
            logger.error(f"Token exchange failed: {response.status_code} - {response.text}")
            raise LinkedInAPIException(f"Token exchange failed: {response.text}")
        
        token_data = response.json()
        
        # Save tokens to database
        self.credentials.access_token = token_data['access_token']
        self.credentials.refresh_token = token_data.get('refresh_token', '')
        
        # Calculate expiration time (default 60 days for LinkedIn)
        expires_in = token_data.get('expires_in', 5184000)  # 60 days default
        self.credentials.token_expires_at = timezone.now() + timedelta(seconds=expires_in)
        
        # Get user info to store authorized user
        try:
            user_info = self._get_user_info(token_data['access_token'])
            self.credentials.authorized_user = user_info.get('name', 'Unknown')
        except Exception as e:
            logger.warning(f"Failed to get user info: {str(e)}")
            self.credentials.authorized_user = 'Unknown'
        
        # Clear state
        self.credentials.state = None
        self.credentials.save()
        
        return token_data
    
    def _get_user_info(self, access_token):
        """Get user info from LinkedIn API"""
        headers = {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json'
        }
        
        response = requests.get(self.LINKEDIN_USERINFO_URL, headers=headers)
        
        if response.status_code == 200:
            return response.json()
        else:
            logger.error(f"Failed to get user info: {response.status_code} - {response.text}")
            return {}
    
    def is_authenticated(self):
        """Check if we have valid LinkedIn credentials"""
        return (self.credentials and 
                self.credentials.access_token and 
                self.credentials.is_token_valid)
    
    def post_entry_to_linkedin(self, entry):
        """
        Post a blog entry to LinkedIn.
        
        Args:
            entry: Entry model instance
            
        Returns:
            dict: LinkedIn post response
        """
        if not self.is_authenticated():
            raise LinkedInAPIException("LinkedIn not authenticated")
        
        # Get post text
        post_text = self._get_entry_post_text(entry)
        
        # Create the post
        post_data = {
            "author": "urn:li:person:" + self._get_user_id(),
            "lifecycleState": "PUBLISHED",
            "specificContent": {
                "com.linkedin.ugc.ShareContent": {
                    "shareCommentary": {
                        "text": post_text
                    },
                    "shareMediaCategory": "NONE"
                }
            },
            "visibility": {
                "com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"
            }
        }
        
        return self._create_post(post_data, entry)
    
    def post_blogmark_to_linkedin(self, blogmark):
        """
        Post a blogmark to LinkedIn.
        
        Args:
            blogmark: Blogmark model instance
            
        Returns:
            dict: LinkedIn post response
        """
        if not self.is_authenticated():
            raise LinkedInAPIException("LinkedIn not authenticated")
        
        # Get post text
        post_text = self._get_blogmark_post_text(blogmark)
        
        # Create the post with link
        post_data = {
            "author": "urn:li:person:" + self._get_user_id(),
            "lifecycleState": "PUBLISHED",
            "specificContent": {
                "com.linkedin.ugc.ShareContent": {
                    "shareCommentary": {
                        "text": post_text
                    },
                    "shareMediaCategory": "ARTICLE",
                    "media": [
                        {
                            "status": "READY",
                            "description": {
                                "text": blogmark.title
                            },
                            "originalUrl": blogmark.url,
                            "title": {
                                "text": blogmark.title
                            }
                        }
                    ]
                }
            },
            "visibility": {
                "com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"
            }
        }
        
        return self._create_post(post_data, blogmark)
    
    def _create_post(self, post_data, content_item, max_retries=3, retry_delay=1):
        """
        Create a LinkedIn post with retry logic.
        
        Args:
            post_data: Post data dict
            content_item: Entry or Blogmark instance
            max_retries: Maximum number of retry attempts
            retry_delay: Delay between retries in seconds
            
        Returns:
            dict: LinkedIn API response
        """
        headers = {
            'Authorization': f'Bearer {self.credentials.access_token}',
            'Content-Type': 'application/json',
            'LinkedIn-Version': '202405',
            'X-Restli-Protocol-Version': '2.0.0'
        }
        
        last_error = None
        
        for attempt in range(max_retries + 1):
            try:
                response = requests.post(
                    self.LINKEDIN_POSTS_URL, 
                    json=post_data, 
                    headers=headers,
                    timeout=30  # 30 second timeout
                )
                
                if response.status_code in [200, 201]:
                    response_data = response.json()
                    
                    # Create LinkedIn post tracking record
                    self._create_post_record(content_item, response_data, 'posted')
                    
                    logger.info(f"Successfully posted to LinkedIn: {content_item.title}")
                    return response_data
                    
                elif response.status_code == 429:
                    # Rate limited - wait longer before retry
                    retry_after = int(response.headers.get('Retry-After', retry_delay * 60))
                    logger.warning(f"Rate limited by LinkedIn API. Waiting {retry_after}s before retry {attempt + 1}/{max_retries}")
                    
                    if attempt < max_retries:
                        time.sleep(retry_after)
                        continue
                    else:
                        last_error = f"Rate limited after {max_retries} attempts"
                        break
                        
                elif response.status_code in [401, 403]:
                    # Authentication/authorization error - don't retry
                    last_error = f"Authentication error: {response.status_code} - {response.text}"
                    logger.error(f"LinkedIn authentication error: {last_error}")
                    break
                    
                elif response.status_code >= 500:
                    # Server error - retry after delay
                    last_error = f"LinkedIn server error: {response.status_code} - {response.text}"
                    logger.warning(f"LinkedIn server error on attempt {attempt + 1}/{max_retries}: {last_error}")
                    
                    if attempt < max_retries:
                        time.sleep(retry_delay * (2 ** attempt))  # Exponential backoff
                        continue
                    else:
                        break
                        
                else:
                    # Client error - don't retry
                    last_error = f"LinkedIn client error: {response.status_code} - {response.text}"
                    logger.error(f"LinkedIn client error: {last_error}")
                    break
                    
            except requests.exceptions.RequestException as e:
                last_error = f"Network error: {str(e)}"
                logger.warning(f"Network error on attempt {attempt + 1}/{max_retries}: {last_error}")
                
                if attempt < max_retries:
                    time.sleep(retry_delay * (2 ** attempt))  # Exponential backoff
                    continue
                else:
                    break
                    
            except Exception as e:
                last_error = f"Unexpected error: {str(e)}"
                logger.error(f"Unexpected error posting to LinkedIn: {last_error}")
                break
        
        # All retries failed
        final_error = f"Failed to post to LinkedIn after {max_retries} attempts. Last error: {last_error}"
        logger.error(final_error)
        
        # Create failed post record
        self._create_post_record(content_item, None, 'failed', final_error)
        
        raise LinkedInAPIException(final_error)
    
    def _create_post_record(self, content_item, response_data, status, error_message=None):
        """Create a LinkedIn post tracking record"""
        try:
            # Import here to avoid circular imports
            from .models import LinkedInPost
            
            # Extract post ID from response
            post_id = None
            post_url = None
            
            if response_data:
                post_id = response_data.get('id', '')
                # LinkedIn post URL format: https://www.linkedin.com/feed/update/{post_id}
                if post_id:
                    post_url = f"https://www.linkedin.com/feed/update/{post_id}"
            
            # Get post text
            if hasattr(content_item, 'linkedin_post_text'):
                post_text = content_item.linkedin_post_text
            else:
                post_text = getattr(content_item, 'summary_text', str(content_item))
            
            LinkedInPost.objects.create(
                entry=content_item,
                linkedin_post_id=post_id or '',
                post_url=post_url or '',
                post_text=post_text,
                status=status,
                error_message=error_message
            )
            
        except Exception as e:
            logger.error(f"Failed to create LinkedIn post record: {str(e)}")
    
    def _get_entry_post_text(self, entry):
        """Get the text to post for a blog entry"""
        settings = self._get_settings()
        
        # Use custom text if provided, otherwise use summary
        if hasattr(entry, 'linkedin_custom_text') and entry.linkedin_custom_text:
            post_text = entry.linkedin_custom_text
        else:
            post_text = entry.summary_text
        
        # Add URL if enabled
        if settings and settings.include_url:
            site = Site.objects.get_current()
            entry_url = f"https://{site.domain}{entry.get_absolute_url()}"
            url_text = settings.url_template.format(url=entry_url)
            post_text = f"{post_text}\n\n{url_text}"
        
        return post_text
    
    def _get_blogmark_post_text(self, blogmark):
        """Get the text to post for a blogmark"""
        # For blogmarks, use the commentary as the post text
        return blogmark.commentary_rendered if hasattr(blogmark, 'commentary_rendered') else blogmark.commentary
    
    def _get_user_id(self):
        """Get the LinkedIn user ID (placeholder - would need actual API call)"""
        # This would need to be implemented with actual LinkedIn API call
        # For now, return empty string - LinkedIn API will handle this
        return ""
    
    def refresh_token_if_needed(self):
        """Check if token needs refreshing and refresh if possible"""
        if not self.credentials:
            return False
        
        # Check if token expires within 7 days
        if self.credentials.token_expires_at < timezone.now() + timedelta(days=7):
            logger.warning("LinkedIn token expires soon, manual re-authentication required")
            return False
        
        return True
    
    def retry_failed_posts(self, max_age_hours=24):
        """
        Retry failed LinkedIn posts that are newer than max_age_hours.
        
        Args:
            max_age_hours: Maximum age of failed posts to retry (in hours)
            
        Returns:
            dict: Summary of retry results
        """
        if not self.is_authenticated():
            raise LinkedInAPIException("LinkedIn not authenticated - cannot retry failed posts")
        
        # Import here to avoid circular imports
        from .models import LinkedInPost
        
        # Find recent failed posts
        cutoff_time = timezone.now() - timedelta(hours=max_age_hours)
        failed_posts = LinkedInPost.objects.filter(
            status='failed',
            posted_at__gte=cutoff_time
        ).select_related('entry')
        
        results = {
            'attempted': 0,
            'succeeded': 0,
            'still_failed': 0,
            'errors': []
        }
        
        for linkedin_post in failed_posts:
            results['attempted'] += 1
            
            try:
                # Check if the original entry is still published
                if not linkedin_post.entry.is_published:
                    logger.info(f"Skipping retry for unpublished entry: {linkedin_post.entry.title}")
                    continue
                
                # Retry the post
                logger.info(f"Retrying failed LinkedIn post for: {linkedin_post.entry.title}")
                
                # Delete the old failed record
                linkedin_post.delete()
                
                # Attempt to post again
                self.post_entry_to_linkedin(linkedin_post.entry)
                results['succeeded'] += 1
                
                logger.info(f"Successfully retried LinkedIn post for: {linkedin_post.entry.title}")
                
            except LinkedInAPIException as e:
                results['still_failed'] += 1
                results['errors'].append(f"{linkedin_post.entry.title}: {str(e)}")
                logger.error(f"Retry failed for {linkedin_post.entry.title}: {str(e)}")
            except Exception as e:
                results['still_failed'] += 1
                results['errors'].append(f"{linkedin_post.entry.title}: Unexpected error: {str(e)}")
                logger.error(f"Unexpected error retrying {linkedin_post.entry.title}: {str(e)}")
        
        logger.info(f"LinkedIn retry results: {results['succeeded']}/{results['attempted']} succeeded")
        return results
    
    def get_failed_posts_summary(self, max_age_days=7):
        """
        Get a summary of failed LinkedIn posts.
        
        Args:
            max_age_days: How many days back to look for failed posts
            
        Returns:
            dict: Summary of failed posts
        """
        # Import here to avoid circular imports
        from .models import LinkedInPost
        
        cutoff_time = timezone.now() - timedelta(days=max_age_days)
        failed_posts = LinkedInPost.objects.filter(
            status='failed',
            posted_at__gte=cutoff_time
        ).select_related('entry')
        
        summary = {
            'total_failed': failed_posts.count(),
            'recent_failures': [],
            'error_types': {}
        }
        
        for post in failed_posts[:10]:  # Limit to 10 most recent
            summary['recent_failures'].append({
                'entry_title': post.entry.title,
                'failed_at': post.posted_at,
                'error': post.error_message
            })
            
            # Categorize error types
            if 'Rate limited' in post.error_message:
                summary['error_types']['rate_limited'] = summary['error_types'].get('rate_limited', 0) + 1
            elif 'Authentication' in post.error_message:
                summary['error_types']['auth_error'] = summary['error_types'].get('auth_error', 0) + 1
            elif 'Network' in post.error_message:
                summary['error_types']['network_error'] = summary['error_types'].get('network_error', 0) + 1
            else:
                summary['error_types']['other'] = summary['error_types'].get('other', 0) + 1
        
        return summary

    def post_til_to_linkedin(self, til):
        """
        Post a TIL entry to LinkedIn.
        
        Args:
            til: TIL model instance
            
        Returns:
            dict: LinkedIn post response
        """
        if not self.is_authenticated():
            raise LinkedInAPIException("LinkedIn not authenticated")
        
        # Get post text
        post_text = self._get_til_post_text(til)
        
        # Create the post
        post_data = {
            "author": "urn:li:person:" + self._get_user_id(),
            "lifecycleState": "PUBLISHED",
            "specificContent": {
                "com.linkedin.ugc.ShareContent": {
                    "shareCommentary": {
                        "text": post_text
                    },
                    "shareMediaCategory": "NONE"
                }
            },
            "visibility": {
                "com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"
            }
        }
        
        # Make the API request with retry logic
        return self._post_with_retry(post_data, til, content_type="TIL")

    def _get_til_post_text(self, til):
        """Get the text to post for a TIL entry"""
        settings = self._get_settings()
        
        # Use custom text if provided, otherwise use body text
        if hasattr(til, 'linkedin_custom_text') and til.linkedin_custom_text:
            post_text = til.linkedin_custom_text
        else:
            # Prefix with "TIL: " to indicate it's a Today I Learned post
            post_text = f"TIL: {til.body_text}"
        
        # Add URL if enabled
        if settings and settings.include_url:
            from django.contrib.sites.models import Site
            site = Site.objects.get_current()
            til_url = f"https://{site.domain}{til.get_absolute_url()}"
            url_text = settings.url_template.format(url=til_url)
            post_text = f"{post_text}\n\n{url_text}"
        
        return post_text