from rest_framework import serializers
from asgiref.sync import async_to_sync
from .models import ChatRoom
from . import services

class ChatRoomCreateSerializer(serializers.ModelSerializer):
    user1_id = serializers.IntegerField()
    user2_id = serializers.IntegerField()
    
    class Meta:
        model = ChatRoom
        fields = ['id', 'user1_id', 'user2_id', 'last_message', 'updated_at']
        
    def validate(self, data):
        user1_id = data['user1_id']
        user2_id = data['user2_id']

        if not async_to_sync(services.validate_users)(user1_id, user2_id):
            raise serializers.ValidationError("users are invalid.")
        
        if async_to_sync(services.chatroom_exist)(user1_id, user2_id):
            raise serializers.ValidationError("Chat room already exists.")

        return data
    
    def create(self, validated_data):
        return async_to_sync(services.create_chatroom)(
            user1_id=validated_data['user1_id'],
            user2_id=validated_data['user2_id']
        )