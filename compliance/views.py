import pandas as pd

from django.shortcuts import render, redirect, get_object_or_404
from django.core.exceptions import PermissionDenied
from django.views.generic import DetailView, CreateView
from django.views.generic.edit import UpdateView
from django.utils.timezone import localdate, now
from django.urls import reverse_lazy, reverse
from django.http import HttpResponseForbidden
from django.db.models import Prefetch, Q
from django.contrib import messages
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.template.loader import render_to_string

from auditlog.models import LogEntry
from auditlog.context import set_actor
from django_tables2 import RequestConfig
from django_tables2.views import SingleTableView

from .models import Template, Task, TaskRemark, PublicHoliday, RegulatoryPublication
from .forms import (
    TemplateForm,
    TaskForm,
    TaskRemarkFormSet,
    DepartmentTaskForm,
    PublicHolidayUploadForm,
    ComplianceTaskForm,
    BoardMeetingBulkForm,
    TaskRemarksForm,
    PublicationForm,
)
from .tables import (
    TemplatesTable,
    TaskTable,
    TaskApprovalTable,
    PublicHolidayTable,
    PublicationTable,
)

from .utils import (
    calculate_due_date,
    calculate_conditional_board_meeting_due_date,
    send_email_async,
)


class PublicHolidayList(LoginRequiredMixin, SingleTableView):
    model = PublicHoliday
    table_class = PublicHolidayTable
    template_name = "public_holiday_list.html"
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


class TemplateDuplicateView(LoginRequiredMixin, CreateView):
    model = Template
    form_class = TemplateForm
    template_name = "template_add.html"
    success_url = reverse_lazy("template_list")

    def dispatch(self, request, *args, **kwargs):
        if request.user.user_type != "admin":
            raise PermissionDenied

        self.source_template = get_object_or_404(Template, pk=kwargs["pk"])
        return super().dispatch(request, *args, **kwargs)

    def get_initial(self):
        initial = super().get_initial()
        initial.update(self._copy_template_fields(self.source_template))
        return initial

    def get_form(self, form_class=None):
        form = super().get_form(form_class)

        form.fields["repeat_month"].initial = self.source_template.repeat_month.all()

        return form

    def form_valid(self, form):
        obj = form.save(commit=False)

        # audit fields
        obj.created_by = self.request.user
        obj.updated_by = self.request.user

        obj.pk = None  # explicit, defensive
        obj.save()

        # ✅ copy M2M fields
        obj.repeat_month.set(self.source_template.repeat_month.all())

        return redirect(self.success_url)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "Create duplicate template"
        return context

    def _copy_template_fields(self, source):
        data = {}
        for field in source._meta.fields:
            if field.name in {
                "id",
                "created_on",
                "updated_on",
                "created_by",
                "updated_by",
            }:
                continue
            data[field.name] = getattr(source, field.name)
        return data


class TemplateDetailView(LoginRequiredMixin, DetailView):
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

        response = super().form_valid(form)  # object is saved here
        self.send_task_created_email()
        return response

    def send_task_created_email(self):
        task = self.object  # saved instance

        html_content = render_to_string(
            "partials/task_creation_email_template.html", context={"task": task}
        )

        attachments = []
        if task.data_document_template:
            attachments.append(task.data_document_template.path)

        # recipients = []
        # # if task.assigned_to and task.assigned_to.email:
        # #     recipients.append(task.assigned_to.email)

        # if not recipients:
        #     return  # avoid mail errors
        send_email_async(
            subject="Subject here",
            body="Here is the message.",
            recipients=["barneedhar@uiic.co.in"],
            attachments=attachments,
            html=html_content,
        )
        print("email sent")
        # send_mail(
        #     subject=f"New Task Assigned: {task.task_name}",
        #     message=(
        #         f"A new task has been created.\n\n"
        #         f"Title: {task.task_name}\n"p[]
        #         f"Due date: {task.due_date}\n"
        #         f"Created by: {task.created_by}\n"
        #     ),
        #     from_email="policy.noreply@uiic.co.in",
        #     recipient_list=["barneedhar@uiic.co.in"],
        #     fail_silently=False,
        # )


class TaskCreateFromTemplateView(LoginRequiredMixin, CreateView):
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
            return ["task_upload_dept.html"]

        return ["task_upload_compliance.html"]

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
                outbound_data = form.cleaned_data.get("outbound_data_document")
                if inbound_email and outbound_email and outbound_data:
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


