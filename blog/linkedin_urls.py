from django.urls import path
from . import linkedin_views

app_name = 'linkedin'

urlpatterns = [
    path('auth/start/', linkedin_views.linkedin_auth_start, name='auth_start'),
    path('auth/callback/', linkedin_views.linkedin_auth_callback, name='auth_callback'),
    path('status/', linkedin_views.linkedin_status, name='status'),
    path('test/', linkedin_views.linkedin_test_post, name='test_post'),
    path('post-entry/', linkedin_views.linkedin_post_entry, name='post_entry'),
    path('settings/', linkedin_views.linkedin_settings_view, name='settings'),
    path('disconnect/', linkedin_views.linkedin_disconnect, name='disconnect'),
]