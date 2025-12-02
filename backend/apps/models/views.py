from rest_framework import viewsets, permissions, status, filters
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser

from .models import Model, ModelImage, ModelReviewLog, VisibilityStatus
from .serializers import (
    ModelSerializer, ModelCreateSerializer, ModelListSerializer,
    ModelImageSerializer, ModelReviewLogSerializer, ModelUpdateSerializer
)
from apps.users.models import Employee


class IsOwnerOrReadOnly(permissions.BasePermission):
    """
    Custom permission to only allow owners of a model to edit it.
    """
    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed for any request
        if request.method in permissions.SAFE_METHODS:
            return True
        # Write permissions only for the owner
        return obj.owner == request.user


class IsEmployee(permissions.BasePermission):
    """
    Permission check for employee-only actions.
    """
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        return Employee.objects.filter(user=request.user).exists()


class ModelViewSet(viewsets.ModelViewSet):
    """
    ViewSet for 3D Models.
    
    - Public models can be viewed by anyone
    - Users can view their own models regardless of status
    - Only authenticated users can create models
    - Only owners can update/delete their models
    """
    parser_classes = [MultiPartParser, FormParser, JSONParser]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['model_name', 'description', 'owner__email']
    ordering_fields = ['created_at', 'model_name', 'download_count', 'view_count']
    ordering = ['-created_at']
    
    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy', 'upload_images']:
            permission_classes = [permissions.IsAuthenticated, IsOwnerOrReadOnly]
        else:
            permission_classes = [permissions.AllowAny]
        return [permission() for permission in permission_classes]
    
    def get_serializer_class(self):
        if self.action == 'create':
            return ModelCreateSerializer
        if self.action in ['update', 'partial_update']:
            return ModelUpdateSerializer
        if self.action == 'list':
            return ModelListSerializer
        return ModelSerializer
    
    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['request'] = self.request
        return context
    
    def get_queryset(self):
        """
        Return models based on user authentication and visibility.
        - Guests: Only PUBLIC models
        - Authenticated: PUBLIC models + own models (any status)
        - Employees: Can also see PENDING models for review
        """
        user = self.request.user
        
        if user.is_authenticated:
            # Check if user is employee (for review actions)
            from apps.users.models import Employee
            is_employee = Employee.objects.filter(user=user).exists()
            
            if is_employee:
                # Employees can see public + pending + their own models
                return Model.objects.filter(
                    visibility_status__in=[VisibilityStatus.PUBLIC, VisibilityStatus.PENDING]
                ) | Model.objects.filter(owner=user)
            else:
                # Regular users can see public models and their own models
                return Model.objects.filter(
                    visibility_status=VisibilityStatus.PUBLIC
                ) | Model.objects.filter(owner=user)
        else:
            # Guests can only see public models
            return Model.objects.filter(visibility_status=VisibilityStatus.PUBLIC)
    
    @action(detail=False, methods=['get'])
    def my_models(self, request):
        """Get all models owned by the authenticated user."""
        if not request.user.is_authenticated:
            return Response({'error': 'Authentication required'}, status=status.HTTP_401_UNAUTHORIZED)
        
        models = Model.objects.filter(owner=request.user)
        serializer = ModelListSerializer(models, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def submit_for_review(self, request, pk=None):
        """Submit a private or rejected model for public review."""
        model = self.get_object()
        
        if model.owner != request.user:
            return Response(
                {'error': 'Only the owner can submit for review'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Allow both PRIVATE and REJECTED models to be submitted for review
        if model.visibility_status not in [VisibilityStatus.PRIVATE, VisibilityStatus.REJECTED]:
            return Response(
                {'error': 'Only private or rejected models can be submitted for review'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        model.visibility_status = VisibilityStatus.PENDING
        model.save()
        
        serializer = ModelSerializer(model, context={'request': request})
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'], parser_classes=[MultiPartParser, FormParser])
    def upload_images(self, request, pk=None):
        """Upload images for a model."""
        model = self.get_object()
        
        if model.owner != request.user:
            return Response(
                {'error': 'Only the owner can upload images'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        images = request.FILES.getlist('images')
        if not images:
            return Response(
                {'error': 'No images provided'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        created_images = []
        existing_count = model.images.count()
        
        for idx, image in enumerate(images):
            model_image = ModelImage.objects.create(
                model=model,
                image=image,
                is_primary=(existing_count == 0 and idx == 0),
                order=existing_count + idx
            )
            created_images.append(model_image)
        
        serializer = ModelImageSerializer(created_images, many=True, context={'request': request})
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
    @action(detail=True, methods=['delete'])
    def delete_image(self, request, pk=None):
        """Delete an image from a model."""
        model = self.get_object()
        
        if model.owner != request.user:
            return Response(
                {'error': 'Only the owner can delete images'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        image_id = request.data.get('image_id')
        if not image_id:
            return Response(
                {'error': 'image_id is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            image = ModelImage.objects.get(id=image_id, model=model)
            image.delete()
            return Response({'message': 'Image deleted successfully'})
        except ModelImage.DoesNotExist:
            return Response(
                {'error': 'Image not found'},
                status=status.HTTP_404_NOT_FOUND
            )
    
    @action(detail=False, methods=['get'], permission_classes=[IsEmployee])
    def pending_review(self, request):
        """Get all models pending review (Employee only)."""
        models = Model.objects.filter(visibility_status=VisibilityStatus.PENDING)
        serializer = ModelListSerializer(models, many=True, context={'request': request})
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'], permission_classes=[IsEmployee])
    def approve(self, request, pk=None):
        """Approve a pending model (Employee only)."""
        model = self.get_object()
        
        if model.visibility_status != VisibilityStatus.PENDING:
            return Response(
                {'error': 'Only pending models can be approved'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Get employee profile
        try:
            employee = Employee.objects.get(user=request.user)
        except Employee.DoesNotExist:
            return Response(
                {'error': 'Employee profile not found'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Log the review
        previous_status = model.visibility_status
        ModelReviewLog.objects.create(
            model=model,
            reviewer=employee,
            previous_status=previous_status,
            new_status=VisibilityStatus.PUBLIC,
            reason=request.data.get('reason', 'Approved')
        )
        
        # Update model status
        model.visibility_status = VisibilityStatus.PUBLIC
        model.save()
        
        serializer = ModelSerializer(model, context={'request': request})
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'], permission_classes=[IsEmployee])
    def reject(self, request, pk=None):
        """Reject a pending model (Employee only). Reason is required."""
        model = self.get_object()
        
        if model.visibility_status != VisibilityStatus.PENDING:
            return Response(
                {'error': 'Only pending models can be rejected'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        reason = request.data.get('reason')
        if not reason:
            return Response(
                {'error': 'Reason is required when rejecting a model'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Get employee profile
        try:
            employee = Employee.objects.get(user=request.user)
        except Employee.DoesNotExist:
            return Response(
                {'error': 'Employee profile not found'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Log the review
        previous_status = model.visibility_status
        ModelReviewLog.objects.create(
            model=model,
            reviewer=employee,
            previous_status=previous_status,
            new_status=VisibilityStatus.REJECTED,
            reason=reason
        )
        
        # Update model status
        model.visibility_status = VisibilityStatus.REJECTED
        model.save()
        
        serializer = ModelSerializer(model, context={'request': request})
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def review_logs(self, request, pk=None):
        """Get review logs for a model."""
        model = self.get_object()
        logs = ModelReviewLog.objects.filter(model=model).order_by('-timestamp')
        serializer = ModelReviewLogSerializer(logs, many=True)
        return Response(serializer.data)


class PublicModelViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Read-only ViewSet for browsing public models (marketplace).
    """
    serializer_class = ModelListSerializer
    permission_classes = [permissions.AllowAny]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['model_name', 'description', 'owner__email', 'category']
    ordering_fields = ['created_at', 'model_name', 'download_count', 'view_count']
    ordering = ['-created_at']
    
    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['request'] = self.request
        return context
    
    def get_queryset(self):
        queryset = Model.objects.filter(visibility_status=VisibilityStatus.PUBLIC)
        
        # Filter by is_featured if provided
        is_featured = self.request.query_params.get('is_featured', None)
        if is_featured is not None:
            queryset = queryset.filter(is_featured=is_featured.lower() == 'true')
        
        # Filter by category if provided
        category = self.request.query_params.get('category', None)
        if category:
            queryset = queryset.filter(category__iexact=category)
        
        return queryset
    
    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        # Increment view count
        instance.view_count += 1
        instance.save(update_fields=['view_count'])
        
        serializer = ModelSerializer(instance, context={'request': request})
        return Response(serializer.data)
