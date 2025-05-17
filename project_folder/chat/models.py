from django.db import models
from django.contrib.auth.models import User
import shortuuid

# Create your models here.


class Room(models.Model):
    name = models.CharField(max_length=128, unique=True, default=shortuuid.uuid)
    users_online = models.ManyToManyField(User, related_name='online_in_rooms', blank=True)
    members = models.ManyToManyField(User, related_name='chat_rooms', blank=True)
    is_private = models.BooleanField(default=False)

    def __str__(self):
        return self.name



class Message(models.Model):
    room = models.ForeignKey(Room, related_name='messages', on_delete=models.CASCADE)
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    message = models.CharField(max_length=1000)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.author.username}: {self.message}'
