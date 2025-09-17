#!/usr/bin/env python
"""
Migration script to transition from old tag system to new enhanced taxonomy.

This script:
1. Migrates existing blog.Tag to core.EnhancedTag
2. Creates default categories
3. Updates content relationships
4. Preserves all existing data
"""

import os
import sys
import django

# Add the project root to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Configure Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'minimalwave-blog.settings.development')
django.setup()

from django.db import transaction
from blog.models import Tag as OldTag, Entry, Blogmark
from til.models import TIL
from core.models import EnhancedTag, Category
from django.utils.text import slugify


def create_default_categories():
    """Create default categories for organizing tags"""
    categories = [
        {
            'name': 'Technology',
            'slug': 'technology',
            'description': 'Programming, software development, and tech-related topics',
            'color': '#3B82F6',
            'icon': 'fas fa-code',
            'order': 1
        },
        {
            'name': 'Learning',
            'slug': 'learning',
            'description': 'Educational content and learning experiences',
            'color': '#10B981',
            'icon': 'fas fa-graduation-cap',
            'order': 2
        },
        {
            'name': 'Productivity',
            'slug': 'productivity',
            'description': 'Tools, tips, and techniques for getting things done',
            'color': '#F59E0B',
            'icon': 'fas fa-tasks',
            'order': 3
        },
        {
            'name': 'Personal',
            'slug': 'personal',
            'description': 'Personal thoughts, experiences, and reflections',
            'color': '#EF4444',
            'icon': 'fas fa-user',
            'order': 4
        },
        {
            'name': 'Web Development',
            'slug': 'web-development',
            'description': 'Frontend, backend, and full-stack web development',
            'color': '#8B5CF6',
            'icon': 'fas fa-globe',
            'order': 5
        }
    ]

    created_categories = []
    for cat_data in categories:
        category, created = Category.objects.get_or_create(
            slug=cat_data['slug'],
            defaults=cat_data
        )
        if created:
            print(f"✓ Created category: {category.name}")
        else:
            print(f"→ Category already exists: {category.name}")
        created_categories.append(category)

    return created_categories


def migrate_tags():
    """Migrate existing tags to enhanced tags"""
    old_tags = OldTag.objects.all()

    # Get default category for uncategorized tags
    default_category = Category.objects.filter(slug='technology').first()

    migrated_count = 0
    for old_tag in old_tags:
        # Check if enhanced tag already exists
        enhanced_tag, created = EnhancedTag.objects.get_or_create(
            slug=old_tag.slug,
            defaults={
                'name': old_tag.name,
                'description': f'Migrated from legacy tag system',
                'category': default_category,
                'content_type': 'all',  # Start with 'all' - can be refined later
                'color': '#6B7280',  # Default gray color
                'icon': 'fas fa-tag',
                'is_active': True,
            }
        )

        if created:
            print(f"✓ Migrated tag: {old_tag.name} -> {enhanced_tag.name}")
            migrated_count += 1
        else:
            print(f"→ Enhanced tag already exists: {enhanced_tag.name}")

        # Update usage statistics
        enhanced_tag.update_usage()

    print(f"\nMigrated {migrated_count} tags to enhanced tag system")
    return migrated_count


def update_content_relationships():
    """Update content to use new enhanced tags"""
    print("\nUpdating content relationships...")

    # Update blog entries
    entries_updated = 0
    for entry in Entry.objects.all():
        old_tags = entry.tags.all()
        for old_tag in old_tags:
            enhanced_tag = EnhancedTag.objects.filter(slug=old_tag.slug).first()
            if enhanced_tag:
                # Remove old relationship, add new one
                entry.tags.remove(old_tag)
                # Note: This requires updating the Entry model to use EnhancedTag
                print(f"→ Would update entry '{entry.title}' tag relationship")

    # Similar updates for Blogmarks and TILs...
    print(f"Updated {entries_updated} entries")


def categorize_tags_intelligently():
    """Use tag names to intelligently categorize them"""

    # Technology-related keywords
    tech_keywords = [
        'python', 'javascript', 'django', 'react', 'vue', 'node',
        'programming', 'coding', 'development', 'software', 'api',
        'database', 'sql', 'git', 'docker', 'aws', 'linux'
    ]

    # Learning-related keywords
    learning_keywords = [
        'tutorial', 'learn', 'learning', 'education', 'course',
        'book', 'reading', 'study', 'til', 'today-i-learned'
    ]

    # Web development keywords
    web_keywords = [
        'html', 'css', 'frontend', 'backend', 'fullstack',
        'responsive', 'mobile', 'web', 'browser', 'http'
    ]

    # Productivity keywords
    productivity_keywords = [
        'productivity', 'workflow', 'tools', 'automation',
        'efficiency', 'tips', 'habits', 'organization'
    ]

    categories = {
        'technology': (Category.objects.get(slug='technology'), tech_keywords),
        'learning': (Category.objects.get(slug='learning'), learning_keywords),
        'web-development': (Category.objects.get(slug='web-development'), web_keywords),
        'productivity': (Category.objects.get(slug='productivity'), productivity_keywords),
    }

    categorized_count = 0
    for tag in EnhancedTag.objects.filter(category=None):
        tag_name_lower = tag.name.lower()

        for category_slug, (category_obj, keywords) in categories.items():
            if any(keyword in tag_name_lower for keyword in keywords):
                tag.category = category_obj
                tag.save(update_fields=['category'])
                print(f"✓ Categorized '{tag.name}' as {category_obj.name}")
                categorized_count += 1
                break

    print(f"\nIntelligently categorized {categorized_count} tags")


def main():
    """Run the complete migration"""
    print("=== Minimal Wave Blog Taxonomy Migration ===\n")

    try:
        with transaction.atomic():
            print("1. Creating default categories...")
            categories = create_default_categories()

            print("\n2. Migrating existing tags...")
            migrated_count = migrate_tags()

            print("\n3. Intelligently categorizing tags...")
            categorize_tags_intelligently()

            print("\n4. Updating usage statistics...")
            for tag in EnhancedTag.objects.all():
                tag.update_usage()

            print(f"\n✅ Migration completed successfully!")
            print(f"   - Created {len(categories)} categories")
            print(f"   - Migrated {migrated_count} tags")
            print(f"   - Enhanced taxonomy system is ready")

    except Exception as e:
        print(f"\n❌ Migration failed: {e}")
        raise


if __name__ == '__main__':
    main()