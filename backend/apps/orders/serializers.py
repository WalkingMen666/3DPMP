from rest_framework import serializers
from decimal import Decimal
from .models import Order, OrderItem, OrderLog, OrderStatus
from apps.materials.models import CartItem


class OrderItemSerializer(serializers.ModelSerializer):
    """Serializer for order items."""
    model_name = serializers.CharField(source='model.model_name', read_only=True)
    material_name = serializers.CharField(source='material.name', read_only=True)
    subtotal = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    
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
        total_price = subtotal + shipping_option.base_fee
        
        # TODO: Apply discounts (Global + Coupon)
        # This would involve checking GlobalDiscount and Coupon tables
        
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
