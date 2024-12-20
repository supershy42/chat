from django.urls import path
from .views import ChatRoomCreateView, ChatRoomMessageListView

urlpatterns = [
    path('create/', ChatRoomCreateView.as_view(), name='create'),
    path('<int:chatroom_id>/messages/', ChatRoomMessageListView.as_view(), name='message_list')
]