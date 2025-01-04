import json

from asgiref.sync import async_to_sync
from channels.generic.websocket import WebsocketConsumer


class TestResultConsumer(WebsocketConsumer):

    def connect(self):
        self.submission_id = self.scope['url_route']['kwargs']['submission_id']
        self.group_name = f"submission_{self.submission_id}"

        async_to_sync(self.channel_layer.group_add)(self.group_name, self.channel_name)

        self.accept()

    def disconnect(self, code):
        async_to_sync(self.channel_layer.group_discard)(self.group_name, self.channel_name)

    def send_test_results(self, event):
        self.send(text_data=json.dumps(event['data']))
