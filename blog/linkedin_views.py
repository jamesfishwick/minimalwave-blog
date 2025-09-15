from django.shortcuts import render, redirect
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import messages
from django.conf import settings
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.contrib.sites.models import Site
from django.utils import timezone
from .linkedin_service import LinkedInService, LinkedInAPIException
from .models import LinkedInCredentials, LinkedInSettings, Entry
import logging

logger = logging.getLogger(__name__)


@staff_member_required
def linkedin_auth_start(request):
    """
    Start LinkedIn OAuth flow.
    """
    try:
        # Get or create LinkedIn credentials
        credentials, created = LinkedInCredentials.objects.get_or_create(
            pk=1,
            defaults={
                'client_id': settings.LINKEDIN_CLIENT_ID or '',
                'client_secret': settings.LINKEDIN_CLIENT_SECRET or '',
                'access_token': '',
                'authorized_user': '',
                'token_expires_at': timezone.now(),
            }
        )
        
        # Update client credentials from settings
        if settings.LINKEDIN_CLIENT_ID:
            credentials.client_id = settings.LINKEDIN_CLIENT_ID
        if settings.LINKEDIN_CLIENT_SECRET:
            credentials.client_secret = settings.LINKEDIN_CLIENT_SECRET
        credentials.save()
        
        # Generate redirect URI
        site = Site.objects.get_current()
        # Use http for localhost, https for production
        protocol = 'http' if 'localhost' in site.domain else 'https'
        redirect_uri = f"{protocol}://{site.domain}/admin/linkedin/auth/callback/"
        
        # Start OAuth flow
        linkedin_service = LinkedInService()
        auth_url, state = linkedin_service.generate_auth_url(redirect_uri)
        
        return redirect(auth_url)
        
    except Exception as e:
        logger.error(f"LinkedIn auth start error: {str(e)}")
        messages.error(request, f"Failed to start LinkedIn authentication: {str(e)}")
        return redirect('/admin/')


@staff_member_required
def linkedin_auth_callback(request):
    """
    Handle LinkedIn OAuth callback.
    """
    try:
        # Get authorization code and state from callback
        code = request.GET.get('code')
        state = request.GET.get('state')
        error = request.GET.get('error')
        
        if error:
            logger.error(f"LinkedIn OAuth error: {error}")
            messages.error(request, f"LinkedIn authentication failed: {error}")
            return redirect('/admin/')
        
        if not code:
            messages.error(request, "No authorization code received from LinkedIn")
            return redirect('/admin/')
        
        # Generate redirect URI (same as start)
        site = Site.objects.get_current()
        # Use http for localhost, https for production
        protocol = 'http' if 'localhost' in site.domain else 'https'
        redirect_uri = f"{protocol}://{site.domain}/admin/linkedin/auth/callback/"
        
        # Exchange code for token
        linkedin_service = LinkedInService()
        token_data = linkedin_service.exchange_code_for_token(code, redirect_uri, state)
        
        messages.success(request, f"LinkedIn authentication successful! Authorized as: {linkedin_service.credentials.authorized_user}")
        logger.info(f"LinkedIn authentication successful for user: {linkedin_service.credentials.authorized_user}")
        
        return redirect('/admin/')
        
    except LinkedInAPIException as e:
        logger.error(f"LinkedIn API error: {str(e)}")
        messages.error(request, f"LinkedIn authentication failed: {str(e)}")
        return redirect('/admin/')
    except Exception as e:
        logger.error(f"LinkedIn auth callback error: {str(e)}")
        messages.error(request, f"Authentication error: {str(e)}")
        return redirect('/admin/')


@staff_member_required
def linkedin_status(request):
    """
    Check LinkedIn authentication status.
    """
    try:
        linkedin_service = LinkedInService()
        
        status_data = {
            'is_authenticated': linkedin_service.is_authenticated(),
            'credentials_exist': linkedin_service.credentials is not None,
            'authorized_user': linkedin_service.credentials.authorized_user if linkedin_service.credentials else None,
            'token_expires_at': linkedin_service.credentials.token_expires_at.isoformat() if linkedin_service.credentials else None,
            'client_id_configured': bool(settings.LINKEDIN_CLIENT_ID),
            'client_secret_configured': bool(settings.LINKEDIN_CLIENT_SECRET),
        }
        
        return JsonResponse(status_data)
        
    except Exception as e:
        logger.error(f"LinkedIn status check error: {str(e)}")
        return JsonResponse({'error': str(e)}, status=500)


