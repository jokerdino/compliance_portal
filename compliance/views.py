import datetime

import pandas as pd

from django.shortcuts import render, redirect, get_object_or_404
from django.core.exceptions import PermissionDenied
from django.views.generic import DetailView, CreateView
from django.views.generic.edit import UpdateView
from django.forms.models import model_to_dict
from django.utils.timezone import now, localdate
from django.urls import reverse_lazy, reverse
from django.http import HttpResponse, HttpResponseForbidden
from django.db.models import Prefetch
from django.contrib import messages
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin

from auditlog.models import LogEntry
from auditlog.context import set_actor
from django_tables2 import RequestConfig
from django_tables2.views import SingleTableView

from .models import Template, Task, TaskRemark, Month, PublicHoliday
from .forms import (
    TemplateForm,
    TaskForm,
    TaskRemarkFormSet,
    DepartmentTaskForm,
    PublicHolidayUploadForm,
    ComplianceTaskForm,
)
from .tables import TemplatesTable, TaskTable, TaskApprovalTable, PublicHolidayTable


class PublicHolidayList(SingleTableView):
    model = PublicHoliday
    table_class = PublicHolidayTable
    template_name = "compliance/public_holiday_list.html"
    table_pagination = False

    def dispatch(self, request, *args, **kwargs):
        if request.user.user_type not in {"staff", "admin"}:
            raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)


class TemplateCreateView(LoginRequiredMixin, CreateView):
    model = Template
    form_class = TemplateForm
    template_name = "template_add.html"
    success_url = reverse_lazy("template_list")

    def dispatch(self, request, *args, **kwargs):
        if request.user.user_type not in {"admin"}:
            raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "Add new template"
        return context

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        form.instance.updated_by = self.request.user
        return super().form_valid(form)


class TemplateUpdateView(LoginRequiredMixin, UpdateView):
    model = Template
    form_class = TemplateForm
    template_name = "template_add.html"
    success_url = reverse_lazy("template_list")

    def dispatch(self, request, *args, **kwargs):
        if request.user.user_type not in {"admin"}:
            raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "Update template"
        return context

    def form_valid(self, form):
        form.instance.updated_by = self.request.user
        return super().form_valid(form)


class TemplateDetailView(DetailView):
    model = Template
    template_name = "template_detail.html"

    def get_queryset(self):
        return super().get_queryset().select_related("created_by", "updated_by")

    def dispatch(self, request, *args, **kwargs):
        if request.user.user_type not in {"viewer", "admin"}:
            raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)


class TaskCreateView(LoginRequiredMixin, CreateView):
    model = Task
    form_class = TaskForm
    template_name = "task_compliance_edit.html"
    success_url = reverse_lazy("task_list", kwargs={"filter": "due-today"})

    def dispatch(self, request, *args, **kwargs):
        if request.user.user_type not in {"staff", "admin"}:
            raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        form.instance.updated_by = self.request.user
        return super().form_valid(form)


class TaskCreateFromTemplateView(CreateView):
    model = Task
    form_class = TaskForm
    template_name = "task_compliance_edit.html"

    def dispatch(self, request, *args, **kwargs):
        self.template_obj = get_object_or_404(Template, pk=kwargs["pk"])
        return super().dispatch(request, *args, **kwargs)

    def get_initial(self):
        initial = super().get_initial()
        initial.update(
            {
                "task_name": self.template_obj.task_name,
                "department": self.template_obj.department,
                "priority": self.template_obj.priority,
                "uiic_contact": self.template_obj.uiic_contact,
                "compliance_contact": self.template_obj.compliance_contact,
                "circular_url": self.template_obj.circular_url,
                "circular_details": self.template_obj.circular_details,
                "type_of_compliance": self.template_obj.type_of_compliance,
                "return_number": self.template_obj.return_number,
                "circular_document": self.template_obj.circular_document,
                "data_document_template": self.template_obj.data_document_template,
            }
        )
        return initial

    def form_valid(self, form):
        form.instance.template = self.template_obj
        form.instance.created_by = self.request.user
        return super().form_valid(form)

    def get_success_url(self):
        return reverse("task_detail", kwargs={"pk": self.object.pk})


