from collections import defaultdict
from typing import Iterable
from compliance.models import Task


def group_tasks_by_department(tasks: Iterable[Task]):
    """
    Groups tasks by department object.

    Returns:
        dict { department_obj: [task1, task2, ...] }
    """
    grouped = defaultdict(list)

    for task in tasks:
        grouped[task.department].append(task)

    return grouped


def get_department_ids_from_tasks(tasks: Iterable[Task]):
    """
    Returns a set of department IDs from task queryset
    """
    return {task.department_id for task in tasks}


def group_tasks_by_email_and_department(tasks):
    grouped = defaultdict(list)

    for task in tasks:
        if not task.uiic_contact:
            continue

        key = (task.uiic_contact.strip().lower(), task.department)
        grouped[key].append(task)

    return grouped
