from django.utils.html import format_html
from django.urls import reverse

import django_tables2 as tables
from .models import Template, Task, PublicHoliday


class PublicHolidayTable(tables.Table):
    date_of_holiday = tables.DateColumn(format="d/m/Y")

    class Meta:
        model = PublicHoliday
        orderable = False
        template_name = "django_tables2/bootstrap5.html"
        attrs = {
            "class": "table table-bordered table-striped table-hover",
            "id": "templateTable",
        }
        fields = ("date_of_holiday", "name_of_holiday")


class TemplatesTable(tables.Table):
    view = tables.Column(empty_values=(), orderable=False)

    class Meta:
        model = Template
        orderable = False
        template_name = "django_tables2/bootstrap5.html"

        attrs = {
            "class": "table table-bordered table-striped table-hover",
            "id": "templateTable",
        }
        # row_attrs = {"class": row_class}
        fields = (
            "type_of_compliance",
            "department",
            "task_name",
            "due_date_days",
            "type_of_due_date",
            "return_number",
            "compliance_contact",
            "circular_details",
        )

    def render_view(self, record):
        url = reverse("template_detail", args=[record.pk])
        return format_html('<a class="btn btn-sm btn-info" href="{}">View</a>', url)


class TaskTable(tables.Table):
    due_date = tables.DateColumn(format="d/m/Y", verbose_name="Due Date")
    view = tables.Column(empty_values=(), orderable=False)

    class Meta:
        model = Task
        orderable = False
        template_name = "django_tables2/bootstrap5.html"

        attrs = {
            "class": "table table-bordered table-striped table-hover",
            "id": "templateTable",
        }
        # row_attrs = {"class": row_class}
        fields = (
            "type_of_compliance",
            "department",
            "task_name",
            "due_date",
            "return_number",
            "compliance_contact",
            "circular_details",
        )

    def render_view(self, record):
        url = reverse("task_detail", args=[record.pk])
        return format_html('<a class="btn btn-sm btn-info" href="{}">View</a>', url)


class TaskApprovalTable(tables.Table):
    due_date = tables.DateColumn(format="d/m/Y", verbose_name="Due Date")
    view = tables.Column(empty_values=(), orderable=False)

    select = tables.CheckBoxColumn(
        accessor="pk",
        attrs={
            "th__input": {"onclick": "toggle(this)", "id": "select-all"},
        },
        orderable=False,
    )

    class Meta:
        model = Task
        orderable = False
        template_name = "django_tables2/bootstrap5.html"

        attrs = {
            "class": "table table-bordered table-striped table-hover",
            "id": "templateTable",
        }
        # row_attrs = {"class": row_class}
        fields = (
            "select",
            "type_of_compliance",
            "department",
            "task_name",
            "due_date",
            "return_number",
            "compliance_contact",
            "circular_details",
        )

    def render_view(self, record):
        url = reverse("task_detail", args=[record.pk])
        return format_html('<a class="btn btn-sm btn-info" href="{}">View</a>', url)
