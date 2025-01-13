from django.urls import path
from django.views.generic import RedirectView

from .views import *

urlpatterns = [
    path('', RedirectView.as_view(permanent=True, url='inbox/'), name='messages_redirect'),
    #path('v1/inbox/', inbox, name='messages_inbox'),
    path('outbox/', outbox, name='messages_outbox'),
    # path('compose/', compose, name='messages_compose'),
    # path('compose/<recipient>/', compose, name='messages_compose_to'),
    # path('reply/<message_id>/', reply, name='messages_reply'),
    #path('v1/view/<message_id>/', view, name='messages_detail'),
    # path('delete/<message_id>/', delete, name='messages_delete'),
    # path('undelete/<message_id>/', undelete, name='messages_undelete'),
    # path('trash/', trash, name='messages_trash'),
    path('move-to-trash/<message_id>/', move_to_trash, name='move_to_trash'),
    # path('move_to_inbox/<message_id>/', move_to_inbox, name='move_to_inbox'),
    # path('communications/<contact>/', communications, name='communications'),
    path('inbox/', inbox_v2, name='messages_inbox_v2'),
    path('view/<message_id>/', view_v2, name='messages_detail_v2')
]
