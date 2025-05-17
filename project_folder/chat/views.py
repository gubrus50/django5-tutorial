from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages # Added
from django.contrib.auth.models import User # Added
from django.contrib.auth.decorators import login_required
from django.http import Http404 # Replaced HttpResponse with Http404
from django.utils import timezone

from .utils import get_or_create_chatroom_for_users # Added
from .forms import MessageForm
from .models import Room




# Create your views here.

@login_required
def roomView(request, room_name='public'): #added room_name

    room = get_object_or_404(Room, name=room_name) #set name to room_name
    form = MessageForm()
    # Added this below script to get other_user
    other_user = None


    if room.is_private:
        members = room.members.all()

        if request.user not in members:
            raise Http404()

        for member in members:
            if member != request.user:
                other_user = member
                break


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
        'other_user': other_user, # Added
        'room_name': room.name,
        'room_messages': room.messages.all()[:30],
        'today': timezone.now().date().strftime("%Y-%m-%d")
    }

    return render(request, 'chat/index.html', context)


# Added below View
@login_required
def chatWithView(request, username):
    
    logged_in_user = request.user 
    chat_with_user = User.objects.get(username=username)

    room_instance = get_or_create_chatroom_for_users(
        logged_in_user, chat_with_user
    )

    if room_instance is None:
        messages.error(request, 'You cannot chat with yourself!')
        return redirect('public-chatroom')

    return redirect('chatroom', room_instance.name)