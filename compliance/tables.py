from django.utils.html import format_html
from django.urls import reverse

import django_tables2 as tables
from .models import Template, Task, PublicHoliday, RegulatoryPublication


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
            "priority",
            "recurring_task_status",
        )

    def render_view(self, record):
        url = reverse("template_detail", args=[record.pk])
        return format_html('<a class="btn btn-sm btn-info" href="{}">View</a>', url)


class TaskTable(tables.Table):
    due_date = tables.DateColumn(
        format="d/m/Y",
        verbose_name="Due Date",
        attrs={
            "td": {
                "data-sort": lambda record: (record.due_date if record.due_date else "")
            }
        },
    )
    data_document = tables.Column(
        verbose_name="Document",
        empty_values=(),
    )

    date_of_document_forwarded = tables.DateColumn(
        format="d/m/Y",
        verbose_name="Date of submission",
        attrs={
            "td": {
                "data-sort": lambda record: (
                    record.date_of_document_forwarded
                    if record.date_of_document_forwarded
                    else ""
                )
            }
        },
    )
    priority = tables.TemplateColumn(template_name="partials/custom_priority_cell.html")
    view = tables.Column(empty_values=(), orderable=False)

    class Meta:
        model = Task
        order_by = ("due_date",)
        orderable = False
        template_name = "django_tables2/bootstrap5.html"

        attrs = {
            "class": "table table-bordered table-striped table-hover",
            "id": "taskTable",
        }
        fields = (
            "type_of_compliance",
            "department",
            "task_name",
            "current_status",
            "priority",
            "due_date",
            "data_document",
            "date_of_document_forwarded",
        )

    def render_view(self, record):
        url = reverse("task_detail", args=[record.pk])
        return format_html('<a class="btn btn-sm btn-info" href="{}">View</a>', url)

    def render_data_document(self, value):
        if not value:
            return "-"
        return format_html(
            '<a href="{}" class="btn btn-sm btn-outline-primary">Download</a>',
            value.url,
        )


class TaskApprovalTable(tables.Table):
    due_date = tables.DateColumn(
        format="d/m/Y",
        verbose_name="Due Date",
        attrs={
            "td": {
                "data-sort": lambda record: (record.due_date if record.due_date else "")
            }
        },
    )
    data_document = tables.Column(
        verbose_name="Document",
        empty_values=(),
    )
    date_of_document_forwarded = tables.DateColumn(
        format="d/m/Y",
        verbose_name="Date of submission",
        attrs={
            "td": {
                "data-sort": lambda record: (
                    record.date_of_document_forwarded
                    if record.date_of_document_forwarded
                    else ""
                )
            }
        },
    )
    view = tables.Column(empty_values=(), orderable=False)
    priority = tables.TemplateColumn(template_name="partials/custom_priority_cell.html")

    select = tables.CheckBoxColumn(
        accessor="pk",
        attrs={
            "th__input": {"onclick": "toggle(this)", "id": "select-all"},
        },
        orderable=False,
    )

    class Meta:
        model = Task
        order_by = ("due_date",)
        orderable = False
        template_name = "django_tables2/bootstrap5.html"

        attrs = {
            "class": "table table-bordered table-striped table-hover",
            "id": "taskTable",
        }
        fields = (
            "select",
            "type_of_compliance",
            "department",
            "task_name",
            "current_status",
            "priority",
            "due_date",
            "data_document",
            "date_of_document_forwarded",
        )

    def render_view(self, record):
        url = reverse("task_detail", args=[record.pk])
        return format_html('<a class="btn btn-sm btn-info" href="{}">View</a>', url)

    def render_data_document(self, value):
        if not value:
            return "-"
        return format_html(
            '<a href="{}" class="btn btn-sm btn-outline-primary">Download</a>',
            value.url,
        )


class PublicationTable(tables.Table):
    date_of_publication = tables.DateColumn(
        format="d/m/Y",
        verbose_name="Date of publication in IRDAI website",
        attrs={
            "td": {
                "data-sort": lambda record: (
                    record.date_of_publication if record.date_of_publication else ""
                )
            }
        },
    )
    effective_from = tables.DateColumn(
        format="d/m/Y",
        attrs={
            "td": {
                "data-sort": lambda record: (
                    record.effective_from if record.effective_from else ""
                )
            }
        },
    )
    view = tables.Column(empty_values=(), orderable=False)

    class Meta:
        model = RegulatoryPublication
        order_by = "effective_from"
        orderable = False
        template_name = "django_tables2/bootstrap5.html"
        attrs = {
            "class": "table table-bordered table-striped table-hover",
            "id": "publicationTable",
        }
        fields = (
            "category",
            "title",
            "url_of_publication",
            "publication_document",
            "date_of_publication",
            "effective_from",
        )

    def render_view(self, record):
        url = reverse("publication_detail", args=[record.pk])
        return format_html('<a class="btn btn-sm btn-info" href="{}">View</a>', url)

    def render_publication_document(self, value):
        if not value:
            return "-"
        return format_html(
            '<a href="{}" class="btn btn-sm btn-outline-primary">Download</a>',
            value.url,
        )
