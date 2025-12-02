import uuid
from django.db import models
from django.conf import settings


class VisibilityStatus(models.TextChoices):
    """Visibility status choices for 3D models."""
    PRIVATE = 'PRIVATE', 'Private'
    PENDING = 'PENDING', 'Pending Review'
    PUBLIC = 'PUBLIC', 'Public'
    REJECTED = 'REJECTED', 'Rejected'


class ModelCategory(models.TextChoices):
    """Category choices for 3D models."""
    TOYS = 'Toys', 'Toys & Games'
    HOME = 'Home', 'Home & Garden'
    GADGETS = 'Gadgets', 'Gadgets & Tech'
    ART = 'Art', 'Art & Sculptures'
    FASHION = 'Fashion', 'Fashion & Accessories'
    TOOLS = 'Tools', 'Tools & Functional'
    EDUCATION = 'Education', 'Education & Learning'
    OTHER = 'Other', 'Other'


class Model(models.Model):
    """
    3D Model entity.
    
    Stores metadata about uploaded 3D models including STL file path,
    generated G-code path, and slicing information from PrusaSlicer.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='models'
    )
    model_name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True, help_text="Detailed description of the model")
    category = models.CharField(
        max_length=50,
        choices=ModelCategory.choices,
        default=ModelCategory.OTHER
    )
    tags = models.JSONField(blank=True, null=True, help_text="List of tags for searching")
    
    visibility_status = models.CharField(
        max_length=20,
        choices=VisibilityStatus.choices,
        default=VisibilityStatus.PRIVATE
    )
    is_featured = models.BooleanField(default=False, help_text="Featured on homepage")
    
    # File paths
    stl_file_path = models.CharField(max_length=500)  # Relative path in storage
    stl_file = models.FileField(upload_to='models/stl/', blank=True, null=True)
    gcode_file_path = models.CharField(max_length=500, blank=True, null=True)
    thumbnail = models.ImageField(upload_to='models/thumbnails/', blank=True, null=True)
    
    # Slicing info
    slicing_info = models.JSONField(blank=True, null=True)  # Stores material usage, print time
    
    # Statistics
    download_count = models.PositiveIntegerField(default=0)
    view_count = models.PositiveIntegerField(default=0)
    
    # Pricing (optional, for marketplace)
    price = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True, help_text="Price in TWD (null = free)")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'model'
        ordering = ['-created_at']
        verbose_name = '3D Model'
        verbose_name_plural = '3D Models'

    def __str__(self):
        return f"{self.model_name} ({self.owner.email})"
    
    @property
    def thumbnail_url(self):
        if self.thumbnail:
            return self.thumbnail.url
        return None
    
    @property
    def primary_image(self):
        """Get the first image as primary."""
        first_image = self.images.first()
        if first_image:
            return first_image.image.url if first_image.image else first_image.image_path
        return self.thumbnail_url


class ModelImage(models.Model):
    """
    Images associated with a 3D model.
    
    Supports multiple preview/render images per model.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    model = models.ForeignKey(
        Model,
        on_delete=models.CASCADE,
        related_name='images'
    )
    image = models.ImageField(upload_to='models/images/', blank=True, null=True)
    image_path = models.CharField(max_length=500, blank=True, null=True)
    is_primary = models.BooleanField(default=False)
    order = models.PositiveIntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'model_image'
        ordering = ['order', '-created_at']
        verbose_name = 'Model Image'
        verbose_name_plural = 'Model Images'

    def __str__(self):
        return f"Image for {self.model.model_name}"
    
    @property
    def url(self):
        if self.image:
            return self.image.url
        return self.image_path


class ModelReviewLog(models.Model):
    """
    Audit log for model visibility status changes by employees.
    
    Every status change by an employee must be logged with the reason.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    model = models.ForeignKey(
        Model,
        on_delete=models.CASCADE,
        related_name='review_logs'
    )
    reviewer = models.ForeignKey(
        'users.Employee',
        on_delete=models.PROTECT,  # Don't allow deleting employee with review history
        related_name='model_reviews'
    )
    previous_status = models.CharField(
        max_length=20,
        choices=VisibilityStatus.choices,
        blank=True,
        null=True
    )
    new_status = models.CharField(
        max_length=20,
        choices=VisibilityStatus.choices
    )
    reason = models.TextField(blank=True, null=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'model_review_log'
        ordering = ['-timestamp']
        verbose_name = 'Model Review Log'
        verbose_name_plural = 'Model Review Logs'

    def __str__(self):
        return f"Review: {self.model.model_name} -> {self.new_status}"
