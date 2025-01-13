from datetime import datetime, timedelta
from logging import getLogger
import os
from django import forms
from django.conf import settings as conf_settings
from django.contrib.auth import login, get_user_model, authenticate, logout
from django.contrib.auth.forms import AuthenticationForm, PasswordResetForm
from django.contrib.auth.views import PasswordContextMixin
from django.contrib.auth.tokens import default_token_generator
from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.urls import reverse, reverse_lazy
from django.utils.decorators import method_decorator
from django.utils.http import urlsafe_base64_decode
from django.views.decorators.csrf import csrf_protect
from django.views.generic import View
from django.views.generic.edit import FormView
from axes.decorators import axes_dispatch
from axes.handlers.proxy import AxesProxyHandler
from axes import helpers as axes_helpers

from social_django.models import UserSocialAuth
from apps.utils.utils import account_activation_token, get_all_timezones_with_offsets
from apps.session_security.utils import get_last_activity, set_last_activity
from apps.session_security.settings import EXPIRE_AFTER
from .forms import (
    CustomUserCreationForm, ResendActivationLinkForm, SimpleUserCreationForm,
    UserProfileForm, PtImageForm, PtImageDeleteForm, CustomUserChangeForm,
    CustomPasswordChangeForm, CustomAdminPasswordChangeForm,
    CustomAdminPasswordChangeWithEmailForm, CustomAuthenticationForm
)
from .utils import send_activation_email, get_axes_remained_attempts, resize

logger = getLogger(__name__)

User = get_user_model()


