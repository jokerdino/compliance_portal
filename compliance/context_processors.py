from django.utils.timezone import localdate
from .models import Task


def tasks_count(request):
    """Returns the count of pending tasks globally."""
    today = localdate()
    due_today_count = Task.objects.filter(
        due_date=today, current_status="pending"
    ).count()

    overdue_count = Task.objects.filter(
        due_date__lt=today, current_status="pending"
    ).count()
    upcoming_count = Task.objects.filter(
        due_date__gt=today, current_status="pending"
    ).count()
    pending_count = Task.objects.filter(current_status="pending").count()
    return {
        "pending_tasks_count": pending_count,
        "due_today_count": due_today_count,
        "overdue_count": overdue_count,
        "upcoming_count": upcoming_count,
    }
