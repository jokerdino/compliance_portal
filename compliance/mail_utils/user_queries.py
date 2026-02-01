from collections import defaultdict
from typing import Iterable

from django.contrib.auth import get_user_model

User = get_user_model()


def get_active_users_by_department(
    department_ids: Iterable[int],
    user_type: str,
) -> dict[int, list[str]]:
    """
    Returns a mapping:

    {
        department_id: [email1, email2]
    }

    for active users of given user_type
    """

    users = User.objects.filter(
        department_id__in=department_ids,
        user_type=user_type,
        is_active=True,
    ).exclude(email_address__isnull=True)

    user_map = defaultdict(list)

    for user in users:
        user_map[user.department_id].append(user.email_address)

    return user_map
