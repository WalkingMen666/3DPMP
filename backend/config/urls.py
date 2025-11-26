from django.contrib import admin
from django.urls import path, include
from django.http import JsonResponse

def hello_world(request):
    return JsonResponse({"message": "Hello from Django Backend!", "status": "ok"})

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/hello/', hello_world),
    path('api/auth/', include('apps.users.urls')),
]
