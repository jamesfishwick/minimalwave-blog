from django.contrib import admin
from .models import LinkedInCredentials, LinkedInPost, LinkedInSettings


@admin.register(LinkedInCredentials)
class LinkedInCredentialsAdmin(admin.ModelAdmin):
    list_display = ['authorized_user', 'is_token_valid', 'created_at', 'updated_at']
    readonly_fields = ['created_at', 'updated_at']

    def has_add_permission(self, request):
        """Prevent creating multiple instances"""
        return LinkedInCredentials.objects.count() == 0


@admin.register(LinkedInPost)
class LinkedInPostAdmin(admin.ModelAdmin):
    list_display = ['entry', 'status', 'posted_at', 'linkedin_post_id']
    list_filter = ['status', 'posted_at']
    search_fields = ['entry__title', 'post_text']
    readonly_fields = ['posted_at', 'linkedin_post_id', 'post_url']


@admin.register(LinkedInSettings)
class LinkedInSettingsAdmin(admin.ModelAdmin):
    list_display = ['enabled', 'auto_post_entries', 'auto_post_blogmarks']

    def has_add_permission(self, request):
        """Prevent creating multiple instances"""
        return LinkedInSettings.objects.count() == 0