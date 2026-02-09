from django.db import models
from django.urls import reverse
from django.conf import settings
from django.core.validators import MinValueValidator
from django.utils import timezone

from auditlog.registry import auditlog

from accounts.models import Department

from .mail_utils import parse_email_list


class Month(models.Model):
    month_name = models.CharField(unique=True)

    def __str__(self):
        return self.month_name


class PublicHoliday(models.Model):
    date_of_holiday = models.DateField(unique=True)
    name_of_holiday = models.CharField(max_length=200)

    def __str__(self):
        return self.name_of_holiday

    class Meta:
        ordering = ["date_of_holiday"]


class Template(models.Model):
    task_name = models.CharField(max_length=100)

    due_date_days = models.PositiveIntegerField(
        default=1,
        null=False,
        blank=False,
        validators=[MinValueValidator(1)],
        help_text="Number of days must be at least 1",
    )  # in days
    type_of_due_date = models.CharField(
        max_length=100,
        default="calendar",
        blank=False,
        null=False,
        choices=(
            ("calendar", "Calendar"),
            ("working", "Working"),
            ("board_meeting", "Board meeting"),
            ("board_meeting_conditional", "Board meeting (conditional)"),
        ),
    )
    alternate_due_date_days = models.PositiveIntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(1)],
        help_text="To be entered if due date type is board meeting conditional (e.g. 180 days)",
    )

    conditional_operator = models.CharField(
        max_length=20,
        null=True,
        blank=True,
        choices=(
            ("earlier", "Whichever is earlier"),
            ("later", "Whichever is later"),
        ),
    )
    recurring_task_status = models.CharField(
        max_length=100, choices=(("Active", "Active"), ("Inactive", "Inactive"))
    )  # active or inactive
    department = models.ForeignKey(Department, on_delete=models.PROTECT)
    uiic_contact = models.CharField(max_length=1000)  # email from uiic
    compliance_contact = models.CharField(max_length=100)  # email to send to compliance
    circular_url = models.URLField(
        verbose_name="Source circular URL", max_length=1000, blank=True, null=True
    )
    circular_details = models.CharField(
        max_length=100, blank=True, null=True
    )  # circular or regulation or email details
    type_of_compliance = models.CharField(
        max_length=100,
        blank=False,
        null=False,
        choices=(
            ("daily", "Daily"),
            ("weekly", "Weekly"),
            ("fortnightly", "Fortnightly"),
            ("monthly", "Monthly"),
            ("quarterly", "Quarterly"),
            ("halfyearly", "Halfyearly"),
            ("annual", "Annual"),
            ("public_disclosure", "Public disclosure"),
        ),
    )  # adhoc/daily/weekly/monthly/quarterly/etc
    recurring_interval = models.CharField(
        max_length=100,
        blank=False,
        null=False,
        choices=(
            ("daily", "Daily"),
            ("weekly", "Weekly"),
            ("fortnightly", "Fortnightly"),
            ("monthly", "Monthly"),
            ("quarterly", "Quarterly"),
            ("halfyearly", "Halfyearly"),
            ("annual", "Annual"),
        ),
    )  # repeat every month/week etc
    repeat_month = models.ManyToManyField(Month, blank=True)

    return_number = models.CharField(max_length=100, blank=True, null=True)
    circular_document = models.FileField(
        blank=True, null=True, upload_to="circulars_document/"
    )
    data_document_template = models.FileField(
        blank=True, null=True, upload_to="data_document_template/"
    )

    priority = models.IntegerField(
        blank=True,
        choices=((3, "High"), (2, "Medium"), (1, "Low")),
        default=2,
    )  # high/medium/low

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name="template_created",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    created_on = models.DateTimeField(auto_now_add=True)

    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name="template_updated",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    updated_on = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.task_name

    def get_absolute_url(self):
        return reverse("template_detail", kwargs={"pk": self.pk})


