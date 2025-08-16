from django.urls import path
from .views import visual_search

urlpatterns = [
    path('visualsearch/', visual_search, name='visual_search'),
]
