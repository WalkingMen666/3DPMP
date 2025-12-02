from rest_framework import serializers
from .models import Model, ModelImage, ModelReviewLog, VisibilityStatus, ModelCategory


class ModelImageSerializer(serializers.ModelSerializer):
    """Serializer for model images."""
    url = serializers.SerializerMethodField()
    
    class Meta:
        model = ModelImage
        fields = ['id', 'image', 'image_path', 'url', 'is_primary', 'order', 'created_at']
        read_only_fields = ['id', 'created_at']
    
    def get_url(self, obj):
        if obj.image:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.image.url)
            return obj.image.url
        return obj.image_path


class ModelSerializer(serializers.ModelSerializer):
    """Serializer for 3D Model with images."""
    images = serializers.SerializerMethodField()
    owner_email = serializers.EmailField(source='owner.email', read_only=True)
    owner_name = serializers.SerializerMethodField()
    thumbnail_url = serializers.SerializerMethodField()
    category_display = serializers.CharField(source='get_category_display', read_only=True)
    
    class Meta:
        model = Model
        fields = [
            'id', 'owner', 'owner_email', 'owner_name', 'model_name', 'description', 
            'category', 'category_display', 'tags', 'visibility_status', 'is_featured',
            'stl_file_path', 'stl_file', 'gcode_file_path', 'thumbnail', 'thumbnail_url',
            'slicing_info', 'download_count', 'view_count', 'price',
            'images', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'owner', 'gcode_file_path', 'slicing_info', 
                           'download_count', 'view_count', 'created_at', 'updated_at']
    
    def get_owner_name(self, obj):
        return obj.owner.first_name or obj.owner.email.split('@')[0]
    
    def get_images(self, obj):
        """Return images with proper absolute URLs."""
        request = self.context.get('request')
        images = []
        for img in obj.images.all():
            image_data = {
                'id': img.id,
                'is_primary': img.is_primary,
                'order': img.order,
            }
            if img.image:
                if request:
                    image_data['url'] = request.build_absolute_uri(img.image.url)
                else:
                    image_data['url'] = img.image.url
            elif img.image_path:
                image_data['url'] = img.image_path
            else:
                image_data['url'] = None
            images.append(image_data)
        return images
    
    def get_thumbnail_url(self, obj):
        if obj.thumbnail:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.thumbnail.url)
            return obj.thumbnail.url
        # Fall back to first image
        first_image = obj.images.first()
        if first_image and first_image.image:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(first_image.image.url)
            return first_image.image.url
        return None


class ModelCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating a new 3D Model."""
    images = serializers.ListField(
        child=serializers.ImageField(),
        write_only=True,
        required=False
    )
    
    class Meta:
        model = Model
        fields = ['model_name', 'description', 'category', 'tags', 
                  'stl_file_path', 'stl_file', 'thumbnail', 'price', 'images']
    
    def create(self, validated_data):
        images_data = validated_data.pop('images', [])
        validated_data['owner'] = self.context['request'].user
        validated_data['visibility_status'] = VisibilityStatus.PRIVATE
        
        model = super().create(validated_data)
        
        # Create associated images
        for idx, image in enumerate(images_data):
            ModelImage.objects.create(
                model=model,
                image=image,
                is_primary=(idx == 0),
                order=idx
            )
        
        return model


class ModelUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating a 3D Model."""
    
    class Meta:
        model = Model
        fields = ['model_name', 'description', 'category', 'tags', 'thumbnail', 'price']


class ModelListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for model listings."""
    owner_email = serializers.EmailField(source='owner.email', read_only=True)
    owner_name = serializers.SerializerMethodField()
    thumbnail_url = serializers.SerializerMethodField()
    category_display = serializers.CharField(source='get_category_display', read_only=True)
    visibility = serializers.CharField(source='visibility_status', read_only=True)
    images = serializers.SerializerMethodField()
    
    class Meta:
        model = Model
        fields = [
            'id', 'model_name', 'description', 'owner_email', 'owner_name',
            'category', 'category_display', 'visibility_status', 'visibility', 'is_featured',
            'slicing_info', 'thumbnail_url', 'download_count', 'view_count', 
            'price', 'images', 'created_at'
        ]
    
    def get_owner_name(self, obj):
        return obj.owner.first_name or obj.owner.email.split('@')[0]
    
    def get_images(self, obj):
        """Return images with proper absolute URLs."""
        request = self.context.get('request')
        images = []
        for img in obj.images.all():
            image_data = {
                'id': img.id,
                'is_primary': img.is_primary,
                'order': img.order,
            }
            if img.image:
                if request:
                    image_data['url'] = request.build_absolute_uri(img.image.url)
                else:
                    image_data['url'] = img.image.url
            elif img.image_path:
                image_data['url'] = img.image_path
            else:
                image_data['url'] = None
            images.append(image_data)
        return images
    
    def get_thumbnail_url(self, obj):
        """Return the thumbnail or first image URL."""
        if obj.thumbnail:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.thumbnail.url)
            return obj.thumbnail.url
        first_image = obj.images.first()
        if first_image:
            if first_image.image:
                request = self.context.get('request')
                if request:
                    return request.build_absolute_uri(first_image.image.url)
                return first_image.image.url
            return first_image.image_path
        return None


class ModelReviewLogSerializer(serializers.ModelSerializer):
    """Serializer for model review logs."""
    reviewer_name = serializers.CharField(source='reviewer.employee_name', read_only=True)
    
    class Meta:
        model = ModelReviewLog
        fields = [
            'id', 'model', 'reviewer', 'reviewer_name',
            'previous_status', 'new_status', 'reason', 'timestamp'
        ]
        read_only_fields = ['id', 'timestamp']
