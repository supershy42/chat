from rest_framework import serializers
from asgiref.sync import async_to_sync
from .models import ChatRoom, Message
from .services import ChatRoomService
from drf_spectacular.utils import extend_schema_field

class ChatRoomSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(read_only=True, help_text="채팅방의 고유 식별자")
    user1_id = serializers.IntegerField(write_only=True, help_text="채팅방의 첫 번째 사용자 ID")
    user2_id = serializers.IntegerField(write_only=True, help_text="채팅방의 두 번째 사용자 ID")
    updated_at = serializers.DateTimeField(read_only=True, help_text="채팅방이 마지막으로 업데이트된 시간")
    last_message = serializers.SerializerMethodField(read_only=True, help_text="채팅방의 마지막 메시지 내용")
    
    class Meta:
        model = ChatRoom
        fields = ['id', 'user1_id', 'user2_id', 'updated_at', 'last_message']
        
    @extend_schema_field(serializers.CharField(allow_null=True))
    def get_last_message(self, obj) -> str:
        last_message = obj.last_message
        return last_message.content if last_message else None
        
    def validate(self, data):
        user1_id = data['user1_id']
        user2_id = data['user2_id']
        token = self.context['token']

        if not async_to_sync(ChatRoomService.validate_users)(user1_id, user2_id, token):
            raise serializers.ValidationError("users are invalid.")

        return data
    
    def create(self, validated_data):
        return async_to_sync(ChatRoomService.create_chatroom)(
            user1_id=validated_data['user1_id'],
            user2_id=validated_data['user2_id']
        )
        
class MessageSerializer(serializers.ModelSerializer):
    avatar = serializers.CharField(read_only=True, help_text="발신자의 아바타 이미지 URL")
    sender = serializers.CharField(read_only=True, help_text="메시지 발신자의 닉네임")
    content = serializers.CharField(help_text="메시지 내용")
    timestamp = serializers.DateTimeField(read_only=True, help_text="메시지가 전송된 시간")
    
    class Meta:
        model = Message
        fields = ['id', 'sender', 'avatar', 'content', 'timestamp']