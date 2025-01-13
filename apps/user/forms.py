import re
from django import forms
from django.contrib.auth.forms import (
    UserCreationForm, UserChangeForm, AuthenticationForm, PasswordChangeForm,
    AdminPasswordChangeForm, UsernameField
)
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _
from zxcvbn_password.fields import PasswordConfirmationField

from apps.utils.widgets import DatePickerInput
from .models import Connection, UserProfile
from .fields import MyPasswordField
from . import validators

User = get_user_model()


class CustomUserCreationForm(UserCreationForm):

    password1 = MyPasswordField(label='Password')
    password2 = PasswordConfirmationField(label='Password confirmation', confirm_with='password1')

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ('username', 'email')

    def __init__(self, *args, **kwargs):
        super(CustomUserCreationForm, self).__init__(*args, **kwargs)
        email_field = User.get_email_field_name()
        self.fields[email_field].validators.append(
            validators.CaseInsensitiveUnique(
                User, email_field,
                validators.DUPLICATE_EMAIL
            )
        )
        username_field = 'username'
        self.fields[username_field].validators.append(
            validators.CaseInsensitiveUnique(
                User, username_field,
                validators.DUPLICATE_USERNAME
            )
        )
        self.fields[username_field].validators.append(
            validators.ReservedNameValidator()
        )


class SimpleUserCreationForm(UserCreationForm):

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ('username', 'email')
        error_messages = {
            'email': {
                'unique': 'This email address is already in use.'
            },
        }

    def __init__(self, *args, **kwargs):
        super(SimpleUserCreationForm, self).__init__(*args, **kwargs)
        email_field = User.get_email_field_name()
        self.fields[email_field].validators.append(
            validators.CaseInsensitiveUnique(
                User, email_field,
                validators.DUPLICATE_EMAIL
            )
        )
        username_field = 'username'
        self.fields[username_field].validators.append(
            validators.CaseInsensitiveUnique(
                User, username_field,
                validators.DUPLICATE_USERNAME
            )
        )
        self.fields[username_field].validators.append(
            validators.ReservedNameValidator()
        )


class CustomAuthenticationForm(AuthenticationForm):
    username = UsernameField(widget=forms.TextInput(attrs={'autofocus': True, 'placeholder': _('email/username')}))
    password = forms.CharField(label=_("Password"), strip=False, widget=forms.PasswordInput(
        attrs={'autocomplete': 'current-password', 'placeholder': _('password')}))


class CustomUserChangeForm(UserChangeForm):

    class Meta:
        model = User
        fields = ('username', 'email', 'password')

    def clean(self):
        cleaned_data = self.cleaned_data
        email = cleaned_data['email']
        username = cleaned_data['username']
        if not username:
            self.add_error('username', 'Username cannot be empty')
        if User.objects.filter(username__iexact=username).exclude(pk=self.instance.pk).exists():
            self.add_error('username', 'This username has already been taken.')
        if username.lower() in validators.DEFAULT_RESERVED_NAMES:
            self.add_error('username', validators.RESERVED_NAME)
        if User.objects.filter(email__iexact=email).exclude(pk=self.instance.pk).exists():
            self.add_error('email', 'This email address is already in use.')
        if hasattr(self.instance, 'social_auth') and \
                self.instance.social_auth.filter(provider='google-oauth2').exists() and \
                (email != self.instance.email):
            self.add_error('email', "Can't change email for Google social account.")
        return cleaned_data


class ResendActivationLinkForm(forms.Form):
    email = forms.EmailField(label='Email', max_length=254)


class CustomPasswordChangeForm(PasswordChangeForm):
    new_password1 = MyPasswordField()
    new_password2 = PasswordConfirmationField(confirm_with='new_password1')


class CustomAdminPasswordChangeForm(AdminPasswordChangeForm):
    password1 = MyPasswordField()
    password2 = PasswordConfirmationField(confirm_with='password1')


class CustomAdminPasswordChangeWithEmailForm(AdminPasswordChangeForm):
    password1 = MyPasswordField()
    password2 = PasswordConfirmationField(confirm_with='password1')
    email = forms.EmailField(label='Email', max_length=254)

    def clean(self):
        cleaned_data = self.cleaned_data
        email = cleaned_data.get('email')
        if email and User.objects.filter(email=email).exists():
            self.add_error('email', 'This email address is already in use.')
        return cleaned_data


class FileForm(forms.Form):
    file = forms.FileField()


class ConnectionForm(forms.ModelForm):
    class Meta:
        model = Connection
        fields = ('created', 'user_grant_perm', 'user_req_perm', 'host_confirmed', 'guest_confirmed')

    def __init__(self, *args, **kwargs):
        self.request_user = kwargs.pop('request_user')
        super(ConnectionForm, self).__init__(*args, **kwargs)

    def clean(self):
        if not self.request_user:
            raise forms.ValidationError("Unauthorized user!")
        else:
            cleaned_data = super(ConnectionForm, self).clean()
            user_grant_perm = cleaned_data.get('user_grant_perm')
            user_req_perm = cleaned_data.get('user_req_perm')
            host_confirmed = cleaned_data.get('host_confirmed')
            guest_confirmed = cleaned_data.get('guest_confirmed')
            old = Connection.objects.filter(pk=getattr(self.instance, 'pk', None)).first()
            flag = False
            if old:
                # Case: request user grants permission is updating host_confirmed
                if (old.guest_confirmed == guest_confirmed) and (old.user_grant_perm == user_grant_perm) \
                        and (user_grant_perm == self.request_user):
                    flag = True
                # Case: request user has permission is updating guest_confirmed
                if (old.host_confirmed == host_confirmed) and (old.user_req_perm == user_req_perm) \
                        and (user_req_perm == self.request_user):
                    flag = True
            else:
                # Case: request user grants permission is creating a connection with grant permission
                if host_confirmed and (not guest_confirmed) and (user_grant_perm == self.request_user):
                    flag = True
                # Case: request user is creating a connection of requesting permission
                if guest_confirmed and (not host_confirmed) and (user_req_perm == self.request_user):
                    flag = True
            if self.request_user.is_superuser:
                flag = True

            if flag:
                return cleaned_data
            else:
                raise forms.ValidationError(
                    "No permission for creating or updating!"
                )


class UserProfileForm(forms.ModelForm):

    class Meta:
        model = UserProfile
        fields = ['firstname', 'lastname', 'birth_date', 'gender', 'address_line1', 'address_line2',
                  'city', 'state', 'code', 'phone', 'time_zone']

    field_order = ['firstname', 'lastname', 'birth_date', 'gender', 'address_line1', 'address_line2',
                   'city', 'state', 'code', 'phone', 'time_zone']

    def __init__(self, *args, **kwargs):
        instance = kwargs.get('instance', None)
        super().__init__(*args, **kwargs)
        self.fields['birth_date'].widget = DatePickerInput()
        self.fields['birth_date'].input_formats = ['%m/%d/%Y']
        if instance and instance.phone:
            self.initial['phone'] = '({}){}-{}'.format(instance.phone[:3], instance.phone[3:6], instance.phone[6:])

    def clean_phone(self):
        phone = self.cleaned_data['phone']
        if phone and not re.search('\(\d{3}\)\d{3}-\d{4}', phone):
            raise forms.ValidationError('Invalid telephone number.', code='invalid')
        return phone.replace('(', '').replace(')', '').replace('-', '')


class PtImageForm(forms.ModelForm):

    class Meta:
        model = UserProfile
        fields = ['image']


class PtImageDeleteForm(forms.Form):
    delete = forms.BooleanField(required=False)
