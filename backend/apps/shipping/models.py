import uuid
from django.db import models
from django.core.validators import MinValueValidator


class ShippingType(models.TextChoices):
    """Shipping method types."""
    HOME_DELIVERY = 'HOME_DELIVERY', 'Home Delivery'
    CONVENIENCE_STORE = 'CONVENIENCE_STORE', 'Convenience Store'
    SELF_PICKUP = 'SELF_PICKUP', 'Self Pickup'


class ShippingOption(models.Model):
    """
    Global shipping options defined by Admin.
    
    These are the available shipping methods customers can choose from.
    When an order is placed, the selected option details are snapshot
    into ORDER.ship_snapshot (not referenced by FK).
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)  # e.g., 'Black Cat Delivery'
    type = models.CharField(
        max_length=30,
        choices=ShippingType.choices,
        default=ShippingType.HOME_DELIVERY
    )
    base_fee = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )
    is_active = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'shipping_option'
        ordering = ['name']
        verbose_name = 'Shipping Option'
        verbose_name_plural = 'Shipping Options'

    def __str__(self):
        return f"{self.name} ({self.get_type_display()}) - ${self.base_fee}"


class SavedAddress(models.Model):
    """
    Personal address book for Customers.
    
    Customers can save multiple addresses with different types
    (home, convenience store, etc.) for easy reuse.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    customer = models.ForeignKey(
        'users.Customer',
        on_delete=models.CASCADE,
        related_name='saved_addresses'
    )
    name = models.CharField(max_length=100)  # e.g., 'My Home', 'Office'
    address_type = models.CharField(
        max_length=30,
        choices=ShippingType.choices,
        help_text="Must match a SHIPPING_OPTION.type for compatibility"
    )
    address_details = models.TextField(
        help_text="Full address details, recipient name, phone number, etc."
    )
    is_default = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'saved_address'
        ordering = ['-is_default', 'name']
        verbose_name = 'Saved Address'
        verbose_name_plural = 'Saved Addresses'

    def __str__(self):
        return f"{self.name} - {self.customer.user.email}"

    def save(self, *args, **kwargs):
        # Ensure only one default address per customer
        if self.is_default:
            SavedAddress.objects.filter(
                customer=self.customer,
                is_default=True
            ).exclude(pk=self.pk).update(is_default=False)
        super().save(*args, **kwargs)
