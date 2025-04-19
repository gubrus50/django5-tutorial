from django.urls import path
from . import views

urlpatterns = [
    # path('room/<str:room_name>/', room, name='room'),
    path('', views.roomView, name='room'),
]