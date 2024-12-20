from .models import ChatRoom, Message
from django.db.models import Q
import aiohttp
from config.settings import USER_SERVICE_URL
from rest_framework.exceptions import PermissionDenied
import asyncio
from asgiref.sync import sync_to_async

class UserService:
    @staticmethod
    async def get_user(user_id, token):
        user_service_url = f'{USER_SERVICE_URL}profile/{user_id}/'
        headers = {'Authorization': f'Bearer {token}'}
        
        async with aiohttp.ClientSession() as session:
            async with session.get(user_service_url, headers=headers, timeout=10) as response:
                if response.status == 200:
                    return await response.json()
                return None
        
class ChatRoomService:
    DEFAULT_PAGE_SIZE = 50
    
    @staticmethod
    def check_user_permission(chatroom, user_id):
        if user_id not in [chatroom.user1_id, chatroom.user2_id]:
            raise PermissionDenied("The user does not have access to the chat room.")
        
    @staticmethod
    async def get_messages(chatroom, last_loaded_message_id=None, limit=DEFAULT_PAGE_SIZE):
        query = Message.objects.filter(chatroom=chatroom)
        if last_loaded_message_id:
            query = query.filter(id__lt=last_loaded_message_id)
        messages = await sync_to_async(list)(query.order_by('-id')[:limit])
        messages.reverse()
        return messages
    
    @staticmethod
    async def add_avatars_to_messages(messages, token):
        sender_ids = {message.sender_id for message in messages}
        profiles = await ChatRoomService.fetch_profiles(sender_ids, token)
        
        result = []
        for message in messages:
            profile = profiles.get(message.sender_id)
            result.append({
                "id": message.id,
                "sender": profile.get('nickname'),
                "avatar": profile.get('avatar'),
                "content": message.content,
                "timestamp": message.timestamp
            })
        
        return result
    
    @staticmethod
    async def fetch_profiles(sender_ids, token):
        tasks = [
            UserService.get_user(user_id, token) for user_id in sender_ids
        ]
        
        profiles = await asyncio.gather(*tasks)
        return {profile['id']: profile for profile in profiles}
    
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
    if not await UserService.get_user(user1_id, token):
        return False
    if not await UserService.get_user(user2_id, token):
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