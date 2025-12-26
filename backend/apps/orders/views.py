from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from rest_framework.decorators import action

from .models import Order, OrderItem, OrderLog
from .serializers import (
    OrderSerializer, OrderListSerializer, OrderCreateSerializer,
    OrderItemSerializer, OrderLogSerializer
)
from apps.users.models import Customer, Employee


def get_or_create_customer(user):
    """Get or create Customer profile for user."""
    customer, created = Customer.objects.get_or_create(user=user)
    return customer


class IsCustomerOwner(permissions.BasePermission):
    """Only allow customers to access their own orders."""

    def has_object_permission(self, request, view, obj):
        # Admin employees can access any order
        try:
            if request.user.employee_profile.is_admin:
                return True
        except Employee.DoesNotExist:
            pass
        
        customer = get_or_create_customer(request.user)
        return obj.customer == customer


class IsAdminEmployee(permissions.BasePermission):
    """Permission class for admin employees."""
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        try:
            return request.user.employee_profile.is_admin
        except Employee.DoesNotExist:
            return False


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
        # Admin employees can see all orders
        if hasattr(self.request.user, 'employee_profile') and self.request.user.employee_profile.is_admin:
            return Order.objects.all().prefetch_related('items', 'customer__user')

        # Regular customers only see their own orders
        customer = self.get_customer()
        return Order.objects.filter(customer=customer).prefetch_related('items')

    def get_permissions(self):
        """
        Override permissions for admin-only actions.
        """
        if self.action in ['pending', 'all_orders', 'update_status']:
            return [IsAdminEmployee()]
        return super().get_permissions()

    @action(detail=False, methods=['get'])
    def pending(self, request):
        """
        Admin-only endpoint to get all pending orders.
        """
        orders = Order.objects.filter(status='PENDING').prefetch_related('items', 'customer__user')
        serializer = OrderListSerializer(orders, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def all_orders(self, request):
        """
        Admin-only endpoint to get all orders.
        """
        orders = Order.objects.all().prefetch_related('items', 'customer__user')
        serializer = OrderListSerializer(orders, many=True)
        return Response(serializer.data)

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

    @action(detail=True, methods=['patch'])
    def update_status(self, request, pk=None):
        """
        Admin-only endpoint to update order status.
        """
        # Check if user is admin
        try:
            if not request.user.employee_profile.is_admin:
                return Response(
                    {'error': 'Only admins can update order status'},
                    status=status.HTTP_403_FORBIDDEN
                )
        except Employee.DoesNotExist:
            return Response(
                {'error': 'Only admins can update order status'},
                status=status.HTTP_403_FORBIDDEN
            )

        order = self.get_object()
        new_status = request.data.get('status')

        if not new_status:
            return Response(
                {'error': 'Status field is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Validate status
        valid_statuses = ['PENDING', 'PROCESSING', 'SHIPPED', 'DELIVERED', 'CANCELLED']
        if new_status not in valid_statuses:
            return Response(
                {'error': f'Invalid status. Must be one of: {", ".join(valid_statuses)}'},
                status=status.HTTP_400_BAD_REQUEST
            )

        order.status = new_status
        order.save()

        # Create order log
        OrderLog.objects.create(
            order=order,
            updated_by=request.user.employee_profile,
            new_status=new_status
        )

        serializer = OrderSerializer(order)
        return Response(serializer.data)


class OrderItemViewSet(viewsets.ReadOnlyModelViewSet):
    """Read-only ViewSet for order items."""
    serializer_class = OrderItemSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        customer = get_or_create_customer(self.request.user)
        return OrderItem.objects.filter(order__customer=customer)
