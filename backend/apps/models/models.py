import uuid
from django.db import models
from django.conf import settings


class VisibilityStatus(models.TextChoices):
    """Visibility status choices for 3D models."""
    PRIVATE = 'PRIVATE', 'Private'
    PENDING = 'PENDING', 'Pending Review'
    PUBLIC = 'PUBLIC', 'Public'
    REJECTED = 'REJECTED', 'Rejected'


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
    visibility_status = models.CharField(
        max_length=20,
        choices=VisibilityStatus.choices,
        default=VisibilityStatus.PRIVATE
    )
    stl_file_path = models.CharField(max_length=500)  # Relative path in Alist
    gcode_file_path = models.CharField(max_length=500, blank=True, null=True)
    slicing_info = models.JSONField(blank=True, null=True)  # Stores material usage, print time
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'model'
        ordering = ['-created_at']
        verbose_name = '3D Model'
        verbose_name_plural = '3D Models'

    def __str__(self):
        return f"{self.model_name} ({self.owner.email})"


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
    image_path = models.CharField(max_length=500)
    
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'model_image'
        verbose_name = 'Model Image'
        verbose_name_plural = 'Model Images'

    def __str__(self):
        return f"Image for {self.model.model_name}"


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
