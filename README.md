# Chat Service API Server

본 프로젝트는 MSA(Microservice Architecture) 기반 서비스의 채팅 기능을 담당하는 백엔드 서버입니다. WebSocket을 이용한 실시간 채팅과 채팅방 관리를 위한 RESTful API를 제공합니다.

## 1. 기술 스택 (Tech Stack)

- **Language**: Python (3.x)
- **Framework**: Django, Django REST Framework, Django Channels
- **Database**: PostgreSQL (운영), SQLite (개발)
- **Cache / Message Broker**: Redis
- **Deployment**: Docker
- **Libraries**:
  - `djangorestframework`: RESTful API 개발
  - `channels`: WebSocket 통신
  - `channels_redis`: Redis 채널 레이어
  - `daphne`: ASGI 서버
  - `psycopg2-binary`: PostgreSQL 드라이버
  - `python-decouple`: 환경변수 관리
  - `aiohttp`: 비동기 HTTP 클라이언트 (외부 서비스 연동)
  - `PyJWT`: JWT 토큰 처리

## 2. 프로젝트 실행 방법 (Getting Started)

### 사전 요구사항 (Prerequisites)

- Python 3.x
- Pip
- Docker (선택 사항)
- Redis

### 설치 및 실행 (Installation & Running)

1.  **프로젝트 클론**
    ```bash
    git clone <repository_url>
    cd chat
    ```

2.  **가상환경 생성 및 패키지 설치**
    ```bash
    python -m venv venv
    # Windows
    venv\Scripts\activate
    # macOS / Linux
    # source venv/bin/activate

    pip install -r requirements.txt
    ```

3.  **환경변수 설정 (Environment Variables)**
    - `.env.example` 파일을 복사하여 `.env` 파일을 생성합니다. 이 파일은 git에 의해 추적되지 않으므로 민감한 정보를 저장하기에 안전합니다.
    ```bash
    cp .env.example .env
    ```
    - 생성된 `.env` 파일을 열어 자신의 로컬 개발 환경에 맞게 변수 값을 수정합니다. 각 변수에 대한 설명은 아래 `6. 환경변수 상세 설명` 섹션을 참고하세요.

4.  **데이터베이스 설정 (Database Setup)**
    - Django 마이그레이션을 실행하여 데이터베이스 스키마를 생성합니다.
    ```bash
    python manage.py migrate
    ```

5.  **개발 서버 실행 (Running the App)**
    - 본 프로젝트는 WebSocket을 포함하고 있으므로 `runserver` 대신 `daphne`와 같은 ASGI 서버로 실행해야 합니다.
    ```bash
    daphne -p 8000 config.asgi:application
    ```
    - 서버가 정상적으로 실행되면 `http://localhost:8000` 에서 API 서버에 접속할 수 있으며, WebSocket도 정상적으로 동작합니다.

## 3. API 문서 (API Documentation)

*현재 API 문서는 이 README 파일로 대체하며, 향후 Postman 또는 Swagger를 이용한 문서가 추가될 예정입니다.*

### Chat Room

#### `POST /api/chat/create/`
- **설명**: 두 사용자 간의 새로운 채팅방을 생성합니다.
- **인증**: `Authorization: Bearer <jwt_token>` 헤더 필요.
- **Request Body**:
  ```json
  {
    "user1_id": 1,
    "user2_id": 2
  }
  ```
- **Response**:
  - **201 Created**: 채팅방 생성 성공. 생성된 채팅방 정보 반환.
  - **400 Bad Request**: 이미 채팅방이 존재하거나, 유효하지 않은 사용자 ID일 경우.
  - **401 Unauthorized**: 인증 토큰이 없거나 유효하지 않을 경우.

#### `POST /api/chat/delete/`
- **설명**: 특정 채팅방을 삭제합니다.
- **인증**: `Authorization: Bearer <jwt_token>` 헤더 필요.
- **Request Body**:
  ```json
  {
    "chatroom_id": 1
  }
  ```
- **Response**:
  - **204 No Content**: 채팅방 삭제 성공.
  - **400 Bad Request**: 요청한 사용자가 채팅방에 속해있지 않을 경우.
  - **401 Unauthorized**: 인증 토큰이 없거나 유효하지 않을 경우.
  - **404 Not Found**: 해당 ID의 채팅방이 존재하지 않을 경우.

### Messages

