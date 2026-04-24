from django.db import models
from django.utils import timezone
from django.contrib.auth import get_user_model
from authentication.models import User  # Using the existing User model
from dishes.models import Dish  # Using the existing Dish model
from decimal import Decimal
import uuid

from .constants import OrderStatus, NotificationType


class Order(models.Model):
    STATUS_CHOICES = OrderStatus.choices

    id = models.BigAutoField(primary_key=True)
    order_id = models.UUIDField(unique=True, default=uuid.uuid4, editable=False)
    customer = models.ForeignKey(User, on_delete=models.PROTECT, related_name='placed_orders',
                                limit_choices_to={'consumer__isnull': False})  # Only consumers can place orders
    chef = models.ForeignKey(User, on_delete=models.PROTECT, related_name='received_orders',
                            limit_choices_to={'chef__isnull': False})  # Only chefs can receive orders
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=OrderStatus.PENDING)

    # Pricing breakdown
    subtotal = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    delivery_fee = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('10.00'))
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    # Preparation time
    estimated_preparation_minutes = models.PositiveIntegerField(
        default=0,
        help_text="Calculated from ordered dishes' preparation times"
    )
    estimated_ready_time = models.DateTimeField(null=True, blank=True)

    # Status timestamps
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    accepted_at = models.DateTimeField(null=True, blank=True)
    out_for_delivery_at = models.DateTimeField(null=True, blank=True)
    delivered_at = models.DateTimeField(null=True, blank=True)
    cancelled_at = models.DateTimeField(null=True, blank=True)
    cancelled_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True,
                                     related_name='cancelled_orders')
    cancellation_reason = models.TextField(blank=True, null=True)

    # Delivery details
    delivery_address = models.TextField()
    delivery_longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    delivery_latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    estimated_delivery_time = models.DateTimeField(null=True, blank=True)

    # Metadata
    special_instructions = models.TextField(blank=True, null=True)
    chef_name_snapshot = models.CharField(max_length=300, default='', help_text="Chef name at order time")

    def __str__(self):
        return f"Order {self.order_id} - {self.customer.email} to {self.chef.email}"

    class Meta:
        ordering = ['-created_at']

    def save(self, *args, **kwargs):
        """Auto-calculate total_amount from subtotal and delivery_fee."""
        if self.subtotal is not None:
            self.total_amount = self.subtotal + self.delivery_fee
        super().save(*args, **kwargs)


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    dish = models.ForeignKey(Dish, on_delete=models.PROTECT)

    # Snapshots (preserve order history even if dish is modified/deleted)
    dish_name_snapshot = models.CharField(max_length=200, default='')
    dish_base_price_snapshot = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    chef_name_snapshot = models.CharField(max_length=300, default='')

    # Quantity & pricing
    quantity = models.PositiveIntegerField(default=1)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)  # Price at time of order
    item_total = models.DecimalField(max_digits=10, decimal_places=2, editable=False)

    # Special requests
    special_requests = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.quantity}x {self.dish_name_snapshot} in order {self.order.order_id}"

    def save(self, *args, **kwargs):
        """Auto-calculate item_total from quantity and unit_price."""
        self.item_total = self.quantity * self.unit_price
        super().save(*args, **kwargs)

    class Meta:
        unique_together = ('order', 'dish')  # Each dish can only appear once per order


class OrderItemVarietySelection(models.Model):
    """Stores variety option selections for an order item with snapshots."""
    order_item = models.ForeignKey(OrderItem, on_delete=models.CASCADE, related_name='variety_selections')
    section_name = models.CharField(max_length=100, help_text="Section name snapshot (e.g., 'Size Options')")
    option_name = models.CharField(max_length=100, help_text="Option name snapshot (e.g., 'Large')")
    option_price_adjustment = models.DecimalField(
        max_digits=6, decimal_places=2, default=0,
        help_text="Price adjustment at order time"
    )

    def __str__(self):
        return f"{self.section_name}: {self.option_name} for {self.order_item}"

    class Meta:
        ordering = ['section_name', 'option_name']


class OrderNotification(models.Model):
    """In-app notification for order-related events."""
    NOTIFICATION_TYPES = NotificationType.choices

    id = models.BigAutoField(primary_key=True)
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='notifications')
    recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='order_notifications')
    notification_type = models.CharField(max_length=30, choices=NOTIFICATION_TYPES)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"{self.get_notification_type_display()} for Order {self.order.order_id}"

    class Meta:
        ordering = ['-created_at']
