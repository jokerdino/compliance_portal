import datetime

import pandas as pd

from django.shortcuts import render, redirect, get_object_or_404
from django.core.exceptions import PermissionDenied
from django.contrib import messages
from django.views import generic
from django.views.generic import DetailView
from django.views.generic.edit import UpdateView
from django.forms.models import model_to_dict
from django.utils.timezone import now
from django.urls import reverse_lazy, reverse
from django.http import HttpResponse, HttpResponseForbidden  # , HttpResponseNotFound
from django.utils.timezone import localdate


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
    TaskFromTemplateForm,
    ComplianceTaskForm,
)
from .tables import TemplatesTable, TaskTable, TaskApprovalTable, PublicHolidayTable

# Create your views here.


def index(request):
    num_topics = Task.objects.all().count()
    compliance_topics = Task.objects.order_by("-created_on")[:5]
    context = {"num_topics": num_topics, "compliance_topics": compliance_topics}
    return render(request, "index.html", context=context)


class PublicHolidayList(SingleTableView):
    model = PublicHoliday
    table_class = PublicHolidayTable
    template_name = "compliance/public_holiday_list.html"
    table_pagination = False

    def dispatch(self, request, *args, **kwargs):
        if request.user.user_type not in {"staff", "admin"}:
            raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)


class TemplateCreateView(LoginRequiredMixin, generic.CreateView):
    model = Template
    form_class = TemplateForm
    template_name = "template_add.html"
    success_url = reverse_lazy("template_list")

    def dispatch(self, request, *args, **kwargs):
        if request.user.user_type not in {"staff", "admin"}:
            raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)


class TemplateUpdateView(LoginRequiredMixin, UpdateView):
    model = Template
    form_class = TemplateForm
    template_name = "template_add.html"
    success_url = reverse_lazy("template_list")

    def dispatch(self, request, *args, **kwargs):
        if request.user.user_type not in {"staff", "admin"}:
            raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)


class TemplateDetailView(DetailView):
    model = Template
    template_name = "template_detail.html"

    def dispatch(self, request, *args, **kwargs):
        if request.user.user_type not in {"staff", "admin"}:
            raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)


class TaskCreateView(LoginRequiredMixin, generic.CreateView):
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


class TaskCreateFromTemplateView(generic.CreateView):
    model = Task
    form_class = TaskForm
    template_name = "task_compliance_edit.html"

    def dispatch(self, request, *args, **kwargs):
        self.template_obj = get_object_or_404(Template, pk=kwargs["template_id"])
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
        return reverse("task_detail", args=[self.object.pk])


