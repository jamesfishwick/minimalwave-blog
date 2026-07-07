from django.urls import path

from . import views

# The TIL section is retired; every route here 301-redirects into the blog.
# Kept so old /til/ links and search results keep resolving. See til.views.
app_name = "til"

urlpatterns = [
    path("", views.index, name="index"),
    path("<int:year>/<str:month>/<int:day>/<slug:slug>/", views.detail, name="detail"),
    path("tag/<slug:slug>/", views.tag, name="tag"),
    path("search/", views.search, name="search"),
    path("feed/", views.feed, name="feed"),
]
