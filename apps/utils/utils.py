import datetime
import dateutil
from zoneinfo import ZoneInfo, available_timezones
from io import BytesIO
from PIL import Image
from typing import Union, Optional
import uuid
import os.path

from kombu import Connection
from django import forms
from django.core.files import File
from django.conf import settings as conf_settings
from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.template.loader import render_to_string
from django.utils import timezone, dateparse
from .widgets import SliderSelect, RangeSelect

from . import constants as C

User = get_user_model()


class AccountActivationTokenGenerator(PasswordResetTokenGenerator):
    def _make_hash_value(self, user, timestamp):
        return (
                str(user.pk) + str(timestamp) + str(user.email_confirmed)
        )


account_activation_token = AccountActivationTokenGenerator()


def base36encode(number, alphabet='0123456789abcdefghijklmnopqrstuvwxyz'):
    """Converts an integer to a base36 string."""
    if not isinstance(number, int):
        raise TypeError('number must be an integer')

    base36 = ''
    sign = ''

    if number < 0:
        sign = '-'
        number = -number

    if 0 <= number < len(alphabet):
        return sign + alphabet[number]

    while number != 0:
        number, i = divmod(number, len(alphabet))
        base36 = alphabet[i] + base36

    return sign + base36


def base36decode(number):
    return int(number, 36)


def base64charencode(binary, alphabet='0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ-~'):
    """Convert a binary to a base64 character. No sign allowed"""
    bstr = list(str(binary))
    if len(bstr) > 6 or not all([s == '0' or s == '1' for s in list(str(binary))]):
        raise TypeError('Input must be a binary number and less than 7 digit')
    pp = len(bstr) - 1
    return alphabet[sum([2**(pp - i)*int(b) for i, b in enumerate(bstr)])]


def base64chardecode(char, alphabet='0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ-~'):
    try:
        number = alphabet.index(char)
        binary = ''
        while number != 0:
            number, i = divmod(number, 2)
            binary = str(i) + binary
        return '0'*(6 - len(binary)) + binary
    except ValueError:
        return None


def send_email_to(user, subject, content):
    message = render_to_string('general_email.html', {
        'user': user,
        'content': content
    })
    user.email_user(subject, message)


def pk2uid(pk):
    prefix = conf_settings.UID_PREFIX
    uid = base36encode(pk)
    if len(uid) < 8:
        uid = (8 - len(uid))*'0' + uid
    return prefix + uid


def to_0decimal(v):
    return '{:.0f}'.format(v)


def to_1decimal(v):
    return '{:.1f}'.format(v)


def to_2decimal(v):
    return '{:.2f}'.format(v)


def awareize_date(date: datetime.datetime, tz=timezone.get_current_timezone(), eod: bool = False) -> datetime.datetime:
    unaware = datetime.datetime.combine(date, datetime.datetime.min.time())
    return timezone.make_aware(unaware, tz) + datetime.timedelta(seconds=C.DAY_SECS) if eod \
        else timezone.make_aware(unaware, tz)


def awareize_date_iso(date_iso: str, tz=timezone.get_current_timezone(), eod: bool = False) -> datetime.datetime:
    unaware = datetime.datetime.strptime(date_iso, '%Y-%m-%d')
    return awareize_date(unaware, tz=tz, eod=eod)


def is_nan(f):
    return f != f


def is_integer(s):
    if s is None:
        return False
    try:
        int(s)
        return True
    except ValueError:
        return False


def is_float(s):
    if s is None:
        return False
    try:
        float(s)
        return True
    except ValueError:
        return False


def is_fraction(s):
    values = s.split('/')
    return len(values) == 2 and all(i.isdigit() for i in values)


def yield_date(start_date, end_date):
    sdate = start_date if isinstance(start_date, datetime.date) else dateparse.parse_date(start_date)
    edate = end_date if isinstance(end_date, datetime.date) else dateparse.parse_date(end_date)
    days_max = (edate - sdate).days + 1
    for days in range(0, days_max):
        yield sdate + datetime.timedelta(days=days)


def serialize_request_meta(meta):
    keys = ['CONTENT_LENGTH', 'CONTEXT_TYPE', 'HTTP_REFERER', 'QUERY_STRING',
            'REMOTE_ADDR', 'REMOTE_HOST', 'REMOTE_USER', 'REQUEST_METHOD', 'HTTP_COOKIE']
    s = ''
    for k in keys:
        if meta.get(k):
            s += '{}:{};'.format(k, meta.get(k))
    return s


