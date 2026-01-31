"""Admin utility views for running management commands"""
from django.http import JsonResponse, HttpResponseForbidden
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from django.core.management import call_command
import os


@csrf_exempt
@require_POST
def run_auto_tag(request):
    """
    Simple webhook to run auto-tagging.
    Protected by a secret token in the request.

    Usage: POST /admin/run-auto-tag/
    Header: X-Admin-Token: <SECRET_TOKEN>
    """
    # Check for admin token
    secret_token = os.environ.get('ADMIN_WEBHOOK_TOKEN', 'change-me-in-production')
    provided_token = request.headers.get('X-Admin-Token', '')

    if provided_token != secret_token:
        return HttpResponseForbidden('Invalid token')

    try:
        # Run the command
        call_command('auto_tag_content', verbosity=2)
        return JsonResponse({
            'status': 'success',
            'message': 'Auto-tagging completed successfully'
        })
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)
