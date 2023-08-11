import json
from channels.generic.websocket import WebsocketConsumer
from django.template.defaultfilters import timesince
from .models import Room, Message
from django.contrib.auth import get_user_model
from asgiref.sync import async_to_sync

User = get_user_model()

class ChatConsumer(WebsocketConsumer):
    def connect(self):
        self.room_id = self.scope['url_route']['kwargs']['pk']
        self.room_group_name = f"chat_{self.room_id}"

        async_to_sync(self.channel_layer.group_add) (
            self.room_group_name,
            self.channel_name
        )

        print(self.room_group_name)
        print(self.channel_name)

        self.accept()

    def receive(self, text_data):
        data = json.loads(text_data)
        message = data['message']
        user = self.scope["user"]

        print("receive :", user)

        async_to_sync(self.channel_layer.group_send)(
            self.room_group_name,
            {
                'type': 'chat_message',
                'message': message,
                'user': user
            }
        )
        Message.objects.create(user=user, body=message, room=Room.objects.get(id=self.scope['url_route']['kwargs']['pk']))
    
    def chat_message(self, event):
        print('Event:', event)
        message = event['message']
        user = event['user']


        # Extract relevant user information
        user_data = {
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'avatar_url': user.avatar.url,
        }
        self.send(text_data=json.dumps({
            'type': 'chat_message',
            'message': message,
            'user': user_data,
        }))
        

class RoomConsumer(WebsocketConsumer):
    def connect(self):
        pass

    def receive(self, text_data):
        data = json.loads(text_data)