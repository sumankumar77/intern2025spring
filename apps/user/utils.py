from PIL import Image, ImageOps
from io import BytesIO as IO
import datetime
import uuid
import os
from django.conf import settings as conf_settings
# from django.contrib.sites.shortcuts import get_current_site
from django.core.files.uploadedfile import SimpleUploadedFile
from django.template.loader import render_to_string
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode

from axes import helpers as axes_helpers
from social_django.models import UserSocialAuth
from apps.utils.constants import ENC_PATH_USER_PROFILE_IMAGE
from apps.utils.utils import account_activation_token
from .models import Connection


def send_activation_email(request, user):
    # current_site = get_current_site(request)
    domain = request.build_absolute_uri('/')[:-1]
    subject = 'Activate Your Account'
    # protocol = 'https' if request.is_secure() else 'http'
    message = render_to_string('user/account_activation_email.html', {
        'user': user,
        'domain': domain,
        'uid': urlsafe_base64_encode(force_bytes(user.pk)),
        'token': account_activation_token.make_token(user),
    })
    user.email_user(subject, message)


def get_axes_remained_attempts(request, credentials):
    """
    failures = 0
    attempts = get_user_attempts(request, credentials)
    cache_hash_key = axes_helpers.get_client_cache_key(request, credentials)

    failures_cached = axes_helpers.get_cache().get(cache_hash_key)
    if failures_cached is not None:
        failures = failures_cached
    else:
        for attempt in attempts:
            failures = max(failures, attempt.failures_since_start)
    failure_limit = axes_helpers.get_failure_limit(request, credentials)
    """
    failures = request.axes_failures_since_start
    failure_limit = axes_helpers.get_failure_limit(request, credentials)
    return failure_limit - failures


def generate_unique_image_name(length=8):
    path = conf_settings.MEDIA_ROOT + ENC_PATH_USER_PROFILE_IMAGE + 'img_'
    s = uuid.uuid4().hex.lower()[0:length]
    while os.path.isfile(path + s + '.jpg'):
        s = uuid.uuid4().hex.lower()[0:length]
    return 'img_' + s + '.jpg'


def resize(file_, max_width=480, max_height=480, crop=1):
    """
    :param file_: InMemoryUploadedFile
    :param max_width:
    :param max_height:
    :param crop: crop to center image
    :return:
    """
    max_width = int(max_width)
    max_height = int(max_height)
    crop = int(crop)

    if max_width == 0 and max_height == 0:
        return file_

    max_width = 9999 if max_width == 0 else max_width
    max_height = 9999 if max_height == 0 else max_height

    size = (max_width, max_height)
    image = Image.open(file_)

    if image.mode == 'RGBA':
        image.load()
        background = Image.new('RGB', image.size, (255, 255, 255))
        background.paste(image, mask=image.split()[3])
        image = background

    temp = IO()

    if crop == 1:
        image = ImageOps.fit(image, size, Image.ANTIALIAS)
    else:
        image.thumbnail(size, Image.ANTIALIAS)

    image.save(temp, 'jpeg')
    temp.seek(0)
    # InMemoryUploadedFile(temp, 'ImageField', "%s.jpg" % self.image.name.split('.')[0], 'image/jpeg', output.len, None)

    return SimpleUploadedFile(generate_unique_image_name(), temp.read(), content_type='image/jpeg')


def get_social_auth_logins(user):
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
    return {'google': google_login, 'twitter': twitter_login, 'facebook': facebook_login}


def create_connection(user_grant_perm, user_req_perm):
    conn, _ = Connection.objects.get_or_create(user_grant_perm=user_grant_perm, user_req_perm=user_req_perm)
    conn.updated = datetime.date.today()
    conn.host_confirmed = True
    conn.guest_confirmed = True
    conn.save()