class Task(models.Model):
    task_name = models.CharField(max_length=100)
    board_meeting_date = models.DateField(
        null=True,
        blank=True,
        help_text="Date of board meeting if applicable",
    )
    due_date = models.DateField(
        blank=False,
        null=True,
    )
    board_meeting_date_flag = models.BooleanField(default=False)

    current_status = models.CharField(
        max_length=100,
        default="pending",
        null=False,
        blank=False,
        choices=(
            ("pending", "Pending"),
            ("to_be_approved", "To be approved"),
            ("review", "In review"),
            ("revision", "Revised document to be uploaded"),
            ("submitted", "Submitted"),
        ),
    )  # submitted  or pending

    department = models.ForeignKey(Department, on_delete=models.PROTECT)
    uiic_contact = models.CharField(
        max_length=1000, blank=True, null=True
    )  # email from uiic
    compliance_contact = models.CharField(
        max_length=100, blank=True, null=True
    )  # email to send to compliance
    circular_url = models.URLField(
        verbose_name="Source circular URL", max_length=1000, blank=True, null=True
    )
    circular_details = models.CharField(
        max_length=100, blank=True, null=True
    )  # circular or regulation or email details
    type_of_compliance = models.CharField(
        max_length=100,
        blank=False,
        null=False,
        choices=(
            ("adhoc", "Adhoc"),
            ("daily", "Daily"),
            ("weekly", "Weekly"),
            ("fortnightly", "Fortnightly"),
            ("monthly", "Monthly"),
            ("quarterly", "Quarterly"),
            ("halfyearly", "Halfyearly"),
            ("annual", "Annual"),
            ("public_disclosure", "Public disclosure"),
        ),
    )  # adhoc/daily/weekly/monthly/quarterly/etc

    return_number = models.CharField(max_length=100, blank=True, null=True)
    circular_document = models.FileField(
        blank=True, null=True, upload_to="circulars_document/"
    )
    inbound_email_communication = models.FileField(
        blank=True, null=True, upload_to="inbound_email/"
    )
    outbound_email_communication = models.FileField(
        blank=True, null=True, upload_to="outbound_email/"
    )
    data_document_template = models.FileField(
        blank=True, null=True, upload_to="data_document_template/"
    )
    data_document = models.FileField(
        verbose_name="Inbound data document",
        blank=True,
        null=True,
        upload_to="data_document/",
    )
    outbound_data_document = models.FileField(
        blank=True, null=True, upload_to="outbound_data_document/"
    )
    priority = models.IntegerField(
        blank=True,
        null=True,
        choices=((3, "High"), (2, "Medium"), (1, "Low")),
        default=2,
    )  # high/medium/low
    date_of_document_received = models.DateField(
        blank=True,
        null=True,
        default=None,
        verbose_name="Date of document received",
    )
    date_of_document_forwarded = models.DateField(
        blank=True,
        null=True,
        default=None,
        verbose_name="Date of submission to IRDA",
    )

    reason_for_delay = models.TextField(
        blank=True, null=True, help_text="Mandatory if task is submitted after due date"
    )

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name="tasks_created",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    created_on = models.DateTimeField(auto_now_add=True)

    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name="tasks_updated",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    updated_on = models.DateTimeField(auto_now=True, null=True)

    template = models.ForeignKey(
        Template,
        related_name="template",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
    )

    def __str__(self):
        return self.task_name

    def get_absolute_url(self):
        return reverse("task_detail", kwargs={"pk": self.pk})

    REVIEWABLE_STATUSES = {"review", "submitted"}
    EDITABLE_STATUSES = {"pending", "revision"}

    def can_request_revision(self, user) -> bool:
        """
        Can the given user request a revision for this task?
        """
        if not user or not user.is_authenticated:
            return False

        return (
            user.user_type == "admin"
            and self.current_status in self.REVIEWABLE_STATUSES
        )

    def can_mark_as_pending(self, user) -> bool:
        """
        Can the given user mark this task as pending?
        """
        if not user or not user.is_authenticated:
            return False

        return (
            user.user_type in ["dept_agm", "dept_dgm"]
            and self.current_status == "to_be_approved"
        )

    def can_edit(self, user) -> bool:
        """
        Can the given user edit this task?
        """
        if not user or not user.is_authenticated:
            return False

        if (
            user.user_type in {"dept_user", "dept_agm", "dept_dgm"}
            and self.current_status in self.EDITABLE_STATUSES
        ):
            return True

        if user.user_type == "admin" and self.current_status != "submitted":
            return True

        return False

    def uiic_emails(self) -> list[str]:
        return parse_email_list(self.uiic_contact)

    def is_overdue(self):
        if not self.due_date:
            return False
        return self.due_date < timezone.now().date()

    class Meta:
        ordering = ["due_date", "priority"]


class TaskRemark(models.Model):
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name="remarks")
    text = models.TextField()
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True
    )
    created_at = models.DateTimeField(auto_now_add=True)

    @property
    def creator_name(self):
        if self.created_by:
            return self.created_by.username
        return "Unknown"

    def __str__(self):
        return f"Remark for {self.task.task_name} at {self.created_at}"


class RegulatoryPublication(models.Model):
    CATEGORY_CHOICES = {
        "REGULATIONS": "Regulations",
        "CIRCULAR": "Circular",
        "NOTIFICATION": "Notification",
        "GUIDELINES": "Guidelines",
        "ORDER": "Order",
        "NOTICE": "Notice",
        "EXPOSURE_DRAFT": "Exposure Draft",
        "OTHER_COMMUNICATION": "Other communication",
    }
    category = models.CharField(null=False, blank=False, choices=CATEGORY_CHOICES)
    title = models.CharField(null=False, blank=False)
    url_of_publication = models.URLField(
        verbose_name="URL of publication", null=True, blank=True
    )
    publication_document = models.FileField(
        null=True, blank=True, upload_to="regulatory_publication"
    )
    date_of_publication = models.DateField(
        verbose_name="Date of publication in IRDAI website", null=False, blank=False
    )
    effective_from = models.DateField(null=False, blank=False)
    remarks = models.TextField(null=True, blank=True)

    # meta columns
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name="publication_created",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    created_on = models.DateTimeField(auto_now_add=True)

    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name="publication_updated",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    updated_on = models.DateTimeField(auto_now=True, null=True)


auditlog.register(Template)
auditlog.register(Task)
