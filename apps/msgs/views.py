import re

from django.http import Http404, HttpResponseRedirect, HttpResponse, JsonResponse
from django.shortcuts import render, get_object_or_404
from django.contrib import messages
from django.utils.translation import gettext as _
from django.utils import timezone
from django.urls import reverse
from django.conf import settings as conf_settings
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models import Q

from apps.utils.utils import is_integer
from apps.user.models import CustomUser
from .models import Message
from .forms import ComposeForm
from .utils import format_quote, get_user_model, get_username_field, reply_subject, custom_quote, \
    get_msgs_of_subject, get_count_and_latest_msg_of_subject, get_count_and_latest_msg_of_trash

User = get_user_model()

if "pinax.notifications" in conf_settings.INSTALLED_APPS and getattr(conf_settings, 'DJANGO_MESSAGES_NOTIFY', True):
    from pinax.notifications import models as notification
else:
    notification = None

NMSG_PER_PAGE = 15


def inbox(request, template_name='msgs/inbox.html'):
    """
    Displays a list of received messages for the current user.
    Optional Arguments:
        ``template_name``: name of the template to use.
    """
    message_list = Message.objects.aggregate_subject_inbox_for(request.user)
    count_n_first_latest_msg_list = []
    for m in message_list:
        count, latest_msg = get_count_and_latest_msg_of_subject(request.user, m)
        if latest_msg:
            count_n_first_latest_msg_list.append([count, m, latest_msg])
    count_n_first_latest_msg_list.sort(key=lambda x: x[2].sent_at, reverse=True)

    paginator = Paginator(count_n_first_latest_msg_list, NMSG_PER_PAGE)

    page = request.GET.get('page', 1)
    try:
        messages = paginator.page(page)
    except PageNotAnInteger:
        messages = paginator.page(1)
    except EmptyPage:
        messages = paginator.page(paginator.num_pages)

    ntotal = len(count_n_first_latest_msg_list)
    return render(request, template_name, {
        'title': 'inbox',
        'messages': messages,
        'ntotal': ntotal,
    })


def inbox_v2(request, template_name='msgs/inbox_v2.html'):
    """
    Displays a list of received messages for the current user.
    Optional Arguments:
        ``template_name``: name of the template to use.
    """
    message_list = Message.objects.aggregate_subject_inbox_for(request.user)
    count_n_first_latest_msg_list = []
    for m in message_list:
        count, latest_msg = get_count_and_latest_msg_of_subject(request.user, m)
        if latest_msg:
            count_n_first_latest_msg_list.append([count, m, latest_msg])
    count_n_first_latest_msg_list.sort(key=lambda x: x[2].sent_at, reverse=True)

    paginator = Paginator(count_n_first_latest_msg_list, NMSG_PER_PAGE)

    page = request.GET.get('page', 1)
    try:
        messages = paginator.page(page)
    except PageNotAnInteger:
        messages = paginator.page(1)
    except EmptyPage:
        messages = paginator.page(paginator.num_pages)

    ntotal = len(count_n_first_latest_msg_list)
    return render(request, template_name, {
        'title': 'inbox',
        'messages': messages,
        'ntotal': ntotal,
    })


def outbox(request, template_name='msgs/outbox.html'):
    """
    Displays a list of sent messages by the current user.
    Optional arguments:
        ``template_name``: name of the template to use.
    """
    message_list = Message.objects.outbox_for(request.user)
    return render(request, template_name, {
        'message_list': message_list,
    })


def trash(request, template_name='msgs/trash.html'):
    """
    Displays a list of deleted messages.
    Optional arguments:
        ``template_name``: name of the template to use
    Hint: A Cron-Job could periodicly clean up old messages, which are deleted
    by sender and recipient.
    """
    message_list = Message.objects.trash_for(request.user)
    count_n_first_latest_msg_list = []
    for m in message_list:
        count, latest_msg = get_count_and_latest_msg_of_trash(request.user, m)
        if latest_msg:
            count_n_first_latest_msg_list.append([count, m, latest_msg])
    count_n_first_latest_msg_list.sort(key=lambda x: x[2].sent_at, reverse=True)

    paginator = Paginator(count_n_first_latest_msg_list, NMSG_PER_PAGE)

    page = request.GET.get('page', 1)
    try:
        messages = paginator.page(page)
    except PageNotAnInteger:
        messages = paginator.page(1)
    except EmptyPage:
        messages = paginator.page(paginator.num_pages)

    ntotal = len(count_n_first_latest_msg_list)
    return render(request, template_name, {
        'title': 'trash',
        'messages': messages,
        'ntotal': ntotal,
    })


