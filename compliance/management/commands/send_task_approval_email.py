from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta

from auditlog.models import LogEntry
from django.contrib.contenttypes.models import ContentType

from compliance.models import Task

from compliance.mail_utils.task_queries import (
    group_tasks_by_department,
    get_department_ids_from_tasks,
)

from compliance.mail_utils.user_queries import get_active_users_by_department
from compliance.mail_utils.email_sender import send_html_email


class Command(BaseCommand):
    help = "Send approval emails for tasks moved to 'to_be_approved' in last 30 mins"

    def handle(self, *args, **options):
        today = timezone.localdate()
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
                if new == "to_be_approved":
                    task_ids.add(log.object_pk)

        if not task_ids:
            self.stdout.write("No tasks moved to 'to be approved' in last 30 minutes.")
            return

        tasks = Task.objects.filter(
            pk__in=task_ids, current_status="to_be_approved"
        ).select_related("department")

        if not tasks.exists():
            self.stdout.write("No matching tasks found. No emails sent.")
            return

        grouped_tasks = group_tasks_by_department(tasks)

        department_ids = get_department_ids_from_tasks(tasks)

        agm_map = get_active_users_by_department(
            department_ids=department_ids,
            user_type="dept_agm",
        )

        emails_sent = 0

        for department, task_list in grouped_tasks.items():
            to_list = agm_map.get(department.id, [])

            if not to_list:
                self.stdout.write(
                    self.style.WARNING(
                        f"No active chief managers with email for department {department.department_name}"
                    )
                )
                continue

            context = {
                "tasks": task_list,
                "department": department,
                "date": today.strftime("%d/%m/%Y"),
            }

            subject = (
                f"Tasks Awaiting Approval - "
                f"{today.strftime('%d/%m/%Y')} - {department.department_name}"
            )

            try:
                send_html_email(
                    subject=subject,
                    template_html="email_templates/task_email_bulk_approval.html",
                    template_txt="email_templates/task_email_bulk_approval.txt",
                    context=context,
                    to=to_list,
                    cc=["uicco@uiic.co.in"],
                    bcc=["44515"],
                )

                emails_sent += 1

            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(
                        f"Failed to send email for department {department.department_name}: {str(e)}"
                    )
                )

        self.stdout.write(self.style.SUCCESS(f"Total emails sent: {emails_sent}"))
