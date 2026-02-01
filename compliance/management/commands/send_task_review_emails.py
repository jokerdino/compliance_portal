from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone
from django.contrib.contenttypes.models import ContentType

from auditlog.models import LogEntry

from compliance.models import Task

from compliance.mail_utils.email_sender import send_html_email


class Command(BaseCommand):
    help = "Send consolidated email to UICCO for tasks that moved to REVIEW in last 30 minutes"

    def handle(self, *args, **options):
        now = timezone.now()
        thirty_mins_ago = now - timedelta(minutes=30)

        task_ct = ContentType.objects.get_for_model(Task)

        logs = LogEntry.objects.filter(
            content_type=task_ct,
            timestamp__gte=thirty_mins_ago,
        )

        task_ids = set()

        for log in logs:
            changes = log.changes_dict

            if "current_status" in changes:
                old, new = changes["current_status"]

                if new == "review":
                    task_ids.add(log.object_pk)

        if not task_ids:
            self.stdout.write("No tasks moved to review in last 30 minutes.")
            return

        tasks = Task.objects.filter(
            pk__in=task_ids, current_status="review"
        ).select_related("department")

        if not tasks.exists():
            self.stdout.write("No matching tasks found. No emails sent.")
            return

        context = {
            "tasks": tasks,
            "generated_on": timezone.localtime(now).strftime("%d/%m/%Y %H:%M"),
            "time_window": "Last 30 minutes",
        }

        subject = (
            f"Tasks Moved to Review - "
            f"{timezone.localtime(now).strftime('%d/%m/%Y %H:%M')}"
        )

        try:
            send_html_email(
                subject=subject,
                template_html="email_templates/task_email_bulk_review.html",
                template_txt="email_templates/task_email_bulk_review.txt",
                context=context,
                to=["uicco@uiic.co.in"],
                bcc=["44515"],
            )

            self.stdout.write(
                self.style.SUCCESS(f"Email sent to UICCO with {tasks.count()} tasks")
            )

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"Failed to send email to UICCO: {str(e)}")
            )
