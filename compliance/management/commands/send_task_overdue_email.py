from django.core.management.base import BaseCommand
from django.utils import timezone

from compliance.models import Task
from compliance.mail_utils.parse_emails import parse_email_list
from compliance.mail_utils.task_queries import (
    group_tasks_by_email_and_department,
    get_department_ids_from_tasks,
)
from compliance.mail_utils.user_queries import get_active_users_by_department
from compliance.mail_utils.email_sender import send_html_email


class Command(BaseCommand):
    help = "Send overdue task reminder emails with optional escalation"

    def add_arguments(self, parser):
        parser.add_argument(
            "--overdue",
            type=int,
            required=True,
            help="Number of days overdue",
        )

    def handle(self, *args, **options):
        overdue_days = options["overdue"]
        escalation = overdue_days > 5

        today = timezone.localdate()
        target_date = today - timezone.timedelta(days=overdue_days)

        tasks = Task.objects.filter(
            due_date=target_date,
            current_status__in=["pending", "to_be_approved"],
        ).select_related("department")

        if not tasks.exists():
            self.stdout.write(
                f"No tasks found due {overdue_days} day(s) ago ({target_date}). No emails sent."
            )
            return

        grouped_tasks = group_tasks_by_email_and_department(tasks)

        department_ids = get_department_ids_from_tasks(tasks)

        dgm_map: dict[int, list[str]] = get_active_users_by_department(
            department_ids=department_ids,
            user_type="dept_dgm",
        )
        cm_map: dict[int, list[str]] = get_active_users_by_department(
            department_ids=department_ids,
            user_type="dept_agm",
        )

        emails_sent = 0

        for (base_email, department), task_list in grouped_tasks.items():
            if escalation:
                to_list: list[str] = list(dgm_map.get(department.id, []))

                cc_list: list[str] = list(
                    {
                        *cm_map.get(department.id, []),
                        *parse_email_list(base_email),
                    }
                )
            else:
                to_list: list[str] = list(
                    {
                        *cm_map.get(department.id, []),
                        *parse_email_list(base_email),
                    }
                )
                cc_list: list[str] = []

            cc_list.append("uicco@uiic.co.in")

            context = {
                "tasks": task_list,
                "department": department,
                "date": target_date.strftime("%d/%m/%Y"),
                "overdue_days": overdue_days,
                "escalation": escalation,
            }

            subject = (
                f"Overdue Tasks Alert ({overdue_days} day(s)) - "
                f"{target_date.strftime('%d/%m/%Y')} - {department.department_name}"
            )

            try:
                send_html_email(
                    subject=subject,
                    template_html="email_templates/task_email_bulk_overdue.html",
                    template_txt="email_templates/task_email_bulk_overdue.txt",
                    context=context,
                    to=to_list,
                    cc=cc_list,
                    bcc=["44515"],
                )

                emails_sent += 1

                self.stdout.write(
                    self.style.SUCCESS(
                        f"Email sent for department {department.department_name}"
                    )
                )

            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(
                        f"Failed to send email for department {department.department_name}: {str(e)}"
                    )
                )

        self.stdout.write(self.style.SUCCESS(f"Total emails sent: {emails_sent}"))
