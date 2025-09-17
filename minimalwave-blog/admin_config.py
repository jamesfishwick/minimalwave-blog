"""
Custom admin site configuration for better organization
"""
from django.contrib import admin
from django.contrib.admin import AdminSite


class MinimalWaveAdminSite(AdminSite):
    site_header = "Minimal Wave Blog Administration"
    site_title = "Minimal Wave Admin"
    index_title = "Content Management"

    def get_app_list(self, request, app_label=None):
        """
        Return a custom app list with better organization
        """
        app_list = super().get_app_list(request, app_label)

        # Custom ordering and grouping
        custom_order = [
            'core',      # Taxonomy & Content Structure
            'blog',      # Blog Content
            'til',       # TIL Content
            'linkedin',  # LinkedIn Integration
            'auth',      # Authentication
            'sites',     # Sites Framework
        ]

        # Rename app labels for better UX
        app_name_mapping = {
            'core': 'Taxonomy & Organization',
            'blog': 'Blog Content',
            'til': 'TIL Content',
            'linkedin': 'LinkedIn Integration',
            'auth': 'Users & Permissions',
            'sites': 'Site Configuration',
        }

        # Sort according to custom order
        ordered_apps = []
        for app_name in custom_order:
            for app in app_list:
                if app['app_label'] == app_name:
                    # Update the display name
                    if app_name in app_name_mapping:
                        app['name'] = app_name_mapping[app_name]
                    ordered_apps.append(app)
                    break

        # Add any remaining apps not in our custom order
        for app in app_list:
            if app not in ordered_apps:
                ordered_apps.append(app)

        return ordered_apps


# Create the custom admin site instance
admin_site = MinimalWaveAdminSite(name='minimalwave_admin')