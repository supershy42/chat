from channels.generic.websocket import AsyncWebsocketConsumer
from django.contrib.auth import get_user_model
from .models import ChatRoom, Message
import json
from . import services

User = get_user_model()

class ChatConsumer(AsyncWebsocketConsumer):
    async def send_json(self, content):
        await self.send(text_data=json.dumps(content))
    
    async def connect(self):
        self.room_name = self.scope['url_route']['kwargs']['chatroom_id']
        self.room_group_name = f'chat_{self.room_name}'
        
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        
        await self.accept()
        
    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )
        
    async def receive(self, text_data):
        data = json.loads(text_data)
        
        sender_id = data['sender_id']
        if not services.is_valid_user(sender_id):
            await self.send_json({
                "type": "error",
                "content": "Invalid sender ID."
            })
            return
        
        chatroom_id = data['chatroom_id']
        content = data['content']
        
        chatroom = await ChatRoom.objects.filter(id=chatroom_id).afirst()
        receiver_id = chatroom.get_receiver_id(sender_id)
        
        message = await Message.objects.acreate(
            chatroom=chatroom,
            sender_id=sender_id,
            receiver_id=receiver_id,
            content=content
        )
        
        chatroom.last_message = content
        await chatroom.asave()
        
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'chat.message',
                'sender_id': sender_id,
                'content': content,
                'timestamp': str(message.timestamp)
            }
        )
        
    async def chat_message(self, event):
        sender_id = event.get("sender_id")
        message_content = event.get("content")
        timestamp = event.get("timestamp")

        await self.send_json({
            "type": "chat.message",
            "sender_id": sender_id,
            "content": message_content,
            "timestamp": timestamp
        })