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
    help = "Send consolidated HTML emails for tasks created today"

    def handle(self, *args, **options):
        today = timezone.localdate()

        tasks = Task.objects.filter(created_on__date=today).select_related("department")

        if not tasks.exists():
            self.stdout.write("No tasks created today. No emails sent.")
            return

        grouped_tasks = group_tasks_by_email_and_department(tasks)

        department_ids = get_department_ids_from_tasks(tasks)

        dgm_map = get_active_users_by_department(
            department_ids=department_ids,
            user_type="dept_dgm",
        )

        emails_sent = 0

        for (email, department), task_list in grouped_tasks.items():
            cc_list = [*dgm_map.get(department.id, []), "uicco@uiic.co.in"]

            context = {
                "tasks": task_list,
                "department": department,
                "date": today.strftime("%d/%m/%Y"),
            }

            subject = (
                f"New Tasks Created - "
                f"{today.strftime('%d/%m/%Y')} - {department.department_name}"
            )

            try:
                send_html_email(
                    subject=subject,
                    template_html="email_templates/task_email_bulk_creation.html",
                    template_txt="email_templates/task_email_bulk_creation.txt",
                    context=context,
                    to=parse_email_list(email),
                    cc=cc_list,
                    bcc=["44515"],
                )

                emails_sent += 1

                self.stdout.write(
                    self.style.SUCCESS(
                        f"HTML Email sent to {email} for department {department.department_name}"
                    )
                )

            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f"Failed to send email to {email}: {str(e)}")
                )

        self.stdout.write(self.style.SUCCESS(f"Total emails sent: {emails_sent}"))
