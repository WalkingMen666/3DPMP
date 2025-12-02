import uuid
from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.utils.translation import gettext_lazy as _


class UserManager(BaseUserManager):
    """Custom user manager for email-based authentication."""
    
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('The Email field must be set')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self.create_user(email, password, **extra_fields)


class User(AbstractUser):
    """
    Custom User model where email is the unique identifier.
    """
    username = None  # Remove username field
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(_('email address'), unique=True)
    display_name = models.CharField(max_length=100, blank=True, default='')
    
    AUTH_PROVIDERS = (
        ('local', 'Local'),
        ('google', 'Google'),
    )
    auth_provider = models.CharField(max_length=20, choices=AUTH_PROVIDERS, default='local')
    
    # Avatar settings
    AVATAR_CHOICES = (
        ('default', 'Default'),
        ('custom', 'Custom Upload'),
    )
    avatar_type = models.CharField(max_length=20, choices=AVATAR_CHOICES, default='default')
    avatar_image = models.ImageField(upload_to='avatars/', null=True, blank=True)
    
    # creation_date is handled by date_joined in AbstractUser
    
    objects = UserManager()
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    def __str__(self):
        return self.email
    
    @property
    def avatar_url(self):
        """Return the URL for the user's avatar"""
        if self.avatar_type == 'custom' and self.avatar_image:
            return self.avatar_image.url
        elif self.avatar_type != 'default' and self.avatar_type != 'custom':
            # Return preset avatar path
            return f'/static/avatars/{self.avatar_type}.png'
        return None

class Customer(models.Model):
    """
    Customer profile (IS-A User via EER Specialization).
    Uses user_id as both PK and FK for proper inheritance semantics.
    """
    user = models.OneToOneField(
        User, 
        on_delete=models.CASCADE, 
        primary_key=True,  # user_id is both PK and FK
        related_name='customer_profile'
    )
    
    class Meta:
        db_table = 'users_customer'
    
    def __str__(self):
        return f"Customer: {self.user.email}"


class Employee(models.Model):
    """
    Employee profile (IS-A User via EER Specialization).
    Uses user_id as both PK and FK for proper inheritance semantics.
    """
    user = models.OneToOneField(
        User, 
        on_delete=models.CASCADE, 
        primary_key=True,  # user_id is both PK and FK
        related_name='employee_profile'
    )
    employee_name = models.CharField(max_length=255)
    is_admin = models.BooleanField(default=False)

    class Meta:
        db_table = 'users_employee'

    def __str__(self):
        return f"Employee: {self.employee_name}"
