
from datetime import datetime
import json

from django import forms
from django.forms import DateTimeInput, DateInput, ClearableFileInput
from django.utils.safestring import mark_safe
from django.utils.encoding import force_str
from django.utils.formats import get_format
from django.utils.translation import get_language
from django.conf import settings
from django.template.loader import render_to_string


# Tempus Dominus 5.0.0-alpha14
class DateTimePickerInput(DateTimeInput):
    template_name = 'utils/bootstrap_datetimepicker.html'

    def get_context(self, name, value, attrs):
        datetimepicker_id = 'datetimepicker_{name}'.format(name=name)
        if attrs is None:
            attrs = dict()
        attrs['data-target'] = '#{id}'.format(id=datetimepicker_id)
        attrs['class'] = 'form-control datetimepicker-input'
        context = super().get_context(name, value, attrs)
        context['widget']['datetimepicker_id'] = datetimepicker_id
        return context


class DatePickerInput(DateInput):
    template_name = 'utils/bootstrap_datepicker.html'

    def get_context(self, name, value, attrs):
        datetimepicker_id = 'datetimepicker_{name}'.format(name=name)
        if attrs is None:
            attrs = dict()
        attrs['data-target'] = '#{id}'.format(id=datetimepicker_id)
        attrs['class'] = 'form-control datetimepicker-input'
        context = super().get_context(name, value, attrs)
        context['widget']['datetimepicker_id'] = datetimepicker_id
        return context


# Tempus Dominus 5.1.2
def cdn_media():
    """
    Returns the CDN locations for Tempus Dominus, included by default.
    """
    css = {
        "all": (
            "//cdnjs.cloudflare.com/ajax/libs/tempusdominus-bootstrap-4/5.1.2/css/tempusdominus-bootstrap-4.min.css",
        )
    }

    if getattr(settings, "TEMPUS_DOMINUS_LOCALIZE", False):
        moment = "moment-with-locales"
    else:
        moment = "moment"

    js = (
        (
            "//cdnjs.cloudflare.com/ajax/libs/moment.js/2.22.2/"
            "{moment}.min.js".format(moment=moment)
        ),
        (
            "//cdnjs.cloudflare.com/ajax/libs/tempusdominus-bootstrap-4/"
            "5.1.2/js/tempusdominus-bootstrap-4.min.js"
        ),
    )

    return forms.Media(css=css, js=js)


