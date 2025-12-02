from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import MaterialViewSet, CartItemViewSet

router = DefaultRouter()
router.register(r'materials', MaterialViewSet, basename='material')
router.register(r'cart', CartItemViewSet, basename='cart')

urlpatterns = [
    path('', include(router.urls)),
]
