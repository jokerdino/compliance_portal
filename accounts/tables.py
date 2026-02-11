# tables.py
import django_tables2 as tables
from django.utils.html import format_html
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.utils import timezone

from .models import Department


class DepartmentTable(tables.Table):
    edit = tables.Column(empty_values=(), orderable=False)

    class Meta:
        model = Department
        orderable = False
        fields = ("department_name", "edit")
        template_name = "django_tables2/bootstrap5.html"
        attrs = {
            "class": "table table-bordered table-striped table-hover",
            "id": "DepartmentTable",
        }

    def render_edit(self, record):
        url = reverse("department_update", args=[record.pk])
        return format_html('<a class="btn btn-sm btn-warning" href="{}">Edit</a>', url)


class UserTable(tables.Table):
    view = tables.Column(empty_values=(), orderable=False)
    edit = tables.Column(empty_values=(), orderable=False)

    class Meta:
        model = get_user_model()
        orderable = False
        fields = (
            "username",
            "groups",
            "department",
            "email_address",
            "reset_password",
            "last_login",
            "view",
            "edit",
        )
        template_name = "django_tables2/bootstrap5.html"
        attrs = {
            "class": "table table-bordered table-striped table-hover",
            "id": "UserTable",
        }

    def render_view(self, record):
        url = reverse("user_detail", args=[record.pk])
        return format_html('<a class="btn btn-sm btn-info" href="{}">View</a>', url)

    def render_edit(self, record):
        url = reverse("user_update", args=[record.pk])
        return format_html('<a class="btn btn-sm btn-warning" href="{}">Edit</a>', url)

    def render_last_login(self, value):
        if value:
            local_value = timezone.localtime(value)
            return format_html(
                '<span data-order="{}">{}</span>',
                local_value.isoformat(),
                local_value.strftime("%d/%m/%Y %H:%M:%S"),
            )
        return ""
