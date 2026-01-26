from django import forms
from django.urls import reverse_lazy
from django.forms import inlineformset_factory

from .models import Template, Task, TaskRemark


TaskRemarkFormSet = inlineformset_factory(
    Task,
    TaskRemark,
    fields=["text"],
    extra=1,
    can_delete=False,
    widgets={
        "text": forms.Textarea(
            attrs={
                "class": "form-control",
                "rows": 4,
                "placeholder": "Add your remark here…",
            }
        )
    },
)


class TemplateForm(forms.ModelForm):
    success_url = reverse_lazy("template_list")
    fieldsets = {
        "Task details": [
            "type_of_compliance",
            "task_name",
            "department",
            "priority",
        ],
        "Due date": [
            "type_of_due_date",
            "due_date_days",
        ],
        "Recurrence Settings": [
            "recurring_task_status",
            "recurring_interval",
            "repeat_month",
        ],
        "Contacts": [
            "uiic_contact",
            "compliance_contact",
        ],
        "Circular / Reference Details": [
            "circular_url",
            "circular_details",
            "return_number",
        ],
        "Upload Documents": [
            "data_document_template",
            "circular_document",
        ],
    }

    class Meta:
        model = Template
        fields = [
            "type_of_compliance",
            "task_name",
            "department",
            "priority",
            "type_of_due_date",
            "due_date_days",
            "recurring_task_status",
            "recurring_interval",
            "repeat_month",
            "uiic_contact",
            "compliance_contact",
            "circular_url",
            "circular_details",
            "return_number",
            "data_document_template",
            "circular_document",
        ]
        widgets = {
            "repeat_month": forms.CheckboxSelectMultiple(),
        }

    def clean_due_date_days(self):
        due_date_days = self.cleaned_data.get("due_date_days")

        if due_date_days is None or due_date_days < 1:
            raise forms.ValidationError("Due date must be at least 1 day.")

        return due_date_days


class TaskForm(forms.ModelForm):
    fieldsets = {
        "Task details": [
            "type_of_compliance",
            "task_name",
            "department",
            "current_status",
            "priority",
            "due_date",
            "data_document_template",
        ],
        "Contacts": ["uiic_contact", "compliance_contact"],
        "Circular / Reference Details": [
            "circular_url",
            "circular_details",
            "return_number",
            "circular_document",
        ],
        "Dates": [
            "date_of_document_received",
            "date_of_document_forwarded",
        ],
        "Upload Documents": [
            "data_document",
            "inbound_email_communication",
            "outbound_email_communication",
        ],
    }

    class Meta:
        model = Task
        fields = [
            "type_of_compliance",
            "task_name",
            "department",
            "current_status",
            "priority",
            "due_date",
            "data_document_template",
            "uiic_contact",
            "compliance_contact",
            "circular_url",
            "circular_details",
            "return_number",
            "circular_document",
            "date_of_document_received",
            "date_of_document_forwarded",
            "data_document",
            "inbound_email_communication",
            "outbound_email_communication",
        ]
        widgets = {
            "due_date": forms.DateInput(attrs={"type": "date"}),
            "date_of_document_forwarded": forms.DateInput(attrs={"type": "date"}),
            "date_of_document_received": forms.DateInput(attrs={"type": "date"}),
        }


class DepartmentTaskForm(forms.ModelForm):
    class Meta:
        model = Task
        fields = [
            "data_document",
        ]


class ComplianceTaskForm(forms.ModelForm):
    class Meta:
        model = Task
        fields = ["inbound_email_communication", "outbound_email_communication"]


class PublicHolidayUploadForm(forms.Form):
    success_url = reverse_lazy("public_holiday_list")
    file = forms.FileField(
        label="Upload Excel File",
        help_text="Accepted formats: .xlsx",
    )


class BoardMeetingBulkForm(forms.Form):
    board_meeting_date = forms.DateField(
        widget=forms.DateInput(
            attrs={
                "type": "date",
                "class": "form-control",
            }
        ),
        required=True,
        label="Board Meeting Date",
    )