def get_email_recipients(emails):
    recipients = [User.objects.get(email=email).username for email in emails
                  if User.objects.filter(email=email).exists()]
    if len(recipients) == 1:
        return recipients[0]
    elif len(recipients) == 2:
        return '%s and %s' % tuple(recipients)
    elif len(recipients) == 2:
        return '%s, %s, and %s' % tuple(recipients)
    else:
        return 'all'


def ts_to_iso(ts):
    # convert timestamp to iso
    return datetime.datetime.fromtimestamp(ts).isoformat()


def iso_to_ts(iso, eod=False):
    # convert iso date to timestamp
    dt = iso + ('T23:59:59' if eod else 'T00:00:00')
    return dateparse.parse_datetime(dt).timestamp()


def is_tz_aware(dt: datetime.datetime) -> bool:
    return (dt.tzinfo is not None) and (dt.tzinfo.utcoffset(dt) is not None)


def to_local_tz(utc_time):
    to_zone = dateutil.tz.tzlocal()
    return utc_time.astimezone(to_zone)


def tz_diff(tz0, tz1, in_seconds=False):
    # accepts pytz time zones
    # e.g tz0, tz1 = "Asian/Hong_Kong", "America/New_York"
    if isinstance(tz0, str):
        # tz0 = pytz.timezone(tz0)
        tz0 = ZoneInfo(tz0)
    if isinstance(tz1, str):
        # tz1 = pytz.timezone(tz1)
        tz1 = ZoneInfo(tz1)
    dt = datetime.datetime.now()
    utc_off0, utc_off1 = dt.astimezone(tz0).utcoffset(), dt.astimezone(tz1).utcoffset()
    diff = (utc_off1 - utc_off0).total_seconds()

    return diff if in_seconds else int(diff/3600)


def parse_date(dt: str | datetime.date | None) -> Optional[datetime.date]:
    try:
        if not dt:
            return None
        elif isinstance(dt, datetime.date):
            return dt
        else:
            return datetime.datetime.strptime(dt, C.ISO_DATE_FMT).date()
    except ValueError:
        try:
            return datetime.datetime.strptime(dt, C.US_DATE_FMT).date()
        except ValueError:
            return None


def to_us_date(dt) -> str:
    if isinstance(dt, datetime.datetime):
        return dt.strftime(C.US_DATE_FMT)
    elif isinstance(dt, datetime.date):
        return '{}/{}/{}'.format(dt.month, dt.day, dt.year)
    else:
        return ''


def get_date_obj(dt):
    return dateparse.parse_date(dt) if isinstance(dt, str) else dt


def get_date_iso(dt):
    return dt.isoformat() if isinstance(dt, datetime.date) else dt


def date_diff(dt0, dt1):
    dt0_, dt1_ = dt0, dt1
    if isinstance(dt0_, str):
        dt0_ = dateparse.parse_date(dt0_)
    if isinstance(dt1_, str):
        dt1_ = dateparse.parse_date(dt1_)
    if dt0_ and dt1_:
        return (dt1_ - dt0_).days


def datetime_diff(dt0, dt1):
    dt0_, dt1_ = dt0, dt1
    if isinstance(dt0_, str):
        dt0_ = dateparse.parse_datetime(dt0_)
    if isinstance(dt1_, str):
        dt1_ = dateparse.parse_datetime(dt1_)
    if dt0_ and dt1_:
        return (dt1_ - dt0_).total_seconds()


def cal_date(dt, delta_days, iso: Optional[bool] = None):
    dt0 = dt
    if isinstance(dt0, str):
        dt0 = dateparse.parse_date(dt0)
    if not dt0:
        return
    dt1 = dt0 + datetime.timedelta(days=delta_days)
    if iso is True:
        return dt1.isoformat()
    elif iso is False:
        return dt1
    else:
        return dt1.isoformat() if isinstance(dt, str) else dt1


def calc_datetime(dt, delta_seconds, iso=False):
    dt0 = dt
    if isinstance(dt0, str):
        dt0 = dateparse.parse_datetime(dt0)
    if not dt0:
        return
    dt1 = dt0 + datetime.timedelta(seconds=delta_seconds)
    return dt1.isoformat() if iso else dt1


def combine_date_time(date, time, iso=False):
    dt, tm = date, time
    if isinstance(date, str):
        dt = dateparse.parse_date(date)
    if isinstance(time, str):
        tm = dateparse.parse_time(time)
    if dt and tm:
        return datetime.datetime.combine(dt, tm).isoformat() if iso else datetime.datetime.combine(dt, tm)
    else:
        return


def monthrange(year, month, iso=False):
    try:
        start_date = datetime.date(int(year), int(month), 1)
        end_date = (datetime.date(int(year) + 1, 1, 1) - datetime.timedelta(days=1)) if int(month) == 12 \
            else (datetime.date(int(year), int(month) + 1, 1) - datetime.timedelta(days=1))
        return (start_date.isoformat(), end_date.isoformat()) if iso else (start_date, end_date)
    except Exception:
        return None, None


