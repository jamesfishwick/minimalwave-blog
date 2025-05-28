from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html
from .models import Tag, Entry, Authorship, Blogmark, SiteSettings

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