#### `GET /api/chat/<chatroom_id>/messages/`
- **설명**: 특정 채팅방의 메시지 목록을 조회합니다. 무한 스크롤을 지원합니다.
- **인증**: `Authorization: Bearer <jwt_token>` 헤더 필요.
- **Query Parameters**:
  - `limit` (optional): 한 번에 가져올 메시지 개수 (기본값: 50)
  - `last_loaded_message_id` (optional): 가장 마지막에 로드된 메시지의 ID. 이 ID보다 오래된 메시지를 가져옵니다.
- **Response**:
  - **200 OK**: 메시지 목록 반환.
  - **401 Unauthorized**: 인증 토큰이 없거나 유효하지 않을 경우.
  - **403 Forbidden**: 해당 채팅방에 접근 권한이 없을 경우.
  - **404 Not Found**: 해당 ID의 채팅방이 존재하지 않을 경우.

### WebSocket

- **Endpoint**: `ws/chat/<chatroom_id>/?token=<jwt_token>`
- **설명**: 실시간 채팅을 위한 WebSocket 연결 주소입니다.
- **메시지 전송 형식**:
  ```json
  {
    "type": "chat",
    "content": "안녕하세요!"
  }
  ```
- **메시지 수신 형식**:
  ```json
  {
    "type": "chat.message",
    "sender": "보내는사람닉네임",
    "avatar": "아바타URL",
    "content": "안녕하세요!",
    "timestamp": "2024-12-25 10:30:00"
  }
  ```

## 4. 테스트 (Running Tests)

- 아래 명령어를 실행하여 모든 테스트를 실행할 수 있습니다.
  ```bash
  python manage.py test
  ```

## 5. 프로젝트 구조 (Project Structure)

```
.
├── chat_app/         # 핵심 채팅 애플리케이션
│   ├── consumers.py  # WebSocket 로직 처리
│   ├── models.py     # 데이터베이스 모델 (ChatRoom, Message)
│   ├── serializers.py# 데이터 직렬화/역직렬화
│   ├── services.py   # 비즈니스 로직 (외부 서비스 연동 등)
│   ├── views.py      # REST API 뷰
│   ├── urls.py       # API 라우팅
│   └── routing.py    # WebSocket 라우팅
├── config/           # 프로젝트 전반의 설정
│   ├── settings.py   # Django 설정
│   ├── middleware.py # 커스텀 HTTP/WS 미들웨어 (인증 처리)
│   ├── urls.py       # 최상위 URL 설정
│   └── asgi.py       # ASGI 서버 설정
├── utils/            # 유틸리티 스크립트
│   └── entrypoint.sh # Docker 컨테이너 실행 스크립트
├── requirements.txt  # Python 패키지 의존성 목록
└── manage.py         # Django 관리 스크립트
```

## 6. 환경변수 상세 설명 (Environment Variables)

| 변수명 | 설명 | 필수 여부 | 예시 값 |
| --- | --- | --- | --- |
| `SECRET_KEY` | Django 애플리케이션의 비밀 키 | 예 | `your-very-secret-key` |
| `DEBUG` | 디버그 모드 활성화 여부 | 예 | `True` |
| `USER_SERVICE_URL` | 유저 정보를 가져올 외부 유저 서비스의 URL | 예 | `http://user-service:8000/api/` |
| `DATABASE_ENGINE` | 사용할 데이터베이스 엔진 | 예 | `postgresql` |
| `POSTGRES_DB` | PostgreSQL 데이터베이스 이름 | 예 | `chat_db` |
| `POSTGRES_USER` | PostgreSQL 사용자 이름 | 예 | `user` |
| `POSTGRES_PASSWORD` | PostgreSQL 비밀번호 | 예 | `password` |
| `POSTGRES_HOST` | PostgreSQL 호스트 주소 | 예 | `db` 또는 `localhost` |
| `POSTGRES_PORT` | PostgreSQL 포트 번호 | 예 | `5432` |
| `REDIS_HOST` | Redis 호스트 주소 | 예 | `redis` 또는 `localhost` |
| `REDIS_PORT` | Redis 포트 번호 | 예 | `6379` |
| `REDIS_DB` | 사용할 Redis 데이터베이스 번호 | 예 | `1` |
| `REDIS_CAPACITY` | 채널 레이어의 메시지 큐 용량 | 예 | `100` |

## 7. 코딩 스타일 및 컨벤션 (Coding Style & Conventions)

*현재 프로젝트에는 별도의 코딩 스타일 가이드나 컨벤션이 정의되어 있지 않습니다. 향후 Black, isort, Flake8 등의 도구를 도입하여 코드 포맷팅과 린팅을 강제할 예정입니다.*
