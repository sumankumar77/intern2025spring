import os
from django.shortcuts import render
from django.http import Http404
from django.http.response import JsonResponse
from django.conf import settings as conf_settings

from apps.user.models import CustomUser, UserProfile, Connection
from apps.django_encrypted_filefield.views import FetchView
from apps.utils.constants import ENC_PATH_USER_PROFILE_IMAGE
from apps.utils.utils import send_email_to
from .forms import ContactUsForm


def home(request):
    return render(request, 'home_bs5.html', {'no_sidebar': True})


def index(request):
    return render(request, 'index_v2.html')


def about_us(request):
    return render(request, 'about_us_v2.html', {'no_sidebar': True})


def terms_of_service(request):
    return render(request, 'terms_of_service_v2.html', {'no_sidebar': True})


def privacy_policy(request):
    return render(request, 'privacy_policy_v2.html', {'no_sidebar': True})


def faq(request):
    return render(request, 'faq_v2.html', {'no_sidebar': True})


def contact_us(request):
    if request.method == 'POST':
        form = ContactUsForm(request.POST)
        if form.is_valid():
            cleaned_data = form.cleaned_data
            content = 'From: {}\n{}'.format(cleaned_data['your_email'], cleaned_data['message'])
            admin = CustomUser.objects.get(username=conf_settings.ADMIN_USERNAME)
            send_email_to(admin, 'DigitalHealth Contact Us', content)
            return JsonResponse({'success': 'Your message is sent.'})
        else:
            return JsonResponse(form.errors.get_json_data())
    elif request.method == 'GET':
        form = ContactUsForm()
        return render(request, 'contact_us_v2.html', {'form': form, 'no_sidebar': True})


def bad_request(request, exception):
    # 400
    msg = 'we are sorry, but the page you requested was not found'
    return render(request, 'error_page.html', {
        'number1': '4',
        'number2': '0',
        'number3': '0',
        'msg': msg,
        'no_sidebar': True
    })


def permission_denied(request, exception):
    # 403
    msg = 'we are sorry, but the page you requested was not found'
    return render(request, 'error_page.html', {
        'number1': '4',
        'number2': '0',
        'number3': '3',
        'msg': msg,
        'no_sidebar': True
    })


def page_not_found(request, exception):
    # 404
    msg = 'we are sorry, but the page you requested was not found'
    return render(request, 'error_page.html', {
        'number1': '4',
        'number2': '0',
        'number3': '4',
        'msg': msg,
        'no_sidebar': True
    })


def server_error(request):
    # 500
    msg = 'internal server error'
    return render(request, 'error_page.html', {
        'number1': '5',
        'number2': '0',
        'number3': '0',
        'msg': msg,
        'no_sidebar': True
    })


class CHFetchView(FetchView):

    def get(self, request, *args, **kwargs):
        # Check permission
        is_authorized = False
        path = kwargs.get("path")
        if not path:
            raise Http404
        if ENC_PATH_USER_PROFILE_IMAGE in path:
            if UserProfile.objects.filter(image=path.replace(conf_settings.MEDIA_URL, '')).exists():
                profile = UserProfile.objects.filter(image=path.replace(conf_settings.MEDIA_URL, ''))[0]
                if request.user == profile.user:
                    is_authorized = True
                elif Connection.objects.filter(
                        user_req_perm=request.user, user_grant_perm=profile.user,
                        guest_confirmed=True, host_confirmed=True).exists():
                    is_authorized = True
                elif request.GET.get('dhhs') and \
                        hasattr(request.user, 'dhhsuser') and hasattr(profile.user, 'dhhsuser'):
                    is_authorized = True
        if not is_authorized:
            raise Http404
        return super().get(request, *args, **kwargs)
