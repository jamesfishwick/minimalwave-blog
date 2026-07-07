"""Redirect shim for the retired TIL section.

TIL content has been folded into blog Entries (see blog migration
0006_migrate_til_to_entry). These views 301-redirect the old /til/ URLs to
their new blog homes so inbound links and search results keep resolving.
"""

from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse

from blog.models import Entry
from blog.views import get_month_number


def index(request):
    """/til/ -> the blog post stream."""
    return redirect("blog:posts", permanent=True)


def detail(request, year, month, day, slug):
    """/til/<date>/<slug>/ -> the migrated Entry's canonical URL."""
    entry = get_object_or_404(
        Entry,
        created__year=year,
        created__month=get_month_number(month),
        created__day=day,
        slug=slug,
    )
    return redirect(entry.get_absolute_url(), permanent=True)


def tag(request, slug):
    """/til/tag/<slug>/ -> the blog tag page for the same slug."""
    return redirect(reverse("blog:tag", kwargs={"slug": slug}), permanent=True)


def search(request):
    """/til/search/ -> blog search, preserving the query string."""
    q = request.GET.get("q", "").strip()
    url = reverse("blog:search")
    if q:
        url = f"{url}?q={q}"
    return redirect(url, permanent=True)


def feed(request):
    """/til/feed/ -> the unified blog feed."""
    return redirect(reverse("blog:feed"), permanent=True)
