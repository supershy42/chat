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