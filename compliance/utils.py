import datetime
from django.utils.timezone import now
from .models import PublicHoliday


def calculate_due_date(
    due_date_days, type_of_due_date, run_date=None, meeting_date=None
):
    """Calculate due date based on due_date_days and type (calendar/working days)."""

    if type_of_due_date == "board_meeting":
        if not meeting_date:
            raise ValueError("meeting_date is required for board_meeting")
        return meeting_date + datetime.timedelta(days=due_date_days)
    if run_date:
        start_date = datetime.datetime.strptime(run_date, "%d/%m/%Y").date()
    else:
        start_date = now().date()

    if type_of_due_date == "calendar":
        return start_date + datetime.timedelta(days=due_date_days - 1)
    else:
        current_date = start_date
        days_added = 1 if is_working_day(current_date) else 0
        while days_added < due_date_days:
            current_date += datetime.timedelta(days=1)
            if is_working_day(current_date):
                days_added += 1
        return current_date


def is_working_day(date):
    # weekday(): 0 = Monday, 6 = Sunday
    if date.weekday() >= 5:  # Saturday or Sunday
        return False

    if PublicHoliday.objects.filter(date_of_holiday=date).exists():
        return False

    return True
