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
    class Meta:
        model = User
        fields = ('id', 'email', 'auth_provider', 'date_joined')
        read_only_fields = ('id', 'date_joined', 'auth_provider')

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
