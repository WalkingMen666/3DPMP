from rest_framework import serializers
from dj_rest_auth.registration.serializers import RegisterSerializer
from dj_rest_auth.serializers import PasswordResetSerializer as DefaultPasswordResetSerializer
from dj_rest_auth.serializers import LoginSerializer
from allauth.account.models import EmailAddress
from django.db import transaction
from django.contrib.auth import authenticate
from .models import Customer, Employee, User
from .forms import CustomPasswordResetForm


class CustomLoginSerializer(LoginSerializer):
    """
    Custom login serializer that bypasses email verification for staff users.
    Regular customers still require email verification.
    """
    
    def validate(self, attrs):
        username = attrs.get('username')
        email = attrs.get('email')
        password = attrs.get('password')
        
        user = None
        
        # Try to authenticate
        if email:
            user = authenticate(
                request=self.context.get('request'),
                email=email,
                password=password
            )
        
        if user is None:
            msg = 'Unable to log in with provided credentials.'
            raise serializers.ValidationError(msg)
        
        # Check if user is active
        if not user.is_active:
            msg = 'User account is disabled.'
            raise serializers.ValidationError(msg)
        
        # For staff users (employees/admins), bypass email verification
        if user.is_staff:
            attrs['user'] = user
            return attrs
        
        # For regular users, check email verification
        email_address = EmailAddress.objects.filter(user=user, email=user.email).first()
        if email_address is None or not email_address.verified:
            msg = 'E-mail is not verified.'
            raise serializers.ValidationError(msg)
        
        attrs['user'] = user
        return attrs

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


class EmployeeListSerializer(serializers.ModelSerializer):
    """Flat serializer for employee listing with user details"""
    id = serializers.UUIDField(source='user.id', read_only=True)
    email = serializers.EmailField(source='user.email', read_only=True)
    display_name = serializers.CharField(source='user.display_name', read_only=True)
    date_joined = serializers.DateTimeField(source='user.date_joined', read_only=True)
    is_active = serializers.BooleanField(source='user.is_active', read_only=True)

    class Meta:
        model = Employee
        fields = ['id', 'email', 'display_name', 'employee_name', 'is_admin', 'date_joined', 'is_active']


class EmployeeCreateSerializer(serializers.Serializer):
    """Serializer for creating a new employee"""
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, min_length=8)
    employee_name = serializers.CharField(max_length=255)
    is_admin = serializers.BooleanField(default=False)

    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("A user with this email already exists.")
        return value

    def create(self, validated_data):
        # Create user
        user = User.objects.create_user(
            email=validated_data['email'],
            password=validated_data['password']
        )
        user.is_staff = True  # Allow admin panel access
        user.save()

        # Create employee profile
        employee = Employee.objects.create(
            user=user,
            employee_name=validated_data['employee_name'],
            is_admin=validated_data.get('is_admin', False)
        )
        return employee


class EmployeeUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating employee"""
    is_active = serializers.BooleanField(required=False)

    class Meta:
        model = Employee
        fields = ['employee_name', 'is_admin', 'is_active']

    def update(self, instance, validated_data):
        is_active = validated_data.pop('is_active', None)

        # Update employee fields
        instance.employee_name = validated_data.get('employee_name', instance.employee_name)
        instance.is_admin = validated_data.get('is_admin', instance.is_admin)
        instance.save()

        # Update user is_active if provided
        if is_active is not None:
            instance.user.is_active = is_active
            instance.user.save()

        return instance


class CustomPasswordResetSerializer(DefaultPasswordResetSerializer):
    """Custom password reset serializer to use custom form."""

    @property
    def password_reset_form_class(self):
        """Return custom password reset form."""
        return CustomPasswordResetForm
