from django.urls import path
from .views import home
from .views import chat_api
from .views import transcribe_audio
from .views import upload_file

app_name = "dashboard"

urlpatterns = [
    path('', home, name='dashboard_home'),
    path('chat-api/', chat_api, name='chat_api'),
    path("transcribe/", transcribe_audio, name="transcribe_audio"),
    path("upload/", upload_file, name="upload"),
]