class TaskUpdateView(LoginRequiredMixin, UpdateView):
    model = Task
    # form_class = TaskForm
    template_name = "task_edit.html"

    DEPT_RESTRICTED_USERS = {"dept_user", "dept_chief_manager", "dept_dgm"}
    COMPLIANCE_DEPT_USERS = {"admin"}
    ALLOWED_STATUSES = {"pending", "revision"}

    def dispatch(self, request, *args, **kwargs):
        self.object = self.get_object()
        user = request.user

        if (
            user.user_type in self.DEPT_RESTRICTED_USERS
            and self.object.current_status not in self.ALLOWED_STATUSES
        ):
            raise PermissionDenied(
                "You are not allowed to edit this task in its current status."
            )

        return super().dispatch(request, *args, **kwargs)

    def get_form_class(self):
        user = self.request.user

        if user.user_type in self.DEPT_RESTRICTED_USERS:
            return DepartmentTaskForm

        if user.user_type not in self.DEPT_RESTRICTED_USERS:
            return ComplianceTaskForm  # TaskForm

        # Fallback (safety)
        return DepartmentTaskForm

    # 2. Dynamically Get Template Name (New method)
    def get_template_names(self):
        """
        Returns a different template name based on the user's role.
        """
        user = self.request.user

        # Check if user is authenticated (should be, due to LoginRequiredMixin, but safe check)
        # if not user.is_authenticated:
        # If user is not authenticated, let the LoginRequiredMixin handle the redirect,
        # but provide a default template name just in case.
        #   return ["compliance/task_edit_default.html"]

        if user.user_type in self.DEPT_RESTRICTED_USERS:
            # Department users see the limited document upload/remark form
            return ["task_edit.html"]
        elif user.user_type not in self.DEPT_RESTRICTED_USERS:
            return ["task_compliance_upload.html"]
        # All other users (Admin, Compliance, etc.) see the full form
        # return ["compliance/task_edit_full.html"]

    def get_success_url(self):
        return reverse_lazy("task_detail", args=[self.object.pk])

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        if self.request.POST:
            data["remarks_formset"] = TaskRemarkFormSet(
                self.request.POST,
                instance=self.object,
                queryset=TaskRemark.objects.none(),
            )
        else:
            data["remarks_formset"] = TaskRemarkFormSet(
                instance=self.object, queryset=TaskRemark.objects.none()
            )
        return data

    def form_valid(self, form):
        context = self.get_context_data()
        remarks_formset = context["remarks_formset"]
        form.instance.updated_by = self.request.user

        if form.is_valid() and remarks_formset.is_valid():
            self.object = form.save(commit=False)

            # ✅ Status changes ONLY if BOTH files are uploaded by department users
            if self.request.user.user_type in self.DEPT_RESTRICTED_USERS:
                data_doc = form.cleaned_data.get("data_document")
                inbound_mail = form.cleaned_data.get("inbound_email_communication")

                if data_doc and inbound_mail:
                    self.object.current_status = "pending_with_chief_manager"

            if self.request.user.user_type in self.COMPLIANCE_DEPT_USERS:
                outbound_email = form.cleaned_data.get("outbound_email_communication")
                if outbound_email:
                    self.object.current_status = "submitted"

            self.object.save()

            # if remarks_formset.is_valid():
            remarks = remarks_formset.save(commit=False)
            for remark in remarks:
                remark.task = self.object
                if not remark.created_by:
                    remark.created_by = self.request.user
                remark.save()
            # remarks_formset.instance = self.object
            # remarks_formset.save()
            return redirect(self.get_success_url())
        else:
            return self.form_invalid(form)


class TaskDetailView(DetailView):
    model = Task
    template_name = "compliance/task_detail.html"

    context_object_name = "task"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        task = self.object

        qs = (
            Task.objects.filter(template_id=task.template_id)
            .exclude(id=task.id)
            .order_by("-id")
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

        return context


class TemplateListView(LoginRequiredMixin, SingleTableView):
    model = Template
    table_class = TemplatesTable
    template_name = "compliance/template_table.html"
    table_pagination = False

    def dispatch(self, request, *args, **kwargs):
        if request.user.user_type not in {"staff", "admin"}:
            raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)


class TaskListView(LoginRequiredMixin, SingleTableView):
    model = Task
    table_class = TaskTable
    template_name = "compliance/task_table.html"
    table_pagination = False

    DEPT_RESTRICTED_USERS = {"dept_user", "dept_chief_manager", "dept_dgm"}
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
        """Pass the current filter type to the template for highlighting active links."""
        context = super().get_context_data(**kwargs)
        context["filter_type"] = self.kwargs.get("filter", "pending")
        # Determine the current recurrence filter (default: all)
        context["recurrence_type"] = self.kwargs.get("recurrence", "all")
        context["recurrence_choices"] = self.RECURRENCE_CHOICES

        return context

    def get_queryset(self):
        """Filter tasks based on the 'filter' query parameter."""
        filter_type = self.kwargs.get("filter", "pending")  # Default to 'pending'
        recurrence_type = self.kwargs.get("recurrence", "all")
        today = localdate()
        user = self.request.user

        qs = Task.objects.all()

        if user.user_type in self.DEPT_RESTRICTED_USERS:
            qs = qs.filter(department=user.department)

        if filter_type == "due-today":
            qs = qs.filter(due_date=today, current_status="pending")
        elif filter_type == "upcoming":
            qs = qs.filter(due_date__gt=today, current_status="pending")
        elif filter_type == "overdue":
            qs = qs.filter(due_date__lt=today, current_status="pending")
        else:  # Default: pending tasks
            qs = qs.filter(
                current_status="pending"
            )  # --- Step 3: Recurrence Type Filtering ---
        if recurrence_type != "all":
            # Note: The model field is 'type_of_compliance'
            qs = qs.filter(type_of_compliance=recurrence_type)

        return qs


