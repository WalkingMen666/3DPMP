import uuid
from django.db import models
from django.core.validators import MinValueValidator


class OrderStatus(models.TextChoices):
    """Order status workflow states."""
    PENDING = 'PENDING', 'Pending'
    CONFIRMED = 'CONFIRMED', 'Confirmed'
    PROCESSING = 'PROCESSING', 'Processing'
    PRINTING = 'PRINTING', 'Printing'
    QUALITY_CHECK = 'QUALITY_CHECK', 'Quality Check'
    READY_TO_SHIP = 'READY_TO_SHIP', 'Ready to Ship'
    SHIPPED = 'SHIPPED', 'Shipped'
    DELIVERED = 'DELIVERED', 'Delivered'
    COMPLETED = 'COMPLETED', 'Completed'
    CANCELLED = 'CANCELLED', 'Cancelled'
    REFUNDED = 'REFUNDED', 'Refunded'


class Order(models.Model):
    """
    Order with immutable snapshots.
    
    CRITICAL: This table MUST NOT have foreign keys to mutable shipping/address tables.
    All shipping and discount information is stored as JSON snapshots at order creation time.
    
    The ship_snapshot stores: {service_name, fee, address_details}
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    customer = models.ForeignKey(
        'users.Customer',
        on_delete=models.PROTECT,
        related_name='orders'
    )
    assignee = models.ForeignKey(
        'users.Employee',
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='assigned_orders'
    )
    status = models.CharField(
        max_length=20,
        choices=OrderStatus.choices,
        default=OrderStatus.PENDING
    )
    
    # Shipping Snapshot: Stores JSON {service_name, fee, address_details}
    # NO Foreign Keys to SHIPPING_OPTION or SAVED_ADDRESS here!
    ship_snapshot = models.JSONField(
        help_text="Immutable snapshot of shipping info at order time"
    )
    
    total_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )
    
    # Additional fields for order tracking
    notes = models.TextField(blank=True, null=True)
    tracking_number = models.CharField(max_length=100, blank=True, null=True)
    
    creation_date = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'order'
        ordering = ['-creation_date']
        verbose_name = 'Order'
        verbose_name_plural = 'Orders'

    def __str__(self):
        return f"Order {str(self.id)[:8]} - {self.customer.user.email}"


class OrderItem(models.Model):
    """
    Individual item in an order with price snapshot.
    
    The price_snapshot is calculated and saved permanently at order creation
    (current MATERIAL.price * slicing_info.weight).
    This ensures price integrity even if material prices change later.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name='items'
    )
    # Keep FKs for reference but price is snapshotted
    model = models.ForeignKey(
        'printing_models.Model',
        on_delete=models.PROTECT,  # Don't allow deleting models that are in orders
        related_name='order_items'
    )
    material = models.ForeignKey(
        'materials.Material',
        on_delete=models.PROTECT,
        related_name='order_items'
    )
    
    item_number = models.PositiveIntegerField(
        help_text="Sequential item number within the order"
    )
    quantity = models.PositiveIntegerField(default=1, validators=[MinValueValidator(1)])
    
    # Price Snapshot: Price at time of purchase (immutable)
    price_snapshot = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        help_text="Price per unit at order time"
    )
    
    # Slicing info at order time (material usage, print time)
    slicing_info_snapshot = models.JSONField(
        blank=True,
        null=True,
        help_text="Slicing information at order time"
    )
    
    # Additional fields for item tracking
    notes = models.TextField(blank=True, null=True)

    class Meta:
        db_table = 'order_item'
        ordering = ['order', 'item_number']
        verbose_name = 'Order Item'
        verbose_name_plural = 'Order Items'
        constraints = [
            models.UniqueConstraint(
                fields=['order', 'item_number'],
                name='unique_item_number_per_order'
            )
        ]

    def __str__(self):
        return f"Order {str(self.order.id)[:8]} - Item #{self.item_number}"

    @property
    def subtotal(self):
        """Calculate subtotal for this item."""
        return self.price_snapshot * self.quantity


class OrderLog(models.Model):
    """
    Audit log for order status changes by employees.
    
    Every status change must be logged with the employee who made the change.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name='logs'
    )
    updated_by = models.ForeignKey(
        'users.Employee',
        on_delete=models.PROTECT,
        related_name='order_updates'
    )
    previous_status = models.CharField(
        max_length=20,
        choices=OrderStatus.choices,
        blank=True,
        null=True
    )
    new_status = models.CharField(
        max_length=20,
        choices=OrderStatus.choices
    )
    notes = models.TextField(blank=True, null=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'order_log'
        ordering = ['-timestamp']
        verbose_name = 'Order Log'
        verbose_name_plural = 'Order Logs'

    def __str__(self):
        return f"Order {str(self.order.id)[:8]}: {self.previous_status} -> {self.new_status}"