def signup(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.is_active = False
            user.save()
            send_activation_email(request, user)
            return redirect('account_activation_sent')
    else:
        if request.user.is_authenticated:
            return redirect('dashboard')
        form = CustomUserCreationForm()
    return render(request, 'user/signup.html', {'form': form, 'no_sidebar': True})


def account_activation_sent(request):
    return render(request, 'user/account_activation_sent.html', {'no_sidebar': True})


def account_activation_invalid(request):
    return render(request, 'user/account_activation_invalid.html', {'no_sidebar': True})


def resend_activation_email(request):
    if request.method == 'POST':
        form = ResendActivationLinkForm(request.POST)
        if form.is_valid():
            # If email field is not unique, using active_users[0] may not be correct.
            # Our User model enforces unique email field.
            active_users = User._default_manager.filter(**{
                '%s__iexact' % User.get_email_field_name(): form.cleaned_data['email'],
                'is_active': False,
            })
            if active_users:
                send_activation_email(request, active_users[0])
            return redirect('account_activation_sent')
    else:
        form = ResendActivationLinkForm()
    return render(request, 'user/resend_activation_email.html', {'no_sidebar': True, 'form': form})


def activate(request, uidb64, token, backend='django.contrib.auth.backends.ModelBackend'):
    try:
        uid = urlsafe_base64_decode(uidb64).decode()
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None
    if user is not None and account_activation_token.check_token(user, token):
        user.is_active = True
        user.email_confirmed = True
        user.save()
        login(request, user, backend=backend)
        return redirect('account_activation_done')
    else:
        return redirect('account_activation_invalid')


@method_decorator(axes_dispatch, name='dispatch')
class Login(View):
    """
    Custom login view that is modified from
    https://django-axes.readthedocs.io/en/latest/usage.html
    Remove csrf_exempt method_decorator
    """
    def post(self, request):
        form = AuthenticationForm(request=request, data=request.POST)
        if not form.is_valid():
            credentials = {'username': form.cleaned_data.get('username')}
            failure_limit = axes_helpers.get_failure_limit(request, credentials)
            remained_attempts = get_axes_remained_attempts(request, credentials)
            return render(request, 'user/login.html', {'no_sidebar': True, 'form': form, 'failure_limit': failure_limit,
                                                       'remained_attempts': remained_attempts})

        user = authenticate(
            request=request,
            username=form.cleaned_data.get('username'),
            password=form.cleaned_data.get('password'),
        )

        if user is not None:
            login(request, user)
            # user_logged_in.send is deleted here as AuthenticationForm has already sent the signal
            if request.GET.get('next'):
                url = request.GET.get('next')
                return redirect(url)
            else:
                return redirect('dashboard')
        else:
            # user_login_failed.send is deleted here as AuthenticationForm has already sent the signal
            # Since AuthenticationForm is_valid method has taken care of authenticate user issue, this
            # path should never be reached.
            return render(request, 'user/login.html', {'no_sidebar': True, 'form': form})

    def get(self, request):
        if request.user.is_authenticated:
            return redirect('dashboard')
        form = AuthenticationForm
        return render(request, 'user/login.html', {'no_sidebar': True, 'form': form})


@method_decorator(axes_dispatch, name='dispatch')
class Auth(View):
    """
    Custom login view that is modified from
    https://django-axes.readthedocs.io/en/latest/usage.html
    Remove csrf_exempt method_decorator
    """
    def post(self, request):
        if request.POST.get('login-password') or request.POST.get('login-username'):
            # login_form = AuthenticationForm(request=request, data=request.POST, prefix='login')
            login_form = CustomAuthenticationForm(request=request, data=request.POST, prefix='login')
            if not login_form.is_valid():
                # credentials = {'username': login_form.cleaned_data.get('username')}
                # failure_limit = axes_helpers.get_failure_limit(request, credentials)
                # remained_attempts = get_axes_remained_attempts(request, credentials)
                # user_login_failed.send is deleted here as AuthenticationForm has already sent the signal
                return render(request, 'user/social_auth_login.html', {
                    'login_form': login_form,
                    'signup_form': SimpleUserCreationForm(),
                    'action': 'login'
                })

            user = authenticate(
                request=request,
                username=login_form.cleaned_data.get('username'),
                password=login_form.cleaned_data.get('password'),
            )

            if user is not None:
                login(request, user)
                set_last_activity(request.session, datetime.now())
                # user_logged_in.send is deleted here as AuthenticationForm has already sent the signal
                if request.GET.get('next'):
                    url = request.GET.get('next')
                    return redirect(url)
                else:
                    return redirect(conf_settings.LOGIN_REDIRECT_URL)
            else:
                # user_login_failed.send is deleted here as AuthenticationForm has already sent the signal
                # Since AuthenticationForm is_valid method has taken care of authenticate user issue, this
                # path should never be reached.
                return render(request, 'user/social_auth_login.html', {
                    'login_form': login_form
                })
        else:
            form = SimpleUserCreationForm(request.POST)
            if form.is_valid():
                user = form.save(commit=False)
                user.is_active = False
                user.save()
                send_activation_email(request, user)
                return JsonResponse({'success': 'done'})
            else:
                return JsonResponse(form.errors.get_json_data())

    def get(self, request):
        if request.user.is_authenticated:
            if '_session_security' not in request.session:
                return redirect(conf_settings.LOGIN_REDIRECT_URL)
            else:
                now = datetime.now()
                delta = now - get_last_activity(request.session)
                if delta < timedelta(seconds=EXPIRE_AFTER):
                    return redirect(conf_settings.LOGIN_REDIRECT_URL)
        login_form = CustomAuthenticationForm(prefix='login')
        signup_form = SimpleUserCreationForm()
        action = request.GET.get('a') if request.GET.get('a') else 'login'
        return render(request, 'user/social_auth_login.html', {
            'login_form': login_form,
            'signup_form': signup_form,
            'action': action
        })


class AjaxableResponseMixin:
    """
    Mixin to add AJAX support to a form.
    """
    def form_invalid(self, form):
        response = super().form_invalid(form)
        if self.request.is_ajax():
            return JsonResponse(form.errors.get_json_data())
        else:
            return response

    def form_valid(self, form):
        # We make sure to call the parent's form_valid() method because
        # it might do some processing (in the case of CreateView, it will
        # call form.save() for example).
        response = super().form_valid(form)
        if self.request.is_ajax():
            return JsonResponse({'success': 'done'})
        else:
            return response


class AuthPasswordResetView(PasswordContextMixin, AjaxableResponseMixin, FormView):
    email_template_name = 'registration/password_reset_email.html'
    extra_email_context = None
    form_class = PasswordResetForm
    from_email = None
    html_email_template_name = None
    subject_template_name = 'registration/password_reset_subject.txt'
    success_url = reverse_lazy('auth')
    template_name = 'registration/password_reset_form.html'
    title = 'Password reset'
    token_generator = default_token_generator

    @method_decorator(csrf_protect)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)

    def form_valid(self, form):
        opts = {
            'use_https': self.request.is_secure(),
            'token_generator': self.token_generator,
            'from_email': self.from_email,
            'email_template_name': self.email_template_name,
            'subject_template_name': self.subject_template_name,
            'request': self.request,
            'html_email_template_name': self.html_email_template_name,
            'extra_email_context': self.extra_email_context,
        }
        form.save(**opts)
        return super().form_valid(form)


