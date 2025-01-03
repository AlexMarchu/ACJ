from django.urls import re_path, path

from channels_app.consumers import TestResultConsumer

websocket_urlpatterns = [
    path('ws/submission/<int:submission_id>/', TestResultConsumer.as_asgi()),
]
