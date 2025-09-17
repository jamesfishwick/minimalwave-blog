from django.contrib import admin
from django.utils.html import format_html
from .models import Category, EnhancedTag, Series, SeriesEntry, ContentLinkedIn


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'color_preview', 'icon', 'order', 'tag_count', 'is_active']
    list_editable = ['order', 'is_active']
    list_filter = ['is_active', 'created']
    search_fields = ['name', 'slug', 'description']
    prepopulated_fields = {'slug': ('name',)}
    ordering = ['order', 'name']

    def color_preview(self, obj):
        if obj.color:
            return format_html(
                '<div style="width: 30px; height: 30px; background-color: {}; border: 1px solid #ccc;"></div>',
                obj.color
            )
        return '-'
    color_preview.short_description = 'Color'

    def tag_count(self, obj):
        return obj.tags.count()
    tag_count.short_description = 'Tags'


@admin.register(EnhancedTag)
class EnhancedTagAdmin(admin.ModelAdmin):
    list_display = [
        'name', 'slug', 'category', 'content_type',
        'color_preview', 'usage_count', 'last_used',
        'is_featured', 'is_active'
    ]
    list_filter = [
        'content_type', 'category', 'is_featured',
        'is_active', 'last_used'
    ]
    list_editable = ['is_featured', 'is_active']
    search_fields = ['name', 'slug', 'description']
    prepopulated_fields = {'slug': ('name',)}
    readonly_fields = ['usage_count', 'last_used', 'created', 'updated']

    fieldsets = (
        (None, {
            'fields': ('name', 'slug', 'description', 'category', 'content_type')
        }),
        ('Display Options', {
            'fields': ('color', 'icon', 'is_featured', 'is_active'),
            'classes': ('collapse',)
        }),
        ('Analytics', {
            'fields': ('usage_count', 'last_used'),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('created', 'updated'),
            'classes': ('collapse',)
        })
    )

    def color_preview(self, obj):
        if obj.color:
            return format_html(
                '<span style="display: inline-block; width: 20px; height: 20px; '
                'background-color: {}; border: 1px solid #ccc; vertical-align: middle;"></span>',
                obj.color
            )
        return '-'
    color_preview.short_description = 'Color'

    actions = ['update_usage_stats', 'mark_featured', 'unmark_featured']

    def update_usage_stats(self, request, queryset):
        for tag in queryset:
            tag.update_usage()
        self.message_user(request, f"Updated usage stats for {queryset.count()} tags.")
    update_usage_stats.short_description = "Update usage statistics"

    def mark_featured(self, request, queryset):
        queryset.update(is_featured=True)
    mark_featured.short_description = "Mark as featured"

    def unmark_featured(self, request, queryset):
        queryset.update(is_featured=False)
    unmark_featured.short_description = "Unmark as featured"


class SeriesEntryInline(admin.TabularInline):
    model = SeriesEntry
    extra = 1
    fields = ['entry', 'order', 'part_title', 'notes']
    ordering = ['order']
    autocomplete_fields = ['entry']


@admin.register(Series)
class SeriesAdmin(admin.ModelAdmin):
    list_display = [
        'title', 'slug', 'author', 'category',
        'entry_count_display', 'is_complete', 'is_featured', 'is_active'
    ]
    list_filter = [
        'is_complete', 'is_featured', 'is_active',
        'category', 'created', 'author'
    ]
    list_editable = ['is_complete', 'is_featured', 'is_active']
    search_fields = ['title', 'slug', 'description']
    prepopulated_fields = {'slug': ('title',)}
    inlines = [SeriesEntryInline]
    readonly_fields = ['created', 'updated']

    fieldsets = (
        (None, {
            'fields': ('title', 'slug', 'description', 'summary', 'author')
        }),
        ('Organization', {
            'fields': ('category', 'cover_image', 'order')
        }),
        ('Status', {
            'fields': ('is_complete', 'is_featured', 'is_active')
        }),
        ('Metadata', {
            'fields': ('created', 'updated'),
            'classes': ('collapse',)
        })
    )

    def entry_count_display(self, obj):
        total = obj.entry_count
        published = obj.published_entry_count
        return f"{published}/{total}"
    entry_count_display.short_description = "Entries (Published/Total)"


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