class TaskUpdateView(LoginRequiredMixin, UpdateView):
    model = Task

    DEPT_RESTRICTED_USERS = {"dept_user", "dept_agm", "dept_dgm"}
    COMPLIANCE_DEPT_USERS = {"admin"}

    def get_queryset(self):
        return (
            super()
            .get_queryset()
            .select_related(
                "created_by",
                "updated_by",
                "department",
                "template",
            )
            .prefetch_related(
                Prefetch(
                    "remarks",
                    queryset=TaskRemark.objects.select_related("created_by").order_by(
                        "created_at"
                    ),
                )
            )
        )

    def dispatch(self, request, *args, **kwargs):
        self.object = self.get_object()

        if not self.object.can_edit(request.user):
            raise PermissionDenied("You are not allowed to edit this task.")

        return super().dispatch(request, *args, **kwargs)

    def get_form_class(self):
        user = self.request.user

        if user.user_type in self.DEPT_RESTRICTED_USERS:
            return DepartmentTaskForm

        return ComplianceTaskForm

    def get_template_names(self):
        """
        Returns a different template name based on the user's role.
        """
        user = self.request.user

        if user.user_type in self.DEPT_RESTRICTED_USERS:
            return ["task_edit.html"]

        return ["task_compliance_upload.html"]

    def get_success_url(self):
        return reverse_lazy("task_detail", args=[self.object.pk])

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        task_ct = ContentType.objects.get_for_model(Task)
        task = self.object
        context["status_audit_logs"] = (
            LogEntry.objects.filter(
                content_type=task_ct,
                object_id=str(task.pk),
                changes__has_key="current_status",
            )
            .select_related("actor")
            .order_by("-timestamp")
        )
        if self.request.POST:
            context["remarks_formset"] = TaskRemarkFormSet(
                self.request.POST,
                instance=self.object,
                queryset=TaskRemark.objects.none(),
            )
        else:
            context["remarks_formset"] = TaskRemarkFormSet(
                instance=self.object, queryset=TaskRemark.objects.none()
            )
        return context

    def form_valid(self, form):
        context = self.get_context_data()
        remarks_formset = context["remarks_formset"]
        form.instance.updated_by = self.request.user

        if remarks_formset.is_valid():
            self.object = form.save(commit=False)

            if self.request.user.user_type in self.DEPT_RESTRICTED_USERS:
                data_doc = form.cleaned_data.get("data_document")

                if data_doc:
                    self.object.current_status = "to_be_approved"

            if self.request.user.user_type in self.COMPLIANCE_DEPT_USERS:
                inbound_email = form.cleaned_data.get("inbound_email_communication")
                outbound_email = form.cleaned_data.get("outbound_email_communication")
                if inbound_email and outbound_email:
                    self.object.current_status = "submitted"
                    self.object.date_of_document_forwarded = localdate()

            self.object.save()

            remarks = remarks_formset.save(commit=False)
            for remark in remarks:
                remark.task = self.object
                if not remark.created_by:
                    remark.created_by = self.request.user
                remark.save()

            return redirect(self.get_success_url())
        else:
            return self.form_invalid(form)


class TaskDetailView(DetailView):
    model = Task
    template_name = "compliance/task_detail.html"

    context_object_name = "task"

    def get_queryset(self):
        return (
            super()
            .get_queryset()
            .select_related(
                "created_by",
                "updated_by",
                "department",
                "template",
            )
            .prefetch_related(
                Prefetch(
                    "remarks",
                    queryset=TaskRemark.objects.select_related("created_by").order_by(
                        "created_at"
                    ),
                )
            )
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        task = self.object
        user = self.request.user

        qs = (
            Task.objects.select_related(
                "department",
            )
            .filter(template_id=task.template_id)
            .exclude(id=task.id)
            .order_by("due_date")
        )

        table = TaskTable(qs)
        RequestConfig(self.request, paginate={"per_page": 100}).configure(table)

        context["related_task_table"] = table

        task_ct = ContentType.objects.get_for_model(Task)

        context["status_audit_logs"] = (
            LogEntry.objects.filter(
                content_type=task_ct,
                object_id=str(task.pk),
                changes__has_key="current_status",
            )
            .select_related("actor")
            .order_by("-timestamp")
        )
        context["can_request_revision"] = task.can_request_revision(user)
        context["can_edit"] = task.can_edit(user)

        return context


class TemplateListView(LoginRequiredMixin, SingleTableView):
    model = Template
    table_class = TemplatesTable
    template_name = "compliance/template_table.html"
    table_pagination = False

    def dispatch(self, request, *args, **kwargs):
        if request.user.user_type not in {"viewer", "admin"}:
            raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self):
        return (
            super()
            .get_queryset()
            .select_related(
                "department",
            )
        )


