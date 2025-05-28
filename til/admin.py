from django.contrib import admin
from .models import TIL

@admin.register(TIL)
class TILAdmin(admin.ModelAdmin):
    list_display = ('title', 'created', 'is_draft')
    list_filter = ('is_draft', 'created', 'tags')
    search_fields = ('title', 'body')
    prepopulated_fields = {'slug': ('title',)}
    date_hierarchy = 'created'
    filter_horizontal = ('tags',)
    fieldsets = (
        (None, {
            'fields': ('title', 'slug', 'body', 'created', 'author')
        }),
        ('Publishing', {
            'fields': ('is_draft', 'tags')
        }),
    )
