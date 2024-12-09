from channels.generic.websocket import AsyncWebsocketConsumer
from .models import Message
import json
from . import services

class ChatConsumer(AsyncWebsocketConsumer):    
    async def connect(self):
        # NOTE: 인증된 user_id 가져와서 채팅방에 접근가능한지 검사해야 함.
        self.chatroom_id = self.scope['url_route']['kwargs']['chatroom_id']
        self.chatroom_group_name = f'chat_{self.chatroom_id}'
        
        self.chatroom = await services.get_chatroom_by_id(self.chatroom_id)
        if not self.chatroom:
            await self.close()
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
        data = json.loads(text_data)
        
        error_response = await services.validate_message(data, self.chatroom)
        if error_response:
            await self.send_json(error_response)
            return
        
        sender_id = data['sender_id']
        content = data['content']
        receiver_id = self.chatroom.get_receiver_id(sender_id)

        message = await Message.objects.acreate(
            chatroom=self.chatroom,
            sender_id=sender_id,
            receiver_id=receiver_id,
            content=content
        )

        self.chatroom.last_message = content
        await self.chatroom.asave()

        await self.channel_layer.group_send(
            self.chatroom_group_name,
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
        
    async def send_json(self, content):
        await self.send(text_data=json.dumps(content))