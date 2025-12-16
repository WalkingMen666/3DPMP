from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from rest_framework.decorators import action
from django.shortcuts import get_object_or_404

from .models import Material, CartItem
from .serializers import MaterialSerializer, CartItemSerializer, CartItemCreateSerializer
from apps.users.models import Customer, Employee


def get_or_create_customer(user):
    """Get or create Customer profile for user."""
    customer, created = Customer.objects.get_or_create(user=user)
    return customer


class IsAdminEmployee(permissions.BasePermission):
    """Permission class for admin employees."""
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        if not request.user.is_authenticated:
            return False
        try:
            return request.user.employee_profile.is_admin
        except Employee.DoesNotExist:
            return False


class MaterialViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing materials.
    - Anyone can view active materials
    - Only admin employees can create/update/delete
    """
    serializer_class = MaterialSerializer
    permission_classes = [IsAdminEmployee]

    def get_queryset(self):
        # Admins see all materials, others only see active ones
        if self.request.user.is_authenticated:
            try:
                if self.request.user.employee_profile.is_admin:
                    return Material.objects.all()
            except Employee.DoesNotExist:
                pass
        return Material.objects.filter(is_active=True)


class CartItemViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing cart items.
    
    Users can only see and modify their own cart items.
    Cart items are tied to the authenticated user's Customer profile.
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return CartItemCreateSerializer
        return CartItemSerializer
    
    def get_customer(self):
        """Get or create Customer profile for the authenticated user."""
        return get_or_create_customer(self.request.user)
    
    def get_queryset(self):
        """Return cart items for the authenticated user only."""
        customer = self.get_customer()
        return CartItem.objects.filter(customer=customer).select_related(
            'material', 'model', 'customer'
        )
    
    def create(self, request, *args, **kwargs):
        """Create a new cart item for the authenticated user."""
        customer = self.get_customer()
        
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        instance = serializer.save()
        
        # Return full details
        output_serializer = CartItemSerializer(instance)
        return Response(output_serializer.data, status=status.HTTP_201_CREATED)
    
    def update(self, request, *args, **kwargs):
        """Update a cart item."""
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        
        # Only allow updating quantity and notes
        data = {
            'model': instance.model.id,
            'material': instance.material.id,
            'quantity': request.data.get('quantity', instance.quantity),
            'notes': request.data.get('notes', instance.notes),
        }
        
        serializer = CartItemCreateSerializer(instance, data=data, partial=partial)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        
        # Return full details
        output_serializer = CartItemSerializer(instance)
        return Response(output_serializer.data)
    
    @action(detail=False, methods=['delete'])
    def clear(self, request):
        """Clear all items from the user's cart."""
        customer = self.get_customer()
        deleted_count, _ = CartItem.objects.filter(customer=customer).delete()
        return Response({
            'message': f'Cleared {deleted_count} items from cart'
        })
    
    @action(detail=False, methods=['get'])
    def summary(self, request):
        """Get cart summary with total estimated price."""
        cart_items = self.get_queryset()
        serializer = CartItemSerializer(cart_items, many=True)
        
        total_items = sum(item.quantity for item in cart_items)
        estimated_total = sum(
            item.get('estimated_price', 0) or 0 
            for item in serializer.data
        )
        
        return Response({
            'items': serializer.data,
            'total_items': total_items,
            'estimated_total': round(estimated_total, 2)
        })
