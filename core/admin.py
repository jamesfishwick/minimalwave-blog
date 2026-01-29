from django.contrib import admin
from .models import EnhancedTag, ContentLinkedIn


@admin.register(EnhancedTag)
class EnhancedTagAdmin(admin.ModelAdmin):
    list_display = [
        'name', 'slug', 'usage_count_display',
        'is_featured', 'is_active'
    ]
    list_filter = [
        'is_featured', 'is_active', 'created'
    ]
    list_editable = ['is_featured', 'is_active']
    search_fields = ['name', 'slug', 'description']
    prepopulated_fields = {'slug': ('name',)}
    readonly_fields = ['created', 'updated']

    fieldsets = (
        (None, {
            'fields': ('name', 'slug', 'description')
        }),
        ('Options', {
            'fields': ('is_featured', 'is_active')
        }),
        ('Metadata', {
            'fields': ('created', 'updated'),
            'classes': ('collapse',)
        })
    )

    def usage_count_display(self, obj):
        """Display usage count"""
        return obj.usage_count()
    usage_count_display.short_description = 'Usage'

    actions = ['mark_featured', 'unmark_featured']

    def mark_featured(self, request, queryset):
        queryset.update(is_featured=True)
    mark_featured.short_description = "Mark as featured"

    def unmark_featured(self, request, queryset):
        queryset.update(is_featured=False)
    unmark_featured.short_description = "Unmark as featured"


@admin.register(ContentLinkedIn)
class ContentLinkedInAdmin(admin.ModelAdmin):
    list_display = [
        'content_type', 'content_id', 'enabled',
        'posted', 'posted_at', 'retry_count'
    ]
    list_filter = [
        'content_type', 'enabled', 'posted',
        'posted_at'
    ]
    search_fields = ['content_id', 'post_id', 'post_url']
    readonly_fields = [
        'posted_at', 'created', 'updated',
        'last_error', 'retry_count'
    ]

    fieldsets = (
        (None, {
            'fields': ('content_type', 'content_id')
        }),
        ('LinkedIn Settings', {
            'fields': ('enabled', 'custom_text')
        }),
        ('Posting Status', {
            'fields': (
                'posted', 'posted_at', 'post_id',
                'post_url', 'last_error', 'retry_count'
            )
        }),
        ('Metadata', {
            'fields': ('created', 'updated'),
            'classes': ('collapse',)
        })
    )

    actions = ['reset_for_retry']

    def reset_for_retry(self, request, queryset):
        queryset.update(
            posted=False,
            last_error='',
            retry_count=0
        )
        self.message_user(request, f"Reset {queryset.count()} items for retry.")
    reset_for_retry.short_description = "Reset for LinkedIn retry"