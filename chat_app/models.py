from django.db import models


class ChatRoom(models.Model):
    user1_id = models.BigIntegerField()
    user2_id = models.BigIntegerField()
    updated_at = models.DateTimeField(auto_now=True)
    
    @property
    def last_message(self):
        return self.message_set.order_by('-timestamp').first()
    
    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['user1_id', 'user2_id'],
                name='unique_chatroom_pair',
            ),
            models.UniqueConstraint(
                fields=['user2_id', 'user1_id'],
                name='unique_chatroom_pair_reverse'
            ),
        ]
    
    def save(self, *args, **kwargs):
        if self.user1_id > self.user2_id:
            self.user1_id, self.user2_id = self.user2_id, self.user1_id
        
        super().save(*args, **kwargs)
    
    def get_receiver_id(self, sender_id):
        if self.user1_id == sender_id:
            return self.user2_id
        return self.user1_id

class Message(models.Model):
    chatroom = models.ForeignKey(ChatRoom, on_delete=models.CASCADE)
    sender_id = models.BigIntegerField()
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)
    
    @property
    def receiver_id(self):
        return self.chatroom.get_receiver_id(self.sender_id)
    
    class Meta:
        indexes = [
            models.Index(fields=['timestamp']),
        ]