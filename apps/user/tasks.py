from celery import shared_task
from celery.exceptions import Reject
from logging import getLogger
from smtplib import SMTPException

from django.template.loader import render_to_string
from django.conf import settings as conf_settings
from django.contrib.auth import get_user_model
from django.core import mail

from apps.api.exceptions import HTTPBadRequest
from apps.api.redcap.redcap_utils import is_redcap_livinglab, create_redcap_livinglab_human_subject
# app = Celery()

logger = getLogger(__name__)
User = get_user_model()


@shared_task
def send_email(content, user_pks):
    """
    content is a list of tuples
    """
    tag = '[send_email]'
    try:
        from_email = conf_settings.DEFAULT_FROM_EMAIL
        subject = 'Important Notification'
        body = render_to_string('user/send_email_template.html', {'tlist': content})
        users = [User.objects.get(pk=pk) for pk in user_pks]
        with mail.get_connection() as connection:
            mail.EmailMessage(
                subject,
                body,
                from_email,
                [user.email for user in users],
                connection=connection
            ).send()
    except SMTPException as e:
        logger.exception('{}SMTP exception: {}'.format(tag, e))
    except Exception as e:
        logger.exception('{}Exception: {}'.format(tag, e))


@shared_task
def send_email_to_admin(content):
    if User.objects.filter(username=conf_settings.ADMIN_USERNAME).exists():
        user_pks = [User.objects.get(username=conf_settings.ADMIN_USERNAME).pk]
        send_email(content, user_pks)
