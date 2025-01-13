import re
import datetime
from django import template

from apps.utils.utils import awareize_date

register = template.Library()


@register.simple_tag
def define(val=None):
    return val


@register.filter
def get_item(dictionary, key):
    return dictionary.get(key)


@register.filter
def mean(li):
    return sum(li) / len(li)


@register.filter(name='zip')
def zip_lists(a, b):
    return zip(a, b)


@register.filter(name='original')
def msg_original_subject(s):
    while s.startswith('Re:'):
        s = re.sub('^Re:', '', s).strip()
    return s


@register.filter
def get_group_user_count(group):
    return group.users.count()


@register.filter
def delta_date(date_, days):
    return (date_ + datetime.timedelta(days=days)).isoformat()


@register.filter
def sync_time_warning(dt0, dt1):
    if dt0 and dt1 and isinstance(dt0, datetime.datetime) and isinstance(dt1, datetime.datetime) and \
            (dt1 - dt0 > datetime.timedelta(days=1)):
        return True
    else:
        return False


@register.filter
def update_time_warning(dt):
    if dt and isinstance(dt, datetime.datetime) and \
            (awareize_date(datetime.date.today()) - dt > datetime.timedelta(days=1)):
        return True
    else:
        return False


@register.filter
def get_display(s):
    return s.replace('_', ' ')


@register.filter
def starts_with_if(s):
    return s.startswith('if')


@register.filter
def has_substring(s, subs):
    if isinstance(s, str):
        return subs in s
    return False


@register.filter
def not_substring(s, subs):
    if isinstance(s, str):
        return not (subs in s)
    return True


@register.filter
def has_not_attr(obj, attr):
    return not hasattr(obj, attr)


@register.filter
def get_part2_item(field1):
    field2 = field1.replace('part1', 'part2')
    return field2


@register.filter
def has_parts(field):
    return 'part1' in field


@register.filter
def get_field_parts(fields, field_name):
    field = field_name.replace('part1', '')
    parts = []
    for f in fields:
        if field in f.name and f.name != field_name:
            parts.append(f)
    return parts


@register.filter
def not_parts(field):
    return ('part' not in field) or ('part1' in field)


@register.filter
def field_name_no_parts(field):
    return field.split('_part')[0]


@register.filter
def has_section_title(cls):
    if isinstance(cls, str):
        return 'section-title' in cls
    return False


@register.filter
def has_real_section_title(cls):
    if isinstance(cls, str):
        return 'section-title' in cls and 'section-title-0' not in cls
    return False


@register.filter
def get_form_line_classes(cls):
    classes = ''
    form_line_classes = ['section-title', 'as-part', 'last-part', 'form-card-one',
                         'form-card-top', 'form-card-mid', 'form-card-bottom']
    for c in cls.split(' '):
        for fl_cls in form_line_classes:
            if fl_cls in c:
                classes = classes + ' ' + fl_cls
    return classes


@register.filter
def get_section_title(cls):
    cls_st = ''
    for c in cls.split(' '):
        if 'section-title' in c:
            cls_st = c
            break
    return cls_st


@register.filter
def get_header_from_label(label):
    match = re.search('\[header:(.*?)\]', label)
    return match[1]


@register.filter
def get_note_from_label(label):
    match = re.search('\[note:(.*?)\]', label)
    return match[1]


@register.filter
def has_sub_label(label):
    match = re.search('<\[(.*?)\]>', label)
    return True if match else False


@register.filter
def extract_field_label(label):
    result = label
    match = re.search('<\[(.*?)\]>', result)
    if match:
        result = result.replace(match[0], '')
    return result


@register.filter
def extract_field_sub_label(label):
    match = re.search('<\[(.*?)\]>', label)
    return match[1]


@register.filter
def has_inline_checkbox(cls):
    if isinstance(cls, str):
        return 'inline-checkbox' in cls
    return False


@register.filter
def is_list(data):
    return True if isinstance(data, list) else False


@register.filter
def get_display_name(choices, ichoice):
    return dict(choices).get(ichoice)


@register.filter
def add(num0, num1):
    return num0 + num1


@register.filter
def subtract(num0, num1):
    return num0 - num1


@register.filter
def split(string, symbol):
    return string.split(symbol)


@register.filter
def days_since(start_date):
    if not start_date:
        return ''
    today = datetime.date.today()
    sdate = start_date
    if isinstance(start_date, str):
        sdate = datetime.datetime.strptime(start_date, '%Y-%m-%d')
    return (today - sdate).days


@register.filter
def includes(val1, val2):
    if isinstance(val1, list):
        return str(val2) in [str(v) for v in val1]
    else:
        return str(val1) == str(val2)
