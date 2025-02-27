import datetime
from django.shortcuts import render, redirect
from .models import Template, Task
from .forms import TemplateForm, TaskForm
from django.views import generic
from django.views.generic.edit import UpdateView
from django.forms.models import model_to_dict
from django.utils.timezone import now
from django.urls import reverse_lazy
from django.http import HttpResponse  # , HttpResponseNotFound
# Create your views here.


def index(request):
    num_topics = Task.objects.all().count()
    compliance_topics = Task.objects.order_by("-created_on")[:5]
    context = {"num_topics": num_topics, "compliance_topics": compliance_topics}
    return render(request, "index.html", context=context)


# def recurring_task_add(request):
#     if request.method == "POST":
#         form = RecurringTaskForm(request.POST)
#         if form.is_valid():
#             print("hello")
#             # recurring_task = RecurringTask(*form)
#             # recurring_task.save()
#             form.save()
#     # return index(request)
#     else:
#         form = RecurringTaskForm()
#     context = {"form": form}
#     return render(request, "recurring_task_add.html", context=context)


class TemplateCreateView(generic.CreateView):
    model = Template
    form_class = TemplateForm
    template_name = "template_add.html"
    # success_url = reverse_lazy("template_list")

    # def form_valid(self, form):
    #     obj = form.save(commit=False)
    #     # obj.created_by = self.request.user
    #     obj.save()
    #     #        print(obj)

    #     obj_dict = model_to_dict(obj, exclude=["id"])
    #     Task.objects.create(**obj_dict).save()

    #     return redirect(self.success_url)


class TemplateUpdateView(UpdateView):
    model = Template
    form_class = TemplateForm
    template_name = "template_add.html"
    success_url = reverse_lazy("template_list")


class TaskCreateView(generic.CreateView):
    model = Task
    form_class = TaskForm
    template_name = "template_add.html"


class TaskUpdateView(UpdateView):
    model = Task
    form_class = TaskForm
    # TODO: to verify or update the template
    template_name = "template_add.html"
    success_url = reverse_lazy("task_list")


class TemplateListView(generic.ListView):
    model = Template


class TaskListView(generic.ListView):
    model = Task


def calculate_due_date(due_date_days, type_of_due_date):
    """Calculate due date based on due_date_days and type (calendar/working days)."""
    start_date = now().date()

    if type_of_due_date == "Calendar":
        return start_date + datetime.timedelta(days=due_date_days)
    else:
        days_added = 0
        current_date = start_date
        while days_added < due_date_days:
            current_date += datetime.timedelta(days=1)
            if current_date.weekday() < 5:  # Monday-Friday (0-4)
                days_added += 1
        return current_date


def populate_daily_templates(request):
    daily_templates = Template.objects.filter(recurring_interval="Daily")
    daily_tasks = []
    for template in daily_templates:
        task_data = model_to_dict(template, exclude=["id"])  # Convert template to dict
        task_data["due_date"] = calculate_due_date(
            template.due_date_days, template.type_of_due_date
        )

        daily_tasks.append(Task(**task_data))  # Create Task instance

    Task.objects.bulk_create(daily_tasks)

    return HttpResponse("Daily tasks populated.")


def populate_weekly_templates():
    pass
