from django.db.models import Count, Q
from django.utils.timezone import localdate
from .models import Task


def tasks_count(request):
    """Returns the count of pending tasks globally."""
    today = localdate()
    # DEPT_RESTRICTED_USERS = {"dept_user", "dept_agm", "dept_dgm"}
    user = request.user

    qs = Task.objects.all()

    if user.is_authenticated:
        # if user.user_type in DEPT_RESTRICTED_USERS:
        if user.has_perm("compliance.can_edit_as_department"):
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
            filter=Q(current_status="pending")
            & (Q(due_date__gt=today) | Q(due_date__isnull=True)),
        ),
        board_meeting_pending_count=Count(
            "id",
            filter=Q(
                current_status="pending",
                template__type_of_due_date__in=[
                    "board_meeting",
                    "board_meeting_conditional",
                ],
                board_meeting_date_flag=False,
            ),
        ),
    )

    return counts
