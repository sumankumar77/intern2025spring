import datetime
from django.contrib.auth.models import AbstractUser, UserManager
from django.core import validators
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils.deconstruct import deconstructible
from django.utils.translation import gettext_lazy as _
from django.utils import timezone

from encrypted_model_fields.fields import EncryptedCharField, EncryptedDateField
from timezone_field import TimeZoneField
from apps.django_encrypted_filefield.fields import EncryptedImageField
from apps.utils.constants import ENC_PATH_USER_PROFILE_IMAGE


@deconstructible
class CustomUnicodeUsernameValidator(validators.RegexValidator):
    regex = r'^[\w.+-]+\Z'
    message = _(
        'Enter a valid username. This value may contain only letters, '
        'numbers, and ./+/-/_ characters.'
    )
    flags = 0


# This Manager does not prevent case-insensitive username creation. It only works in authentication.
# To prevent duplicate case-insensitive username creation, refer to UserCreationForm
class CustomUserManager(UserManager):
    def get_by_natural_key(self, username):
        case_insensitive_username_field = '{}__iexact'.format(self.model.USERNAME_FIELD)
        return self.get(**{case_insensitive_username_field: username})


class CustomUser(AbstractUser):
    username_validator = CustomUnicodeUsernameValidator()

    username = models.CharField(
        _('username'),
        max_length=150,
        unique=True,
        help_text=_('Required. 150 characters or fewer. Letters, digits and ./+/-/_ only.'),
        validators=[username_validator],
        error_messages={
            'unique': _("A user with that username already exists."),
        },
    )
    email_confirmed = models.BooleanField(default=False)
    is_project_manager = models.BooleanField(default=False)

    objects = CustomUserManager()

    def __str__(self):
        return '%s (%s)' % (self.username, self.email)

    def __init__(self, *args, **kwargs):
        super(CustomUser, self).__init__(*args, **kwargs)
        self.original_password = self.password

    def save(self, *args, **kwargs):
        super(CustomUser, self).save(*args, **kwargs)
        if self._password_has_been_changed():
            CustomUserPasswordHistory.remember_password(self)

    def _password_has_been_changed(self):
        return self.original_password != self.password


class CustomUserPasswordHistory(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    old_pass = models.CharField(max_length=128)
    pass_date = models.DateTimeField()

    @classmethod
    def remember_password(cls, user):
        cls(user=user, old_pass=user.password, pass_date=timezone.now()).save()


class UserProfile(models.Model):
    # Delete all user information if a user account is deleted.
    # Suggest putting a user to be inactive rather than delete a user.
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE)
    image = EncryptedImageField(upload_to=ENC_PATH_USER_PROFILE_IMAGE, null=True, blank=True)
    firstname = EncryptedCharField(_('First Name'), max_length=30, blank=True)
    lastname = EncryptedCharField(_('Last Name'), max_length=30, blank=True)

    birth_date = EncryptedDateField(_('Birth Date'), null=True, blank=True)
    GENDERS = (
        ('FEMALE', _('Female')),
        ('MALE', _('Male')),
        ('UNKNOWN', _('Unknown')),
    )
    gender = EncryptedCharField(_('Gender'), max_length=10, choices=GENDERS, null=True, blank=True)

    address_line1 = EncryptedCharField(_('Address line 1'), max_length=50, blank=True)
    address_line2 = EncryptedCharField(_('Address line 2'), max_length=50, blank=True)
    city = EncryptedCharField(_('City'), max_length=50, blank=True)
    state = EncryptedCharField(_('State'), max_length=40, blank=True)
    code = EncryptedCharField(_('Postal Code'), max_length=12, blank=True)
    phone = EncryptedCharField(_('Phone Number'), max_length=20, blank=True, help_text=_('Example: (123)456-7890'))

    time_zone = TimeZoneField(_('Time Zone'), default='America/New_York')

    n_new_msg = models.PositiveIntegerField(default=0)
    n_new_tsh = models.PositiveIntegerField(default=0)

    def __str__(self):
        return self.user.username


@receiver(post_save, sender=CustomUser)
def create_or_update_user_profile(sender, instance, created, **kwargs):
    # Update this in production
    # if created:
    if created and not UserProfile.objects.filter(user=instance).exists():
        UserProfile.objects.create(user=instance)
    instance.userprofile.save()


class Connection(models.Model):
    created = models.DateField(default=datetime.date.today, null=False, blank=False)
    user_grant_perm = models.ForeignKey(CustomUser, related_name='hosts',
                                        blank=True, null=True, on_delete=models.CASCADE)
    user_req_perm = models.ForeignKey(CustomUser, related_name='guests',
                                      blank=True, null=True, on_delete=models.CASCADE)
    host_confirmed = models.BooleanField(default=False)
    guest_confirmed = models.BooleanField(default=False)
    updated = models.DateField(null=True, blank=True)

    class Meta:
        unique_together = (('user_grant_perm', 'user_req_perm'),)
        ordering = ['-created']
