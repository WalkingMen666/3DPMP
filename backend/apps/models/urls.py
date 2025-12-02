from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import ModelViewSet, PublicModelViewSet

router = DefaultRouter()
router.register(r'models', ModelViewSet, basename='model')
router.register(r'public-models', PublicModelViewSet, basename='public-model')

urlpatterns = [
    path('', include(router.urls)),
]
