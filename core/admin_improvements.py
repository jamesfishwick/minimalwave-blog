"""
Enhanced admin configurations with better UX and organization
"""
from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.db import models
from django.forms import ModelForm, Textarea


class TaggedContentListFilter(admin.SimpleListFilter):
    """Filter content by tags in admin"""
    title = 'tags'
    parameter_name = 'tag'

    def lookups(self, request, model_admin):
        from core.models import EnhancedTag
        return [(tag.slug, tag.name) for tag in EnhancedTag.objects.filter(is_active=True)[:20]]

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(tags__slug=self.value())
        return queryset


class CategoryListFilter(admin.SimpleListFilter):
    """Filter by category"""
    title = 'category'
    parameter_name = 'category'

    def lookups(self, request, model_admin):
        from core.models import Category
        return [(cat.slug, cat.name) for cat in Category.objects.filter(is_active=True)]

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(category__slug=self.value())
        return queryset


class AdminColorMixin:
    """Mixin for displaying colors in admin"""

    def color_preview(self, obj):
        if hasattr(obj, 'color') and obj.color:
            return format_html(
                '<div style="width: 30px; height: 20px; background-color: {}; '
                'border: 1px solid #ddd; border-radius: 3px; display: inline-block;"></div>',
                obj.color
            )
        return '—'
    color_preview.short_description = 'Color'


class AdminIconMixin:
    """Mixin for displaying icons in admin"""

    def icon_preview(self, obj):
        if hasattr(obj, 'icon') and obj.icon:
            return format_html(
                '<i class="{}" style="font-size: 16px; color: #666;"></i>',
                obj.icon
            )
        return '—'
    icon_preview.short_description = 'Icon'


class ContentStatusMixin:
    """Mixin for consistent content status display"""

    def status_badge(self, obj):
        if hasattr(obj, 'status'):
            colors = {
                'draft': '#6B7280',
                'review': '#F59E0B',
                'published': '#10B981'
            }
            return format_html(
                '<span style="background-color: {}; color: white; '
                'padding: 2px 8px; border-radius: 12px; font-size: 11px; font-weight: bold;">{}</span>',
                colors.get(obj.status, '#6B7280'),
                obj.get_status_display() if hasattr(obj, 'get_status_display') else obj.status
            )
        elif hasattr(obj, 'is_draft'):
            return format_html(
                '<span style="background-color: {}; color: white; '
                'padding: 2px 8px; border-radius: 12px; font-size: 11px; font-weight: bold;">{}</span>',
                '#10B981' if not obj.is_draft else '#6B7280',
                'Published' if not obj.is_draft else 'Draft'
            )
        return '—'
    status_badge.short_description = 'Status'


class QuickEditMixin:
    """Mixin for quick editing capabilities"""

    def quick_edit_link(self, obj):
        if obj.pk:
            url = reverse(f'admin:{obj._meta.app_label}_{obj._meta.model_name}_change', args=[obj.pk])
            return format_html('<a href="{}" class="button">Edit</a>', url)
        return '—'
    quick_edit_link.short_description = 'Quick Edit'


class ViewOnSiteMixin:
    """Mixin for view on site links"""

    def view_on_site_link(self, obj):
        if hasattr(obj, 'get_absolute_url'):
            try:
                url = obj.get_absolute_url()
                return format_html(
                    '<a href="{}" target="_blank" class="button">View</a>',
                    url
                )
            except:
                pass
        return '—'
    view_on_site_link.short_description = 'View on Site'


class TaxonomyAdminMixin(AdminColorMixin, AdminIconMixin):
    """Combined mixin for taxonomy-related admin"""

    class Media:
        css = {
            'all': ('admin/css/taxonomy_admin.css',)
        }
        js = ('admin/js/taxonomy_admin.js',)


# Custom form widgets for better UX
class ColorPickerWidget(admin.widgets.AdminTextInputWidget):
    """Color picker widget for admin"""

    def __init__(self, attrs=None):
        super().__init__(attrs)
        if attrs:
            attrs.update({'type': 'color'})
        else:
            attrs = {'type': 'color'}

    class Media:
        css = {
            'all': ('admin/css/color_picker.css',)
        }


class MarkdownWidget(Textarea):
    """Enhanced textarea for markdown content"""

    def __init__(self, attrs=None):
        if attrs is None:
            attrs = {}
        attrs.update({
            'rows': 20,
            'cols': 100,
            'style': 'font-family: monospace;'
        })
        super().__init__(attrs)

    class Media:
        css = {
            'all': ('admin/css/markdown_editor.css',)
        }
        js = ('admin/js/markdown_editor.js',)