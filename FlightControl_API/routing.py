from django.urls import re_path
from .consumers import PlaneConsumer

websocket_urlpatterns = [
    re_path(r'ws/planes/$', PlaneConsumer.as_asgi()),
    re_path(r'ws/commands/$', PlaneConsumer.as_asgi()),
]
