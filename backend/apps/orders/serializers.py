from rest_framework import serializers
from decimal import Decimal
from django.utils import timezone
from django.db.models import Q
from .models import Order, OrderItem, OrderLog, OrderStatus
from apps.materials.models import CartItem


class OrderItemSerializer(serializers.ModelSerializer):
    """Serializer for order items."""
    model_name = serializers.SerializerMethodField()
    material_name = serializers.CharField(source='material.name', read_only=True)
    subtotal = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)

    def get_model_name(self, obj):
        """Return model name or [Deleted Model] if model was deleted."""
        return obj.model.model_name if obj.model else '[Deleted Model]'
    
    class Meta:
        model = OrderItem
        fields = [
            'id', 'order', 'model', 'model_name', 'material', 'material_name',
            'item_number', 'quantity', 'price_snapshot', 'slicing_info_snapshot',
            'notes', 'subtotal'
        ]
        read_only_fields = ['id', 'order', 'item_number', 'price_snapshot', 'slicing_info_snapshot']


class OrderSerializer(serializers.ModelSerializer):
    """Serializer for orders with items."""
    items = OrderItemSerializer(many=True, read_only=True)
    customer_email = serializers.EmailField(source='customer.user.email', read_only=True)
    assignee_name = serializers.CharField(source='assignee.employee_name', read_only=True)
    
    class Meta:
        model = Order
        fields = [
            'id', 'customer', 'customer_email', 'assignee', 'assignee_name',
            'status', 'ship_snapshot', 'total_price', 'notes', 'tracking_number',
            'creation_date', 'updated_at', 'items'
        ]
        read_only_fields = [
            'id', 'customer', 'total_price', 'creation_date', 'updated_at'
        ]


class OrderListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for order listings."""
    customer_email = serializers.EmailField(source='customer.user.email', read_only=True)
    item_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Order
        fields = [
            'id', 'customer_email', 'status', 'total_price',
            'creation_date', 'item_count'
        ]
    
    def get_item_count(self, obj):
        return obj.items.count()


class OrderCreateSerializer(serializers.Serializer):
    """
    Serializer for creating an order from cart items.
    
    Handles the conversion of cart items to order items with price snapshots.
    """
    shipping_option_id = serializers.UUIDField(required=True)
    saved_address_id = serializers.UUIDField(required=True)
    notes = serializers.CharField(required=False, allow_blank=True)
    coupon_code = serializers.CharField(required=False, allow_blank=True)
    
    def validate(self, data):
        user = self.context['request'].user
        
        # Check user has customer profile
        if not hasattr(user, 'customer_profile'):
            raise serializers.ValidationError("User does not have a customer profile")
        
        customer = user.customer_profile
        
        # Check cart is not empty
        cart_items = CartItem.objects.filter(customer=customer)
        if not cart_items.exists():
            raise serializers.ValidationError("Cart is empty")
        
        data['cart_items'] = cart_items
        data['customer'] = customer
        
        return data
    
    def create(self, validated_data):
        from apps.shipping.models import ShippingOption, SavedAddress
        from apps.discounts.models import Coupon, CouponRedemption, GlobalDiscount, IsAffected
        
        customer = validated_data['customer']
        cart_items = validated_data['cart_items']
        
        # Get shipping info and create snapshot
        try:
            shipping_option = ShippingOption.objects.get(
                id=validated_data['shipping_option_id'],
                is_active=True
            )
        except ShippingOption.DoesNotExist:
            raise serializers.ValidationError("Invalid shipping option")
        
        try:
            saved_address = SavedAddress.objects.get(
                id=validated_data['saved_address_id'],
                customer=customer
            )
        except SavedAddress.DoesNotExist:
            raise serializers.ValidationError("Invalid address")

        # Validate that shipping option type matches address type
        if shipping_option.type != saved_address.address_type:
            raise serializers.ValidationError(
                f"Shipping method type ({shipping_option.get_type_display()}) must match "
                f"delivery address type ({saved_address.get_address_type_display()})"
            )

        # Create shipping snapshot (immutable)
        ship_snapshot = {
            'service_name': shipping_option.name,
            'type': shipping_option.type,
            'fee': str(shipping_option.base_fee),
            'address_name': saved_address.name,
            'address_type': saved_address.address_type,
            'address_details': saved_address.address_details,
        }
        
        # Calculate total from cart items
        subtotal = Decimal('0')
        order_items_data = []
        
        for idx, cart_item in enumerate(cart_items, start=1):
            # Calculate price snapshot
            if cart_item.model.slicing_info and 'weight_g' in cart_item.model.slicing_info:
                weight = Decimal(str(cart_item.model.slicing_info['weight_g']))
                unit_price = weight * cart_item.material.price_twd_g
            else:
                unit_price = Decimal('0')
            
            item_subtotal = unit_price * cart_item.quantity
            subtotal += item_subtotal
            
            order_items_data.append({
                'model': cart_item.model,
                'material': cart_item.material,
                'item_number': idx,
                'quantity': cart_item.quantity,
                'price_snapshot': unit_price,
                'slicing_info_snapshot': cart_item.model.slicing_info,
                'notes': cart_item.notes,
            })
        
        # Add shipping fee
        shipping_fee = shipping_option.base_fee

        # Apply Global Discounts
        now = timezone.now()
        active_global_discounts = GlobalDiscount.objects.select_related('discount').filter(
            discount__is_active=True
        ).filter(
            Q(discount__start_date__lte=now) | Q(discount__start_date__isnull=True)
        ).filter(
            Q(discount__due_date__gte=now) | Q(discount__due_date__isnull=True)
        ).order_by('-priority')

        global_discount_total = Decimal('0')
        applied_global_discounts = []

        for gd in active_global_discounts:
            min_order = gd.discount.min_price or Decimal('0')
            if subtotal < min_order:
                continue

            if gd.discount.is_fixed:
                discount_amount = min(gd.discount.dis_value, subtotal)
            else:
                discount_amount = subtotal * (gd.discount.dis_value / Decimal('100'))
                if gd.discount.max_discount:
                    discount_amount = min(discount_amount, gd.discount.max_discount)

            global_discount_total += discount_amount
            applied_global_discounts.append({
                'global_discount': gd,
                'amount': discount_amount,
                'snapshot': {
                    'name': gd.discount.name,
                    'is_fixed': gd.discount.is_fixed,
                    'value': str(gd.discount.dis_value),
                    'min_price': str(gd.discount.min_price or 0),
                    'priority': gd.priority,
                }
            })

        # Apply Coupon if provided
        coupon_discount = Decimal('0')
        applied_coupon = None
        coupon_code = validated_data.get('coupon_code', '').strip()

        if coupon_code:
            try:
                coupon = Coupon.objects.select_related('discount').get(coupon_code__iexact=coupon_code)

                # Validate coupon
                if not coupon.discount.is_active:
                    raise serializers.ValidationError("Coupon is not active")
                if coupon.discount.start_date and now < coupon.discount.start_date:
                    raise serializers.ValidationError("Coupon is not yet valid")
                if coupon.discount.due_date and now > coupon.discount.due_date:
                    raise serializers.ValidationError("Coupon has expired")
                if coupon.max_uses_total and coupon.total_redemptions >= coupon.max_uses_total:
                    raise serializers.ValidationError("Coupon usage limit reached")
                if not coupon.is_valid_for_customer(customer):
                    raise serializers.ValidationError("Coupon already used by this customer")

                min_order = coupon.discount.min_price or Decimal('0')
                if subtotal < min_order:
                    raise serializers.ValidationError(f"Order subtotal must be at least NT${min_order}")

                # Check if coupon is stackable with global discounts
                if not coupon.is_stackable and global_discount_total > Decimal('0'):
                    raise serializers.ValidationError("This coupon cannot be combined with other discounts")

                # Calculate coupon discount from ORIGINAL subtotal (not after global discounts)
                if coupon.discount.is_fixed:
                    coupon_discount = min(coupon.discount.dis_value, subtotal)
                else:
                    coupon_discount = subtotal * (coupon.discount.dis_value / Decimal('100'))
                    if coupon.discount.max_discount:
                        coupon_discount = min(coupon_discount, coupon.discount.max_discount)

                applied_coupon = {
                    'coupon': coupon,
                    'amount': coupon_discount,
                    'snapshot': {
                        'code': coupon.coupon_code,
                        'name': coupon.discount.name,
                        'is_fixed': coupon.discount.is_fixed,
                        'value': str(coupon.discount.dis_value),
                        'min_price': str(coupon.discount.min_price or 0),
                    }
                }

            except Coupon.DoesNotExist:
                raise serializers.ValidationError("Invalid coupon code")

        # Calculate final total (cap total discount at subtotal)
        total_discount = min(global_discount_total + coupon_discount, subtotal)
        total_price = max(Decimal('0'), subtotal - total_discount + shipping_fee)

        # Create order
        order = Order.objects.create(
            customer=customer,
            ship_snapshot=ship_snapshot,
            total_price=total_price,
            notes=validated_data.get('notes', ''),
        )

        # Create order items
        for item_data in order_items_data:
            OrderItem.objects.create(order=order, **item_data)

        # Record applied global discounts
        for gd_data in applied_global_discounts:
            IsAffected.objects.create(
                order=order,
                global_discount=gd_data['global_discount'],
                discount_snapshot_info=gd_data['snapshot'],
                discount_amount=gd_data['amount'],
            )

        # Record coupon redemption
        if applied_coupon:
            CouponRedemption.objects.create(
                customer=customer,
                coupon=applied_coupon['coupon'],
                order=order,
                discount_snapshot_info=applied_coupon['snapshot'],
                discount_amount=applied_coupon['amount'],
            )

        # Clear cart after successful order
        cart_items.delete()

        return order


class OrderLogSerializer(serializers.ModelSerializer):
    """Serializer for order logs."""
    updated_by_name = serializers.CharField(source='updated_by.employee_name', read_only=True)
    
    class Meta:
        model = OrderLog
        fields = ['id', 'order', 'updated_by', 'updated_by_name', 'new_status', 'timestamp']
        read_only_fields = ['id', 'timestamp']
