from rest_framework import status
from rest_framework.decorators import api_view, permission_classes, parser_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from rest_framework.authtoken.models import Token
from django.conf import settings

from .models import User, Employee, Customer
from .serializers import UserSerializer, UserAvatarSerializer


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_current_user(request):
    """Get current authenticated user details including role information"""
    user = request.user
    data = UserSerializer(user).data
    
    # Add role information
    data['role'] = 'customer'
    data['is_employee'] = False
    data['is_admin'] = False
    
    try:
        employee = Employee.objects.get(user=user)
        data['role'] = 'admin' if employee.is_admin else 'employee'
        data['is_employee'] = True
        data['is_admin'] = employee.is_admin
        data['employee_name'] = employee.employee_name
    except Employee.DoesNotExist:
        pass
    
    return Response(data)


@api_view(['POST'])
@permission_classes([AllowAny])
def google_login(request):
    """
    Handle Google OAuth login.
    Expects: { id_token: string } from frontend after Google Sign-In
    """
    from google.oauth2 import id_token
    from google.auth.transport import requests as google_requests
    
    token = request.data.get('id_token') or request.data.get('credential')
    if not token:
        return Response({'error': 'ID token is required'}, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        # Verify the token
        client_id = settings.GOOGLE_CLIENT_ID
        if not client_id:
            return Response(
                {'error': 'Google OAuth is not configured on the server'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
        idinfo = id_token.verify_oauth2_token(
            token, 
            google_requests.Request(), 
            client_id
        )
        
        # Get user info from token
        email = idinfo.get('email')
        if not email:
            return Response({'error': 'Email not provided by Google'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Check if user exists or create new one
        user, created = User.objects.get_or_create(
            email=email,
            defaults={
                'auth_provider': 'google',
            }
        )
        
        # If user was created, also create Customer profile (per requirements)
        if created:
            Customer.objects.create(user=user)
        else:
            # Update auth provider if user registered with local auth first
            if user.auth_provider == 'local':
                user.auth_provider = 'google'
                user.save()
        
        # Create or get auth token
        auth_token, _ = Token.objects.get_or_create(user=user)
        
        # Get role info
        role = 'customer'
        is_employee = False
        is_admin = False
        employee_name = None
        
        try:
            employee = Employee.objects.get(user=user)
            role = 'admin' if employee.is_admin else 'employee'
            is_employee = True
            is_admin = employee.is_admin
            employee_name = employee.employee_name
        except Employee.DoesNotExist:
            pass
        
        return Response({
            'key': auth_token.key,
            'user': {
                'id': str(user.id),
                'email': user.email,
                'avatar_url': user.avatar_url,
                'avatar_type': user.avatar_type,
                'auth_provider': user.auth_provider,
                'role': role,
                'is_employee': is_employee,
                'is_admin': is_admin,
                'employee_name': employee_name,
            }
        })
        
    except ValueError as e:
        # Invalid token
        return Response({'error': f'Invalid token: {str(e)}'}, status=status.HTTP_401_UNAUTHORIZED)
    except Exception as e:
        return Response({'error': f'Authentication failed: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([AllowAny])
def google_client_id(request):
    """Return Google Client ID for frontend initialization"""
    client_id = settings.GOOGLE_CLIENT_ID
    if not client_id:
        return Response({'error': 'Google OAuth not configured'}, status=status.HTTP_503_SERVICE_UNAVAILABLE)
    return Response({'client_id': client_id})


@api_view(['PUT', 'PATCH'])
@permission_classes([IsAuthenticated])
@parser_classes([MultiPartParser, FormParser, JSONParser])
def update_avatar(request):
    """Update user avatar"""
    serializer = UserAvatarSerializer(
        request.user, 
        data=request.data, 
        partial=True
    )
    
    if serializer.is_valid():
        serializer.save()
        # Return full user data with updated avatar
        user_serializer = UserSerializer(request.user)
        return Response(user_serializer.data)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_avatar_choices(request):
    """Get available avatar choices - only default and custom"""
    choices = [
        {'id': 'default', 'name': 'Default', 'url': None},
        {'id': 'custom', 'name': 'Custom Upload', 'url': None},
    ]
    return Response(choices)


@api_view(['PUT', 'PATCH'])
@permission_classes([IsAuthenticated])
@parser_classes([JSONParser])
def update_profile(request):
    """Update user profile (display name)"""
    user = request.user
    
    display_name = request.data.get('display_name')
    if display_name is not None:
        user.display_name = display_name
        user.save()
    
    return Response({
        'id': str(user.id),
        'email': user.email,
        'display_name': user.display_name,
        'avatar_type': user.avatar_type,
        'avatar_url': user.avatar_url,
    })
