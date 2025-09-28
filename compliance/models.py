from django.db import models
from django.urls import reverse

from auditlog.registry import auditlog


# Create your models here.
class Task(models.Model):
    task_name = models.CharField(max_length=100)
    due_date = models.DateField(
        blank=True,
        null=True,
        default=None,
    )
    due_date_days = models.IntegerField(default=0)  # in days
    type_of_due_date = models.CharField(max_length=100)  # calendar days or working days
    current_status = models.CharField(
        max_length=100, choices=(("pending", "Pending"), ("submitted", "Submitted"))
    )  # submitted  or pending
    recurring_task_status = models.CharField(
        max_length=100, choices=(("Active", "Active"), ("Inactive", "Inactive"))
    )  # active or inactive
    department = models.CharField(max_length=100)  # department
    uiic_contact = models.CharField(max_length=1000)  # email from uiic
    compliance_contact = models.CharField(max_length=100)  # email to send to compliance
    circular_details = models.CharField(
        max_length=100, blank=True
    )  # circular or regulation or email details
    type_of_compliance = models.CharField(
        max_length=100,
        blank=True,
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
    recurring_interval = models.CharField(
        max_length=100, blank=True
    )  # repeat every month/week etc
    repeat_month = models.CharField(
        max_length=100,
        blank=True,
        choices=(
            ("January", "January"),
            ("February", "February"),
            ("March", "March"),
            ("April", "April"),
            ("May", "May"),
            ("June", "June"),
            ("July", "July"),
            ("August", "August"),
            ("September", "September"),
            ("October", "October"),
            ("November", "November"),
            ("December", "December"),
        ),
    )  # repeat month for annual interval
    return_number = models.CharField(max_length=100, blank=True)
    circular_document = models.FileField(blank=True)
    inbound_email_communication = models.FileField(blank=True)
    outbound_email_communication = models.FileField(blank=True)
    data_document = models.FileField(blank=True)
    priority = models.IntegerField(
        blank=True,
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

    created_by = models.CharField(max_length=100, blank=True, default="")
    created_on = models.DateTimeField(auto_now_add=True)

    updated_by = models.CharField(max_length=100, blank=True, default="")
    updated_on = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.task_name

    def get_absolute_url(self):
        return reverse("task_detail", args=[str(self.id)])


class Template(models.Model):
    task_name = models.CharField(max_length=100)

    due_date_days = models.IntegerField(default=0)  # in days
    type_of_due_date = models.CharField(
        max_length=100,
        default="calendar",
        blank=True,
        choices=(("calendar", "Calendar"), ("working", "Working")),
    )  # calendar days or working days
    recurring_task_status = models.CharField(
        max_length=100, choices=(("Active", "Active"), ("Inactive", "Inactive"))
    )  # active or inactive
    department = models.CharField(max_length=100)  # department
    uiic_contact = models.CharField(max_length=1000)  # email from uiic
    compliance_contact = models.CharField(max_length=100)  # email to send to compliance
    circular_details = models.CharField(
        max_length=100, blank=True
    )  # circular or regulation or email details
    type_of_compliance = models.CharField(
        max_length=100,
        blank=True,
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
    recurring_interval = models.CharField(
        max_length=100,
        blank=True,
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
    repeat_month = models.CharField(
        max_length=100,
        blank=True,
        choices=(
            ("January", "January"),
            ("February", "February"),
            ("March", "March"),
            ("April", "April"),
            ("May", "May"),
            ("June", "June"),
            ("July", "July"),
            ("August", "August"),
            ("September", "September"),
            ("October", "October"),
            ("November", "November"),
            ("December", "December"),
        ),
    )  # repeat month for annual interval
    return_number = models.CharField(max_length=100, blank=True)
    circular_document = models.FileField(blank=True)

    priority = models.IntegerField(
        blank=True,
        choices=((3, "High"), (2, "Medium"), (1, "Low")),
        default=2,
    )  # high/medium/low

    created_by = models.CharField(max_length=100, blank=True, default="")
    created_on = models.DateTimeField(auto_now_add=True)

    updated_by = models.CharField(max_length=100, blank=True, default="")
    updated_on = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.task_name

    def get_absolute_url(self):
        return reverse("template_detail", args=[str(self.id)])


auditlog.register(Template)
auditlog.register(Task)
