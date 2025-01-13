from django.urls import path
# from django.views.generic import TemplateView

from chealth.middleware import login_not_required
from . import views

urlpatterns = [
    path('doc/pdf/<app>/<filename>/', login_not_required(views.pdf_view), name='pdf_view'),
    path('pg/bs-form/', login_not_required(views.bs_form), name='bs_form'),
    path('email-template/<app>/<template_name>/',
         login_not_required(views.html_email_template_view), name='email_template_view')
]
