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
    widgets={"text": forms.Textarea(attrs={"class": "form-control", "rows": 4})},
)


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
            "data_document_template",
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
    due_date = forms.DateField(
        widget=forms.DateInput(attrs={"type": "date"}),
        required=True,
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
            "department",
            "uiic_contact",
            "compliance_contact",
            "circular_details",
            "type_of_compliance",
            "return_number",
            "circular_document",
            "inbound_email_communication",
            "outbound_email_communication",
            "data_document_template",
            "data_document",
            "priority",
            "date_of_document_received",
            "date_of_document_forwarded",
        ]


class TaskFromTemplateForm(forms.ModelForm):
    class Meta:
        model = Task
        fields = ["task_name", "due_date"]


class DepartmentTaskForm(forms.ModelForm):
    class Meta:
        model = Task
        fields = ["data_document", "inbound_email_communication"]


class ComplianceTaskForm(forms.ModelForm):
    class Meta:
        model = Task
        fields = ["outbound_email_communication"]


class PublicHolidayUploadForm(forms.Form):
    file = forms.FileField(
        label="Upload Excel File",
        help_text="Accepted formats: .xlsx",
    )
