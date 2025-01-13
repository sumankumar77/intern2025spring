"""
Fields module.

It provides a password field and a password confirmation field.
"""

from __future__ import unicode_literals

from django.forms import CharField

from zxcvbn_password.fields import GlobalValidator
from .widgets import MyPasswordStrengthInput


class MyPasswordField(CharField):
    """Password field."""

    default_validators = [GlobalValidator()]

    def __init__(self, *args, **kwargs):
        """
        Init method.

        Args:
            *args (): Django's args for a form field.
            **kwargs (): Django's kwargs for a form field.
        """
        if "widget" not in kwargs:
            kwargs["widget"] = MyPasswordStrengthInput(render_value=False)

        super(MyPasswordField, self).__init__(*args, **kwargs)
