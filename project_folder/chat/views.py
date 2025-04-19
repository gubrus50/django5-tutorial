from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.utils import timezone

from .forms import MessageForm
from .models import Room




# Create your views here.

@login_required
def roomView(request):

    room = get_object_or_404(Room, name='public')
    form = MessageForm()


    if request.htmx:
        form = MessageForm(request.POST)

        if form.is_valid():
            message = form.save(commit=False)
            message.author = request.user
            message.room = room
            message.save()

            context = {
                'msg': message,
                'user': request.user,
                'today': timezone.now().date().strftime("%Y-%m-%d")
            }
            return render(request, 'chat/partials/message.html', context)


    context = {
        'form': form,
        'user': request.user,
        'room_name': room.name,
        'room_messages': room.messages.all()[:30],
        'today': timezone.now().date().strftime("%Y-%m-%d")
    }

    return render(request, 'chat/index.html', context)