from datetime import datetime

from django.core.management.base import BaseCommand
from django.utils.timezone import localdate
from django.forms.models import model_to_dict

from compliance.models import Template, Task
from compliance.utils import calculate_due_date


class Command(BaseCommand):
    help = "Populate tasks from active recurring templates"

    def add_arguments(self, parser):
        parser.add_argument(
            "recurring_interval",
            type=str,
            choices=[
                "daily",
                "weekly",
                "fortnightly",
                "monthly",
                "quarterly",
                "halfyearly",
                "annual",
            ],
            help="Recurring interval for which tasks should be populated",
        )
        parser.add_argument(
            "--run-date",
            type=str,
            help="Override today's date (format: DD/MM/YYYY)",
        )

    def handle(self, *args, **options):
        recurring_interval = options["recurring_interval"]
        run_date = options.get("run_date")

        def bulk_create(queryset):
            periodical_tasks = []

            for template in queryset:
                task_data = model_to_dict(
                    template,
                    exclude=[
                        "id",
                        "repeat_month",
                        "created_by",
                        "updated_by",
                        "due_date_days",
                        "type_of_due_date",
                        "recurring_task_status",
                        "recurring_interval",
                        "department",
                    ],
                )

                if template.type_of_due_date == "board_meeting":
                    task_data["due_date"] = None
                else:
                    task_data["due_date"] = calculate_due_date(
                        type_of_due_date=template.type_of_due_date,
                        due_date_days=template.due_date_days,
                        run_date=run_date,
                    )
                task_data["created_by_id"] = 1  # system user
                task_data["department_id"] = template.department_id
                task_data["current_status"] = "pending"
                task_data["template"] = template

                periodical_tasks.append(Task(**task_data))

            Task.objects.bulk_create(periodical_tasks)

        # Base recurring templates
        periodical_templates = Template.objects.filter(
            recurring_interval=recurring_interval,
            recurring_task_status="Active",
        )

        bulk_create(periodical_templates)

        # Include annual templates when running monthly
        if recurring_interval == "monthly":
            if run_date:
                today = datetime.strptime(run_date, "%d/%m/%Y").date()
            else:
                today = localdate()
            month_string = today.strftime("%B")

            annual_templates = Template.objects.filter(
                recurring_interval="annual",
                repeat_month__month_name=month_string,
                recurring_task_status="Active",
            ).distinct()

            bulk_create(annual_templates)

        self.stdout.write(
            self.style.SUCCESS(
                f"{recurring_interval.capitalize()} tasks populated successfully."
            )
        )
