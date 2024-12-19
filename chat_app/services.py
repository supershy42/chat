from .models import ChatRoom
from django.db.models import Q
import aiohttp
from config.settings import USER_SERVICE_URL

async def get_user(user_id, token):
    user_service_url = f'{USER_SERVICE_URL}{user_id}/'
    headers = {'Authorization': f'Bearer {token}'}
    
    async with aiohttp.ClientSession() as session:
        async with session.get(user_service_url, headers=headers, timeout=10) as response:
            if response.status == 200:
                return await response.json()
            return None

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

async def validate_users(user1_id, user2_id, token):
    if user1_id == user2_id:
        return False
    if not await get_user(user1_id, token):
        return False
    if not await get_user(user2_id, token):
        return False
    return True

async def get_chatroom_by_id(chatroom_id):
    return await ChatRoom.objects.filter(id=chatroom_id).afirst()

async def is_user_in_chatroom(user_id, chatroom):
    return user_id in [chatroom.user1_id, chatroom.user2_id]
    
async def error_response(message):
    return {
        "type": "error",
        "content": message
    }