class TempusDominusMixin:
    """
    The Tempus Dominus Mixin contains shared functionality for the three types of date
    pickers offered.
    """

    def __init__(self, attrs=None, options=None):
        super().__init__()

        # Set default options to include a clock item, otherwise datetimepicker
        # shows no icon to switch into time mode
        self.js_options = {
            "format": self.get_js_format(),
            "icons": {"time": "fa fa-clock-o"},
        }
        # If a dictionary of options is passed, combine it with our pre-set js_options.
        if isinstance(options, dict):
            self.js_options = {**self.js_options, **options}
        # save any additional attributes that the user defined in self
        self.attrs = attrs or {}

    @property
    def media(self):
        if getattr(settings, "TEMPUS_DOMINUS_INCLUDE_ASSETS", True):
            return cdn_media()
        return forms.Media()

    def render(self, name, value, attrs=None, renderer=None):
        context = super().get_context(name, value, attrs)

        # self.attrs = user-defined attributes from __init__
        # attrs = attributes added for rendering.
        # context['attrs'] contains a merge of self.attrs and attrs
        # NB If crispy forms is used, it will already contain
        # 'class': 'datepicker form-control'
        # for DatePicker widget

        all_attrs = context["widget"]["attrs"]
        all_attrs["id"] = all_attrs["id"].replace('-', '_')
        cls = all_attrs.get("class", "")
        if "form-control" not in cls:
            cls = "form-control " + cls

        # Add the attribute that makes datepicker popup close when focus is lost
        cls += " datetimepicker-input"
        all_attrs["class"] = cls

        # defaults for our widget attributes
        input_toggle = True
        icon_toggle = True
        input_group = True
        append = ""
        prepend = ""
        size = ""

        attr_html = ""
        for attr_key, attr_value in all_attrs.items():
            if attr_key == "prepend":
                prepend = attr_value
            elif attr_key == "append":
                append = attr_value
            elif attr_key == "input_toggle":
                input_toggle = attr_value
            elif attr_key == "input_group":
                input_group = attr_value
            elif attr_key == "icon_toggle":
                icon_toggle = attr_value
            elif attr_key == "size":
                size = attr_value
            elif attr_key == "icon_toggle":
                icon_toggle = attr_value
            else:
                attr_html += ' {key}="{value}"'.format(key=attr_key, value=attr_value)

        options = {}
        options.update(self.js_options)

        if (
            getattr(settings, "TEMPUS_DOMINUS_LOCALIZE", False) and
            "locale" not in self.js_options
        ):
            options["locale"] = get_language()

        if context["widget"]["value"] is not None:
            # Append an option to set the datepicker's value using a Javascript
            # moment object
            options.update(self.moment_option(value))

        # picker_id below has to be changed to underscores, as hyphens are not
        # valid in JS function names.
        field_html = render_to_string(
            "utils/tempus_dominus_widget_5.1.2.html",
            {
                "type": context["widget"]["type"],
                "picker_id": context["widget"]["attrs"]["id"].replace("-", "_"),
                "name": context["widget"]["name"],
                "attrs": mark_safe(attr_html),
                "js_options": mark_safe(json.dumps(options)),
                "prepend": prepend,
                "append": append,
                "icon_toggle": icon_toggle,
                "input_toggle": input_toggle,
                "input_group": input_group,
                "size": size,
            },
        )

        return mark_safe(force_text(field_html))

    def moment_option(self, value):
        """
        Returns an option dict to set the default date and/or time using a Javascript
        moment object. When a form is first instantiated, value is a date, time or
        datetime object, but after a form has been submitted with an error and
        re-rendered, value contains a formatted string that we need to parse back to a
        date, time or datetime object.
        """
        if isinstance(value, str):
            if isinstance(self, DatePicker):
                formats = "DATE_INPUT_FORMATS"
            elif isinstance(self, TimePicker):
                formats = "TIME_INPUT_FORMATS"
            else:
                formats = "DATETIME_INPUT_FORMATS"
            fmts = get_format(formats)
            if isinstance(self, TimePicker):
                fmts = fmts + ['%I:%M:%S %p', '%I:%M %p']
            for fmt in fmts:
                try:
                    value = datetime.strptime(value, fmt)
                    break
                except (ValueError, TypeError):
                    continue
            else:
                return {}

        # Append an option to set the datepicker's value using iso formatted string
        iso_date = value.isoformat()

        # iso format for time requires a prepended T
        # if isinstance(self, TimePicker):
        #     iso_date = "T" + iso_date
        #    iso_date = iso_date.split('T')[1]

        return {"date": iso_date}

    def get_js_format(self):
        raise NotImplementedError


class DatePicker(TempusDominusMixin, forms.widgets.DateInput):
    """
    Widget for Tempus Dominus DatePicker.
    """

    def get_js_format(self):
        if getattr(settings, "TEMPUS_DOMINUS_LOCALIZE", False):
            js_format = "L"
        else:
            js_format = "YYYY-MM-DD"
        return js_format


class DateTimePicker(TempusDominusMixin, forms.widgets.DateTimeInput):
    """
    Widget for Tempus Dominus DateTimePicker.
    """

    def get_js_format(self):
        if getattr(settings, "TEMPUS_DOMINUS_LOCALIZE", False):
            js_format = "L LTS"
        else:
            js_format = "YYYY-MM-DD HH:mm:ss"
        return js_format


class TimePicker(TempusDominusMixin, forms.widgets.TimeInput):
    """
    Widget for Tempus Dominus TimePicker.
    """

    def get_js_format(self):
        if getattr(settings, "TEMPUS_DOMINUS_LOCALIZE", False):
            js_format = "LTS"
        else:
            js_format = "HH:mm:ss"
        return js_format


class CustomDateInput(DateInput):
    template_name = 'utils/custom_date_input.html'


class CustomSwitchInput(forms.widgets.CheckboxInput):
    template_name = 'utils/custom_switch_input.html'


class BootstrapFileUploadInput(ClearableFileInput):
    template_name = 'utils/bootstrap_fileupload_widget.html'

    def get_context(self, name, value, attrs):
        custom_file_id = 'custom_file_{name}'.format(name=name)
        if attrs is None:
            attrs = dict()
        context = super().get_context(name, value, attrs)
        context['widget']['custom_file_id'] = custom_file_id
        return context


class CustomNumberInput(forms.widgets.NumberInput):
    template_name = 'utils/custom_number_input.html'


class CustomRadioSelect(forms.widgets.RadioSelect):
    template_name = "utils/custom_radio_select.html"
    option_template_name = "utils/custom_input_option.html"


class BootstrapRadioSelect(forms.widgets.RadioSelect):
    template_name = "utils/bs_radio_select.html"
    option_template_name = "utils/bs_input_option.html"


class SliderSelect(forms.widgets.NumberInput):
    template_name = 'utils/slide_select.html'


class RangeSelect(forms.widgets.SelectMultiple):
    template_name = 'utils/slide_select.html'