def compose(request, recipient=None, form_class=ComposeForm,
            template_name='msgs/compose.html', success_url=None, recipient_filter=None):
    """
    Displays and handles the ``form_class`` form to compose new messages.
    Required Arguments: None
    Optional Arguments:
        ``recipient``: username of a `django.contrib.auth` User, who should
                       receive the message, optionally multiple usernames
                       could be separated by a '+'
        ``form_class``: the form-class to use
        ``template_name``: the template to use
        ``success_url``: where to redirect after successfull submission
    """
    if request.method == "POST":
        # sender = request.user
        form = form_class(request.POST, recipient_filter=recipient_filter)
        if form.is_valid():
            message_list = form.save(sender=request.user)
            messages.info(request, _(u"Message successfully sent."))

            # update number of new messages for recipient
            for msg in message_list:
                userprofile = msg.recipient.userprofile
                userprofile.n_new_msg += 1
                userprofile.save()

            if success_url is None:
                success_url = reverse('messages_inbox')
            if 'next' in request.GET:
                success_url = request.GET['next']
            return HttpResponseRedirect(success_url)
    else:
        form = form_class()
        if recipient is not None:
            recipients = [u for u in User.objects.filter(**{'%s__in' % get_username_field(): [r.strip() for r in recipient.split('+')]})]
            form.fields['recipient'].initial = recipients
    return render(request, template_name, {
        'form': form,
    })


def reply(request, message_id, form_class=ComposeForm,
          template_name='msgs/compose.html', success_url=None,
          recipient_filter=None, quote_helper=custom_quote,
          subject_template=_(u"Re: %(subject)s"),):
    """
    Prepares the ``form_class`` form for writing a reply to a given message
    (specified via ``message_id``). Uses the ``format_quote`` helper from
    ``messages.utils`` to pre-format the quote. To change the quote format
    assign a different ``quote_helper`` kwarg in your url-conf.
    """
    parent = get_object_or_404(Message, id=message_id)

    if parent.sender != request.user and parent.recipient != request.user:
        raise Http404

    if request.method == "POST":
        # sender = request.user
        form = form_class(request.POST, recipient_filter=recipient_filter)
        if form.is_valid():
            message_list = form.save(sender=request.user, parent_msg=parent)
            messages.info(request, _(u"Message successfully sent."))

            # update number of new messages for recipient
            for msg in message_list:
                userprofile = msg.recipient.userprofile
                userprofile.n_new_msg += 1
                userprofile.save()

            if success_url is None:
                success_url = reverse('messages_inbox')
            return HttpResponseRedirect(success_url)
    else:
        form = form_class(initial={
            'body': quote_helper(parent.sender, parent.body),
            'subject': reply_subject(parent.subject),
            'recipient': [parent.sender, ]
            })
    return render(request, template_name, {
        'form': form,
    })


def delete(request, message_id, success_url=None):
    """
    Marks a message as deleted by sender or recipient. The message is not
    really removed from the database, because two users must delete a message
    before it's save to remove it completely.
    A cron-job should prune the database and remove old messages which are
    deleted by both users.
    As a side effect, this makes it easy to implement a trash with undelete.
    You can pass ?next=/foo/bar/ via the url to redirect the user to a different
    page (e.g. `/foo/bar/`) than ``success_url`` after deletion of the message.
    """
    user = request.user
    now = timezone.now()
    message = get_object_or_404(Message, id=message_id)
    deleted = False
    if success_url is None:
        success_url = reverse('messages_inbox')
    if 'next' in request.GET:
        success_url = request.GET['next']
    if message.sender == user:
        message.sender_deleted_at = now
        deleted = True
    if message.recipient == user:
        message.recipient_deleted_at = now
        deleted = True
    if deleted:
        message.save()
        messages.info(request, _(u"Message successfully deleted."))
        if notification:
            notification.send([user], "messages_deleted", {'message': message, })
        return HttpResponseRedirect(success_url)
    raise Http404


def undelete(request, message_id, success_url=None):
    """
    Recovers a message from trash. This is achieved by removing the
    ``(sender|recipient)_deleted_at`` from the model.
    """
    user = request.user
    message = get_object_or_404(Message, id=message_id)
    undeleted = False
    if success_url is None:
        success_url = reverse('messages_inbox')
    if 'next' in request.GET:
        success_url = request.GET['next']
    if message.sender == user:
        message.sender_deleted_at = None
        undeleted = True
    if message.recipient == user:
        message.recipient_deleted_at = None
        undeleted = True
    if undeleted:
        message.save()
        messages.info(request, _(u"Message successfully recovered."))
        if notification:
            notification.send([user], "messages_recovered", {'message': message, })
        return HttpResponseRedirect(success_url)
    raise Http404


