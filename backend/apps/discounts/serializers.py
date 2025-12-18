from rest_framework import serializers
from django.utils import timezone
from .models import Discount, GlobalDiscount, Coupon


class GlobalDiscountListSerializer(serializers.ModelSerializer):
    """Flat serializer for listing and creating GlobalDiscounts with simplified fields."""
    id = serializers.UUIDField(source='discount.id', read_only=True)
    name = serializers.CharField(source='discount.name')
    discount_type = serializers.SerializerMethodField()
    discount_value = serializers.DecimalField(
        source='discount.dis_value', max_digits=10, decimal_places=2
    )
    min_order_amount = serializers.DecimalField(
        source='discount.min_price', max_digits=10, decimal_places=2, required=False, default=0
    )
    start_date = serializers.DateTimeField(source='discount.start_date', required=False, allow_null=True)
    end_date = serializers.DateTimeField(source='discount.due_date', required=False, allow_null=True)
    is_active = serializers.BooleanField(source='discount.is_active')
    created_at = serializers.DateTimeField(source='discount.created_at', read_only=True)

    class Meta:
        model = GlobalDiscount
        fields = [
            'id', 'name', 'discount_type', 'discount_value',
            'min_order_amount', 'start_date', 'end_date',
            'is_active', 'priority', 'created_at'
        ]

    def get_discount_type(self, obj):
        return 'FIXED' if obj.discount.is_fixed else 'PERCENTAGE'

    def to_internal_value(self, data):
        # Work with a copy to avoid mutating input
        data = data.copy()
        # Convert discount_type to is_fixed
        if 'discount_type' in data:
            data['is_fixed'] = data.pop('discount_type') == 'FIXED'
        return super().to_internal_value(data)

    def create(self, validated_data):
        discount_data = validated_data.pop('discount', {})

        # Handle is_fixed from converted discount_type
        is_fixed = self.initial_data.get('discount_type') == 'FIXED'

        # Set defaults
        discount_data['is_fixed'] = is_fixed
        if 'start_date' not in discount_data or not discount_data['start_date']:
            discount_data['start_date'] = timezone.now()
        if 'min_price' not in discount_data:
            discount_data['min_price'] = 0
        discount_data['works_on'] = 'ORDER_SUBTOTAL'

        discount = Discount.objects.create(**discount_data)
        global_discount = GlobalDiscount.objects.create(
            discount=discount,
            priority=validated_data.get('priority', 0)
        )
        return global_discount

    def update(self, instance, validated_data):
        discount_data = validated_data.pop('discount', {})

        # Handle is_fixed from converted discount_type
        if 'discount_type' in self.initial_data:
            discount_data['is_fixed'] = self.initial_data['discount_type'] == 'FIXED'

        # Update discount fields
        for attr, value in discount_data.items():
            setattr(instance.discount, attr, value)
        instance.discount.save()

        # Update priority if provided
        if 'priority' in validated_data:
            instance.priority = validated_data['priority']
            instance.save()

        return instance


class CouponListSerializer(serializers.ModelSerializer):
    """Flat serializer for listing and creating Coupons with simplified fields."""
    id = serializers.UUIDField(source='discount.id', read_only=True)
    name = serializers.CharField(source='discount.name')
    code = serializers.CharField(source='coupon_code')
    discount_type = serializers.SerializerMethodField()
    discount_value = serializers.DecimalField(
        source='discount.dis_value', max_digits=10, decimal_places=2
    )
    min_order_amount = serializers.DecimalField(
        source='discount.min_price', max_digits=10, decimal_places=2, required=False, default=0
    )
    max_uses = serializers.IntegerField(source='max_uses_total', required=False, allow_null=True)
    times_used = serializers.SerializerMethodField()
    start_date = serializers.DateTimeField(source='discount.start_date', required=False, allow_null=True)
    end_date = serializers.DateTimeField(source='discount.due_date', required=False, allow_null=True)
    is_active = serializers.BooleanField(source='discount.is_active')
    created_at = serializers.DateTimeField(source='discount.created_at', read_only=True)

    class Meta:
        model = Coupon
        fields = [
            'id', 'name', 'code', 'discount_type', 'discount_value',
            'min_order_amount', 'max_uses', 'times_used', 'is_stackable',
            'start_date', 'end_date', 'is_active', 'created_at'
        ]

    def get_discount_type(self, obj):
        return 'FIXED' if obj.discount.is_fixed else 'PERCENTAGE'

    def get_times_used(self, obj):
        return obj.total_redemptions

    def to_internal_value(self, data):
        # Work with a copy to avoid mutating input
        data = data.copy()
        # Convert discount_type to is_fixed
        if 'discount_type' in data:
            data['is_fixed'] = data.pop('discount_type') == 'FIXED'
        return super().to_internal_value(data)

    def create(self, validated_data):
        discount_data = validated_data.pop('discount', {})

        # Handle is_fixed from converted discount_type
        is_fixed = self.initial_data.get('discount_type') == 'FIXED'

        # Set defaults
        discount_data['is_fixed'] = is_fixed
        if 'start_date' not in discount_data or not discount_data['start_date']:
            discount_data['start_date'] = timezone.now()
        if 'min_price' not in discount_data:
            discount_data['min_price'] = 0
        discount_data['works_on'] = 'ORDER_SUBTOTAL'

        discount = Discount.objects.create(**discount_data)

        coupon = Coupon.objects.create(
            discount=discount,
            coupon_code=validated_data.get('coupon_code'),
            max_uses_total=validated_data.get('max_uses_total'),
            max_uses_per_customer=validated_data.get('max_uses_per_customer', 1),
            is_stackable=validated_data.get('is_stackable', True)
        )
        return coupon

    def update(self, instance, validated_data):
        discount_data = validated_data.pop('discount', {})

        # Handle is_fixed from converted discount_type
        if 'discount_type' in self.initial_data:
            discount_data['is_fixed'] = self.initial_data['discount_type'] == 'FIXED'

        # Update discount fields
        for attr, value in discount_data.items():
            setattr(instance.discount, attr, value)
        instance.discount.save()

        # Update coupon fields
        if 'max_uses_total' in validated_data:
            instance.max_uses_total = validated_data['max_uses_total']
        if 'max_uses_per_customer' in validated_data:
            instance.max_uses_per_customer = validated_data['max_uses_per_customer']
        if 'is_stackable' in validated_data:
            instance.is_stackable = validated_data['is_stackable']
        instance.save()

        return instance


class CouponValidationSerializer(serializers.Serializer):
    """Serializer for coupon validation requests."""
    code = serializers.CharField()
    order_subtotal = serializers.DecimalField(max_digits=10, decimal_places=2, required=False)
