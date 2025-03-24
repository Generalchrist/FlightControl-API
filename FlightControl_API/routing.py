from django.urls import re_path
from .consumers import PlaneConsumer

websocket_urlpatterns = [
    re_path(r'ws/planes/$', PlaneConsumer.as_asgi()),
]
