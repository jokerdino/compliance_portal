from django.db import models
from django.urls import reverse
from django.conf import settings
from django.core.validators import MinValueValidator

from auditlog.registry import auditlog

from accounts.models import DEPARTMENT


class Month(models.Model):
    month_name = models.CharField(unique=True)

    def __str__(self):
        return self.month_name


class PublicHoliday(models.Model):
    date_of_holiday = models.DateField(unique=True)
    name_of_holiday = models.CharField(max_length=200)


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
        choices=(("calendar", "Calendar"), ("working", "Working")),
    )  # calendar days or working days
    recurring_task_status = models.CharField(
        max_length=100, choices=(("Active", "Active"), ("Inactive", "Inactive"))
    )  # active or inactive
    department = models.CharField(choices=DEPARTMENT)  # department
    uiic_contact = models.CharField(max_length=1000)  # email from uiic
    compliance_contact = models.CharField(max_length=100)  # email to send to compliance
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
    repeat_month = models.ManyToManyField(Month, blank=True, null=True)

    return_number = models.CharField(max_length=100, blank=True, null=True)
    circular_document = models.FileField(blank=True, null=True)
    data_document_template = models.FileField(blank=True, null=True)

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
        return reverse("template_detail", args=[str(self.id)])


# Create your models here.
class Task(models.Model):
    task_name = models.CharField(max_length=100)
    due_date = models.DateField(
        blank=False,
        null=False,
    )

    current_status = models.CharField(
        max_length=100,
        default="pending",
        null=False,
        blank=False,
        choices=(
            ("pending", "Pending"),
            ("pending_with_chief_manager", "To be approved"),
            ("review", "In review"),
            ("revision", "Revised document to be uploaded"),
            ("submitted", "Submitted"),
        ),
    )  # submitted  or pending

    department = models.CharField(
        choices=DEPARTMENT, max_length=100, blank=False, null=False
    )  # department
    uiic_contact = models.CharField(
        max_length=1000, blank=True, null=True
    )  # email from uiic
    compliance_contact = models.CharField(
        max_length=100, blank=True, null=True
    )  # email to send to compliance
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
        ),
    )  # adhoc/daily/weekly/monthly/quarterly/etc

    return_number = models.CharField(max_length=100, blank=True, null=True)
    circular_document = models.FileField(blank=True, null=True)
    inbound_email_communication = models.FileField(blank=True, null=True)
    outbound_email_communication = models.FileField(blank=True, null=True)
    data_document_template = models.FileField(blank=True, null=True)
    data_document = models.FileField(blank=True, null=True)
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
    )
    date_of_document_forwarded = models.DateField(
        blank=True,
        null=True,
        default=None,
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
        return reverse("task_detail", args=[str(self.id)])


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


auditlog.register(Template)
auditlog.register(Task)
