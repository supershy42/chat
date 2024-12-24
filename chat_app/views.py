from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .serializers import ChatRoomSerializer, MessageSerializer
from .services import ChatRoomService, is_user_in_chatroom
from django.shortcuts import get_object_or_404
from .models import ChatRoom
from asgiref.sync import async_to_sync

class ChatRoomCreateView(APIView):
    def post(self, request):
        serializer = ChatRoomSerializer(data=request.data, context={'token': request.token})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class ChatRoomMessageListView(APIView):
    def get(self, request, chatroom_id):
        limit = int(request.query_params.get('limit', ChatRoomService.DEFAULT_PAGE_SIZE))
        last_loaded_message_id = request.query_params.get('last_loaded_message_id')
        token = self.request.token

        chatroom = get_object_or_404(ChatRoom, id=chatroom_id)
        ChatRoomService.check_user_permission(chatroom, request.user_id)
        
        messages = async_to_sync(ChatRoomService.get_messages)(chatroom, last_loaded_message_id, limit)
        messages = async_to_sync(ChatRoomService.add_avatars_to_messages)(messages, token)
        serializer = MessageSerializer(messages, many=True)
        
        return Response(serializer.data)

class ChatRoomDeleteView(APIView):
    def post(self, request):
        user_id = request.user_id
        chatroom_id = request.data.get('chatroom_id')
        chatroom = get_object_or_404(ChatRoom, id=chatroom_id)
        
        if not is_user_in_chatroom(user_id, chatroom):
            return Response({"error": "User is not in chat room."}, status=status.HTTP_400_BAD_REQUEST)     
    
        chatroom.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)