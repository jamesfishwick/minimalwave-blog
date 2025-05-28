from django.urls import path
from . import views

app_name = 'til'

urlpatterns = [
    path('', views.index, name='index'),
    path('<int:year>/<str:month>/<int:day>/<slug:slug>/', views.detail, name='detail'),
    path('tag/<slug:slug>/', views.tag, name='tag'),
    path('search/', views.search, name='search'),
    path('feed/', views.TILAtomFeed(), name='feed'),
]
