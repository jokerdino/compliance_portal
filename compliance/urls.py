from django.urls import path
from django.views.generic import RedirectView
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
    path("templates/<int:pk>/",
    views.TemplateDetailView.as_view(),
    name="template_detail"),
    path(
        "templates/<int:pk>/edit/",
        views.TemplateUpdateView.as_view(),
        name="template_edit",
    ),
    path(
        "templates/populate_tasks/<recurring_interval>/",
        views.populate_templates,
        name="populate_tasks",
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
    path(
        "tasks/<int:pk>/",
        views.TaskDetailView.as_view(),
        name="task_detail",
    ),
    path(
        "tasks/<filter>/",
        views.TaskListView.as_view(),
        name="task_list",
    ),
]

urlpatterns += [path("", RedirectView.as_view(url="tasks/due-today/", permanent=True))]
