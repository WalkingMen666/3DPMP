from django.apps import AppConfig


class ModelsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.models'
    label = 'printing_models'  # Avoid conflict with Django's models module
    verbose_name = '3D Models'
