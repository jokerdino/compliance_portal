from django import forms
from django.urls import reverse_lazy
from .models import Template, Task


class TemplateForm(forms.ModelForm):
    success_url = reverse_lazy("template_list")

    class Meta:
        model = Template
        fields = [
            "task_name",
            "due_date_days",
            "type_of_due_date",
            "recurring_task_status",
            "department",
            "uiic_contact",
            "compliance_contact",
            "circular_details",
            "type_of_compliance",
            "recurring_interval",
            "repeat_month",
            "return_number",
            "circular_document",
            "priority",
        ]


class TaskForm(forms.ModelForm):
    due_date = forms.DateField(
        widget=forms.DateInput(attrs={"type": "date"}),
        required=False,
    )
    date_of_document_received = forms.DateField(
        widget=forms.DateInput(attrs={"type": "date"}),
        required=False,
    )

    date_of_document_forwarded = forms.DateField(
        widget=forms.DateInput(attrs={"type": "date"}),
        required=False,
    )

    class Meta:
        model = Task
        fields = [
            "task_name",
            "due_date",
            "current_status",
            # "type_of_due_date",
            # "recurring_task_status",
            "department",
            "uiic_contact",
            "compliance_contact",
            "circular_details",
            "type_of_compliance",
            # "recurring_interval",
            # "repeat_month",
            "return_number",
            "circular_document",
            "inbound_email_communication",
            "outbound_email_communication",
            "data_document",
            "date_of_document_received",
            "date_of_document_forwarded",
            "priority",
        ]