def tz_conversion(t0, tz0, tz1):
    pass


def to_iso_tz_fmt(dt):
    if isinstance(dt, str):
        dt = dateparse.parse_datetime(dt)
    elif isinstance(dt, int):
        dt = datetime.datetime.fromtimestamp(dt)
    elif isinstance(dt, datetime.datetime):
        pass
    else:
        return
    return dt.strftime(C.ISO_DATETIME_TZ_FMT)


def get_utc_timestamp(in_millisecond=False, from_dt=None):
    # dt = from_dt.astimezone(pytz.utc) if from_dt else datetime.datetime.now(timezone.utc)
    dt = from_dt.astimezone(timezone.utc) if from_dt else datetime.datetime.now(timezone.utc)
    return int(dt.timestamp()*1000) if in_millisecond else int(dt.timestamp())


def get_or_none(Model, query_params):
    try:
        ins = Model.objects.get(**query_params)
    except Model.DoesNotExist:
        ins = None
    return ins


def get_model_params(data, attrs, char_fields=None):
    char_fields = char_fields or []
    params = {}
    for s_attr, t_attr in attrs.items():
        if isinstance(t_attr, dict):
            params.update(get_model_params(data[s_attr], attrs[s_attr], char_fields=char_fields))
        else:
            t_val = data.get(s_attr, '') or '' if t_attr in char_fields else (data.get(s_attr) or None)
            params[t_attr] = t_val
    return params


def set_model_attrs(model, params):
    for attr, val in params.items():
        setattr(model, attr, val)
    return model


def create_or_update_model_instance(Model, attrs, resp, query_params, char_fields=None,
                                    check_update_attrs=None, always_update=False):
    """
    check_update_attrs is a dictionary that contains
    source attribute from resp (key) and target attribute from model instance (value)
    if the corresponding values are different, then update the model instance
    """
    model_params = get_model_params(resp, attrs, char_fields=char_fields)
    model = Model.objects.filter(**query_params).first()
    if model:
        # model = Model.objects.get(**query_params)
        if always_update or \
                (check_update_attrs and not all([resp.get(s_attr) == getattr(model, t_attr)
                                                 for s_attr, t_attr in check_update_attrs.items()])):
            set_model_attrs(model, model_params)
            model.save()
    else:
        model_params.update(query_params)
        model = Model.objects.create(**model_params)
    return model


def delete_if_exists(Model, filter_params):
    if Model.objects.filter(**filter_params).exists():
        Model.objects.filter(**filter_params).delete()


def get_form_json_errors(field_name, message, code='invalid', json_errors=None):
    if isinstance(json_errors, dict):
        json_errors.update({field_name: [{'message': message, 'code': code}]})
    else:
        json_errors = {field_name: [{'message': message, 'code': code}]}
    return json_errors


def flat_form_json_errors(json_errors: dict) -> dict:
    errors = {}
    for field, field_errors in json_errors.items():
        error = ' '.join([err['message'] for err in field_errors])
        errors[field] = error
    return errors


def json_errors_to_error(json_errors: dict) -> dict:
    errors = []
    for field, field_errors in json_errors.items():
        error = ', '.join([err['message'] for err in field_errors])
        if error not in errors:
            errors.append(error)
    return {'error': '; '.join(errors)}


def get_error_response(res, unknown_error='Unknown error') -> dict:
    if not isinstance(res, dict):
        return {'error': unknown_error}
    return json_errors_to_error(res['errors']) if res.get('errors') else {'error': res.get('error') or unknown_error}


def get_site_url(request):
    absolute_url = request.build_absoulte_uri()
    return absolute_url.replace(request.path, '')


def merge_dicts(dict1, dict2):
    for k, v in dict2.items():
        if dict1.get(k):
            dict1[k].update(v)
        else:
            dict1.update({k: v})
    return dict1


def compress_image(image, name=None, max_image_size=5242880):
    quality = max_image_size / image.size * 100 if image.size > max_image_size else 100
    im = Image.open(image)
    # Pillow Image Modes
    # https://pillow.readthedocs.io/en/latest/handbook/concepts.html#modes
    fmt = 'PNG' if im.mode == 'RGBA' or im.mode == 'P' else 'JPEG'
    im_io = BytesIO()
    im.save(im_io, fmt, quality=int(quality))
    new_image = File(im_io, name=name or image.name)
    return new_image


