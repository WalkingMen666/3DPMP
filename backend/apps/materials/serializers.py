from rest_framework import serializers
from .models import Material, CartItem


class MaterialSerializer(serializers.ModelSerializer):
    """Serializer for Material model."""
    
    class Meta:
        model = Material
        fields = ['id', 'name', 'density_g_cm3', 'price_twd_g', 'is_active', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']


class CartItemSerializer(serializers.ModelSerializer):
    """Serializer for CartItem with nested details."""
    material_name = serializers.CharField(source='material.name', read_only=True)
    material_price = serializers.DecimalField(
        source='material.price_twd_g', 
        max_digits=10, 
        decimal_places=2, 
        read_only=True
    )
    model_name = serializers.CharField(source='model.model_name', read_only=True)
    model_slicing_info = serializers.JSONField(source='model.slicing_info', read_only=True)
    
    # Estimated price based on current material prices
    estimated_price = serializers.SerializerMethodField()
    
    class Meta:
        model = CartItem
        fields = [
            'id', 'customer', 'model', 'material', 'quantity', 'notes',
            'material_name', 'material_price', 'model_name', 'model_slicing_info',
            'estimated_price', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'customer', 'created_at', 'updated_at']
    
    def get_estimated_price(self, obj):
        """Calculate estimated price based on current material price and slicing info."""
        if obj.model.slicing_info and 'weight_g' in obj.model.slicing_info:
            weight = obj.model.slicing_info['weight_g']
            price_per_gram = float(obj.material.price_twd_g)
            return round(weight * price_per_gram * obj.quantity, 2)
        return None


class CartItemCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating/updating CartItem."""
    
    class Meta:
        model = CartItem
        fields = ['model', 'material', 'quantity', 'notes']
    
    def validate_quantity(self, value):
        if value < 1:
            raise serializers.ValidationError("Quantity must be at least 1.")
        return value
    
    def create(self, validated_data):
        # Get customer from the authenticated user
        user = self.context['request'].user
        customer = user.customer_profile
        validated_data['customer'] = customer
        
        # Check if same model+material combo exists, if so update quantity
        existing = CartItem.objects.filter(
            customer=customer,
            model=validated_data['model'],
            material=validated_data['material']
        ).first()
        
        if existing:
            existing.quantity += validated_data.get('quantity', 1)
            existing.notes = validated_data.get('notes', existing.notes)
            existing.save()
            return existing
        
        return super().create(validated_data)
