"""Data migration: fold every TIL row into a blog Entry.

Each TIL becomes a published/draft Entry that carries the same slug, created
date, body, image, and tags, plus a "til" tag so the archive stays browsable
at /blog/tag/til/. The TIL table is left in place; a later migration drops it
once this has been verified against production data.

Tags are copied through taggit's TaggedItem/ContentType tables directly rather
than the TaggableManager, because historical models from apps.get_model do not
expose the manager's helper methods reliably.
"""

from django.db import migrations


def _summary_from_body(body):
    """First paragraph of the body, capped, for the Entry card excerpt."""
    body = (body or "").strip()
    if not body:
        return ""
    para = body.split("\n\n", 1)[0].strip()
    if len(para) > 300:
        para = para[:297].rstrip() + "..."
    return para


def _unique_slug(slug, created, Entry, Blogmark):
    """Avoid slug+date collisions with existing entries/blogmarks.

    slug is unique_for_date on both models; two rows sharing slug+date would
    make the date-based detail view raise MultipleObjectsReturned. Suffix until
    free.
    """

    def taken(candidate):
        for model in (Entry, Blogmark):
            if model.objects.filter(
                slug=candidate,
                created__year=created.year,
                created__month=created.month,
                created__day=created.day,
            ).exists():
                return True
        return False

    if not taken(slug):
        return slug
    n = 1
    while True:
        candidate = f"{slug}-til" if n == 1 else f"{slug}-til-{n}"
        if not taken(candidate):
            return candidate
        n += 1


def migrate_tils_to_entries(apps, schema_editor):
    TIL = apps.get_model("til", "TIL")
    Entry = apps.get_model("blog", "Entry")
    Blogmark = apps.get_model("blog", "Blogmark")
    Authorship = apps.get_model("blog", "Authorship")
    Tag = apps.get_model("taggit", "Tag")
    TaggedItem = apps.get_model("taggit", "TaggedItem")
    ContentType = apps.get_model("contenttypes", "ContentType")

    til_ct = ContentType.objects.get_for_model(TIL)
    entry_ct = ContentType.objects.get_for_model(Entry)

    til_tag, _ = Tag.objects.get_or_create(
        slug="til", defaults={"name": "til"}
    )

    for til in TIL.objects.all():
        slug = _unique_slug(til.slug, til.created, Entry, Blogmark)
        status = "draft" if til.is_draft else "published"
        entry = Entry.objects.create(
            title=til.title,
            slug=slug,
            created=til.created,
            publish_date=None,
            body=til.body,
            summary=_summary_from_body(til.body) or til.title,
            card_image=til.card_image,
            image=til.image,
            image_caption=til.image_caption,
            is_draft=til.is_draft,
            status=status,
        )

        if til.author_id:
            Authorship.objects.create(user_id=til.author_id, entry=entry, order=0)

        # Copy the TIL's tags, then ensure the "til" marker tag is attached.
        tag_ids = set(
            TaggedItem.objects.filter(
                content_type=til_ct, object_id=til.id
            ).values_list("tag_id", flat=True)
        )
        tag_ids.add(til_tag.id)
        for tag_id in tag_ids:
            TaggedItem.objects.get_or_create(
                tag_id=tag_id, content_type=entry_ct, object_id=entry.id
            )


class Migration(migrations.Migration):

    dependencies = [
        ("blog", "0005_alter_blogmark_tags_alter_entry_tags"),
        ("til", "0005_alter_til_tags"),
        ("taggit", "0001_initial"),
    ]

    operations = [
        # One-way consolidation; the reverse is a no-op. The TIL rows are left
        # untouched, so re-running forward after a manual cleanup is possible.
        migrations.RunPython(migrate_tils_to_entries, migrations.RunPython.noop),
    ]
