from django.db.models import DecimalField, FloatField
from encrypted_model_fields.fields import EncryptedMixin

from django.forms import MultipleChoiceField


class EncryptedDecimalField(EncryptedMixin, DecimalField):
    pass


class EncryptedFloatField(EncryptedMixin, FloatField):
    pass


class RangeSliderField(MultipleChoiceField):
    pass
