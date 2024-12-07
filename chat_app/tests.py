from django.test import TransactionTestCase
from rest_framework.test import APITestCase, APIClient
from unittest.mock import patch
from django.urls import reverse, path
from channels.testing import WebsocketCommunicator
from channels.routing import URLRouter
from chat_app.models import ChatRoom
from chat_app.consumers import ChatConsumer


class ChatRoomCreateViewTests(APITestCase):
    def setUp(self):
        self.client = APIClient()
        self.url = reverse('create')
        self.user1_id = 1
        self.user2_id = 2

    @patch('chat_app.services.is_valid_user')
    def test_create_chatroom_with_valid_users(self, mock_is_valid_user):
        mock_is_valid_user.return_value = True

        data = {
            'user1_id': self.user1_id,
            'user2_id': self.user2_id
        }

        response = self.client.post(self.url, data, format='json')

        self.assertEqual(response.status_code, 201)
        self.assertEqual(ChatRoom.objects.count(), 1)
        chatroom = ChatRoom.objects.first()
        self.assertEqual(chatroom.user1_id, self.user1_id)
        self.assertEqual(chatroom.user2_id, self.user2_id)
        self.assertEqual(response.data['id'], chatroom.id)

    @patch('chat_app.services.is_valid_user')
    def test_create_chatroom_with_invalid_users(self, mock_is_valid_user):
        mock_is_valid_user.return_value = False

        data = {
            'user1_id': self.user1_id,
            'user2_id': self.user2_id
        }

        response = self.client.post(self.url, data, format='json')

        self.assertEqual(response.status_code, 400)
        self.assertEqual(ChatRoom.objects.count(), 0)
        self.assertIn('users are invalid', str(response.data))

    @patch('chat_app.services.is_valid_user')
    def test_create_chatroom_already_exists(self, mock_is_valid_user):
        mock_is_valid_user.return_value = True

        ChatRoom.objects.create(user1_id=self.user1_id, user2_id=self.user2_id)

        data = {
            'user1_id': self.user1_id,
            'user2_id': self.user2_id
        }

        response = self.client.post(self.url, data, format='json')

        self.assertEqual(response.status_code, 400)
        self.assertEqual(ChatRoom.objects.count(), 1)
        self.assertEqual(
            response.data['non_field_errors'][0].code,
            'unique'
        )


# Tests for ChatConsumer
class ChatConsumerTests(TransactionTestCase):
    def setUp(self):
        self.user1_id = 1
        self.user2_id = 2
        self.chatroom = ChatRoom.objects.create(user1_id=self.user1_id, user2_id=self.user2_id)
        self.application = URLRouter([
            path('ws/chat/<int:chatroom_id>/', ChatConsumer.as_asgi()),
        ])

    @patch('chat_app.services.is_valid_user')
    async def test_chat_consumer_sends_and_receives_messages(self, mock_is_valid_user):
        mock_is_valid_user.return_value = True

        chatroom_id = self.chatroom.id
        communicator = WebsocketCommunicator(self.application, f'/ws/chat/{chatroom_id}/')
        connected, _ = await communicator.connect()
        self.assertTrue(connected)

        message = {
            'sender_id': self.user1_id,
            'chatroom_id': chatroom_id,
            'content': 'Hello, World!'
        }

        await communicator.send_json_to(message)

        response = await communicator.receive_json_from()

        self.assertEqual(response['type'], 'chat.message')
        self.assertEqual(response['sender_id'], self.user1_id)
        self.assertEqual(response['content'], 'Hello, World!')

        await communicator.disconnect()

    @patch('chat_app.services.is_valid_user')
    async def test_chat_consumer_rejects_invalid_sender(self, mock_is_valid_user):
        mock_is_valid_user.return_value = False

        chatroom_id = self.chatroom.id
        communicator = WebsocketCommunicator(self.application, f'/ws/chat/{chatroom_id}/')
        connected, _ = await communicator.connect()
        self.assertTrue(connected)

        message = {
            'sender_id': 999,
            'chatroom_id': chatroom_id,
            'content': 'This should fail'
        }

        await communicator.send_json_to(message)

        response = await communicator.receive_json_from()

        self.assertEqual(response['type'], 'error')
        self.assertIn('Invalid sender ID.', response['content'])

        await communicator.disconnect()

    async def test_chat_consumer_disconnects_on_invalid_chatroom(self):
        communicator = WebsocketCommunicator(self.application, f'/ws/chat/999/')
        connected, _ = await communicator.connect()
        self.assertFalse(connected)