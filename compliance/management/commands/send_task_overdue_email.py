from collections import defaultdict


from django.core.management.base import BaseCommand
from django.conf import settings
from django.utils import timezone
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string

from compliance.models import Task
from compliance.mail_utils import parse_email_list


class Command(BaseCommand):
    help = "Send consolidated HTML emails for overdue tasks"

    def add_arguments(self, parser):
        parser.add_argument(
            "--overdue",
            type=int,
            default=1,
            help="Number of days overdue (default=1 means tasks due yesterday)",
        )

    def handle(self, *args, **options):
        overdue_days = options["overdue"]

        today = timezone.localdate()

        # Calculate target due date dynamically
        target_date = today - timezone.timedelta(days=overdue_days)

        tasks = Task.objects.filter(due_date=target_date).select_related("department")

        if not tasks.exists():
            self.stdout.write(
                f"No tasks found due {overdue_days} day(s) ago ({target_date}). No emails sent."
            )
            return

        grouped_tasks = defaultdict(list)

        for task in tasks:
            if not task.uiic_contact:
                continue

            key = (task.uiic_contact.strip().lower(), task.department)
            grouped_tasks[key].append(task)

        emails_sent = 0

        for (email, department), task_list in grouped_tasks.items():
            context = {
                "tasks": task_list,
                "department": department,
                "date": target_date.strftime("%d/%m/%Y"),
                "overdue_days": overdue_days,
            }

            subject = (
                f"Overdue Tasks Alert ({overdue_days} day(s)) - "
                f"{target_date.strftime('%d/%m/%Y')} - {department.department_name}"
            )

            html_content = render_to_string(
                "email_templates/task_email_bulk_overdue.html", context
            )

            text_content = render_to_string(
                "email_templates/task_email_bulk_overdue.txt", context
            )

            try:
                msg = EmailMultiAlternatives(
                    subject=subject,
                    body=text_content,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    to=parse_email_list(email),
                )

                msg.attach_alternative(html_content, "text/html")
                msg.send()

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
