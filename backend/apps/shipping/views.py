from rest_framework import viewsets, permissions
from rest_framework.response import Response
from .models import ShippingOption, SavedAddress
from .serializers import (
    ShippingOptionSerializer, SavedAddressSerializer, SavedAddressCreateSerializer
)


class ShippingOptionViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Read-only ViewSet for shipping options.
    
    Available to all authenticated users.
    """
    serializer_class = ShippingOptionSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return ShippingOption.objects.filter(is_active=True)


class SavedAddressViewSet(viewsets.ModelViewSet):
    """
    ViewSet for customer saved addresses.
    
    Customers can:
    - List their saved addresses
    - Create new addresses
    - Update existing addresses
    - Delete addresses
    - Set default address
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return SavedAddressCreateSerializer
        return SavedAddressSerializer
    
    def get_queryset(self):
        user = self.request.user
        if hasattr(user, 'customer_profile'):
            return SavedAddress.objects.filter(customer=user.customer_profile)
        return SavedAddress.objects.none()
    
    def perform_create(self, serializer):
        serializer.save()
