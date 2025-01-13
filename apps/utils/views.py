import json
from django.http import JsonResponse
from django.shortcuts import render

from .utils import get_all_timezones_with_offsets, get_json_form
from .forms import JsTestForm


def pdf_view(request, app, filename):
    doc_name = ''
    doc_path = 'main/{app}/{filename}.pdf'.format(app=app, filename=filename)
    return render(request, 'utils/pdf_view.html', {
        'doc_name': doc_name,
        'doc_path': doc_path,
    })


def bs_form(request):
    if request.method == 'POST':
        print(request.POST, request.FILES)
        form = JsTestForm(request.POST, request.FILES)
        if form.is_valid():
            print('valid form')
            return JsonResponse({'success': True})
        else:
            print(form.errors.get_json_data())
            return JsonResponse({'errors': form.errors.get_json_data()})
    else:
        timezones = get_all_timezones_with_offsets()
        return render(request, 'utils/bs_form_playground.html', {
            'timezones': timezones,
            'form': json.dumps(get_json_form(JsTestForm()))
        })


def html_email_template_view(request, app, template_name):
    # Example URL:
    # http://localhost:8000/email-template/plwh_ema/survey_email_template/?date_time=10/2/24%207:15%20AM&url=https://digitalhealth.fsu.edu/
    html_path = '{app}/{template_name}.html'.format(app=app, template_name=template_name)
    params = dict([(k, v) for k, v in request.GET.items()])
    return render(request, html_path, params)
