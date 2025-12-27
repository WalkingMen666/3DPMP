import uuid
from django.db import models
from django.core.validators import MinValueValidator


class Material(models.Model):
    """
    3D printing material definition.
    
    Stores material properties used for cost calculation after slicing.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100, unique=True)
    # Note: DBML says density_g_cm2 but it should be density_g_cm3 (volume).
    # Using g/cm³ which is standard for filament density.
    density_g_cm3 = models.DecimalField(
        max_digits=10,
        decimal_places=5,
        validators=[MinValueValidator(0)],
        help_text="Density in grams per cubic centimeter"
    )
    price_twd_g = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        help_text="Price in TWD per gram"
    )
    is_active = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'material'
        ordering = ['name']
        verbose_name = 'Material'
        verbose_name_plural = 'Materials'

    def __str__(self):
        return self.name


class CartItem(models.Model):
    """
    Shopping cart item - temporary holding area before order creation.
    
    Prices here are "estimates" based on current material prices.
    Cart items are deleted when converted to order items.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    customer = models.ForeignKey(
        'users.Customer',
        on_delete=models.CASCADE,
        related_name='cart_items'
    )
    model = models.ForeignKey(
        'printing_models.Model',
        on_delete=models.CASCADE,
        related_name='cart_items'
    )
    material = models.ForeignKey(
        Material,
        on_delete=models.PROTECT,  # Don't allow deleting material that's in carts
        related_name='cart_items'
    )
    quantity = models.PositiveIntegerField(default=1, validators=[MinValueValidator(1)])
    notes = models.TextField(blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'cart_item'
        verbose_name = 'Cart Item'
        verbose_name_plural = 'Cart Items'
        # Prevent duplicate model+material combinations for same customer
        constraints = [
            models.UniqueConstraint(
                fields=['customer', 'model', 'material'],
                name='unique_cart_item_per_customer'
            )
        ]

    def __str__(self):
        return f"{self.customer.user.email} - {self.model.model_name} x{self.quantity}"