def auth_error(request):
    return render(request, 'user/auth_error.html', {'no_sidebar': True})


def auth_react(request):
    if request.method == 'POST' and request.is_ajax():
        form = ResendActivationLinkForm(request.POST)
        if form.is_valid():
            # If email field is not unique, using active_users[0] may not be correct.
            # Our User model enforces unique email field.
            active_users = User._default_manager.filter(**{
                '%s__iexact' % User.get_email_field_name(): form.cleaned_data['email'],
                'is_active': False,
            })
            if active_users:
                send_activation_email(request, active_users[0])
            return JsonResponse({'success': 'done'})
        else:
            return JsonResponse(form.errors.get_json_data())
    return JsonResponse({'error': 'failed'})


def auth_inactive_user(request):
    if hasattr(request.user, 'social_auth') and not request.user.is_active:
        user = request.user
        if not user.social_auth.filter(provider='google-oauth2').exists():
            user.email = ''
        user.set_unusable_password()
        user.is_active = True
        user.save()
        return redirect('auth_account_reset')
    return redirect('home')


def auth_account_reset(request):
    return render(request, 'user/account_reset.html', {'no_sidebar': True})


def lockout(request):
    # Only if lock out using IP. If lock out with other options AXES_ONLY_USER_FAILURES or
    # AXES_LOCK_OUT_BY_COMBINATION_USER_AND_IP, then the user won't be redirect to this page.
    if AxesProxyHandler.is_locked(request):
        return render(request, 'user/lockout.html', {'no_sidebar': True})
    else:
        return redirect('login')


def profile(request, template_name):
    if request.method == 'POST':
        print(request.POST)
        email_changed = False
        if request.POST.get('username', ''):
            user_form = CustomUserChangeForm(request.POST, instance=request.user)
            up_form = UserProfileForm(request.POST, instance=request.user.userprofile)
            flag_save = False
            if user_form.is_valid() and up_form.is_valid():
                email_changed = True if 'email' in user_form.changed_data else False
                if user_form.changed_data:
                    user_form.save()
                    flag_save = True
                    if email_changed:
                        user = request.user
                        user.is_active = False
                        user.save()
                        send_activation_email(request, user)
                if up_form.changed_data:
                    up_form.save()
                    flag_save = True
            json_data = {}
            if not user_form.is_valid():
                json_data.update(user_form.errors.get_json_data())
            if not up_form.is_valid():
                json_data.update(up_form.errors.get_json_data())
            if json_data:
                return JsonResponse(json_data)
            else:
                if flag_save:
                    if email_changed:
                        return JsonResponse({
                            'success': 'Activation email sent.',
                            'url': reverse('account_activation_sent')
                        })
                    else:
                        return JsonResponse({"success": "Your profile is saved!"})
                else:
                    return JsonResponse({"success": "No change is made!"})
        else:
            return JsonResponse({"error": "Username is not found!"})
    else:
        user = request.user
        # User account information
        user_form = CustomUserChangeForm(instance=user)
        user_form.fields['password'].widget = forms.HiddenInput()
        # Patient picture form
        image_form = PtImageForm()
        delete_image_form = PtImageDeleteForm()
        # Patient information
        up_form = UserProfileForm(instance=user.userprofile)
        # Social Auth
        try:
            google_login = user.social_auth.get(provider='google-oauth2')
        except UserSocialAuth.DoesNotExist:
            google_login = None

        try:
            twitter_login = user.social_auth.get(provider='twitter')
        except UserSocialAuth.DoesNotExist:
            twitter_login = None

        try:
            facebook_login = user.social_auth.get(provider='facebook')
        except UserSocialAuth.DoesNotExist:
            facebook_login = None
        can_disconnect = (request.user.social_auth.count() > 1 or request.user.has_usable_password())
        timezones = get_all_timezones_with_offsets()
        return render(request, template_name, {
            'user_form': user_form,
            'image_form': image_form,
            'delete_image_form': delete_image_form,
            'up_form': up_form,
            'google_login': google_login,
            'twitter_login': twitter_login,
            'facebook_login': facebook_login,
            'can_disconnect': can_disconnect,
            'timezones': timezones
        })


