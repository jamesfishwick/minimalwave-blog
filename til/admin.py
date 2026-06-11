from django.contrib import admin
from .models import TIL

@admin.register(TIL)
class TILAdmin(admin.ModelAdmin):
    list_display = ('title', 'created', 'is_draft')
    list_filter = ('is_draft', 'created')
    search_fields = ('title', 'body')
    prepopulated_fields = {'slug': ('title',)}
    date_hierarchy = 'created'
    fieldsets = (
        (None, {
            'fields': ('title', 'slug', 'body', 'created', 'author')
        }),
        ('Image', {
            'fields': ('image', 'image_caption'),
            'description': 'Upload an image for this TIL.'
        }),
        ('Publishing', {
            'fields': ('is_draft', 'tags', 'card_image')
        }),
    )
