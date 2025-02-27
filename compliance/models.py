import datetime
from django import forms
from django.db import models
from django.urls import reverse

from django.utils.timezone import now

from auditlog.registry import auditlog


# Create your models here.
class Task(models.Model):
    task_name = models.CharField(max_length=100)
    due_date = models.DateField(
        blank=True,
        null=True,
        default=None,
        # widget=forms.DateInput(attrs={"type": "date"}),
    )
    due_date_days = models.IntegerField(default=0)  # in days
    type_of_due_date = models.CharField(max_length=100)  # calendar days or working days
    current_status = models.CharField(
        max_length=100, choices=(("Pending", "Pending"), ("Submitted", "Submitted"))
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
            ("Adhoc", "Adhoc"),
            ("Daily", "Daily"),
            ("Weekly", "Weekly"),
            ("Fortnightly", "Fortnightly"),
            ("Monthly", "Monthly"),
            ("Quarterly", "Quarterly"),
            ("Halfyearly", "Halfyearly"),
            ("Annual", "Annual"),
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
        # widget=forms.DateInput(attrs={"type": "date"}),
    )
    date_of_document_forwarded = models.DateField(
        blank=True,
        null=True,
        default=None,
        # widget=forms.DateInput(attrs={"type": "date"}),
    )

    created_by = models.CharField(max_length=100, blank=True, default="")
    created_on = models.DateTimeField(auto_now_add=True)

    updated_by = models.CharField(max_length=100, blank=True, default="")
    updated_on = models.DateTimeField(auto_now=True)

    # def calculate_due_date(self):
    #     """Calculate the due date based on type (calendar or working days)."""
    #     start_date = now().date()  # Use today's date as the base

    #     if self.type_of_due_date == "calendar_days":
    #         return start_date + datetime.timedelta(days=self.due_date_days)
    #     else:
    #         return self.get_working_day_due_date(start_date)

    # def get_working_day_due_date(self, start_date):
    #     """Calculate the due date considering only working days (excluding weekends)."""
    #     days_added = 0
    #     current_date = start_date

    #     while days_added < self.due_date_days:
    #         current_date += datetime.timedelta(days=1)
    #         if current_date.weekday() < 5:  # Monday to Friday (0-4)
    #             days_added += 1

    #     return current_date

    # def save(self, *args, **kwargs):
    #     """Override save method to set due_date before saving."""
    #     print(self.due_date_days)
    #     if self.due_date_days:  # Only calculate if due_date_days is set
    #         self.due_date = self.calculate_due_date()
    #     super().save(*args, **kwargs)

    # def create(self, *args, **kwargs):
    #     """Override create method to set due_date before saving."""
    #     print(self.due_date_days)
    #     if self.due_date_days:  # Only calculate if due_date_days is set
    #         self.due_date = self.calculate_due_date()
    #     return super().create(*args, **kwargs)

    def __str__(self):
        return self.task_name

    def get_absolute_url(self):
        return reverse("task_detail", args=[str(self.id)])


class Template(models.Model):
    task_name = models.CharField(max_length=100)

    due_date_days = models.IntegerField(default=0)  # in days
    type_of_due_date = models.CharField(
        max_length=100,
        default="",
        blank=True,
        choices=(("Calendar", "Calendar"), ("Working", "Working")),
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
            ("Adhoc", "Adhoc"),
            ("Daily", "Daily"),
            ("Weekly", "Weekly"),
            ("Fortnightly", "Fortnightly"),
            ("Monthly", "Monthly"),
            ("Quarterly", "Quarterly"),
            ("Halfyearly", "Halfyearly"),
            ("Annual", "Annual"),
        ),
    )  # adhoc/daily/weekly/monthly/quarterly/etc
    recurring_interval = models.CharField(
        max_length=100,
        blank=True,
        choices=(
            ("Daily", "Daily"),
            ("Weekly", "Weekly"),
            ("Fortnightly", "Fortnightly"),
            ("Monthly", "Monthly"),
            ("Quarterly", "Quarterly"),
            ("Halfyearly", "Halfyearly"),
            ("Annual", "Annual"),
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
