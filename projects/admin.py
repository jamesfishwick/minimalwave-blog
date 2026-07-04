from django.contrib import admin

from .models import Project


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "project_status",
        "status",
        "featured",
        "sort_order",
        "start_date",
    )
    list_filter = ("project_status", "status", "featured", "tags")
    list_editable = ("featured", "sort_order")
    search_fields = ("title", "summary", "body", "tech_stack")
    prepopulated_fields = {"slug": ("title",)}
    date_hierarchy = "start_date"
    fieldsets = (
        (
            None,
            {
                "fields": ("title", "slug", "summary", "body"),
            },
        ),
        (
            "Links",
            {
                "fields": ("repo_url", "live_url"),
            },
        ),
        (
            "Media",
            {
                "fields": ("screenshot",),
                "description": "Screenshot or thumbnail for the card and social cards.",
            },
        ),
        (
            "Tech",
            {
                "fields": ("tech_stack",),
                "description": "Comma-separated technologies (its own facet, separate from tags).",
            },
        ),
        (
            "Curation",
            {
                "fields": ("featured", "sort_order", "project_status"),
            },
        ),
        (
            "Dates",
            {
                "fields": ("start_date", "end_date", "created", "publish_date"),
            },
        ),
        (
            "Publishing",
            {
                "fields": ("status", "is_draft", "tags"),
            },
        ),
    )
