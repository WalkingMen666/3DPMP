from rest_framework import viewsets, permissions
from rest_framework.response import Response
from .models import ShippingOption, SavedAddress
from .serializers import (
    ShippingOptionSerializer, SavedAddressSerializer, SavedAddressCreateSerializer
)
from apps.users.models import Employee


class IsAdminEmployeeOrReadOnly(permissions.BasePermission):
    """Permission class for admin employees."""
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return request.user.is_authenticated
        if not request.user.is_authenticated:
            return False
        try:
            return request.user.employee_profile.is_admin
        except Employee.DoesNotExist:
            return False


class ShippingOptionViewSet(viewsets.ModelViewSet):
    """
    ViewSet for shipping options.
    - Authenticated users can view active options
    - Admin employees can manage all options
    """
    serializer_class = ShippingOptionSerializer
    permission_classes = [IsAdminEmployeeOrReadOnly]

    def get_queryset(self):
        # Admins see all options, others only see active ones
        if self.request.user.is_authenticated:
            try:
                if self.request.user.employee_profile.is_admin:
                    return ShippingOption.objects.all()
            except Employee.DoesNotExist:
                pass
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
