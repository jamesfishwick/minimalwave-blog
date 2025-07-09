from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html
from .models import Tag, Entry, Authorship, Blogmark, SiteSettings  # LinkedInCredentials, LinkedInPost, LinkedInSettings

class AuthorshipInline(admin.TabularInline):
    model = Authorship
    extra = 1

@admin.register(SiteSettings)
class SiteSettingsAdmin(admin.ModelAdmin):
    """Admin interface for site settings"""
    fieldsets = (
        (None, {
            'fields': ('site_title', 'site_description'),
        }),
        ('Media', {
            'fields': ('header_logo', 'favicon'),
        }),
    )

    def has_add_permission(self, request):
        """Prevent creating multiple instances"""
        return SiteSettings.objects.count() == 0

@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug')
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ('name',)

@admin.register(Entry)
class EntryAdmin(admin.ModelAdmin):
    list_display = ('title', 'created', 'status', 'get_publish_date', 'preview_link')
    list_filter = ('status', 'created', 'tags')
    search_fields = ('title', 'summary', 'body')
    prepopulated_fields = {'slug': ('title',)}
    date_hierarchy = 'created'
    inlines = [AuthorshipInline]
    filter_horizontal = ('tags',)
    fieldsets = (
        (None, {
            'fields': ('title', 'slug', 'summary', 'body', 'created')
        }),
        ('Publishing', {
            'fields': ('status', 'publish_date', 'is_draft', 'tags', 'card_image', 'preview_link')
        }),
        # ('LinkedIn Integration', {
        #     'fields': ('linkedin_enabled', 'linkedin_custom_text', 'linkedin_posted'),
        #     'classes': ('collapse',)
        # }),
    )

    def get_publish_date(self, obj):
        if obj.publish_date:
            return obj.publish_date.strftime("%Y-%m-%d %H:%M")
        return "-"
    get_publish_date.short_description = "Publish Date"

    def preview_link(self, obj):
        if obj.slug:
            return format_html('<a href="{}" target="_blank">Preview</a>',
                              reverse('blog:entry_preview', args=[obj.slug]))
        return ""
    preview_link.short_description = "Preview"
    readonly_fields = ['preview_link']

@admin.register(Blogmark)
class BlogmarkAdmin(admin.ModelAdmin):
    list_display = ('title', 'url', 'created', 'status', 'get_publish_date', 'preview_link')
    list_filter = ('status', 'created', 'tags')
    search_fields = ('title', 'commentary', 'url')
    prepopulated_fields = {'slug': ('title',)}
    date_hierarchy = 'created'
    filter_horizontal = ('tags',)

    def preview_link(self, obj):
        if obj.slug:
            return format_html('<a href="{}" target="_blank">Preview</a>',
                              reverse('blog:blogmark_preview', args=[obj.slug]))
        return ""
    preview_link.short_description = "Preview"
    readonly_fields = ['preview_link']

    def get_publish_date(self, obj):
        if obj.publish_date:
            return obj.publish_date.strftime("%Y-%m-%d %H:%M")
        return "-"
    get_publish_date.short_description = "Publish Date"

    fieldsets = (
        (None, {
            'fields': ('title', 'slug', 'url', 'commentary', 'created')
        }),
        ('Publishing', {
            'fields': ('status', 'publish_date', 'is_draft', 'tags')
        }),
        ('Via', {
            'fields': ('via', 'via_title'),
            'classes': ('collapse',)
        }),
    )


# @admin.register(LinkedInCredentials)
class LinkedInCredentialsAdmin(admin.ModelAdmin):
    """Admin interface for LinkedIn credentials"""
    list_display = ('authorized_user', 'token_expires_at', 'is_token_valid', 'linkedin_actions')
    readonly_fields = ('access_token', 'refresh_token', 'authorized_user', 'created_at', 'updated_at', 'linkedin_actions')
    
    fieldsets = (
        ('App Configuration', {
            'fields': ('client_id', 'client_secret'),
        }),
        ('Authentication Status', {
            'fields': ('authorized_user', 'token_expires_at', 'is_token_valid'),
        }),
        ('Actions', {
            'fields': ('linkedin_actions',),
        }),
        ('Advanced', {
            'fields': ('access_token', 'refresh_token', 'state', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def has_add_permission(self, request):
        """Prevent creating multiple instances"""
        return LinkedInCredentials.objects.count() == 0
    
    def linkedin_actions(self, obj):
        """Provide action buttons for LinkedIn integration"""
        if obj.is_token_valid:
            return format_html(
                '<a href="/admin/linkedin/status/" class="button">Check Status</a> '
                '<a href="/admin/linkedin/test/" class="button">Test Post</a> '
                '<a href="/admin/linkedin/disconnect/" class="button" onclick="return confirm(\'Are you sure?\')">Disconnect</a>'
            )
        else:
            return format_html(
                '<a href="/admin/linkedin/auth/start/" class="button default">Connect LinkedIn</a>'
            )
    linkedin_actions.short_description = "LinkedIn Actions"


# @admin.register(LinkedInPost)
class LinkedInPostAdmin(admin.ModelAdmin):
    """Admin interface for LinkedIn posts"""
    list_display = ('entry', 'status', 'posted_at', 'linkedin_link')
    list_filter = ('status', 'posted_at')
    search_fields = ('entry__title', 'post_text')
    readonly_fields = ('linkedin_post_id', 'post_url', 'post_text', 'posted_at', 'linkedin_link')
    
    fieldsets = (
        (None, {
            'fields': ('entry', 'status', 'posted_at')
        }),
        ('LinkedIn Details', {
            'fields': ('linkedin_post_id', 'post_url', 'linkedin_link', 'post_text')
        }),
        ('Error Information', {
            'fields': ('error_message',),
            'classes': ('collapse',)
        }),
    )
    
    def linkedin_link(self, obj):
        """Provide link to LinkedIn post"""
        if obj.post_url:
            return format_html('<a href="{}" target="_blank">View on LinkedIn</a>', obj.post_url)
        return "No URL available"
    linkedin_link.short_description = "LinkedIn Link"


# @admin.register(LinkedInSettings)
class LinkedInSettingsAdmin(admin.ModelAdmin):
    """Admin interface for LinkedIn settings"""
    fieldsets = (
        ('Global Settings', {
            'fields': ('enabled', 'include_url', 'url_template'),
        }),
        ('Auto-posting Settings', {
            'fields': ('auto_post_entries', 'auto_post_blogmarks'),
        }),
    )
    
    def has_add_permission(self, request):
        """Prevent creating multiple instances"""
        return LinkedInSettings.objects.count() == 0
