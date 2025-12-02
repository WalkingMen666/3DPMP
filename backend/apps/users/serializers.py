from rest_framework import serializers
from dj_rest_auth.registration.serializers import RegisterSerializer
from django.db import transaction
from .models import Customer, Employee, User

class CustomRegisterSerializer(RegisterSerializer):
    # Remove username field requirement
    username = None
    
    def get_cleaned_data(self):
        return {
            'email': self.validated_data.get('email', ''),
            'password1': self.validated_data.get('password1', ''),
        }
    
    def save(self, request):
        user = super().save(request)
        user.auth_provider = 'local'
        user.save()
        
        # Automatically create Customer profile
        Customer.objects.create(user=user)
        return user

class UserSerializer(serializers.ModelSerializer):
    avatar_url = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = ('id', 'email', 'display_name', 'auth_provider', 'date_joined', 'avatar_type', 'avatar_image', 'avatar_url')
        read_only_fields = ('id', 'date_joined', 'auth_provider', 'avatar_url')
    
    def get_avatar_url(self, obj):
        return obj.avatar_url


class UserAvatarSerializer(serializers.ModelSerializer):
    """Serializer for updating user avatar"""
    class Meta:
        model = User
        fields = ('avatar_type', 'avatar_image')
    
    def validate(self, data):
        avatar_type = data.get('avatar_type')
        avatar_image = data.get('avatar_image')
        
        if avatar_type == 'custom' and not avatar_image and not self.instance.avatar_image:
            raise serializers.ValidationError("Custom avatar requires an uploaded image")
        
        # Clear image if not using custom type
        if avatar_type != 'custom':
            data['avatar_image'] = None
            
        return data

class CustomerSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    class Meta:
        model = Customer
        fields = '__all__'

class EmployeeSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    class Meta:
        model = Employee
        fields = '__all__'
