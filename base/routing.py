# routing.py
from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    re_path(r'ws/new_room/$', consumers.NewRoomConsumer.as_asgi()),
    re_path(r'ws/room/(?P<pk>\w+)/$', consumers.ChatConsumer.as_asgi()),
]
