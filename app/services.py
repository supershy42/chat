import requests
from .models import ChatRoom
from django.db.models import Q

USER_SERVICE_URL = "http://127.0.0.1:8000/api/user/"

def is_valid_user(user_id):
    try:
        response = requests.get(f"{USER_SERVICE_URL}{user_id}/")
        if response.status_code == 200:
            return True
        return False
    except requests.RequestException as e:
        return False
    
def chatroom_exist(user1_id, user2_id):
    return ChatRoom.objects.filter(
        Q(user1_id=user1_id, user2_id=user2_id) |
        Q(user1_id=user2_id, user2_id=user1_id)
    ).exists()
    
def create_chatroom(user1_id, user2_id):
    if chatroom_exist(user1_id, user2_id):
        raise ValueError("Chat room already exists.")
    
    chatroom = ChatRoom.objects.create(user1_id=user1_id, user2_id=user2_id)
    return chatroom

def validate_users(user1_id, user2_id):
    if user1_id == user2_id:
        return False
    if not is_valid_user(user1_id):
        return False
    if not is_valid_user(user2_id):
        return False
    return True

async def get_chatroom_by_id(chatroom_id):
    return await ChatRoom.objects.filter(id=chatroom_id).afirst()

async def is_user_in_chatroom(user_id, chatroom):
    return user_id in [chatroom.user1_id, chatroom.user2_id]

async def validate_message(data, chatroom):
    # NOTE: 인증된 user_id로 검사하게 수정해야 함.
    sender_id = data.get('sender_id')
    chatroom_id = data.get('chatroom_id')
    content = data.get('content')

    if missing_fields := check_missing_fields(sender_id, chatroom_id, content):
        return error_response("Missing required fields: " + ", ".join(missing_fields))

    if not is_valid_user(sender_id):
        return error_response("Invalid sender ID.")

    if int(chatroom_id) != chatroom.id:
        return error_response("Chatroom ID mismatch.")

    if not await is_user_in_chatroom(sender_id, chatroom):
        return error_response("Sender is not a participant in the chatroom.")

    return None
    
def error_response(message):
    return {
        "type": "error",
        "content": message
    }
    
def check_missing_fields(sender_id, chatroom_id, content):
    missing_fields = []
    if not sender_id:
        missing_fields.append('sender_id')
    if not chatroom_id:
        missing_fields.append('chatroom_id')
    if not content:
        missing_fields.append('content')
    return missing_fields