class BaseTaskListView(LoginRequiredMixin, SingleTableView):
    model = Task
    table_class = TaskTable
    table_pagination = False

    status = None
    template_name = "task_list.html"
    recurrence_url_name = None
    date_filter = None

    DEPT_RESTRICTED_USERS = {"dept_agm", "dept_dgm"}

    RECURRENCE_CHOICES = [
        "all",
        "adhoc",
        "daily",
        "weekly",
        "fortnightly",
        "monthly",
        "quarterly",
        "halfyearly",
        "annual",
    ]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["recurrence_type"] = self.kwargs.get("recurrence", "all")
        context["recurrence_choices"] = self.RECURRENCE_CHOICES
        context["recurrence_url_name"] = self.recurrence_url_name
        context["status"] = self.status
        context["filter"] = self.kwargs.get("filter")
        return context

    def base_queryset(self):
        qs = Task.objects.select_related("department")
        user = self.request.user

        if user.user_type in self.DEPT_RESTRICTED_USERS:
            qs = qs.filter(department=user.department)

        return qs

    def apply_status_filter(self, qs):
        if self.status:
            qs = qs.filter(current_status=self.status)
        return qs

    def apply_recurrence_filter(self, qs):
        recurrence = self.kwargs.get("recurrence", "all")
        if recurrence != "all":
            qs = qs.filter(type_of_compliance=recurrence)
        return qs

    def apply_date_filter(self, qs):
        today = localdate()

        if self.date_filter == "due-today":
            return qs.filter(due_date=today)
        elif self.date_filter == "upcoming":
            return qs.filter(due_date__gt=today)
        elif self.date_filter == "overdue":
            return qs.filter(due_date__lt=today)

        return qs

    def get_queryset(self):
        qs = self.base_queryset()
        qs = self.apply_status_filter(qs)
        qs = self.apply_recurrence_filter(qs)
        qs = self.apply_date_filter(qs)
        return qs


class TaskSubmittedListView(BaseTaskListView):
    status = "submitted"
    recurrence_url_name = "task_list_filtered_recurrence_submitted"


class TaskRevisionListView(BaseTaskListView):
    status = "revision"
    recurrence_url_name = "task_list_filtered_recurrence_revision"


class TaskReviewListView(BaseTaskListView):
    status = "review"
    recurrence_url_name = "task_list_filtered_recurrence_review"


class TaskApprovalPendingListView(BaseTaskListView):
    table_class = TaskApprovalTable
    status = "to_be_approved"
    recurrence_url_name = "task_list_filtered_recurrence_approval_pending"

    def post(self, request, *args, **kwargs):
        if request.user.user_type not in self.DEPT_RESTRICTED_USERS:
            return self.handle_no_permission()

        task_ids = request.POST.getlist("select")
        action = request.POST.get("action")

        if not task_ids:
            messages.warning(request, "Please select at least one task.")
            return redirect(request.path)

        transitions = {
            "approve": ("review", "approved and moved to Review"),
            "send_back": ("pending", "sent back to Pending"),
        }

        if action not in transitions:
            messages.error(request, "Invalid action.")
            return redirect(request.path)

        new_status, message = transitions[action]

        tasks = Task.objects.filter(
            id__in=task_ids,
            current_status=self.status,
        )
        updated = 0
        with set_actor(request.user):
            for task in tasks:
                task.current_status = new_status
                task.date_of_document_received = localdate()
                task.save(update_fields=["current_status", "date_of_document_received"])
                updated += 1
        messages.success(request, f"{updated} task(s) {message}.")
        return redirect(request.path)


class TaskListView(BaseTaskListView):
    status = "pending"
    recurrence_url_name = "task_list_filtered_recurrence"

    def dispatch(self, request, *args, **kwargs):
        filter_type = kwargs.get("filter", "pending")
        self.date_filter = filter_type if filter_type != "pending" else None
        return super().dispatch(request, *args, **kwargs)


