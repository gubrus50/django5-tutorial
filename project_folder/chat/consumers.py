from channels.generic.websocket import WebsocketConsumer
from asgiref.sync import async_to_sync

from django.shortcuts import get_object_or_404
from django.template.loader import render_to_string
from django.utils import timezone

from .models import Message, Room
import json


class ChatroomConsumer(WebsocketConsumer):

    def connect(self):
        self.user = self.scope['user']
        self.room_name = self.scope['url_route']['kwargs']['room_name']
        self.room = get_object_or_404(Room, name=self.room_name)
        
        async_to_sync(self.channel_layer.group_add)(
            self.room_name, self.channel_name
        )
        
        # ADD User TO online list, AND UPDATE online count 
        if self.user not in self.room.users_online.all():
            self.room.users_online.add(self.user)
            self.update_online_count()

        self.accept()


    def disconnect(self, close_code):
        async_to_sync(self.channel_layer.group_discard)(
            self.room_name, self.channel_name
        )
        # REMOVE User FROM online list, AND UPDATE online count 
        if self.user in self.room.users_online.all():
            self.room.users_online.remove(self.user)
            self.update_online_count()


    def receive(self, text_data):
        text_data_json = json.loads(text_data)

        message = Message.objects.create(
            room=self.room,
            author=self.user,
            message=text_data_json['message']
        )

        event = {
            'type': 'message_handler',
            'message_id': message.id
        }
        async_to_sync(self.channel_layer.group_send)(
            self.room_name, event
        )


    def message_handler(self, event):
        message_id = event['message_id']
        message = Message.objects.get(id=message_id)
        context = {
            'msg': message,
            'today': timezone.now().date().strftime("%Y-%m-%d"),
            'user': self.user
        }

        html = render_to_string('chat/partials/message.html', context)
        self.send(text_data=html)

    
    def update_online_count(self):
        online_count = self.room.users_online.count()
        event = {
            'type': 'online_count_handler',
            'online_count': online_count
        }
        async_to_sync(self.channel_layer.group_send)(
            self.room_name, event
        )


    def online_count_handler(self, event):
        online_count = event['online_count']
        partial = 'chat/partials/online_count.html'

        html = render_to_string(partial, {'online_count': online_count})
        self.send(text_data=html)