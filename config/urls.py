from django.urls import path, include

urlpatterns = [
    path('api/chat/', include('app.urls')),
]
