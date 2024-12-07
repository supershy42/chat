from django.urls import path
from .views import ChatRoomCreateView

urlpatterns = [
    path('create/', ChatRoomCreateView.as_view(), name='create')
]