class TaskSubmittedListView(LoginRequiredMixin, SingleTableView):
    model = Task
    table_class = TaskTable
    template_name = "compliance/task_submitted_list.html"
    table_pagination = False

    DEPT_RESTRICTED_USERS = {"dept_chief_manager", "dept_dgm"}
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
        """Pass the current filter type to the template for highlighting active links."""
        context = super().get_context_data(**kwargs)
        # context["filter_type"] = self.kwargs.get("filter", "pending_with_chief_manager")
        # Determine the current recurrence filter (default: all)
        context["recurrence_type"] = self.kwargs.get("recurrence", "all")
        context["recurrence_choices"] = self.RECURRENCE_CHOICES

        return context

    def get_queryset(self):
        """Filter tasks based on the 'filter' query parameter."""

        # filter_type = self.kwargs.get(
        #     "filter", "pending_with_chief_manager"
        # )  # Default to 'pending'
        recurrence_type = self.kwargs.get("recurrence", "all")
        # today = localdate()
        user = self.request.user

        qs = Task.objects.all()

        if user.user_type in self.DEPT_RESTRICTED_USERS:
            qs = qs.filter(department=user.department)

        qs = qs.filter(
            current_status="submitted"
        )  # --- Step 3: Recurrence Type Filtering ---
        if recurrence_type != "all":
            # Note: The model field is 'type_of_compliance'
            qs = qs.filter(type_of_compliance=recurrence_type)

        return qs


class TaskRevisionListView(LoginRequiredMixin, SingleTableView):
    model = Task
    table_class = TaskTable
    template_name = "compliance/task_revision_list.html"
    table_pagination = False

    DEPT_RESTRICTED_USERS = {"dept_chief_manager", "dept_dgm"}
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
        """Pass the current filter type to the template for highlighting active links."""
        context = super().get_context_data(**kwargs)
        # context["filter_type"] = self.kwargs.get("filter", "pending_with_chief_manager")
        # Determine the current recurrence filter (default: all)
        context["recurrence_type"] = self.kwargs.get("recurrence", "all")
        context["recurrence_choices"] = self.RECURRENCE_CHOICES

        return context

    def get_queryset(self):
        """Filter tasks based on the 'filter' query parameter."""

        # filter_type = self.kwargs.get(
        #     "filter", "pending_with_chief_manager"
        # )  # Default to 'pending'
        recurrence_type = self.kwargs.get("recurrence", "all")
        # today = localdate()
        user = self.request.user

        qs = Task.objects.all()

        if user.user_type in self.DEPT_RESTRICTED_USERS:
            qs = qs.filter(department=user.department)

        qs = qs.filter(
            current_status="revision"
        )  # --- Step 3: Recurrence Type Filtering ---
        if recurrence_type != "all":
            # Note: The model field is 'type_of_compliance'
            qs = qs.filter(type_of_compliance=recurrence_type)

        return qs