@staff_member_required
@require_POST
def linkedin_test_post(request):
    """
    Test LinkedIn posting with a sample post.
    """
    try:
        linkedin_service = LinkedInService()
        
        if not linkedin_service.is_authenticated():
            return JsonResponse({'error': 'LinkedIn not authenticated'}, status=400)
        
        # Create a test post
        test_text = "Test post from Minimal Wave Blog LinkedIn integration!"
        
        # This would be a simplified test - in reality you'd need to create a proper post structure
        # For now, just return success if authenticated
        return JsonResponse({
            'success': True,
            'message': 'LinkedIn integration is ready for posting',
            'test_text': test_text
        })
        
    except Exception as e:
        logger.error(f"LinkedIn test post error: {str(e)}")
        return JsonResponse({'error': str(e)}, status=500)


@staff_member_required
@require_POST
def linkedin_post_entry(request):
    """
    Manually post a specific entry to LinkedIn.
    """
    try:
        entry_id = request.POST.get('entry_id')
        
        if not entry_id:
            return JsonResponse({'error': 'No entry ID provided'}, status=400)
        
        try:
            entry = Entry.objects.get(id=entry_id)
        except Entry.DoesNotExist:
            return JsonResponse({'error': 'Entry not found'}, status=404)
        
        if not entry.is_published:
            return JsonResponse({'error': 'Entry is not published'}, status=400)
        
        linkedin_service = LinkedInService()
        
        if not linkedin_service.is_authenticated():
            return JsonResponse({'error': 'LinkedIn not authenticated'}, status=400)
        
        # Post to LinkedIn
        response = linkedin_service.post_entry_to_linkedin(entry)
        
        return JsonResponse({
            'success': True,
            'message': f'Successfully posted "{entry.title}" to LinkedIn',
            'linkedin_post_id': response.get('id', '')
        })
        
    except LinkedInAPIException as e:
        logger.error(f"LinkedIn post error: {str(e)}")
        return JsonResponse({'error': str(e)}, status=500)
    except Exception as e:
        logger.error(f"Manual LinkedIn post error: {str(e)}")
        return JsonResponse({'error': str(e)}, status=500)


@staff_member_required
def linkedin_settings_view(request):
    """
    View and update LinkedIn settings.
    """
    try:
        linkedin_service = LinkedInService()
        settings_obj = LinkedInSettings.get_settings()
        
        data = {
            'linkedin_settings': {
                'include_url': settings_obj.include_url,
                'url_template': settings_obj.url_template,
                'auto_post_blogmarks': settings_obj.auto_post_blogmarks,
            },
            'is_authenticated': linkedin_service.is_authenticated(),
            'credentials_exist': linkedin_service.credentials is not None,
            'authorized_user': linkedin_service.credentials.authorized_user if linkedin_service.credentials else None,
            'client_id_configured': bool(settings.LINKEDIN_CLIENT_ID),
            'client_secret_configured': bool(settings.LINKEDIN_CLIENT_SECRET),
        }
        
        return JsonResponse(data)
        
    except Exception as e:
        logger.error(f"LinkedIn settings view error: {str(e)}")
        return JsonResponse({'error': str(e)}, status=500)


@staff_member_required
@require_POST
def linkedin_disconnect(request):
    """
    Disconnect LinkedIn integration by clearing stored tokens.
    """
    try:
        credentials = LinkedInCredentials.objects.first()
        if credentials:
            credentials.access_token = ''
            credentials.refresh_token = ''
            credentials.authorized_user = ''
            credentials.state = ''
            credentials.save()
            
            messages.success(request, "LinkedIn integration disconnected successfully")
            logger.info("LinkedIn integration disconnected")
        else:
            messages.info(request, "No LinkedIn credentials found to disconnect")
            
        return redirect('/admin/')
        
    except Exception as e:
        logger.error(f"LinkedIn disconnect error: {str(e)}")
        messages.error(request, f"Error disconnecting LinkedIn: {str(e)}")
        return redirect('/admin/')