class TaskDetailView(LoginRequiredMixin, DetailView):
    model = Task
    template_name = "task_detail.html"

    context_object_name = "task"

    def dispatch(self, request, *args, **kwargs):
        self.object = self.get_object()

        if not self.object.can_view(request.user):
            raise PermissionDenied("You are not allowed to view this task.")

        return super().dispatch(request, *args, **kwargs)

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

        if not task.template_id:
            qs = Task.objects.none()
        else:
            qs = (
                Task.objects.select_related("department")
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
        context["can_mark_as_pending"] = task.can_mark_as_pending(user)
        context["can_edit"] = task.can_edit(user)
        context["revision_form"] = TaskRemarksForm(
            help_text="Please explain why revision is required."
        )
        context["approval_form"] = TaskRemarksForm(help_text="Remarks for approval.")
        context["remarks_form"] = TaskRemarksForm(help_text="Add remarks.")

        context["can_send_reminder_email"] = task.can_send_reminder_email(user)

        return context


class TemplateListView(LoginRequiredMixin, SingleTableView):
    model = Template
    table_class = TemplatesTable
    template_name = "template_table.html"
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

    DEPT_RESTRICTED_USERS = {"dept_agm", "dept_dgm", "dept_user"}

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
        "public_disclosure",
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
            return qs.filter(Q(due_date__gt=today) | Q(due_date__isnull=True))
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
    # table_class = TaskApprovalTable
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


class TaskBoardMeetingPendingListView(BaseTaskListView):
    """
    Tasks whose due date depends on board meeting
    and due date has not yet been calculated.
    """

    status = "pending"
    recurrence_url_name = "task_list_board_meeting_pending_recurrence"
    table_class = TaskApprovalTable

    def get_queryset(self):
        qs = super().get_queryset()

        return qs.filter(
            template__type_of_due_date__in=[
                "board_meeting",
                "board_meeting_conditional",
            ],
            board_meeting_date_flag=False,
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["enable_selection"] = True
        context["board_form"] = BoardMeetingBulkForm()
        return context


@login_required
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
    if request.user.user_type not in ("staff", "admin"):
        return HttpResponseForbidden("Not authorized")

    task = get_object_or_404(Task, pk=pk)

    if request.method == "POST":
        form = TaskRemarksForm(request.POST)
        if form.is_valid():
            # Update task
            task.current_status = "revision"
            task.date_of_document_received = None
            task.date_of_document_forwarded = None
            task.save(
                update_fields=[
                    "current_status",
                    "date_of_document_received",
                    "date_of_document_forwarded",
                    "updated_on",
                ]
            )

            # Save remark
            TaskRemark.objects.create(
                task=task,
                text=form.cleaned_data["remark"],
                created_by=request.user,
            )

            return redirect("task_detail", pk=task.pk)
    else:
        return HttpResponseForbidden("Invalid request")


@login_required
def task_mark_pending(request, pk):
    if request.user.user_type not in ("dept_agm", "dept_dgm"):
        return HttpResponseForbidden("Not authorized")

    task = get_object_or_404(Task, pk=pk)

    if request.method == "POST":
        form = TaskRemarksForm(request.POST)
        if form.is_valid():
            # Update task
            task.current_status = "pending"

            task.save(update_fields=["current_status", "updated_on"])

            # Save remark
            TaskRemark.objects.create(
                task=task,
                text=form.cleaned_data["remark"],
                created_by=request.user,
            )

            return redirect("task_detail", pk=task.pk)
    else:
        return HttpResponseForbidden("Invalid request")


@login_required
def task_mark_approve(request, pk):
    if request.user.user_type not in ("dept_agm", "dept_dgm"):
        return HttpResponseForbidden("Not authorized")

    task = get_object_or_404(Task, pk=pk)

    if request.method == "POST":
        form = TaskRemarksForm(request.POST)
        if form.is_valid():
            task.current_status = "review"
            task.date_of_document_received = localdate()
            task.save(
                update_fields=[
                    "current_status",
                    "updated_on",
                    "date_of_document_received",
                ]
            )
            TaskRemark.objects.create(
                task=task,
                text=form.cleaned_data["remark"],
                created_by=request.user,
            )

            return redirect("task_detail", pk=task.pk)
    else:
        return HttpResponseForbidden("Invalid request")


@login_required
def task_add_remarks(request, pk):
    task = get_object_or_404(Task, pk=pk)

    if request.method == "POST":
        form = TaskRemarksForm(request.POST)
        if form.is_valid():
            TaskRemark.objects.create(
                task=task,
                text=form.cleaned_data["remark"],
                created_by=request.user,
            )

            return redirect("task_detail", pk=task.pk)
    else:
        return HttpResponseForbidden("Invalid request")


@login_required
def bulk_set_board_meeting_date(request):
    if request.method != "POST":
        return redirect("task_list_board_meeting_pending")

    form = BoardMeetingBulkForm(request.POST)
    task_ids_raw = request.POST.get("task_ids", "")

    task_ids = [pk for pk in task_ids_raw.split(",") if pk]

    if not task_ids or not form.is_valid():
        messages.error(request, "Invalid submission.")
        return redirect("task_list_board_meeting_pending")

    board_date = form.cleaned_data["board_meeting_date"]

    tasks = Task.objects.filter(
        id__in=task_ids,
        template__type_of_due_date__in=["board_meeting"],
        board_meeting_date_flag=False,
    )

    for task in tasks:
        task.board_meeting_date = board_date
        task.due_date = calculate_due_date(
            type_of_due_date="board_meeting",
            meeting_date=board_date,
            due_date_days=task.template.due_date_days,
        )
        task.board_meeting_date_flag = True
        task.save(
            update_fields=["board_meeting_date", "due_date", "board_meeting_date_flag"]
        )

    conditional_tasks = Task.objects.filter(
        id__in=task_ids,
        template__type_of_due_date__in=["board_meeting_conditional"],
        board_meeting_date_flag=False,
    )
    for task in conditional_tasks:
        task.board_meeting_date = board_date
        task.due_date = calculate_conditional_board_meeting_due_date(task)
        task.board_meeting_date_flag = True
        task.save(
            update_fields=["board_meeting_date", "due_date", "board_meeting_date_flag"]
        )
    messages.success(request, f"{tasks.count()} task(s) updated.")
    return redirect("task_list_board_meeting_pending")


class PublicationCreateView(LoginRequiredMixin, CreateView):
    model = RegulatoryPublication
    form_class = PublicationForm
    template_name = "generic_form.html"
    success_url = reverse_lazy("publication_list")

    def dispatch(self, request, *args, **kwargs):
        if request.user.user_type not in {"admin"}:
            raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["form_title"] = "Add new IRDAI publication"
        return context

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        form.instance.updated_by = self.request.user
        return super().form_valid(form)


class PublicationUpdateView(LoginRequiredMixin, UpdateView):
    model = RegulatoryPublication
    form_class = PublicationForm
    template_name = "generic_form.html"
    success_url = reverse_lazy("publication_list")

    def dispatch(self, request, *args, **kwargs):
        if request.user.user_type not in {"admin"}:
            raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["form_title"] = "Update IRDAI publication"
        return context

    def form_valid(self, form):
        form.instance.updated_by = self.request.user
        return super().form_valid(form)


class PublicationDetailView(LoginRequiredMixin, DetailView):
    model = RegulatoryPublication
    template_name = "publication_detail.html"

    def get_queryset(self):
        return super().get_queryset().select_related("created_by", "updated_by")


class PublicationListView(LoginRequiredMixin, SingleTableView):
    model = RegulatoryPublication
    table_class = PublicationTable
    template_name = "publication_list.html"
    table_pagination = False


@login_required
def task_send_reminder_email(request, pk):
    if request.user.user_type not in ("staff", "admin"):
        return HttpResponseForbidden("Not authorized")

    task = get_object_or_404(Task, pk=pk)

    if request.method == "POST":
        # saved instance

        html_content = render_to_string(
            "partials/task_reminder_email_template.html", context={"task": task}
        )
        reminder_count = task.reminder_email_count + 1
        attachments = []
        if task.data_document_template:
            attachments.append(task.data_document_template.path)

        send_email_async(
            task=task,
            email_type="task_reminder",
            subject=f"Reminder #{reminder_count}: This is a reminder email",
            body="Here is the message.",
            recipients=["barneedhar@uiic.co.in"],
            attachments=attachments,
            html=html_content,
            user=request.user,
        )
        task.reminder_email_count += 1
        task.last_reminder_on = now()
        task.save()

        return redirect("task_detail", pk=task.pk)
    else:
        return HttpResponseForbidden("Invalid request")
