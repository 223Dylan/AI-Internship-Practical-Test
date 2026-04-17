from django.urls import path

from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("api/extract-intent/", views.extract_intent, name="extract_intent"),
]

