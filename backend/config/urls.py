from django.contrib import admin
from django.urls import path, include
from django.http import JsonResponse
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView, SpectacularRedocView

def hello_world(request):
    return JsonResponse({"message": "Hello from Django Backend!", "status": "ok"})

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/hello/', hello_world),
    path('api/auth/', include('apps.users.urls')),
    
    # API Documentation
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
]
