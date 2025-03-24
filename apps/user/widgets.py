# -*- coding: utf-8 -*-

"""Widgets for form fields."""

from __future__ import unicode_literals

from django.forms import PasswordInput
from django.utils.safestring import mark_safe
from django.utils.translation import gettext as _

from zxcvbn_password.utils import zxcvbn_min_score


class MyPasswordStrengthInput(PasswordInput):
    """
    Form widget to show the user how strong his/her password is. Edit strength message
    """

    def render(self, name, value, attrs=None, **kwargs):
        """Widget render method."""
        min_score = zxcvbn_min_score()
        message_title = _('Warning')
        message_body = _('Password strength: <em class="password_strength_time"></em>.')

        strength_markup = """
        <div class="progress-bloc" style="margin-top: 10px;">
            <div class="progress" style="margin-bottom: 10px;">
                <div class="progress-bar
                            progress-bar-warning
                            password_strength_bar"
                     role="progressbar"
                     aria-valuenow="0"
                     aria-valuemin="{min_score}"
                     aria-valuemax="4"
                     style="width: 0%%">
                </div>
            </div>
            <p class="text-muted password_strength_info hidden">
                <span class="label label-danger">
                    {title}
                </span>
                <span style="margin-left:5px;">
                    {body}
                </span>
            </p>
        </div>
        """

        strength_markup = strength_markup.format(
            title=message_title,
            body=message_body,
            min_score=min_score)

        try:
            self.attrs['class'] = '%s password_strength'.strip() % self.attrs['class']  # noqa
        except KeyError:
            self.attrs['class'] = 'password_strength'

        return mark_safe(super(MyPasswordStrengthInput, self).render(  # nosec
            name, value, attrs) + strength_markup)

    class Media(object):
        """Media class to use in templates."""

        js = (
            'zxcvbn_password/js/zxcvbn.js',
            'js/password_strength.js',
        )
