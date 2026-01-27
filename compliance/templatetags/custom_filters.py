from django import template

register = template.Library()


@register.filter
def replace(value, arg):
    """
    Replaces all occurrences of a substring with another substring.
    Usage: {{ value|replace:"search_string|replace_string" }}
    """
    try:
        # Split the argument into 'search_string' and 'replace_string'
        what, to = arg.split("|", 1)
        return value.replace(what, to)
    except ValueError:
        # Handle cases where the argument is not correctly formatted
        return value
