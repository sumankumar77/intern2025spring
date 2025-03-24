import re
import django
from django.utils.text import wrap
from django.utils.translation import gettext, gettext_lazy as _
# from django.contrib.sites.models import Site
from django.template.loader import render_to_string
from django.conf import settings

# favour django-mailer but fall back to django.core.mail
from django.core.mail import send_mail

from .models import Message


def format_quote(sender, body):
    """
    Wraps text at 55 chars and prepends each
    line with `> `.
    Used for quoting messages in replies.
    """
    lines = wrap(body, 55).split('\n')
    for i, line in enumerate(lines):
        lines[i] = "> %s" % line
    quote = '\n'.join(lines)
    return gettext(u"%(sender)s wrote:\n%(body)s") % {
        'sender': sender,
        'body': quote
    }


def custom_quote(sender, body):
    return gettext(u"\n\n <hr>\n%(sender)s wrote:\n%(body)s") % {
        'sender': sender,
        'body': body
    }


def format_subject(subject):
    """
    Prepends 'Re:' to the subject. To avoid multiple 'Re:'s
    a counter is added.
    NOTE: Currently unused. First step to fix Issue #48.
    FIXME: Any hints how to make this i18n aware are very welcome.
    """
    subject_prefix_re = r'^Re\[(\d*)\]:\ '
    m = re.match(subject_prefix_re, subject, re.U)
    prefix = u""
    if subject.startswith('Re: '):
        prefix = u"[2]"
        subject = subject[4:]
    elif m is not None:
        try:
            num = int(m.group(1))
            prefix = u"[%d]" % (num+1)
            subject = subject[6+len(str(num)):]
        except:
            # if anything fails here, fall back to the old mechanism
            pass

    return gettext(u"Re%(prefix)s: %(subject)s") % {
        'subject': subject,
        'prefix': prefix
    }


def new_message_email(sender, instance, signal,
                      subject_prefix=_(u'New Message: %(subject)s'),
                      template_name="django_messages/new_message.html",
                      default_protocol=None, *args, **kwargs):
    """
    This function sends an email and is called via Django's signal framework.
    Optional arguments:
        ``template_name``: the template to use
        ``subject_prefix``: prefix for the email subject.
        ``default_protocol``: default protocol in site URL passed to template
    """
    if default_protocol is None:
        default_protocol = getattr(settings, 'DEFAULT_HTTP_PROTOCOL', 'http')

    if 'created' in kwargs and kwargs['created']:
        try:
            # current_domain = Site.objects.get_current().domain
            current_domain = 'chealth.fsu.edu'
            subject = subject_prefix % {'subject': instance.subject}
            message = render_to_string(template_name, {
                'site_url': '%s://%s' % (default_protocol, current_domain),
                'message': instance,
            })
            if instance.recipient.email != "":
                send_mail(subject, message, settings.DEFAULT_FROM_EMAIL,
                          [instance.recipient.email, ])
        except Exception as e:
            # print e
            pass  # fail silently


def get_user_model():
    if django.VERSION[:2] >= (1, 5):
        from django.contrib.auth import get_user_model
        return get_user_model()
    else:
        from django.contrib.auth.models import User
        return User


def get_username_field():
    if django.VERSION[:2] >= (1, 5):
        return get_user_model().USERNAME_FIELD
    else:
        return 'username'


def reply_subject(parent_subject):
    if parent_subject.startswith('Re:'):
        return parent_subject
    else:
        return _(u"Re: %(subject)s") % {'subject': parent_subject}


def get_count_and_latest_msg_of_subject_v1(user, message):
    nmsg = 1
    if message.recipient == user:
        latest_msg = message
    else:
        latest_msg = None

    next_msgs = message.next_messages.all()
    if next_msgs:
        for next_msg in next_msgs:
            n_next_msg, l_msg = get_count_and_latest_msg_of_subject(user, next_msg)
            nmsg += n_next_msg
            if l_msg and l_msg.recipient == user:
                if latest_msg and l_msg.sent_at > latest_msg.sent_at:
                    latest_msg = l_msg
                if not latest_msg:
                    latest_msg = l_msg

    # Check if the latest message is deleted
    if latest_msg and latest_msg.recipient_deleted_at is not None:
        latest_msg = None

    return nmsg, latest_msg


def get_count_and_latest_msg_of_subject(user, message):
    nmsg = 0
    latest_msg = None
    if (user == message.recipient and not message.recipient_deleted_at) \
            or (user == message.sender and not message.sender_deleted_at):
        nmsg = 1
        if user == message.recipient:
            latest_msg = message

    next_msgs = message.next_messages.all()
    if next_msgs:
        for next_msg in next_msgs:
            n_next_msg, l_msg = get_count_and_latest_msg_of_subject(user, next_msg)
            nmsg += n_next_msg
            if l_msg and l_msg.recipient == user:
                if latest_msg and l_msg.sent_at > latest_msg.sent_at:
                    latest_msg = l_msg
                if not latest_msg:
                    latest_msg = l_msg

    # Check if the latest message is deleted
    if latest_msg and latest_msg.recipient_deleted_at is not None:
        latest_msg = None

    return nmsg, latest_msg


def get_count_and_latest_msg_of_trash(user, message):
    nmsg = 1
    if message.recipient == user:
        latest_msg = message
    else:
        latest_msg = None

    next_msgs = message.next_messages.all()
    if next_msgs:
        for next_msg in next_msgs:
            n_next_msg, l_msg = get_count_and_latest_msg_of_trash(user, next_msg)
            nmsg += n_next_msg
            if l_msg and l_msg.recipient == user:
                if latest_msg and l_msg.sent_at > latest_msg.sent_at:
                    latest_msg = l_msg
                if not latest_msg:
                    latest_msg = l_msg

    # Check if the latest message is deleted
    if latest_msg and latest_msg.recipient_deleted_at is None:
        latest_msg = None

    return nmsg, latest_msg


def get_msgs_of_subject(user, message):
    if (message.sender == user and not message.sender_deleted_at) or \
            (message.recipient == user and not message.recipient_deleted_at):
    # if message.sender == user or message.recipient == user:
        msgs = [message]
    else:
        msgs = []
    next_msgs = message.next_messages.all()
    if next_msgs:
        for next_msg in next_msgs:
            next_next_msgs = get_msgs_of_subject(user, next_msg)
            msgs = msgs + next_next_msgs

    return msgs
