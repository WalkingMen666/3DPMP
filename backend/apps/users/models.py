import uuid
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils.translation import gettext_lazy as _

class User(AbstractUser):
    """
    Custom User model where email is the unique identifier.
    """
    username = None  # Remove username field
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(_('email address'), unique=True)
    
    AUTH_PROVIDERS = (
        ('local', 'Local'),
        ('google', 'Google'),
    )
    auth_provider = models.CharField(max_length=20, choices=AUTH_PROVIDERS, default='local')
    
    # creation_date is handled by date_joined in AbstractUser
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    def __str__(self):
        return self.email

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
