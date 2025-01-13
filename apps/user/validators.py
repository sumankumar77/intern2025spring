"""
Copyright (c) 2007-2018, James Bennett
All rights reserved.

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are
met:

    * Redistributions of source code must retain the above copyright
      notice, this list of conditions and the following disclaimer.
    * Redistributions in binary form must reproduce the above
      copyright notice, this list of conditions and the following
      disclaimer in the documentation and/or other materials provided
      with the distribution.
    * Neither the name of the author nor the names of other
      contributors may be used to endorse or promote products derived
      from this software without specific prior written permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
"AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT
OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
(INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
"""

#
# https://github.com/ubernostrum/django-registration/blob/master/src/django_registration/validators.py
#
import unicodedata

from confusable_homoglyphs import confusables
from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import check_password
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

from .models import CustomUserPasswordHistory


CONFUSABLE = _(u"This name cannot be registered. "
               "Please choose a different name.")
CONFUSABLE_EMAIL = _(u"This email address cannot be registered. "
                     "Please supply a different email address.")
DUPLICATE_EMAIL = _(u"This email address is already in use. "
                    u"Please supply a different email address.")
DUPLICATE_USERNAME = _("A user with that username already exists.")
FREE_EMAIL = _(u"Registration using free email addresses is prohibited. "
               u"Please supply a different email address.")
RESERVED_NAME = _(u"This name is reserved and cannot be registered.")
TOS_REQUIRED = _(u"You must agree to the terms to register")

User = get_user_model()

# Below we construct a large but non-exhaustive list of names which
# users probably should not be able to register with, due to various
# risks:
#
# * For a site which creates email addresses from username, important
#   common addresses must be reserved.
#
# * For a site which creates subdomains from usernames, important
#   common hostnames/domain names must be reserved.
#
# * For a site which uses the username to generate a URL to the user's
#   profile, common well-known filenames must be reserved.
#
# etc., etc.
#
# Credit for basic idea and most of the list to Geoffrey Thomas's blog
# post about names to reserve:
# https://ldpreload.com/blog/names-to-reserve
SPECIAL_HOSTNAMES = [
    # Hostnames with special/reserved meaning.
    'autoconfig',     # Thunderbird autoconfig
    'autodiscover',   # MS Outlook/Exchange autoconfig
    'broadcasthost',  # Network broadcast hostname
    'isatap',         # IPv6 tunnel autodiscovery
    'localdomain',    # Loopback
    'localhost',      # Loopback
    'wpad',           # Proxy autodiscovery
]

PROTOCOL_HOSTNAMES = [
    # Common protocol hostnames.
    'ftp',
    'imap',
    'mail',
    'news',
    'pop',
    'pop3',
    'smtp',
    'usenet',
    'uucp',
    'webmail',
    'www',
]

CA_ADDRESSES = [
    # Email addresses known used by certificate authorities during
    # verification.
    'admin',
    'administrator',
    'hostmaster',
    'info',
    'is',
    'it',
    'mis',
    'postmaster',
    'root',
    'ssladmin',
    'ssladministrator',
    'sslwebmaster',
    'sysadmin',
    'webmaster',
]

RFC_2142 = [
    # RFC-2142-defined names not already covered.
    'abuse',
    'marketing',
    'noc',
    'sales',
    'security',
    'support',
]

NOREPLY_ADDRESSES = [
    # Common no-reply email addresses.
    'mailer-daemon',
    'nobody',
    'noreply',
    'no-reply',
]

SENSITIVE_FILENAMES = [
    # Sensitive filenames.
    'clientaccesspolicy.xml',  # Silverlight cross-domain policy file.
    'crossdomain.xml',         # Flash cross-domain policy file.
    'favicon.ico',
    'humans.txt',
    'keybase.txt',  # Keybase ownership-verification URL.
    'robots.txt',
    '.htaccess',
    '.htpasswd',
]

