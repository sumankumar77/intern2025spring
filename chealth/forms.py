from django import forms


class ContactUsForm(forms.Form):
    your_email = forms.EmailField(help_text='Your Email')
    message = forms.CharField(widget=forms.Textarea(attrs={"rows": 10}), help_text='Message')