def is_working_day(date):
    # weekday(): 0 = Monday, 6 = Sunday
    if date.weekday() >= 5:  # Saturday or Sunday
        return False

    if PublicHoliday.objects.filter(date_of_holiday=date).exists():
        return False

    return True


def calculate_due_date(due_date_days, type_of_due_date):
    """Calculate due date based on due_date_days and type (calendar/working days)."""
    start_date = now().date()

    if type_of_due_date == "calendar":
        return start_date + datetime.timedelta(days=due_date_days - 1)
    else:
        current_date = start_date
        days_added = 1 if is_working_day(current_date) else 0
        while days_added < due_date_days:
            current_date += datetime.timedelta(days=1)
            if is_working_day(current_date):
                days_added += 1
        return current_date


def populate_templates(request, recurring_interval):
    def bulk_create(query):
        periodical_tasks = []
        for template in query:
            task_data = model_to_dict(
                template,
                exclude=[
                    "id",
                    "repeat_month",
                    "created_by",
                    "updated_by",
                    "due_date_days",
                    "type_of_due_date",
                    "recurring_task_status",
                    "recurring_interval",
                    "repeat_month",
                    "department",
                ],
            )  # Convert template to dict
            task_data["due_date"] = calculate_due_date(
                template.due_date_days, template.type_of_due_date
            )
            task_data["created_by_id"] = 1
            task_data["department_id"] = template.department_id
            task_data["current_status"] = "pending"
            task_data["template"] = template
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
            repeat_month__month_name=month_string,
            recurring_task_status="Active",
        ).distinct()
        bulk_create(annual_templates)

    return HttpResponse(f"{recurring_interval} tasks populated.")


def seed_data_view(request):
    # Your list of data
    data_to_seed = [
        {"month_name": "January"},
        {"month_name": "February"},
        {"month_name": "March"},
        {"month_name": "April"},
        {"month_name": "May"},
        {"month_name": "June"},
        {"month_name": "July"},
        {"month_name": "August"},
        {"month_name": "September"},
        {"month_name": "October"},
        {"month_name": "November"},
        {"month_name": "December"},
    ]

    # Check if data already exists to prevent duplicate seeding
    if Month.objects.count() == 0:
        objects_to_create = [Month(**data_item) for data_item in data_to_seed]
        Month.objects.bulk_create(objects_to_create)
        return HttpResponse("Database seeded with initial data!")


def upload_public_holidays(request):
    if request.method == "POST":
        form = PublicHolidayUploadForm(request.POST, request.FILES)

        if form.is_valid():
            excel_file = form.cleaned_data["file"]

            try:
                df = pd.read_excel(excel_file)

                # Normalize column names
                df.columns = df.columns.str.strip().str.lower()

                required_cols = {"date_of_holiday", "name_of_holiday"}
                if not required_cols.issubset(df.columns):
                    messages.error(
                        request,
                        "Excel must contain columns: date_of_holiday, name_of_holiday",
                    )
                    return redirect("upload_public_holidays")

                # Convert date column (Indian format safe)
                df["date_of_holiday"] = pd.to_datetime(
                    df["date_of_holiday"], dayfirst=True
                ).dt.date

                holidays = [
                    PublicHoliday(
                        date_of_holiday=row["date_of_holiday"],
                        name_of_holiday=row["name_of_holiday"],
                    )
                    for _, row in df.iterrows()
                ]

                PublicHoliday.objects.bulk_create(
                    holidays,
                    ignore_conflicts=True,  # avoids duplicate dates
                )

                messages.success(
                    request,
                    f"{len(holidays)} holidays imported successfully",
                )

                return redirect("upload_public_holidays")

            except Exception as e:
                messages.error(request, f"Error processing file: {e}")

    else:
        form = PublicHolidayUploadForm()

    return render(
        request,
        "upload_public_holidays.html",
        {"form": form},
    )


@login_required
def task_mark_revision(request, pk):
    if request.method != "POST":
        return HttpResponseForbidden("Invalid request method")

    if request.user.user_type not in ("staff", "admin"):
        return HttpResponseForbidden("Not authorized")

    task = get_object_or_404(Task, pk=pk)

    task.current_status = "revision"
    task.date_of_document_received = None
    task.date_of_document_forwarded = None
    task.save(
        update_fields=[
            "current_status",
            "date_of_document_received",
            "date_of_document_forwarded",
        ]
    )

    return redirect("task_detail", pk=task.pk)
