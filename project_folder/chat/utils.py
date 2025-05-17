from .models import Room



def get_or_create_chatroom_for_users(User_A, User_B):
    """This utility searches for an existing private chatroom between
    the provided user instances. If chatroom is not found,
    then a new private chatroom is created for those users."""

    if User_A == User_B:
        print('Cannot create chatroom for the same user!')
        return None

    my_chat_rooms = User_A.chat_rooms.filter(is_private=True)
    room_instance = None

    # GET private chatroom OF User_A and User_B
    if my_chat_rooms.exists():
        for room in my_chat_rooms:
            if User_B in room.members.all():
                room_instance = room
                break
    
    # Otherwise, create new private chatroom for them
    if room_instance is None:
        room_instance = Room.objects.create(is_private=True)
        room_instance.members.add(User_B, User_A)

    return room_instance