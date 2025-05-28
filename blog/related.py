from django.db.models import Count
from django.conf import settings

def get_related_entries(entry, limit=3):
    """
    Get related blog entries based on shared tags
    """
    # Get the tags for this entry
    entry_tags = entry.tags.all()
    
    if not entry_tags:
        # If no tags, return recent entries
        return get_recent_entries(exclude_id=entry.id, limit=limit)
    
    # Find entries that share tags with this entry
    related_entries = (
        type(entry).objects
        .filter(tags__in=entry_tags)
        .exclude(id=entry.id)
        .filter(is_draft=False)
        .annotate(same_tags=Count('id'))
        .order_by('-same_tags', '-created')
        .distinct()[:limit]
    )
    
    # If we don't have enough related entries, supplement with recent entries
    if related_entries.count() < limit:
        recent_entries = get_recent_entries(
            exclude_id=entry.id, 
            exclude_ids=[e.id for e in related_entries],
            limit=limit - related_entries.count()
        )
        return list(related_entries) + list(recent_entries)
    
    return related_entries

def get_recent_entries(exclude_id=None, exclude_ids=None, limit=3):
    """
    Get recent blog entries, excluding specified IDs
    """
    from blog.models import Entry
    
    queryset = Entry.objects.filter(is_draft=False).order_by('-created')
    
    if exclude_id:
        queryset = queryset.exclude(id=exclude_id)
    
    if exclude_ids:
        queryset = queryset.exclude(id__in=exclude_ids)
    
    return queryset[:limit]
