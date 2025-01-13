from celery import shared_task
from logging import getLogger
from smtplib import SMTPException

# from django.template.loader import render_to_string
from django.conf import settings as conf_settings
from django.contrib.auth import get_user_model
from django.core import mail


logger = getLogger(__name__)
User = get_user_model()


@shared_task
def send_email_to_address(emails, subject, body, from_email=None, html=False):
    """
    content is a list of tuples
    """
    log_id = '[send_email_to_address]'
    try:
        from_email = from_email or conf_settings.DEFAULT_FROM_EMAIL
        # body = render_to_string('user/send_email_template.html', {'tlist': content})
        with mail.get_connection() as connection:
            msg = mail.EmailMessage(
                subject, body, from_email, emails, connection=connection
            )
            if html:
                msg.content_subtype = "html"
            msg.send()
        return True
    except SMTPException as e:
        logger.exception('{}SMTP exception: {}'.format(log_id, e))
    except Exception as e:
        logger.exception('{}Exception: {}'.format(log_id, e))
    return False
