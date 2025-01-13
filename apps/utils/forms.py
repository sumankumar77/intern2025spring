from django import forms

from .fields import RangeSliderField
from .widgets import SliderSelect, RangeSelect


class JsTestForm(forms.Form):
    text_field_1 = forms.CharField(label='Plain Text Field', max_length=255,
                                   required=True, help_text='A plain text field')
    select_field_choices = (
        (1, 'Choice 1'),
        (2, 'Choice 2'),
        (3, 'Choice 3'),
    )
    select_field_1 = forms.ChoiceField(label='Dropdown Select Field', choices=select_field_choices,
                                       help_text='A dropdown select field')
    select_field_2 = forms.ChoiceField(label='Radio Select Field', choices=select_field_choices,
                                       help_text='A radio select field', widget=forms.RadioSelect)
    select_field_3 = forms.IntegerField(label='Single Slide Select Field',
                                        widget=SliderSelect(attrs={'min': 1, 'max': 20, 'step': 1, 'reels': True}))
    select_field_4 = RangeSliderField(
        label='Dual Slide Select Field', choices=[(i, str(i)) for i in range(1, 20)],
        widget=RangeSelect(attrs={'min': 1, 'max': 20, 'step': 2, 'labels': True}))
    # Check https://docs.google.com/document/d/1PoV369NNOTZBsOeCWDfecBzMnl8zr8ggGEYrTpIIiRA/edit
    # for using model field with multiselect field
    multiselect_field_choices = (
        (1, 'Choice 1'),
        (2, 'Choice 2'),
        (3, 'Choice 3'),
        (4, 'Choice 4'),
        (5, 'Choice 5'),
        (6, 'Choice 6'),
    )
    multiselect_field_1 = forms.MultipleChoiceField(
        label='Dropdown Multiple Choice Field', choices=multiselect_field_choices, help_text='A multi-select field')
    multiselect_field_2 = forms.MultipleChoiceField(
        label='Checkbox Multiple Choice Field', choices=multiselect_field_choices,
        help_text='A multi-select field', widget=forms.CheckboxSelectMultiple)
    boolean_field_1 = forms.BooleanField(label='Checkbox Boolean Field', required=False)
    # A toggle switch and toggle button boolean fields can be achieved by using customFieldWrapperClass attr in js
    textarea_field_1 = forms.CharField(label='Textarea Field', widget=forms.Textarea(attrs={'rows': 5}),
                                       help_text='A textarea field')
    file_field_1 = forms.FileField(label='File Field', help_text='A plain file field')
    file_field_2 = forms.FileField(
        label='File Field using Choose Button',
        widget=forms.ClearableFileInput(attrs={'useChooseButton': True})
    )
    file_field_3 = forms.FileField(
        label='File Field with Drag and Drop',
        widget=forms.ClearableFileInput(attrs={'useChooseButton': True, 'showDragAndDrop': True})
    )
    # Django does not support multiple files for one input out of box.
    # https://docs.djangoproject.com/en/5.1/topics/http/file-uploads/#uploading-multiple-files

