from django.utils.html import format_html
from django.urls import reverse

import django_tables2 as tables
from .models import Template


def row_class(record):
    print(record)
    if record.type_of_due_date == "calendar":
        return "table-danger"
    elif record.type_of_due_date == "working":
        return "table-warning"
    return "table-success"


class TemplatesTable(tables.Table):
    view = tables.Column(empty_values=(), orderable=False)
    edit = tables.Column(empty_values=(), orderable=False)

    class Meta:
        model = Template
        template_name = "django_tables2/bootstrap5.html"

        attrs = {
            "class": "table table-bordered table-striped table-hover",
            "id": "templateTable",
        }
        row_attrs = {"class": row_class}
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

    def render_edit(self, record):
        url = reverse("template_edit", args=[record.pk])
        return format_html('<a class="btn btn-sm btn-warning" href="{}">Edit</a>', url)
