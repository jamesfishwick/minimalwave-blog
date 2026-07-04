"""
Shared registry of editable markdown content across the content apps.

Used by the dump_content / load_content commands so both agree on which models
and fields are "content" (markdown prose) that skills may edit. Every model
here has `title` and `slug` attributes, which the commands rely on.

Filename starts with `_` so Django's management command loader skips it.
"""

from django.core.management.base import CommandError

from blog.models import Blogmark, Entry
from projects.models import Project
from til.models import TIL

# type-name -> {model, fields}. `fields` are the markdown columns to export.
CONTENT_TYPES = {
    "entry": {"model": Entry, "fields": ["summary", "body"]},
    "blogmark": {"model": Blogmark, "fields": ["commentary"]},
    "til": {"model": TIL, "fields": ["body"]},
    "project": {"model": Project, "fields": ["summary", "body"]},
}


def resolve_types(options):
    """Return the list of type-names selected by --all / --type."""
    if options.get("all"):
        return list(CONTENT_TYPES)
    t = options.get("type")
    if not t:
        raise CommandError("Specify --type <type> or --all")
    if t not in CONTENT_TYPES:
        raise CommandError(
            f"Unknown type '{t}'. Choices: {', '.join(sorted(CONTENT_TYPES))}"
        )
    return [t]
