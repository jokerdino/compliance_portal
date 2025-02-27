from django.urls import path
from . import views

# urlpatterns = [path("", views.index, name="index")]
urlpatterns = [
    path(
        "templates/",
        views.TemplateListView.as_view(),
        name="template_list",
    ),
    path(
        "templates/add",
        views.TemplateCreateView.as_view(),
        name="template_add",
    ),
    path(
        "templates/<int:pk>/edit/",
        views.TemplateUpdateView.as_view(),
        name="template_edit",
    ),
    path(
        "templates/populate_daily/",
        views.populate_daily_templates,
        name="populate_daily",
    ),
    path(
        "tasks/",
        views.TaskListView.as_view(),
        name="task_list",
    ),
    path(
        "tasks/add/",
        views.TaskCreateView.as_view(),
        name="task_add",
    ),
    path(
        "tasks/<int:pk>/edit/",
        views.TaskUpdateView.as_view(),
        name="task_edit",
    ),
]
