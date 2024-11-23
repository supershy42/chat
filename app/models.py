from django.db import models


class ChatRoom(models.Model):
    user1_id = models.BigIntegerField()
    user2_id = models.BigIntegerField()
    
    last_message = models.TextField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def get_receiver_id(self, sender_id):
        if self.user1_id == sender_id:
            return self.user2_id
        return self.user1_id

class Message(models.Model):
    chatroom = models.ForeignKey(ChatRoom, on_delete=models.CASCADE)
    sender_id = models.BigIntegerField()
    receiver_id = models.BigIntegerField()
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)