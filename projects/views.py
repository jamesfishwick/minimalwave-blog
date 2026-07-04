from django.contrib.syndication.views import Feed
from django.db import models
from django.shortcuts import get_object_or_404, render
from django.utils import timezone
from django.utils.feedgenerator import Atom1Feed
from taggit.models import Tag

from .models import Project


def _published_projects():
    """Published projects, respecting scheduled publish_date (as blog views do)."""
    return Project.objects.filter(status="published").filter(
        models.Q(publish_date__isnull=True) | models.Q(publish_date__lte=timezone.now())
    )  # Meta.ordering handles sort_order, -start_date


def index(request):
    projects = _published_projects().prefetch_related("tags")
    return render(
        request,
        "projects/index.html",
        {
            "featured_projects": projects.filter(featured=True),
            "projects": projects.filter(featured=False),
        },
    )


def detail(request, slug):
    project = get_object_or_404(_published_projects(), slug=slug)
    return render(
        request,
        "projects/detail.html",
        {"project": project},
    )


def tag(request, slug):
    tag = get_object_or_404(Tag, slug=slug)
    projects = _published_projects().filter(tags__slug=slug)
    return render(
        request,
        "projects/tag.html",
        {"tag": tag, "projects": projects},
    )


class ProjectAtomFeed(Feed):
    title = "Minimal Wave Projects"
    link = "/projects/"
    subtitle = "Software projects"
    feed_type = Atom1Feed

    def items(self):
        return _published_projects()[:15]

    def item_title(self, item):
        return item.title

    def item_description(self, item):
        return item.summary_text

    def item_pubdate(self, item):
        return item.created
