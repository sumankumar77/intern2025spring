from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model
from django.db.models import Q

User = get_user_model()


class EmailOrUsernameModelBackend(ModelBackend):
    def authenticate(self, request, username=None, password=None, **kwargs):
        # The `username` field is allows to contain `@` characters so
        # technically a given email address could be present in either field,
        # possibly even for different users, so we'll query for all matching
        # records and test each one.
        users = User._default_manager.filter(
            Q(username__iexact=username) | Q(email__iexact=username))

        # Test whether any matched user has the provided password:
        for user in users:
            if user.check_password(password):
                return user
        if not users:
            # Run the default password hasher once to reduce the timing
            # difference between an existing and a non-existing user (see
            # https://code.djangoproject.com/ticket/20760)
            User().set_password(password)

    def get_user(self, user_id):
        try:
            user = User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None

        return user if self.user_can_authenticate(user) else None
