# sonoshareapp/routing.py

from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    re_path(r'ws/convert_playlist/$', consumers.ConvertPlaylistConsumer.as_asgi()),
]
