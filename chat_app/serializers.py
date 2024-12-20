from rest_framework import serializers
from asgiref.sync import async_to_sync
from .models import ChatRoom
from . import services

class ChatRoomSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(read_only=True)
    user1_id = serializers.IntegerField(write_only=True)
    user2_id = serializers.IntegerField(write_only=True)
    updated_at = serializers.DateTimeField(read_only=True)
    last_message = serializers.SerializerMethodField(read_only=True)
    
    class Meta:
        model = ChatRoom
        fields = ['id', 'user1_id', 'user2_id', 'updated_at', 'last_message']
        
    def get_last_message(self, obj):
        last_message = obj.last_message
        return last_message.content if last_message else None
        
    def validate(self, data):
        user1_id = data['user1_id']
        user2_id = data['user2_id']
        token = self.context['token']

        if not async_to_sync(services.validate_users)(user1_id, user2_id, token):
            raise serializers.ValidationError("users are invalid.")
        
        if async_to_sync(services.chatroom_exist)(user1_id, user2_id):
            raise serializers.ValidationError("Chat room already exists.")

        return data
    
    def create(self, validated_data):
        return async_to_sync(services.create_chatroom)(
            user1_id=validated_data['user1_id'],
            user2_id=validated_data['user2_id']
        )