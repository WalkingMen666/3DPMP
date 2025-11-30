import uuid
from django.db import models
from django.core.validators import MinValueValidator
from django.core.exceptions import ValidationError


class DiscountWorksOn(models.TextChoices):
    """What the discount applies to."""
    ORDER_SUBTOTAL = 'ORDER_SUBTOTAL', 'Order Subtotal'
    SHIPPING = 'SHIPPING', 'Shipping Fee'
    TOTAL = 'TOTAL', 'Order Total'


class Discount(models.Model):
    """
    Base discount entity (Superclass for GlobalDiscount and Coupon).
    
    This implements EER Specialization pattern where GlobalDiscount
    and Coupon are subclasses with additional attributes.
    
    Discount can be:
    - Fixed amount (is_fixed=True): subtracts dis_value from target
    - Percentage (is_fixed=False): multiplies target by (1 - dis_value/100)
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    
    start_date = models.DateTimeField()
    due_date = models.DateTimeField(blank=True, null=True)
    
    # Minimum order price to qualify for this discount
    min_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(0)]
    )
    
    # Maximum discount amount (for percentage discounts)
    max_discount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        blank=True,
        null=True,
        validators=[MinValueValidator(0)]
    )
    
    # What this discount applies to
    works_on = models.CharField(
        max_length=20,
        choices=DiscountWorksOn.choices,
        default=DiscountWorksOn.ORDER_SUBTOTAL
    )
    
    # True = fixed amount, False = percentage
    is_fixed = models.BooleanField(default=False)
    
    # The discount value (amount in TWD if fixed, percentage if not)
    dis_value = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        help_text="Amount in TWD (if fixed) or percentage (if not fixed)"
    )
    
    is_active = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'discount'
        ordering = ['-created_at']
        verbose_name = 'Discount'
        verbose_name_plural = 'Discounts'

    def __str__(self):
        if self.is_fixed:
            return f"{self.name} (-${self.dis_value})"
        return f"{self.name} (-{self.dis_value}%)"

    def clean(self):
        if not self.is_fixed and self.dis_value > 100:
            raise ValidationError("Percentage discount cannot exceed 100%")

    @property
    def discount_type(self):
        """Return the subclass type (global_discount or coupon)."""
        if hasattr(self, 'global_discount'):
            return 'global_discount'
        elif hasattr(self, 'coupon'):
            return 'coupon'
        return None


class GlobalDiscount(models.Model):
    """
    Auto-applied discount (IS-A Discount).
    
    Global discounts are automatically applied to qualifying orders.
    Multiple global discounts can apply to a single order (M:N relationship).
    """
    discount = models.OneToOneField(
        Discount,
        on_delete=models.CASCADE,
        primary_key=True,
        related_name='global_discount'
    )
    
    # Additional fields specific to global discounts can go here
    # e.g., priority for applying multiple discounts
    priority = models.PositiveIntegerField(
        default=0,
        help_text="Higher priority discounts are applied first"
    )

    class Meta:
        db_table = 'global_discount'
        ordering = ['-priority']
        verbose_name = 'Global Discount'
        verbose_name_plural = 'Global Discounts'

    def __str__(self):
        return f"[Global] {self.discount.name}"


class Coupon(models.Model):
    """
    User-entered coupon code (IS-A Discount).
    
    Coupons require a code and have usage limits.
    Max 1 coupon per order (enforced by CouponRedemption.order unique constraint).
    """
    discount = models.OneToOneField(
        Discount,
        on_delete=models.CASCADE,
        primary_key=True,
        related_name='coupon'
    )
    
    coupon_code = models.CharField(max_length=50, unique=True)
    
    # Total usage limit across all customers
    max_uses_total = models.PositiveIntegerField(
        blank=True,
        null=True,
        help_text="Leave empty for unlimited uses"
    )
    
    # Per-customer usage limit
    max_uses_per_customer = models.PositiveIntegerField(
        default=1,
        validators=[MinValueValidator(1)]
    )

    class Meta:
        db_table = 'coupon'
        verbose_name = 'Coupon'
        verbose_name_plural = 'Coupons'

    def __str__(self):
        return f"[Coupon: {self.coupon_code}] {self.discount.name}"

    @property
    def total_redemptions(self):
        """Get total number of times this coupon has been used."""
        return self.redemptions.count()

    def is_valid_for_customer(self, customer):
        """Check if this coupon can be used by a specific customer."""
        # Check total usage limit
        if self.max_uses_total and self.total_redemptions >= self.max_uses_total:
            return False
        
        # Check per-customer limit
        customer_uses = self.redemptions.filter(customer=customer).count()
        if customer_uses >= self.max_uses_per_customer:
            return False
        
        return True


class IsAffected(models.Model):
    """
    M:N link between Order and GlobalDiscount.
    
    Records which global discounts were applied to an order,
    storing a snapshot of the discount rules at order time.
    Multiple global discounts can affect a single order.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    order = models.ForeignKey(
        'orders.Order',
        on_delete=models.CASCADE,
        related_name='applied_global_discounts'
    )
    global_discount = models.ForeignKey(
        GlobalDiscount,
        on_delete=models.PROTECT,  # Don't allow deleting discount with history
        related_name='affected_orders'
    )
    
    # Snapshot of discount rules at order time
    discount_snapshot_info = models.JSONField(
        help_text="Snapshot of discount rules at order time"
    )
    
    # Calculated discount amount
    discount_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )
    
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'is_affected'
        verbose_name = 'Applied Global Discount'
        verbose_name_plural = 'Applied Global Discounts'
        constraints = [
            models.UniqueConstraint(
                fields=['order', 'global_discount'],
                name='unique_global_discount_per_order'
            )
        ]

    def __str__(self):
        return f"Order {str(self.order.id)[:8]} - {self.global_discount}"


class CouponRedemption(models.Model):
    """
    1:1 link between Order and Coupon.
    
    Tracks coupon usage with unique constraint on order_id
    to enforce max 1 coupon per order at the database level.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    customer = models.ForeignKey(
        'users.Customer',
        on_delete=models.PROTECT,
        related_name='coupon_redemptions'
    )
    coupon = models.ForeignKey(
        Coupon,
        on_delete=models.PROTECT,
        related_name='redemptions'
    )
    # Unique constraint ensures max 1 coupon per order
    order = models.OneToOneField(
        'orders.Order',
        on_delete=models.CASCADE,
        related_name='coupon_redemption'
    )
    
    # Snapshot of discount info at redemption time
    discount_snapshot_info = models.JSONField(
        blank=True,
        null=True,
        help_text="Snapshot of coupon rules at redemption time"
    )
    
    # Calculated discount amount
    discount_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )
    
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'coupon_redemption'
        ordering = ['-timestamp']
        verbose_name = 'Coupon Redemption'
        verbose_name_plural = 'Coupon Redemptions'

    def __str__(self):
        return f"{self.customer.user.email} used {self.coupon.coupon_code}"