def generate_uuid4_filename(filename):
    """
    Generates a uuid4 (random) filename, keeping file extension
    :param filename: Filename passed in. In the general case, this will
                     be provided by django-ckeditor's uploader.
    :return: Randomized filename in urn format.
    :rtype: str
    """
    discard, ext = os.path.splitext(filename)
    basename = str(uuid.uuid4())
    return ''.join([basename, ext])


def stddev(ls: list):
    return (sum((x - (sum(ls) / len(ls))) ** 2 for x in ls) / (len(ls) - 1)) ** 0.5


def us_weekday(dt: datetime.date):
    return (dt.weekday() + 1) % 7


def get_dt_at_tz(dt: datetime.datetime, tz: Union[str, ZoneInfo]) -> datetime.datetime:
    if isinstance(tz, str):
        return dt.astimezone(ZoneInfo(tz))
    else:
        return dt.astimezone(tz)


def is_celery_connected():
    try:
        broker_url = conf_settings.CELERY_BROKER_URL
        connection = Connection(broker_url)
        connection.connect()
        connection.close()
        return True
    except (AttributeError, ConnectionError):
        return False


def get_all_timezones_with_offsets():
    timezones = []
    now = datetime.datetime.now()
    tz_names = []
    # excludes = []
    for tz_name in available_timezones():
        tz = tz_name
        if 'Etc' not in tz and 'GMT' not in tz and 'HST' not in tz and 'CET' not in tz and 'WET' not in tz \
                and 'YST' not in tz and 'PST' not in tz and tz != 'MST' and tz != 'localtime' \
                and 'EST' not in tz and 'CST' not in tz and tz != 'UTC' and tz != 'Factory' and 'GB' not in tz \
                and tz != 'Universal' and 'NZ' not in tz and tz != 'UCT' and tz != 'MET' and tz != 'ROC' \
                and tz != 'PRC' and tz != 'W-SU' and tz != 'EET' and tz != 'ROK' and tz != 'MST7MDT' \
                and 'System' not in tz:
            tz = ZoneInfo(tz_name)
            offset = tz.utcoffset(now).total_seconds() / 3600
            timezones.append([tz_name, offset])
            tz_names.append(tz_name)
        # else:
        #    excludes.append(tz_name)
    timezones.sort(key=lambda x: x[1])
    return timezones


def get_attrs_dict(src_attrs, list_attrs):
    dest_attrs = {}
    for attr in list_attrs:
        if src_attrs.get(attr):
            dest_attrs[attr] = src_attrs[attr]
    return dest_attrs


def get_json_form(form):
    json_form = []
    for field in form.visible_fields():
        json_field = {
            'label': field.label,
            'name': field.name,
            'helpText': field.help_text
        }
        if isinstance(field.field, forms.CharField):
            if isinstance(field.field.widget, forms.TextInput):
                json_field['type'] = 'text'
            elif isinstance(field.field.widget, forms.Textarea):
                json_field['type'] = 'textarea'
                if field.field.widget.attrs.get('rows'):
                    json_field['rows'] = field.field.widget.attrs['rows']
        elif isinstance(field.field, forms.FloatField):
            json_field['type'] = 'number'
        elif isinstance(field.field, forms.ChoiceField):
            json_field['options'] = field.field.choices
            if isinstance(field.field, forms.MultipleChoiceField):
                # MultipleChoiceField is a subclass of ChoiceField
                if isinstance(field.field.widget, RangeSelect):
                    json_field['type'] = 'range'
                    json_field['isRange'] = True
                    json_field.update(get_attrs_dict(field.field.widget.attrs, ['min', 'max', 'step']))
                elif isinstance(field.field.widget, forms.SelectMultiple):
                    json_field['type'] = 'select'
                    json_field['multiple'] = True
                elif isinstance(field.field.widget, forms.CheckboxSelectMultiple):
                    json_field['type'] = 'multicheck'
            elif isinstance(field.field.widget, forms.Select):
                json_field['type'] = 'select'
            elif isinstance(field.field.widget, forms.RadioSelect):
                json_field['type'] = 'radio'
        elif isinstance(field.field, forms.BooleanField):
            if isinstance(field.field.widget, forms.CheckboxInput):
                json_field['type'] = 'checkbox'
        elif isinstance(field.field, forms.IntegerField):
            if isinstance(field.field.widget, SliderSelect):
                json_field['type'] = 'range'
                json_field.update(get_attrs_dict(field.field.widget.attrs, ['min', 'max', 'step']))
        elif isinstance(field.field, forms.FileField):
            json_field['type'] = 'file'
            json_field.update(get_attrs_dict(field.field.widget.attrs, ['useChooseButton', 'showDragAndDrop']))

        json_form.append(json_field)
    return json_form
