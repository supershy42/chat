from pathlib import Path
from decouple import config

# ENV
SECRET_KEY = config("SECRET_KEY")
DEBUG = config("DEBUG", cast=bool)

USER_SERVICE_URL = config("USER_SERVICE_URL")

DATABASE_ENGINE = config('DATABASE_ENGINE', default='sqlite3')

REDIS_HOST = config('REDIS_HOST')
REDIS_PORT = config('REDIS_PORT', cast=int)
REDIS_DB = config('REDIS_DB', cast=int)
REDIS_CAPACITY = config('REDIS_CAPACITY', cast=int)

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = SECRET_KEY

DEBUG = DEBUG

ALLOWED_HOSTS = ['api-gateway', 'localhost', '127.0.0.1', 'chat']

# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'channels',
    'chat_app',
    'drf_spectacular',
]

MIDDLEWARE = [
    'config.middleware.CustomHttpMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'


# Database
# https://docs.djangoproject.com/en/5.1/ref/settings/#databases

if DATABASE_ENGINE == 'sqlite3':
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3'
        }
    }
elif DATABASE_ENGINE == 'postgresql':
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': config('POSTGRES_DB', default=''),
            'USER': config('POSTGRES_USER', default=''),
            'PASSWORD': config('POSTGRES_PASSWORD', default=''),
            'HOST': config('POSTGRES_HOST', default='localhost'),
            'PORT': config('POSTGRES_PORT', default='5432'),
        }
    }
else:
    raise ValueError("Unsupported DATABASE_ENGINE value")


# Password validation
# https://docs.djangoproject.com/en/5.1/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# Internationalization
# https://docs.djangoproject.com/en/5.1/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'Asia/Seoul'

USE_I18N = True

USE_TZ = False


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.1/howto/static-files/

STATIC_URL = 'static/'

# Default primary key field type
# https://docs.djangoproject.com/en/5.1/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# ASGI 애플리케이션 설정
ASGI_APPLICATION = 'config.asgi.application'

# Redis 채널 레이어 추가
CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels_redis.core.RedisChannelLayer',
        'CONFIG': {
            "hosts": [(REDIS_HOST, REDIS_PORT)],
            "capacity": REDIS_CAPACITY, # 메시지 큐 용량
        },
    },
}

REST_FRAMEWORK = {
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
}

# DRF 스펙터 설정
SPECTACULAR_SETTINGS = {
    'TITLE': 'Chat Service API',
    'DESCRIPTION': '''
# 채팅 서비스 API 문서

## 인증
모든 API 엔드포인트는 유효한 JWT 토큰이 필요합니다.

- 토큰은 Authorization 헤더에 다음과 같이 제공되어야 합니다: `Authorization: Bearer <token>`
- 토큰은 미들웨어에 의해 검증됩니다
- 인증되지 않은 요청은 401 Unauthorized 응답을 받습니다

## 데이터베이스 제약조건
- 채팅방은 두 사용자 간에 유일해야 합니다 (user1_id, user2_id 쌍이 고유)
- 사용자 ID는 자동으로 정렬됩니다 (작은 ID가 user1_id, 큰 ID가 user2_id)
- 메시지는 timestamp 필드에 인덱스가 걸려있어 효율적인 조회가 가능합니다

## API 사용 흐름
1. 채팅방 생성
   - 두 사용자 간의 채팅방을 생성합니다
   - 사용자 ID는 자동으로 정렬됩니다
   - 이미 존재하는 채팅방인 경우 기존 채팅방을 반환합니다

2. 메시지 조회
   - 페이지네이션을 지원합니다 (기본 50개, 최대 100개)
   - 마지막으로 로드된 메시지 ID를 기준으로 이전 메시지를 조회할 수 있습니다
   - 메시지는 시간순으로 정렬됩니다 (오래된 것부터 최신순)

3. 채팅방 삭제
   - 채팅방에 속한 사용자만 삭제할 수 있습니다
   - 삭제 시 관련된 모든 메시지도 함께 삭제됩니다

## 웹소켓 연결
실시간 메시지 교환을 위한 웹소켓 연결은 다음 주소로 할 수 있습니다:
`ws://<host>/ws/chat/<chatroom_id>/?token=<jwt_token>`

## 오류 응답
모든 오류 응답은 다음과 같은 표준 형식을 따릅니다:
```json
{
    "error": "오류 메시지 설명"
}
```
유효성 검사 오류의 경우, 더 자세한 형식이 반환됩니다:
```json
{
    "필드_이름": ["이 필드에 대한 오류 메시지"]
}
```

## 주요 오류 코드
- 400: 잘못된 요청 (유효하지 않은 사용자 ID, 이미 존재하는 채팅방 등)
- 401: 인증 실패 (유효하지 않은 토큰)
- 403: 권한 거부 (채팅방에 대한 접근 권한 없음)
- 404: 리소스를 찾을 수 없음 (존재하지 않는 채팅방)
''',
    'VERSION': '1.0.0',
    'SERVE_INCLUDE_SCHEMA': False,
    'COMPONENT_SPLIT_REQUEST': True,
    'SWAGGER_UI_SETTINGS': {
        'deepLinking': True,
        'displayRequestDuration': True,
        'defaultModelsExpandDepth': 3,
        'defaultModelExpandDepth': 3,
        'defaultModelRendering': 'model',
        'displayOperationId': True,
        'docExpansion': 'list',
        'showExtensions': True,
        'supportedSubmitMethods': ['get', 'post', 'put', 'delete', 'patch'],
    },
    'TAGS': [
        {
            'name': '채팅방',
            'description': '''
채팅방 생성 및 관리를 위한 API

- 채팅방은 두 사용자 간에 유일합니다
- 사용자 ID는 자동으로 정렬됩니다
- 채팅방 삭제 시 관련된 모든 메시지도 함께 삭제됩니다
'''
        },
        {
            'name': '메시지',
            'description': '''
채팅 메시지 조회를 위한 API

- 페이지네이션을 지원합니다
- 메시지는 시간순으로 정렬됩니다
- 실시간 메시지 교환은 웹소켓을 통해 이루어집니다
'''
        }
    ],
    # 모든 응답 예시를 보여주도록 설정
    'DISPLAY_ALL_RESPONSES': True,
}