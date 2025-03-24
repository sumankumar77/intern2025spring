"""chealth URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include, re_path
from django.conf import settings
from django.conf.urls.static import static

from chealth.middleware import login_not_required, session_security_exempt
from apps.django_encrypted_filefield.constants import FETCH_URL_NAME
from . import views
from apps.dashboard.views import chat_api


urlpatterns = [
    path('', login_not_required(views.home), name='home'),
    path('index/', login_not_required(views.index), name='index'),
    path('about-us/', login_not_required(views.about_us), name='about_us'),
    path('terms-of-service/', login_not_required(views.terms_of_service), name='terms_of_service'),
    path('privacy-policy/', login_not_required(views.privacy_policy), name='privacy_policy'),
    path('faq/', login_not_required(views.faq), name='faq'),
    path('contact-us/', login_not_required(views.contact_us), name='contact_us'),
    path('', include('apps.utils.urls')),
    path('user/', include('apps.user.urls')),
    path('messages/', include('apps.msgs.urls')),
    path('session_security/', include('apps.session_security.urls')),
    path('admin/', admin.site.urls),
    path('social-auth/', include('social_django.urls', namespace='social')),
    path('dashboard/', include('apps.dashboard.urls')), # Dashboard URLs
    path('chat-api/', chat_api, name='chat_api'),
    re_path(r"^fetch/(?P<path>.+)", session_security_exempt(views.CHFetchView.as_view()), name=FETCH_URL_NAME),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

if not settings.DEBUG:
    handler400 = 'chealth.views.bad_request'
    handler403 = 'chealth.views.permission_denied'
    handler404 = 'chealth.views.page_not_found'
    handler500 = 'chealth.views.server_error'


admin.site.site_header = "Connected Health Admin"
admin.site.site_title = "Connected Health - Admin Portal"
admin.site.index_title = "Welcome to Connected Health"
