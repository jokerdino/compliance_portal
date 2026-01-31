from datetime import datetime, timedelta
from pathlib import Path
import mimetypes
import threading
import logging


from django.utils.timezone import localdate
from django.core.mail import EmailMultiAlternatives
from django.conf import settings


from .models import EmailLog, PublicHoliday


logger = logging.getLogger(__name__)


def calculate_due_date(
    due_date_days, type_of_due_date, run_date=None, meeting_date=None
):
    """Calculate due date based on due_date_days and type (calendar/working days)."""

    if type_of_due_date == "board_meeting":
        if not meeting_date:
            raise ValueError("meeting_date is required for board_meeting")
        return meeting_date + timedelta(days=due_date_days)
    if run_date:
        start_date = datetime.strptime(run_date, "%d/%m/%Y").date()
    else:
        start_date = localdate()

    if type_of_due_date in ["calendar", "board_meeting_conditional"]:
        return start_date + timedelta(days=due_date_days - 1)
    elif type_of_due_date == "working":
        current_date = start_date
        days_added = 1 if is_working_day(current_date) else 0
        while days_added < due_date_days:
            current_date += timedelta(days=1)
            if is_working_day(current_date):
                days_added += 1
        return current_date


def calculate_conditional_board_meeting_due_date(task):
    template = task.template

    if not task.board_meeting_date:
        return None

    primary = task.due_date

    alternate = task.board_meeting_date + timedelta(
        days=template.alternate_due_date_days
    )

    if template.conditional_operator == "earlier":
        return min(primary, alternate)

    if template.conditional_operator == "later":
        return max(primary, alternate)

    raise ValueError("Invalid conditional operator")


def is_working_day(date):
    # weekday(): 0 = Monday, 6 = Sunday
    if date.weekday() >= 5:  # Saturday or Sunday
        return False

    if PublicHoliday.objects.filter(date_of_holiday=date).exists():
        return False

    return True


def send_email(
    *,
    subject: str,
    recipients: list[str],
    cc: list[str] | None = None,
    bcc: list[str] | None = None,
    body: str,
    html: str | None = None,
    attachments: list[str | Path] | None = None,
):
    email = EmailMultiAlternatives(
        subject=subject,
        body=body,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=recipients,
        cc=cc or [],
        bcc=bcc or [],
    )

    if html:
        email.attach_alternative(html, "text/html")

    if attachments:
        for file_path in attachments:
            path = Path(file_path)
            if not path.exists():
                raise FileNotFoundError(path)

            mime_type, _ = mimetypes.guess_type(path)
            email.attach_file(
                path,
                mime_type or "application/octet-stream",
            )

    email.send(fail_silently=False)


def send_email_async(**kwargs):
    def _send():
        try:
            send_email_and_log(**kwargs)
            print("test")
        except Exception:
            logger.exception("Email sending failed")

    threading.Thread(
        target=_send,
        daemon=True,
    ).start()


def send_email_and_log(
    *,
    task,
    email_type,
    subject,
    recipients,
    body,
    html=None,
    attachments=None,
    user=None,
):
    try:
        print("test2")
        send_email(
            subject=subject,
            recipients=recipients,
            body=body,
            html=html,
            attachments=attachments,
        )
        print("test3")
        EmailLog.objects.create(
            task=task,
            email_type=email_type,
            subject=subject,
            to=recipients,
            sent_by=user,
            status="success",
        )
        print("test4")

    except Exception as exc:
        EmailLog.objects.create(
            task=task,
            email_type=email_type,
            subject=subject,
            to=recipients,
            sent_by=user,
            status="failed",
            error_message=str(exc),
        )
        raise
