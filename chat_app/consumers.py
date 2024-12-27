from channels.generic.websocket import AsyncWebsocketConsumer
from .models import Message
import json
from .services import UserService, ChatRoomService
from .close_codes import CloseCode
from django.utils.timezone import now

class ChatConsumer(AsyncWebsocketConsumer):    
    async def connect(self):
        self.chatroom_id = self.scope['url_route']['kwargs']['chatroom_id']
        self.chatroom_group_name = f'chat_{self.chatroom_id}'
        
        self.chatroom = await ChatRoomService.get_chatroom_by_id(self.chatroom_id)
        if not self.chatroom:
            await self.close(code=CloseCode.CHATROOM_NOT_FOUND)
            return
        
        self.user_id = self.scope['user_id']
        self.user = await UserService.get_user(self.user_id, self.scope['token'])
        if not self.user:
            await self.close(code=CloseCode.USER_NOT_FOUND)
            return
        self.user_name = self.user.get('nickname')
        
        if not await ChatRoomService.is_user_in_chatroom(self.user_id, self.chatroom):
            await self.close(code=CloseCode.INVALID_USER)
            return
        
        await self.channel_layer.group_add(
            self.chatroom_group_name,
            self.channel_name
        )
        
        await self.accept()
        
    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.chatroom_group_name,
            self.channel_name
        )
        
    async def receive(self, text_data):
        data = None
        try:
            data = json.loads(text_data)
        except json.JSONDecodeError:
            await self.send_error("Invalid JSON format.")
            return
            
        type = data.get('type')
        if type == 'chat':
            await self.handle_chat(data)
        else:
            await self.send_error("Invalid message type.")
    
    async def handle_chat(self, data):
        content = data.get('content')
        if not content:
            await self.send_error("content is required.")
            return

        message = await Message.objects.acreate(
            chatroom=self.chatroom,
            sender_id=self.user_id,
            content=content
        )

        await self.channel_layer.group_send(
            self.chatroom_group_name,
            {
                'type': 'chat.message',
                'sender_name': self.user_name,
                'content': content,
                'timestamp': str(message.timestamp)
            }
        )
        
        self.chatroom.updated_at = now()
        await self.chatroom.asave(update_fields=['updated_at'])
        
    async def chat_message(self, event):
        await self.send_json({
            "type": "chat.message",
            "sender_name": event.get("sender_name"),
            "content": event.get("content"),
            "timestamp": event.get("timestamp")
        })
        
    async def send_json(self, content):
        await self.send(text_data=json.dumps(content))
        
    async def send_error(self, message):
        await self.send_json({
            "type": "error",
            "message": message
        })