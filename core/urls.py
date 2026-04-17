from django.urls import path

from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("api/extract-intent/", views.extract_intent, name="extract_intent"),
    path("api/tasks/create/", views.create_task, name="create_task"),
    path("api/tasks/", views.list_tasks, name="list_tasks"),
]