class TaskApprovalPendingListView(LoginRequiredMixin, SingleTableView):
    model = Task
    table_class = TaskApprovalTable
    template_name = "compliance/task_approval_list.html"
    table_pagination = False

    DEPT_RESTRICTED_USERS = {"dept_chief_manager", "dept_dgm"}
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
        """Pass the current filter type to the template for highlighting active links."""
        context = super().get_context_data(**kwargs)
        # context["filter_type"] = self.kwargs.get("filter", "pending_with_chief_manager")
        # Determine the current recurrence filter (default: all)
        context["recurrence_type"] = self.kwargs.get("recurrence", "all")
        context["recurrence_choices"] = self.RECURRENCE_CHOICES

        return context

    def get_queryset(self):
        """Filter tasks based on the 'filter' query parameter."""

        # filter_type = self.kwargs.get(
        #     "filter", "pending_with_chief_manager"
        # )  # Default to 'pending'
        recurrence_type = self.kwargs.get("recurrence", "all")
        # today = localdate()
        user = self.request.user

        qs = Task.objects.all()

        if user.user_type in self.DEPT_RESTRICTED_USERS:
            qs = qs.filter(department=user.department)

        qs = qs.filter(
            current_status="pending_with_chief_manager"
        )  # --- Step 3: Recurrence Type Filtering ---
        if recurrence_type != "all":
            # Note: The model field is 'type_of_compliance'
            qs = qs.filter(type_of_compliance=recurrence_type)

        return qs

    def post(self, request, *args, **kwargs):
        # Authorization guard
        if request.user.user_type not in self.DEPT_RESTRICTED_USERS:
            return self.handle_no_permission()

        task_ids = request.POST.getlist("select")
        action = request.POST.get("action")

        if not task_ids:
            messages.warning(request, "Please select at least one task.")
            return redirect(request.path)

        if action == "approve":
            new_status = "review"
            message = "approved and moved to Review"

        elif action == "send_back":
            new_status = "pending"
            message = "sent back to Pending"

        else:
            messages.error(request, "Invalid action.")
            return redirect(request.path)

        tasks = Task.objects.filter(
            id__in=task_ids,
            current_status="pending_with_chief_manager",
        )

        updated_count = 0

        # 🔑 Ensure actor + change tracking is recorded
        with set_actor(request.user):
            for task in tasks:
                task.current_status = new_status
                task.save(update_fields=["current_status"])
                updated_count += 1

        messages.success(request, f"{updated_count} task(s) {message}.")
        return redirect(request.path)


class TaskReviewListView(LoginRequiredMixin, SingleTableView):
    model = Task
    table_class = TaskTable
    template_name = "compliance/task_review_list.html"
    table_pagination = False

    DEPT_RESTRICTED_USERS = {"dept_chief_manager", "dept_dgm"}
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
        """Pass the current filter type to the template for highlighting active links."""
        context = super().get_context_data(**kwargs)
        # context["filter_type"] = self.kwargs.get("filter", "pending_with_chief_manager")
        # Determine the current recurrence filter (default: all)
        context["recurrence_type"] = self.kwargs.get("recurrence", "all")
        context["recurrence_choices"] = self.RECURRENCE_CHOICES

        return context

    def get_queryset(self):
        """Filter tasks based on the 'filter' query parameter."""

        # filter_type = self.kwargs.get(
        #     "filter", "pending_with_chief_manager"
        # )  # Default to 'pending'
        recurrence_type = self.kwargs.get("recurrence", "all")
        # today = localdate()
        user = self.request.user

        qs = Task.objects.all()

        if user.user_type in self.DEPT_RESTRICTED_USERS:
            qs = qs.filter(department=user.department)

        qs = qs.filter(
            current_status="review"
        )  # --- Step 3: Recurrence Type Filtering ---
        if recurrence_type != "all":
            # Note: The model field is 'type_of_compliance'
            qs = qs.filter(type_of_compliance=recurrence_type)

        return qs

    def post(self, request, *args, **kwargs):
        task_ids = request.POST.getlist("select")
        action = request.POST.get("action")

        if not task_ids:
            messages.warning(request, "Please select at least one task.")
            return redirect(request.path)

        if action == "approve":
            new_status = "submitted"
            message = "approved and moved to Review"

        elif action == "send_back":
            new_status = "revision"
            message = "sent back to Pending"

        else:
            messages.error(request, "Invalid action.")
            return redirect(request.path)

        tasks = Task.objects.filter(
            id__in=task_ids,
            current_status="review",
        )

        updated_count = 0

        # 🔑 This ensures actor + timestamp are recorded in auditlog
        with set_actor(request.user):
            for task in tasks:
                task.current_status = new_status
                task.save(update_fields=["current_status"])
                updated_count += 1

        messages.success(request, f"{updated_count} task(s) {message}.")
        return redirect(request.path)


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
        return start_date + datetime.timedelta(days=due_date_days)
    else:
        days_added = 0

        current_date = start_date
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
                ],
            )  # Convert template to dict
            task_data["due_date"] = calculate_due_date(
                template.due_date_days, template.type_of_due_date
            )
            task_data["created_by_id"] = 1
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
    task.save(update_fields=["current_status"])

    return redirect("task_detail", pk=task.pk)