OTHER_SENSITIVE_NAMES = [
    # Other names which could be problems depending on URL/subdomain
    # structure.
    'account',
    'accounts',
    'auth',
    'authorize',
    'blog',
    'buy',
    'cart',
    'clients',
    'contact',
    'contactus',
    'contact-us',
    'copyright',
    'dashboard',
    'doc',
    'docs',
    'download',
    'downloads',
    'enquiry',
    'faq',
    'help',
    'inquiry',
    'license',
    'login',
    'logout',
    'me',
    'myaccount',
    'oauth',
    'pay',
    'payment',
    'payments',
    'plans',
    'portfolio',
    'preferences',
    'pricing',
    'privacy',
    'profile',
    'register',
    'secure',
    'settings',
    'signin',
    'signup',
    'ssl',
    'status',
    'store',
    'subscribe',
    'terms',
    'tos',
    'user',
    'users',
    'weblog',
    'work',
]

DEFAULT_RESERVED_NAMES = (
    SPECIAL_HOSTNAMES + PROTOCOL_HOSTNAMES + CA_ADDRESSES + RFC_2142 +
    NOREPLY_ADDRESSES + SENSITIVE_FILENAMES + OTHER_SENSITIVE_NAMES
)


class ReservedNameValidator(object):
    """
    Validator which disallows many reserved names as form field
    values.
    """
    def __init__(self, reserved_names=DEFAULT_RESERVED_NAMES):
        self.reserved_names = reserved_names

    def __call__(self, value):
        # GH issue 82: this validator only makes sense when the
        # username field is a string type.
        if not isinstance(value, str):
            return
        if value.lower() in self.reserved_names or \
           value.startswith('.well-known'):
            raise ValidationError(
                RESERVED_NAME, code='invalid'
            )


class CaseInsensitiveUnique(object):
    """
    Validator which performs a case-insensitive uniqueness check.
    """
    def __init__(self, model, field_name, error_message):
        self.model = model
        self.field_name = field_name
        self.error_message = error_message

    def __call__(self, value):
        # Only run if the username is a string.
        if not isinstance(value, str):
            return
        value = unicodedata.normalize('NFKC', value)
        if hasattr(value, 'casefold'):
            value = value.casefold()  # pragma: no cover
        if self.model._default_manager.filter(**{
                '{}__iexact'.format(self.field_name): value
        }).exists():
            raise ValidationError(self.error_message, code='unique')


def validate_confusables(value):
    """
    Validator which disallows 'dangerous' usernames likely to
    represent homograph attacks.
    A username is 'dangerous' if it is mixed-script (as defined by
    Unicode 'Script' property) and contains one or more characters
    appearing in the Unicode Visually Confusable Characters file.
    """
    if not isinstance(value, str):
        return
    if confusables.is_dangerous(value):
        raise ValidationError(CONFUSABLE, code='invalid')


def validate_confusables_email(value):
    """
    Validator which disallows 'dangerous' email addresses likely to
    represent homograph attacks.
    An email address is 'dangerous' if either the local-part or the
    domain, considered on their own, are mixed-script and contain one
    or more characters appearing in the Unicode Visually Confusable
    Characters file.
    """
    if '@' not in value:
        return
    local_part, domain = value.split('@')
    if confusables.is_dangerous(local_part) or \
       confusables.is_dangerous(domain):
        raise ValidationError(CONFUSABLE_EMAIL, code='invalid')


class DontRepeatValidator:
    def __init__(self, history=5):
        self.history = history

    def validate(self, password, user=None):
        for last_pass in self._get_last_passwords(user):
            if check_password(password=password, encoded=last_pass):
                self._raise_validation_error()

    def get_help_text(self):
        return _("You cannot repeat passwords")

    def _raise_validation_error(self):
        raise ValidationError(
            _("This password has been used before. Do not use the previous %d passwords." % self.history),
            code='password_has_been_used',
            params={'history': self.history},
        )

    def _get_last_passwords(self, user):
        all_history_user_passwords = CustomUserPasswordHistory.objects.filter(user=user).order_by('-pass_date')

        to_index = all_history_user_passwords.count() - self.history
        to_index = to_index if to_index > 0 else None
        if to_index:
            [u.delete() for u in all_history_user_passwords[0:to_index]]

        return [p.old_pass for p in all_history_user_passwords[to_index:]]
