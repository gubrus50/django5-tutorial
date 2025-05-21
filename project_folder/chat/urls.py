from django.urls import path
from . import views

urlpatterns = [
    path('', views.roomView, name='public-chatroom'),
    path('room/<str:room_name>', views.roomView, name='chatroom'),
    path('with-user/<username>', views.chatWithView, name='chat-with'),
]