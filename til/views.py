from django.shortcuts import render, get_object_or_404
from django.contrib.syndication.views import Feed
from django.utils.feedgenerator import Atom1Feed
from django.db import models
from .models import TIL
from core.models import EnhancedTag
from blog.views import get_month_number, get_month_name

def index(request):
    tils = TIL.objects.filter(is_draft=False).order_by("-created")
    tags = EnhancedTag.objects.filter(is_active=True)
    return render(
        request,
        "til/index.html",
        {"tils": tils, "tags": tags},
    )

def detail(request, year, month, day, slug):
    til = get_object_or_404(
        TIL,
        created__year=year,
        created__month=get_month_number(month),
        created__day=day,
        slug=slug
    )
    return render(
        request,
        "til/detail.html",
        {"til": til},
    )

def tag(request, slug):
    tag = get_object_or_404(EnhancedTag, slug=slug)
    tils = TIL.objects.filter(tags=tag, is_draft=False).order_by("-created")
    return render(
        request,
        "til/tag.html",
        {"tag": tag, "tils": tils},
    )

def search(request):
    q = request.GET.get("q", "").strip()
    if q:
        # Simple search implementation - can be enhanced later
        tils = TIL.objects.filter(
            is_draft=False
        ).filter(
            models.Q(title__icontains=q) | 
            models.Q(body__icontains=q)
        ).order_by("-created")
    else:
        tils = []
    
    return render(
        request,
        "til/search.html",
        {"q": q, "tils": tils},
    )

class TILAtomFeed(Feed):
    title = "Minimal Wave TILs"
    link = "/til/"
    subtitle = "Today I Learned"
    feed_type = Atom1Feed

    def items(self):
        return TIL.objects.filter(is_draft=False).order_by("-created")[:15]

    def item_title(self, item):
        return item.title

    def item_description(self, item):
        return item.body_rendered

    def item_pubdate(self, item):
        return item.created
