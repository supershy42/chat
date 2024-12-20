import requests
from .models import ChatRoom
from django.db.models import Q
import httpx
import aiohttp

USER_SERVICE_URL = "http://127.0.0.1:8000/api/user/"

async def get_user(user_id):
    user_service_url = f'{USER_SERVICE_URL}{user_id}/'
    # headers = {'Authorization': f'Bearer {token}'}
    
    async with aiohttp.ClientSession() as session:
        async with session.get(user_service_url, timeout=10) as response:
            if response.status == 200:
                return await response.json()
            return None

async def is_valid_user(user_id):
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(f"{USER_SERVICE_URL}{user_id}/")
            return response.status_code == 200
    except httpx.RequestError:
        return False

async def chatroom_exist(user1_id, user2_id):
    return await ChatRoom.objects.filter(
        Q(user1_id=user1_id, user2_id=user2_id) |
        Q(user1_id=user2_id, user2_id=user1_id)
    ).aexists()
    
async def create_chatroom(user1_id, user2_id):
    if await chatroom_exist(user1_id, user2_id):
        raise ValueError("Chat room already exists.")
    
    chatroom = await ChatRoom.objects.acreate(user1_id=user1_id, user2_id=user2_id)
    return chatroom

async def validate_users(user1_id, user2_id):
    if user1_id == user2_id:
        return False
    if not await is_valid_user(user1_id):
        return False
    if not await is_valid_user(user2_id):
        return False
    return True

async def get_chatroom_by_id(chatroom_id):
    return await ChatRoom.objects.filter(id=chatroom_id).afirst()

async def is_user_in_chatroom(user_id, chatroom):
    return user_id in [chatroom.user1_id, chatroom.user2_id]

async def validate_message(data):
    content = data.get('content')

    if missing_fields := await check_missing_fields(content):
        return await error_response("Missing required fields: " + ", ".join(missing_fields))

    return None
    
async def error_response(message):
    return {
        "type": "error",
        "content": message
    }
    
async def check_missing_fields(content):
    missing_fields = []
    if not content:
        missing_fields.append('content')
    return missing_fields