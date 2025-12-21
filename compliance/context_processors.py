from django.db.models import Count, Q
from django.utils.timezone import localdate
from .models import Task


# def tasks_count(request):
#     """Returns the count of pending tasks globally."""
#     today = localdate()
#     due_today_count = Task.objects.filter(
#         due_date=today, current_status="pending"
#     ).count()

#     overdue_count = Task.objects.filter(
#         due_date__lt=today, current_status="pending"
#     ).count()
#     upcoming_count = Task.objects.filter(
#         due_date__gt=today, current_status="pending"
#     ).count()
#     pending_count = Task.objects.filter(current_status="pending").count()
#     return {
#         "pending_tasks_count": pending_count,
#         "due_today_count": due_today_count,
#         "overdue_count": overdue_count,
#         "upcoming_count": upcoming_count,
#     }


def tasks_count(request):
    """Returns the count of pending tasks globally."""
    today = localdate()
    DEPT_RESTRICTED_USERS = {"dept_user", "dept_chief_manager", "dept_dgm"}
    user = request.user

    qs = Task.objects.all()

    if user.is_authenticated:
        if user.user_type in DEPT_RESTRICTED_USERS:
            qs = qs.filter(department=user.department)

    counts = qs.aggregate(
        pending_tasks_count=Count(
            "id",
            filter=Q(),
        ),
        approval_pending_count=Count(
            "id",
            filter=Q(current_status="to_be_approved"),
        ),
        revision_count=Count(
            "id",
            filter=Q(current_status="revision"),
        ),
        review_count=Count(
            "id",
            filter=Q(current_status="review"),
        ),
        due_today_count=Count(
            "id",
            filter=Q(current_status="pending", due_date=today),
        ),
        overdue_count=Count(
            "id",
            filter=Q(current_status="pending", due_date__lt=today),
        ),
        upcoming_count=Count(
            "id",
            filter=Q(current_status="pending", due_date__gt=today),
        ),
    )

    return counts
