import datetime

from django.shortcuts import render
from .models import Template, Task
from .forms import TemplateForm, TaskForm
from django.views import generic
from django.views.generic.edit import UpdateView
from django.forms.models import model_to_dict
from django.utils.timezone import now
from django.urls import reverse_lazy
from django.http import HttpResponse  # , HttpResponseNotFound
from django.utils.timezone import localdate

from django.contrib.auth.mixins import LoginRequiredMixin
# Create your views here.


def index(request):
    num_topics = Task.objects.all().count()
    compliance_topics = Task.objects.order_by("-created_on")[:5]
    context = {"num_topics": num_topics, "compliance_topics": compliance_topics}
    return render(request, "index.html", context=context)


class TemplateCreateView(LoginRequiredMixin, generic.CreateView):
    model = Template
    form_class = TemplateForm
    template_name = "template_add.html"
    success_url = reverse_lazy("template_list")


class TemplateUpdateView(LoginRequiredMixin, UpdateView):
    model = Template
    form_class = TemplateForm
    template_name = "template_add.html"
    success_url = reverse_lazy("template_list")


class TaskCreateView(LoginRequiredMixin, generic.CreateView):
    model = Task
    form_class = TaskForm
    template_name = "template_add.html"
    success_url = reverse_lazy("task_list", kwargs={"filter": "due-today"})


class TaskUpdateView(LoginRequiredMixin, UpdateView):
    model = Task
    form_class = TaskForm
    # TODO: to verify or update the template
    template_name = "template_add.html"
    success_url = reverse_lazy("task_list", kwargs={"filter": "due-today"})


class TemplateListView(LoginRequiredMixin, generic.ListView):
    model = Template


class TaskListView(LoginRequiredMixin, generic.ListView):
    model = Task

    def get_context_data(self, **kwargs):
        """Pass the current filter type to the template for highlighting active links."""
        context = super().get_context_data(**kwargs)
        context["filter_type"] = self.kwargs.get("filter", "pending")
        return context

    def get_queryset(self):
        """Filter tasks based on the 'filter' query parameter."""
        filter_type = self.kwargs.get("filter", "pending")  # Default to 'pending'
        today = localdate()

        if filter_type == "due-today":
            return Task.objects.filter(due_date=today, current_status="pending")
        elif filter_type == "upcoming":
            return Task.objects.filter(due_date__gt=today, current_status="pending")
        elif filter_type == "overdue":
            return Task.objects.filter(due_date__lt=today, current_status="pending")
        else:  # Default: pending tasks
            return Task.objects.filter(current_status="pending")


def calculate_due_date(due_date_days, type_of_due_date):
    """Calculate due date based on due_date_days and type (calendar/working days)."""
    start_date = now().date()

    if type_of_due_date == "calendar":
        return start_date + datetime.timedelta(days=due_date_days)
    else:
        days_added = 0
        current_date = start_date
        while days_added < due_date_days:
            current_date += datetime.timedelta(days=1)
            if current_date.weekday() < 5:  # Monday-Friday (0-4)
                days_added += 1
        return current_date


def populate_templates(request, recurring_interval):
    def bulk_create(query):
        periodical_tasks = []
        for template in query:
            task_data = model_to_dict(
                template, exclude=["id"]
            )  # Convert template to dict
            task_data["due_date"] = calculate_due_date(
                template.due_date_days, template.type_of_due_date
            )
            task_data["current_status"] = "pending"
            periodical_tasks.append(Task(**task_data))  # Create Task instance
        Task.objects.bulk_create(periodical_tasks)

    periodical_templates = Template.objects.filter(
        recurring_interval=recurring_interval,
        recurring_task_status="Active",
    )

    bulk_create(periodical_templates)

    if recurring_interval == "monthly":
        today = localdate()
        month_string = today.strftime("%B")  # Full month name
        annual_templates = Template.objects.filter(
            recurring_interval__in=["halfyearly", "annual"],
            repeat_month=month_string,
            recurring_task_status="Active",
        )
        bulk_create(annual_templates)

    return HttpResponse(f"{recurring_interval} tasks populated.")