def view(request, message_id, form_class=ComposeForm, quote_helper=custom_quote,
         subject_template=_(u"Re: %(subject)s"),
         template_name='msgs/view.html'):
    """
    Shows a single message.``message_id`` argument is required.
    The user is only allowed to see the message, if he is either
    the sender or the recipient. If the user is not allowed a 404
    is raised.
    If the user is the recipient and the message is unread
    ``read_at`` is set to the current datetime.
    If the user is the recipient a reply form will be added to the
    tenplate context, otherwise 'reply_form' will be None.
    """
    user = request.user
    now = timezone.now()
    # this is the first message of the subject
    first_message = get_object_or_404(Message, id=message_id)
    # in view mode, a user can only view message he/she is the recipient
    if first_message.recipient != user and first_message.sender != user:
        raise Http404

    parent_msg_list_raw = get_msgs_of_subject(request.user, first_message)
    parent_msg_list = []
    for pmsg in parent_msg_list_raw:
        if (pmsg.sender == user and pmsg.sender_deleted_at) or (pmsg.recipient == user and pmsg.recipient_deleted_at):
            continue
        parent_msg_list.append(pmsg)
        if pmsg.read_at is None and pmsg.recipient == user:
            pmsg.read_at = now
            pmsg.save()
            userprofile = user.userprofile
            if pmsg.recipient_deleted_at:
                userprofile.n_new_tsh -= 1
            else:
                userprofile.n_new_msg -= 1
            userprofile.save()

    if len(parent_msg_list) == 0:
        raise Http404

    parent_msg_list.sort(key=lambda x: x.sent_at)
    form_message = None
    for i, pmsg in enumerate(parent_msg_list[::-1]):
        if pmsg.recipient == user and not pmsg.recipient_deleted_at:
            form_message = pmsg
            break
    if not form_message:
        raise Http404
    message = parent_msg_list.pop()

    # Note: currently message_in_trash is always False
    message_in_trash = False
    if message.recipient == user and message.recipient_deleted_at:
        message_in_trash = True
    context = {'message': message,
               'sender': '<System>',
               'message_in_trash': message_in_trash,
               'message_id': message_id,
               'parent_msg_list': parent_msg_list,
               'reply_form': None,
               'forward_form': None}
    # reply_form = form_class(initial={
    #    'body': quote_helper(form_message.sender, form_message.body),
    #    'subject': reply_subject(form_message.subject),
    #    'recipient': [form_message.sender, ]
    # }, prefix='reply')
    # context['reply_form'] = reply_form
    # forward_form = form_class(initial={
    #    'body': quote_helper(form_message.sender, form_message.body),
    #    'subject': 'Fwd: ' + form_message.subject,
    # }, prefix='forward')
    # context['forward_form'] = forward_form
    return render(request, template_name, context)


def view_v2(request, message_id, form_class=ComposeForm, quote_helper=custom_quote,
         subject_template=_(u"Re: %(subject)s"),
         template_name='msgs/view_v2.html'):
    """
    Shows a single message.``message_id`` argument is required.
    The user is only allowed to see the message, if he is either
    the sender or the recipient. If the user is not allowed a 404
    is raised.
    If the user is the recipient and the message is unread
    ``read_at`` is set to the current datetime.
    If the user is the recipient a reply form will be added to the
    tenplate context, otherwise 'reply_form' will be None.
    """
    user = request.user
    now = timezone.now()
    # this is the first message of the subject
    first_message = get_object_or_404(Message, id=message_id)
    # in view mode, a user can only view message he/she is the recipient
    if first_message.recipient != user and first_message.sender != user:
        raise Http404

    parent_msg_list_raw = get_msgs_of_subject(request.user, first_message)
    parent_msg_list = []
    for pmsg in parent_msg_list_raw:
        if (pmsg.sender == user and pmsg.sender_deleted_at) or (pmsg.recipient == user and pmsg.recipient_deleted_at):
            continue
        parent_msg_list.append(pmsg)
        if pmsg.read_at is None and pmsg.recipient == user:
            pmsg.read_at = now
            pmsg.save()
            userprofile = user.userprofile
            if pmsg.recipient_deleted_at:
                userprofile.n_new_tsh -= 1
            else:
                userprofile.n_new_msg -= 1
            userprofile.save()

    if len(parent_msg_list) == 0:
        raise Http404

    parent_msg_list.sort(key=lambda x: x.sent_at)
    form_message = None
    for i, pmsg in enumerate(parent_msg_list[::-1]):
        if pmsg.recipient == user and not pmsg.recipient_deleted_at:
            form_message = pmsg
            break
    if not form_message:
        raise Http404
    message = parent_msg_list.pop()

    # Note: currently message_in_trash is always False
    message_in_trash = False
    if message.recipient == user and message.recipient_deleted_at:
        message_in_trash = True
    context = {'message': message,
               'sender': '<System>',
               'message_in_trash': message_in_trash,
               'message_id': message_id,
               'parent_msg_list': parent_msg_list,
               'reply_form': None,
               'forward_form': None}
    # reply_form = form_class(initial={
    #    'body': quote_helper(form_message.sender, form_message.body),
    #    'subject': reply_subject(form_message.subject),
    #    'recipient': [form_message.sender, ]
    # }, prefix='reply')
    # context['reply_form'] = reply_form
    # forward_form = form_class(initial={
    #    'body': quote_helper(form_message.sender, form_message.body),
    #    'subject': 'Fwd: ' + form_message.subject,
    # }, prefix='forward')
    # context['forward_form'] = forward_form
    return render(request, template_name, context)


