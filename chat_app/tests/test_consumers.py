from unittest.mock import AsyncMock, patch
from channels.testing import WebsocketCommunicator
from django.test import TestCase
from chat_app.consumers import ChatConsumer
from chat_app.models import ChatRoom, Message
from channels.layers import get_channel_layer
import json

class ChatConsumerTestCase(TestCase):
    def setUp(self):
        # 채팅방 생성
        self.chatroom = ChatRoom.objects.create(user1_id=1, user2_id=2)
        self.channel_layer = get_channel_layer()
        self.chatroom_id = self.chatroom.id

    async def test_connect_successful(self):
        # WebsocketCommunicator로 연결
        communicator = WebsocketCommunicator(
            ChatConsumer.as_asgi(),
            f"/ws/chat/{self.chatroom_id}/"
        )
        
        # 테스트용 scope 정의
        communicator.scope['url_route'] = {
            'kwargs': {'chatroom_id': str(self.chatroom_id)}
        }
        communicator.scope['user_id'] = 1

        # Mock 패치
        with patch("chat_app.consumers.get_chatroom_by_id", new=AsyncMock(return_value=self.chatroom)), \
             patch("chat_app.consumers.get_user", new=AsyncMock(return_value={"nickname": "User1"})), \
             patch("chat_app.consumers.is_user_in_chatroom", new=AsyncMock(return_value=True)):

            # 연결
            connected, subprotocol = await communicator.connect()
            self.assertTrue(connected)

            # 연결 종료
            await communicator.disconnect()

    async def test_connect_invalid_chatroom(self):
        communicator = WebsocketCommunicator(
            ChatConsumer.as_asgi(),
            "/ws/chat/9999/"
        )
        
        # 테스트용 scope 정의
        communicator.scope['url_route'] = {
            'kwargs': {'chatroom_id': '9999'}
        }
        communicator.scope['user_id'] = 1

        # Mock 패치: get_chatroom_by_id가 None 반환
        with patch("chat_app.consumers.get_chatroom_by_id", new=AsyncMock(return_value=None)):
            connected, subprotocol = await communicator.connect()
            self.assertFalse(connected)

    async def test_receive_message(self):
        communicator = WebsocketCommunicator(
            ChatConsumer.as_asgi(),
            f"/ws/chat/{self.chatroom_id}/"
        )
        
        # 테스트용 scope 정의
        communicator.scope['url_route'] = {
            'kwargs': {'chatroom_id': str(self.chatroom_id)}
        }
        communicator.scope['user_id'] = 1

        # Mock 패치
        with patch("chat_app.consumers.get_chatroom_by_id", new=AsyncMock(return_value=self.chatroom)), \
             patch("chat_app.consumers.get_user", new=AsyncMock(return_value={"nickname": "User1"})), \
             patch("chat_app.consumers.is_user_in_chatroom", new=AsyncMock(return_value=True)), \
             patch("chat_app.consumers.validate_message", new=AsyncMock(return_value=None)):
            
            # 연결
            connected, subprotocol = await communicator.connect()
            self.assertTrue(connected)

            # 메시지 데이터
            message_data = {
                "content": "Hello, world!"
            }

            # 메시지 전송
            await communicator.send_json_to(message_data)

            # 그룹으로 메시지 브로드캐스트 검증
            response = await communicator.receive_json_from()
            self.assertEqual(response['type'], "chat.message")
            self.assertEqual(response['content'], "Hello, world!")
            self.assertEqual(response['sender_name'], "User1")

            # 연결 종료
            await communicator.disconnect()

    async def test_invalid_json_message(self):
        communicator = WebsocketCommunicator(
            ChatConsumer.as_asgi(),
            f"/ws/chat/{self.chatroom_id}/"
        )
        
        # 테스트용 scope 정의
        communicator.scope['url_route'] = {
            'kwargs': {'chatroom_id': str(self.chatroom_id)}
        }
        communicator.scope['user_id'] = 1

        with patch("chat_app.consumers.get_chatroom_by_id", new=AsyncMock(return_value=self.chatroom)), \
             patch("chat_app.consumers.get_user", new=AsyncMock(return_value={"nickname": "User1"})), \
             patch("chat_app.consumers.is_user_in_chatroom", new=AsyncMock(return_value=True)):

            # 연결
            connected, subprotocol = await communicator.connect()
            self.assertTrue(connected)

            # 잘못된 JSON 데이터 전송
            await communicator.send_to("Invalid JSON")
            response = await communicator.receive_json_from()
            self.assertEqual(response, {"error": "Invalid JSON format"})

            # 연결 종료
            await communicator.disconnect()
