from django.contrib import admin
from .models import EnhancedTag


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


