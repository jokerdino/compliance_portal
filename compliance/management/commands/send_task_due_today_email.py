from collections import defaultdict

from django.core.management.base import BaseCommand
from django.conf import settings
from django.utils import timezone
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string


from compliance.models import Task
from compliance.mail_utils import parse_email_list


class Command(BaseCommand):
    help = "Send consolidated HTML emails for tasks created today"

    def handle(self, *args, **options):
        today = timezone.localdate()

        tasks = Task.objects.filter(
            due_date=today, current_status__in=["pending", "to_be_approved"]
        ).select_related("department")

        if not tasks.exists():
            self.stdout.write("No tasks are due today. No emails sent.")
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
                "date": today.strftime("%d/%m/%Y"),
            }

            subject = f"Tasks due today - {today.strftime('%d/%m/%Y')} - {department.department_name}"

            # Render templates
            html_content = render_to_string(
                "email_templates/task_email_bulk_due_today.html", context
            )

            text_content = render_to_string(
                "email_templates/task_email_bulk_due_today.txt", context
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
