from django.test import TransactionTestCase
from rest_framework.test import APITestCase, APIClient
from unittest.mock import patch
from django.urls import reverse, path
from channels.testing import WebsocketCommunicator
from channels.routing import URLRouter
from chat_app.models import ChatRoom
from chat_app.consumers import ChatConsumer
import jwt
from datetime import datetime, timedelta

SECRET_KEY = 'your_secret_key'

def generate_jwt(user_id):
    """JWT 생성"""
    payload = {
        'user_id': user_id,
        'exp': datetime.utcnow() + timedelta(hours=1),  # 1시간 유효
        'iat': datetime.utcnow()  # 발행 시간
    }
    return jwt.encode(payload, SECRET_KEY, algorithm='HS256')



class ChatRoomCreateViewTests(APITestCase):
    def setUp(self):
        self.client = APIClient()
        self.url = reverse('create')
        self.user1_id = 1
        self.user2_id = 2
        self.token = generate_jwt(self.user1_id)  # JWT 생성
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token}')

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
        
    def test_create_chatroom_without_jwt(self):
        self.client.credentials()  # 헤더 제거
        data = {
            'user1_id': self.user1_id,
            'user2_id': self.user2_id
        }

        response = self.client.post(self.url, data, format='json')

        self.assertEqual(response.status_code, 401)  # 인증 실패
        self.assertEqual(ChatRoom.objects.count(), 0)


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
