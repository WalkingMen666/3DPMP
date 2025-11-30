from django.contrib import admin
from .models import Model, ModelImage, ModelReviewLog


class ModelImageInline(admin.TabularInline):
    model = ModelImage
    extra = 0
    readonly_fields = ('id', 'created_at')


class ModelReviewLogInline(admin.TabularInline):
    model = ModelReviewLog
    extra = 0
    readonly_fields = ('id', 'reviewer', 'previous_status', 'new_status', 'reason', 'timestamp')
    can_delete = False


@admin.register(Model)
class ModelAdmin(admin.ModelAdmin):
    list_display = ('model_name', 'owner', 'visibility_status', 'created_at')
    list_filter = ('visibility_status', 'created_at')
    search_fields = ('model_name', 'owner__email')
    readonly_fields = ('id', 'created_at', 'updated_at', 'slicing_info')
    inlines = [ModelImageInline, ModelReviewLogInline]


@admin.register(ModelImage)
class ModelImageAdmin(admin.ModelAdmin):
    list_display = ('id', 'model', 'image_path', 'created_at')
    search_fields = ('model__model_name',)
    readonly_fields = ('id', 'created_at')


@admin.register(ModelReviewLog)
class ModelReviewLogAdmin(admin.ModelAdmin):
    list_display = ('model', 'reviewer', 'previous_status', 'new_status', 'timestamp')
    list_filter = ('new_status', 'timestamp')
    search_fields = ('model__model_name', 'reviewer__employee_name')
    readonly_fields = ('id', 'model', 'reviewer', 'previous_status', 'new_status', 'reason', 'timestamp')
