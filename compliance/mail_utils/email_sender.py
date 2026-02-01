from django.core.mail import EmailMultiAlternatives
from django.conf import settings
from django.template.loader import render_to_string


def send_html_email(
    subject: str,
    template_html: str,
    template_txt: str,
    context: dict,
    to: list[str],
    cc: list[str] | None = None,
    bcc: list[str] | None = None,
):
    """
    Generic helper to send HTML + text emails
    """

    html_content = render_to_string(template_html, context)
    text_content = render_to_string(template_txt, context)

    msg = EmailMultiAlternatives(
        subject=subject,
        body=text_content,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=to,
        cc=cc or [],
        bcc=bcc or [],
    )

    msg.attach_alternative(html_content, "text/html")
    msg.send()
