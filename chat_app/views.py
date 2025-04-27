from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .serializers import ChatRoomSerializer, MessageSerializer
from .services import ChatRoomService
from django.shortcuts import get_object_or_404
from .models import ChatRoom
from asgiref.sync import async_to_sync
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiExample, OpenApiResponse
from rest_framework import serializers

# 채팅방 삭제를 위한 시리얼라이저 추가
class ChatRoomDeleteSerializer(serializers.Serializer):
    chatroom_id = serializers.IntegerField(help_text="삭제할 채팅방의 ID")

class ChatRoomCreateView(APIView):
    @extend_schema(
        request=ChatRoomSerializer,
        responses={
            201: OpenApiResponse(
                response=ChatRoomSerializer, 
                description="채팅방이 성공적으로 생성됨",
                examples=[
                    OpenApiExample(
                        '성공 응답',
                        value={
                            "id": 1,
                            "updated_at": "2023-04-06T15:30:45.123456Z",
                            "last_message": None
                        }
                    )
                ]
            ),
            400: OpenApiResponse(
                description="유효하지 않은 입력 데이터",
                examples=[
                    OpenApiExample(
                        '유효성 검사 오류',
                        value={
                            "user1_id": ["이 필드는 필수 항목입니다."],
                            "user2_id": ["유효하지 않은 사용자 ID입니다."]
                        }
                    )
                ]
            ),
            401: OpenApiResponse(
                description="인증 실패",
                examples=[
                    OpenApiExample(
                        '인증 오류',
                        value={"error": "인증 토큰이 없습니다."}
                    )
                ]
            )
        },
        description="두 사용자 간의 새로운 채팅방을 생성합니다. 사용자 ID는 서로 달라야 하고 유효해야 합니다.",
        tags=["채팅방"],
        examples=[
            OpenApiExample(
                '채팅방 생성 예시',
                value={
                    "user1_id": 1,
                    "user2_id": 2
                },
                request_only=True
            )
        ]
    )
    def post(self, request):
        serializer = ChatRoomSerializer(data=request.data, context={'token': request.token})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class ChatRoomMessageListView(APIView):
    @extend_schema(
        parameters=[
            OpenApiParameter(
                name="limit", 
                description="조회할 메시지 수 (기본값: 50, 최대: 100)", 
                type=int, 
                required=False,
                examples=[
                    OpenApiExample('기본 제한', value=50),
                    OpenApiExample('사용자 지정 제한', value=20)
                ]
            ),
            OpenApiParameter(
                name="last_loaded_message_id", 
                description="페이지네이션을 위한 마지막으로 로드된 메시지의 ID. 제공된 경우, 이 ID보다 오래된 메시지를 반환합니다.", 
                type=int, 
                required=False,
                examples=[OpenApiExample('마지막 메시지 ID', value=42)]
            )
        ],
        responses={
            200: OpenApiResponse(
                response=MessageSerializer(many=True),
                description="채팅방의 메시지 목록",
                examples=[
                    OpenApiExample(
                        '메시지 목록',
                        value=[
                            {
                                "id": 24,
                                "sender": "홍길동",
                                "avatar": "https://example.com/avatars/hong.jpg",
                                "content": "안녕하세요, 어떻게 지내세요?",
                                "timestamp": "2023-04-06T14:30:12Z"
                            },
                            {
                                "id": 23,
                                "sender": "김철수",
                                "avatar": "https://example.com/avatars/kim.jpg",
                                "content": "잘 지내고 있어요, 감사합니다!",
                                "timestamp": "2023-04-06T14:31:05Z"
                            }
                        ]
                    )
                ]
            ),
            401: OpenApiResponse(
                description="인증 실패",
                examples=[
                    OpenApiExample(
                        '인증 오류',
                        value={"error": "인증 토큰이 없습니다."}
                    )
                ]
            ),
            403: OpenApiResponse(
                description="권한 거부",
                examples=[
                    OpenApiExample(
                        '권한 오류',
                        value={"error": "사용자가 채팅방에 접근할 권한이 없습니다."}
                    )
                ]
            ),
            404: OpenApiResponse(
                description="채팅방을 찾을 수 없음",
                examples=[
                    OpenApiExample(
                        '존재하지 않음 오류',
                        value={"error": "찾을 수 없습니다."}
                    )
                ]
            )
        },
        description="페이지네이션을 지원하는 특정 채팅방의 메시지를 가져옵니다. 메시지는 가장 오래된 것부터 최신 순으로 정렬됩니다.",
        tags=["메시지"]
    )
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
    @extend_schema(
        request=ChatRoomDeleteSerializer,
        responses={
            204: OpenApiResponse(
                description="채팅방이 성공적으로 삭제됨",
                examples=[
                    OpenApiExample(
                        '성공 응답',
                        value=None
                    )
                ]
            ),
            400: OpenApiResponse(
                description="잘못된 요청 또는 사용자가 채팅방에 없음",
                examples=[
                    OpenApiExample(
                        '채팅방에 없음 오류',
                        value={"error": "사용자가 채팅방에 없습니다."}
                    )
                ]
            ),
            401: OpenApiResponse(
                description="인증 실패",
                examples=[
                    OpenApiExample(
                        '인증 오류',
                        value={"error": "인증 토큰이 없습니다."}
                    )
                ]
            ),
            404: OpenApiResponse(
                description="채팅방을 찾을 수 없음",
                examples=[
                    OpenApiExample(
                        '존재하지 않음 오류',
                        value={"error": "찾을 수 없습니다."}
                    )
                ]
            )
        },
        description="채팅방을 삭제합니다. 채팅방에 속한 사용자만 삭제할 수 있습니다.",
        tags=["채팅방"],
        examples=[
            OpenApiExample(
                '삭제 요청',
                value={"chatroom_id": 1},
                request_only=True
            )
        ]
    )
    def post(self, request):
        serializer = ChatRoomDeleteSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            
        user_id = request.user_id
        chatroom_id = serializer.validated_data['chatroom_id']
        chatroom = get_object_or_404(ChatRoom, id=chatroom_id)
        
        if not ChatRoomService.is_user_in_chatroom(user_id, chatroom):
            return Response({"error": "사용자가 채팅방에 없습니다."}, status=status.HTTP_400_BAD_REQUEST)     
    
        chatroom.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)