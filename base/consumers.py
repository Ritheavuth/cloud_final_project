import json
from channels.generic.websocket import WebsocketConsumer, AsyncWebsocketConsumer
from django.template.defaultfilters import timesince
from .models import Room, Message, Topic
from django.contrib.auth import get_user_model
from asgiref.sync import async_to_sync
from django.core.serializers import serialize

User = get_user_model()

class ChatConsumer(WebsocketConsumer):
    def connect(self):
        self.room_id = self.scope['url_route']['kwargs']['pk']
        self.room_group_name = f"chat_{self.room_id}"
        user = self.scope["user"]

        async_to_sync(self.channel_layer.group_add) (
            self.room_group_name,
            self.channel_name
        )

        room = Room.objects.get(id=self.room_id)
        room.participants.add(User.objects.get(email=user))
        participants_list = serialize('json', room.participants.all())
        participants = room.participants.count()
        async_to_sync(self.channel_layer.group_send)(
            self.room_group_name,
            {
                'type': 'join_room',
                'participants': participants,
                'participants_list': participants_list
            }
        )

        # print(self.room_group_name)
        # print(self.channel_name)
        self.accept()

    def receive(self, text_data):
        data = json.loads(text_data)
        message = data['message']
        user = self.scope["user"]

        # print("receive :", user)

        async_to_sync(self.channel_layer.group_send)(
            self.room_group_name,
            {
                'type': 'chat_message',
                'message': message,
                'user': user
            }
        )
        Message.objects.create(user=user, body=message, room=Room.objects.get(id=self.scope['url_route']['kwargs']['pk']))
    
    def disconnect(self, close_code):
        self.room_id = self.scope['url_route']['kwargs']['pk']
        user = self.scope["user"]
        self.room_group_name = f"chat_{self.room_id}"
        async_to_sync(self.channel_layer.group_discard)(
            self.room_group_name,
            self.channel_name
        )

        room = Room.objects.get(id=self.room_id)
        room.participants.remove(User.objects.get(email=user))
        participants_list = serialize('json', room.participants.all())
        participants = room.participants.count()
        async_to_sync(self.channel_layer.group_send)(
            self.room_group_name,
            {
                'type': 'join_room',
                'participants': participants,
                'participants_list': participants_list
            }
        )

    def chat_message(self, event):
        # print('Event:', event)
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

    def join_room(self, event):
        # print("Join Event: ", event)
        participants = event['participants']
        participants_list = event['participants_list']
        
        self.send(text_data=json.dumps({
            'type': 'join_room',
            'participants': participants,
            'participants_list': participants_list
        }))
        # print("Join Room Event:", event)

    def leave_room(self, event):
        participants = event['participants']
        participants_list = event['participants_list']

        self.send(text_data=json.dumps({
            'type': 'leave_room',
            'participants': participants,
            'participants_list': participants_list
        }))
        # print("Leave Room Event:", event)
        
class NewRoomConsumer(WebsocketConsumer):
    def connect(self):
        self.room_group_name = "home"

        # Add the channel to the group so that it can receive messages
        async_to_sync(self.channel_layer.group_add)(
            self.room_group_name,
            self.channel_name
        )
        self.accept()
    
    def receive(self, text_data):
        data = json.loads(text_data)
        print('Receive:', data)
        name = data['name']
        description = data['description']

        user = User.objects.get(email=self.scope["user"])

        topic_name = data['topic']
        topic = Topic.objects.filter(name=topic_name).first()
        room = ''
        if topic:
            room = Room.objects.create(host=user, topic=topic, name=name, description=description)
        else:
            new_topic = Topic.objects.create(name=topic_name)
            room = Room.objects.create(host=user, topic=new_topic, name=name, description=description)

        topic_data = {
            "id": topic.pk,
            "name": topic.name
        }

        user_data = {
            'id': user.pk,
            'avatar': user.avatar.url,
            'username': user.username,
            'name': user.name
        }

        room.participants.add(user)

        async_to_sync(self.channel_layer.group_send)(
            self.room_group_name,
            {
                'type': 'room_created',
                'room_id': room.pk,
                'room_participants_count': room.participants.count(),
                'topic': topic_data,
                'user': user_data,
                'name': name,
                'description': description
            }
        )
        # if topic:
        # else:

        

    def disconnect(self, close_code):
        # Remove the channel from the group when disconnected
        async_to_sync(self.channel_layer.group_discard)(
            self.room_group_name,
            self.channel_name
        )

    def room_created(self, event):
        # Send the event data to the client
        self.send(text_data=json.dumps({
            'type': 'room_created',
            'room_id': event['room_id'],
            'room_participants_count': event['room_participants_count'],
            'user': event['user'],
            'topic': event["topic"],
            'name': event["name"],
            'description': event["description"],
        }))