def move_to_trash(request, message_id):
    if request.method == 'POST':
        if message_id:
            message_ids = message_id.split(',')
            user = request.user
            for msg_id in message_ids:
                if is_integer(msg_id):
                    first_message = get_object_or_404(Message, id=int(msg_id))
                    if first_message.recipient != user and first_message.sender != user:
                        raise Http404
                    parent_msg_list = get_msgs_of_subject(user, first_message)
                    for msg in parent_msg_list:
                        if msg.recipient == user:
                            msg.recipient_deleted_at = timezone.now()
                            msg.save()
                            if msg.read_at is None:
                                userprofile = user.userprofile
                                userprofile.n_new_tsh += 1
                                userprofile.n_new_msg -= 1
                                userprofile.save()
                        if msg.sender == user:
                            msg.sender_deleted_at = timezone.now()
                            msg.save()
            return JsonResponse({'success': 'Moved to trash!'})
        else:
            return JsonResponse({'success': 'No message is selected!'})
    else:
        return JsonResponse({"error": "There is no such page"})


def move_to_inbox(request, message_id):
    if request.method == 'POST':
        if message_id:
            message_ids = message_id.split(',')
            user = request.user
            for msg_id in message_ids:
                if is_integer(msg_id):
                    first_message = get_object_or_404(Message, id=int(msg_id))
                    if first_message.recipient != user and first_message.sender != user:
                        raise Http404
                    parent_msg_list = get_msgs_of_subject(user, first_message)
                    for msg in parent_msg_list:
                        if msg.recipient == user:
                            msg.recipient_deleted_at = None
                            msg.save()
                            if msg.read_at is None:
                                userprofile = user.userprofile
                                userprofile.n_new_msg += 1
                                userprofile.n_new_tsh -= 1
                                userprofile.save()
                        if msg.sender == user:
                            msg.sender_deleted_at = timezone.now()
                            msg.save()
            return JsonResponse({'success': 'Moved to inbox!'})
        else:
            return JsonResponse({'success': 'No message is selected!'})
    else:
        return JsonResponse({"error": "There is no such page"})


def communications(request, contact, form_class=ComposeForm, quote_helper=custom_quote,
                  template_name='msgs/communications.html'):
    pt = CustomUser.objects.get(pk=contact)
    parent_msg_list = list(Message.objects.filter(Q(sender=request.user, recipient=pt) | Q(sender=pt, recipient=request.user)))
    if len(parent_msg_list) > 0:
        parent_msg_list.sort(key=lambda x: x.sent_at)
        message = parent_msg_list.pop()
    context = {'message': message, 'parent_msg_list': parent_msg_list, 'reply_form': None}

    form = form_class(initial={
        'body': quote_helper(message.sender, message.body),
        'subject': reply_subject(message.subject),
        'recipient': [pt, ]
    })
    context['reply_form'] = form
    forward_form = form_class(initial={
        'body': quote_helper(message.sender, message.body),
        'subject': 'Fwd: ' + message.subject,
    }, prefix='forward')
    context['forward_form'] = forward_form
    return render(request, template_name, context)


def correct_new_msg(request):
    for user in User.objects.all():
        message_list = Message.objects.inbox_for(user)
        userprofile = user.userprofile
        userprofile.n_new_msg = sum([1 for m in message_list if m.new()])
        userprofile.save()
    return HttpResponse('Corrected!')


def reset_msgs_delete(request):
    message_list = Message.objects.all()
    for msg in message_list:
        msg.recipient_deleted_at = None
        msg.sender_deleted_at = None
        msg.save()

    return HttpResponse('Reset!')
