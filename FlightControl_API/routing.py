from django.urls import re_path
from FlightControl_API.consumers.planeConsumer import PlaneConsumer
from FlightControl_API.consumers.commandConsumer import CommandConsumer

websocket_urlpatterns = [
    re_path(r'ws/planes/$', PlaneConsumer.as_asgi()),
    re_path(r'ws/commands/$', CommandConsumer.as_asgi()),
]
