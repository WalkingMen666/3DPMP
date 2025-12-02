from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ShippingOptionViewSet, SavedAddressViewSet

router = DefaultRouter()
router.register(r'shipping-options', ShippingOptionViewSet, basename='shipping-option')
router.register(r'addresses', SavedAddressViewSet, basename='saved-address')

urlpatterns = [
    path('', include(router.urls)),
]
