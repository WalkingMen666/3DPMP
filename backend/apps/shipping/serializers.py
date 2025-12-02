from rest_framework import serializers
from .models import ShippingOption, SavedAddress


class ShippingOptionSerializer(serializers.ModelSerializer):
    """Serializer for shipping options."""
    type_display = serializers.CharField(source='get_type_display', read_only=True)
    
    class Meta:
        model = ShippingOption
        fields = ['id', 'name', 'type', 'type_display', 'base_fee', 'is_active']
        read_only_fields = ['id']


class SavedAddressSerializer(serializers.ModelSerializer):
    """Serializer for customer saved addresses."""
    address_type_display = serializers.CharField(source='get_address_type_display', read_only=True)
    
    class Meta:
        model = SavedAddress
        fields = [
            'id', 'name', 'address_type', 'address_type_display',
            'address_details', 'is_default', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class SavedAddressCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating saved addresses."""
    
    class Meta:
        model = SavedAddress
        fields = ['name', 'address_type', 'address_details', 'is_default']
    
    def create(self, validated_data):
        user = self.context['request'].user
        if not hasattr(user, 'customer_profile'):
            raise serializers.ValidationError("User does not have a customer profile")
        
        validated_data['customer'] = user.customer_profile
        return super().create(validated_data)
