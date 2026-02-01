from django.core.validators import validate_email
from django.core.exceptions import ValidationError


def parse_email_list(value: str | None) -> list[str]:
    """
    Converts a comma-separated email string into a clean list.
    Invalid emails are ignored.
    """
    if not value:
        return []

    emails = []
    for raw in value.split(","):
        email = raw.strip()
        if not email:
            continue
        try:
            validate_email(email)
            emails.append(email)
        except ValidationError:
            continue

    return emails
