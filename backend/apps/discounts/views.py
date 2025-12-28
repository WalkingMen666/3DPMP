from rest_framework import viewsets, status
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, BasePermission, AllowAny
from django.utils import timezone
from django.db.models import Q

from .models import GlobalDiscount, Coupon
from .serializers import GlobalDiscountListSerializer, CouponListSerializer


@api_view(['GET'])
@permission_classes([AllowAny])
def active_global_discounts(request):
    """Get all currently active global discounts for customers."""
    now = timezone.now()

    discounts = GlobalDiscount.objects.select_related('discount').filter(
        discount__is_active=True
    ).filter(
        Q(discount__start_date__lte=now) | Q(discount__start_date__isnull=True)
    ).filter(
        Q(discount__due_date__gte=now) | Q(discount__due_date__isnull=True)
    ).order_by('-priority')

    serializer = GlobalDiscountListSerializer(discounts, many=True)
    return Response(serializer.data)


class IsEmployeeOrAdmin(BasePermission):
    """Permission class to check if user is an employee or admin."""
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        # Require employee profile for discount management
        return hasattr(request.user, 'employee_profile')


class GlobalDiscountViewSet(viewsets.ModelViewSet):
    """ViewSet for managing GlobalDiscounts (Employee/Admin only)"""
    permission_classes = [IsAuthenticated, IsEmployeeOrAdmin]
    queryset = GlobalDiscount.objects.select_related('discount').all()
    serializer_class = GlobalDiscountListSerializer

    def list(self, request):
        """List all global discounts"""
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    def retrieve(self, request, pk=None):
        """Get a single global discount"""
        try:
            global_discount = GlobalDiscount.objects.select_related('discount').get(pk=pk)
            serializer = self.get_serializer(global_discount)
            return Response(serializer.data)
        except GlobalDiscount.DoesNotExist:
            return Response({'error': 'Global discount not found'}, status=status.HTTP_404_NOT_FOUND)

    def create(self, request):
        """Create a new global discount"""
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            global_discount = serializer.save()
            return Response(
                self.get_serializer(global_discount).data,
                status=status.HTTP_201_CREATED
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def update(self, request, pk=None):
        """Update a global discount"""
        try:
            global_discount = GlobalDiscount.objects.select_related('discount').get(pk=pk)
            serializer = self.get_serializer(global_discount, data=request.data)
            if serializer.is_valid():
                serializer.save()
                return Response(self.get_serializer(global_discount).data)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except GlobalDiscount.DoesNotExist:
            return Response({'error': 'Global discount not found'}, status=status.HTTP_404_NOT_FOUND)

    def partial_update(self, request, pk=None):
        """Partially update a global discount"""
        try:
            global_discount = GlobalDiscount.objects.select_related('discount').get(pk=pk)
            serializer = self.get_serializer(global_discount, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response(self.get_serializer(global_discount).data)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except GlobalDiscount.DoesNotExist:
            return Response({'error': 'Global discount not found'}, status=status.HTTP_404_NOT_FOUND)

    def destroy(self, request, pk=None):
        """Delete a global discount"""
        try:
            global_discount = GlobalDiscount.objects.select_related('discount').get(pk=pk)
            # Delete the linked Discount (will cascade delete GlobalDiscount)
            global_discount.discount.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except GlobalDiscount.DoesNotExist:
            return Response({'error': 'Global discount not found'}, status=status.HTTP_404_NOT_FOUND)


class CouponViewSet(viewsets.ModelViewSet):
    """ViewSet for managing Coupons (Employee/Admin only)"""
    permission_classes = [IsAuthenticated, IsEmployeeOrAdmin]
    queryset = Coupon.objects.select_related('discount').all()
    serializer_class = CouponListSerializer

    def list(self, request):
        """List all coupons"""
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    def retrieve(self, request, pk=None):
        """Get a single coupon"""
        try:
            coupon = Coupon.objects.select_related('discount').get(pk=pk)
            serializer = self.get_serializer(coupon)
            return Response(serializer.data)
        except Coupon.DoesNotExist:
            return Response({'error': 'Coupon not found'}, status=status.HTTP_404_NOT_FOUND)

    def create(self, request):
        """Create a new coupon"""
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            coupon = serializer.save()
            return Response(
                self.get_serializer(coupon).data,
                status=status.HTTP_201_CREATED
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def update(self, request, pk=None):
        """Update a coupon"""
        try:
            coupon = Coupon.objects.select_related('discount').get(pk=pk)
            serializer = self.get_serializer(coupon, data=request.data)
            if serializer.is_valid():
                serializer.save()
                return Response(self.get_serializer(coupon).data)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Coupon.DoesNotExist:
            return Response({'error': 'Coupon not found'}, status=status.HTTP_404_NOT_FOUND)

    def partial_update(self, request, pk=None):
        """Partially update a coupon"""
        try:
            coupon = Coupon.objects.select_related('discount').get(pk=pk)
            serializer = self.get_serializer(coupon, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response(self.get_serializer(coupon).data)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Coupon.DoesNotExist:
            return Response({'error': 'Coupon not found'}, status=status.HTTP_404_NOT_FOUND)

    def destroy(self, request, pk=None):
        """Delete a coupon"""
        try:
            coupon = Coupon.objects.select_related('discount').get(pk=pk)
            # Delete the linked Discount (will cascade delete Coupon)
            coupon.discount.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except Coupon.DoesNotExist:
            return Response({'error': 'Coupon not found'}, status=status.HTTP_404_NOT_FOUND)

    @action(detail=False, methods=['post'], permission_classes=[IsAuthenticated])
    def validate(self, request):
        """Validate a coupon code (available to authenticated customers)"""
        code = request.data.get('code')
        order_subtotal = request.data.get('order_subtotal')
        
        if not code:
            return Response({
                'valid': False, 
                'error': 'Coupon code is required',
                'error_code': 'CODE_REQUIRED'
            }, status=status.HTTP_400_BAD_REQUEST)

        try:
            coupon = Coupon.objects.select_related('discount').get(coupon_code__iexact=code)
        except Coupon.DoesNotExist:
            return Response({
                'valid': False, 
                'error': 'Invalid coupon code',
                'error_code': 'NOT_FOUND'
            }, status=status.HTTP_404_NOT_FOUND)

        # Check if active
        if not coupon.discount.is_active:
            return Response({
                'valid': False, 
                'error': 'This coupon is no longer active',
                'error_code': 'INACTIVE'
            })

        # Check date validity
        now = timezone.now()
        
        if coupon.discount.start_date and now < coupon.discount.start_date:
            start_date_str = coupon.discount.start_date.strftime('%Y-%m-%d %H:%M')
            return Response({
                'valid': False, 
                'error': f'This coupon will be valid starting from {start_date_str}',
                'error_code': 'NOT_YET_VALID',
                'start_date': coupon.discount.start_date.isoformat(),
                'details': {
                    'start_date': start_date_str
                }
            })
            
        if coupon.discount.due_date and now > coupon.discount.due_date:
            end_date_str = coupon.discount.due_date.strftime('%Y-%m-%d %H:%M')
            return Response({
                'valid': False, 
                'error': f'This coupon expired on {end_date_str}',
                'error_code': 'EXPIRED',
                'end_date': coupon.discount.due_date.isoformat(),
                'details': {
                    'end_date': end_date_str
                }
            })

        # Check usage limits
        if coupon.max_uses_total and coupon.total_redemptions >= coupon.max_uses_total:
            return Response({
                'valid': False, 
                'error': f'This coupon has reached its usage limit ({coupon.max_uses_total} uses)',
                'error_code': 'USAGE_LIMIT_REACHED',
                'details': {
                    'max_uses': coupon.max_uses_total,
                    'times_used': coupon.total_redemptions
                }
            })

        # Check per-customer usage limit
        if hasattr(request.user, 'customer_profile'):
            customer = request.user.customer_profile
            customer_uses = coupon.redemptions.filter(customer=customer).count()
            if customer_uses >= coupon.max_uses_per_customer:
                return Response({
                    'valid': False, 
                    'error': f'You have already used this coupon {customer_uses} time(s) (limit: {coupon.max_uses_per_customer})',
                    'error_code': 'CUSTOMER_LIMIT_REACHED',
                    'details': {
                        'customer_uses': customer_uses,
                        'max_per_customer': coupon.max_uses_per_customer
                    }
                })

        # Check minimum order amount if order_subtotal is provided
        if order_subtotal:
            min_order = float(coupon.discount.min_price)
            if float(order_subtotal) < min_order:
                return Response({
                    'valid': False,
                    'error': f'Minimum order amount is NT${min_order:.0f} (your order: NT${float(order_subtotal):.0f})',
                    'error_code': 'MIN_ORDER_NOT_MET',
                    'details': {
                        'min_order_amount': min_order,
                        'order_subtotal': float(order_subtotal)
                    }
                })

        return Response({
            'valid': True,
            'coupon': self.get_serializer(coupon).data
        })