def upload_image(request):
    if request.method == "POST":
        user = request.user
        if user.userprofile.image:
            original = user.userprofile.image.name
        else:
            original = None
        form = PtImageForm(request.POST, request.FILES, instance=user.userprofile)
        if form.is_valid():
            # form.save()
            image = form.cleaned_data['image']
            user.userprofile.image = resize(image)
            user.userprofile.save()
            if original:
                try:
                    os.remove(os.path.join(conf_settings.MEDIA_ROOT, original))
                except OSError:
                    pass
            url = user.userprofile.image.url
            return JsonResponse({'success': 'Image updated!', 'url': url})
        else:
            return JsonResponse({"error": "Invalid form!"})
    else:
        return JsonResponse({"error": "There is no such page"})


def delete_image(request):
    if (request.method == "POST" and request.POST.get('delete', '')) or request.method == 'DELETE':
        user = request.user
        if user.userprofile.image:
            original = user.userprofile.image.name
            try:
                os.remove(os.path.join(conf_settings.MEDIA_ROOT, original))
            except OSError:
                pass
            user.userprofile.image = None
            user.userprofile.save()
            url = os.path.join(conf_settings.STATIC_ROOT, 'main/avatar_2x.png')
            return JsonResponse({'success': 'Image deleted!', 'url': url})
        else:
            return JsonResponse({'error': 'No image'})

    else:
        return JsonResponse({"error": "There is no such page"})


def set_password(request):
    if request.user.has_usable_password():
        PasswordForm = CustomPasswordChangeForm
    elif not request.user.email:
        PasswordForm = CustomAdminPasswordChangeWithEmailForm
    else:
        PasswordForm = CustomAdminPasswordChangeForm

    if request.method == 'POST':
        form = PasswordForm(request.user, request.POST)
        if form.is_valid():
            form.save()
            if form.cleaned_data.get('email'):
                user = request.user
                user.email = form.cleaned_data['email']
                user.is_active = False
                user.save()
                send_activation_email(request, user)
                return redirect('set_pw_react')
            # update_session_auth_hash(request, form.user)
            # messages.success(request, 'Your password was successfully updated!')
            # return redirect('password')
            return redirect('set_pw_done')
        # else:
            # messages.error(request, 'Please correct the error below.')
    else:
        form = PasswordForm(request.user)
    return render(request, 'user/set_password.html', {'form': form})


def set_password_done(request):
    return render(request, 'user/set_password_done.html')


def set_password_reactivation(request):
    return render(request, 'user/set_password_reactivation.html')


def ajax_logout(request):
    did_logout = False
    if request.is_ajax() and request.user.is_authenticated:
        logout(request)
        did_logout = True
    return JsonResponse({'success': True, 'did_logout': did_logout})
