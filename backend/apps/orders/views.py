from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from rest_framework.decorators import action

from .models import Order, OrderItem, OrderLog
from .serializers import (
    OrderSerializer, OrderListSerializer, OrderCreateSerializer,
    OrderItemSerializer, OrderLogSerializer
)
from apps.users.models import Customer


def get_or_create_customer(user):
    """Get or create Customer profile for user."""
    customer, created = Customer.objects.get_or_create(user=user)
    return customer


class IsCustomerOwner(permissions.BasePermission):
    """Only allow customers to access their own orders."""
    
    def has_object_permission(self, request, view, obj):
        customer = get_or_create_customer(request.user)
        return obj.customer == customer


class OrderViewSet(viewsets.ModelViewSet):
    """
    ViewSet for customer orders.
    
    Customers can:
    - View their own orders
    - Create new orders from cart
    - Cancel pending orders
    """
    permission_classes = [permissions.IsAuthenticated, IsCustomerOwner]
    
    def get_serializer_class(self):
        if self.action == 'create':
            return OrderCreateSerializer
        if self.action == 'list':
            return OrderListSerializer
        return OrderSerializer
    
    def get_customer(self):
        """Get or create Customer profile for the authenticated user."""
        return get_or_create_customer(self.request.user)
    
    def get_queryset(self):
        customer = self.get_customer()
        return Order.objects.filter(customer=customer).prefetch_related('items')
    
    def create(self, request, *args, **kwargs):
        """Create an order from cart items."""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        order = serializer.save()
        
        output_serializer = OrderSerializer(order)
        return Response(output_serializer.data, status=status.HTTP_201_CREATED)
    
    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        """Cancel a pending order."""
        order = self.get_object()
        
        if order.status != 'PENDING':
            return Response(
                {'error': 'Only pending orders can be cancelled'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        order.status = 'CANCELLED'
        order.save()
        
        serializer = OrderSerializer(order)
        return Response(serializer.data)


class OrderItemViewSet(viewsets.ReadOnlyModelViewSet):
    """Read-only ViewSet for order items."""
    serializer_class = OrderItemSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        customer = get_or_create_customer(self.request.user)
        return OrderItem.objects.filter(order__customer=customer)
