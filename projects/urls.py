from django.urls import path

from . import views

app_name = "projects"

urlpatterns = [
    path("", views.index, name="index"),
    # Static sub-paths must precede the <slug:slug> catch-all so they are not
    # swallowed by it.
    path("feed/", views.ProjectAtomFeed(), name="feed"),
    path("tag/<slug:slug>/", views.tag, name="tag"),
    path("<slug:slug>/", views.detail, name="detail"),
]
