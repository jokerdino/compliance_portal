from datetime import datetime, timedelta


from django.utils.timezone import localdate


from .models import PublicHoliday


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
