from django.urls import path
from .views import ChatRoomCreateView
from .views import (
    ChatRoomCreateView,
    ChatRoomMessageListView,
    ChatRoomDeleteView
)

urlpatterns = [
    path('create/', ChatRoomCreateView.as_view(), name='create'),
    path('<int:chatroom_id>/messages/', ChatRoomMessageListView.as_view(), name='message_list'),
    path('delete/', ChatRoomDeleteView.as_view(), name='delete')
]