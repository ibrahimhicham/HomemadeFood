from django.db import models
from decimal import Decimal


class OrderStatus(models.TextChoices):
    """Order status choices with defined lifecycle."""
    PENDING = 'pending', 'Pending'
    ACCEPTED = 'accepted', 'Accepted'
    OUT_FOR_DELIVERY = 'out_for_delivery', 'Out for Delivery'
    DELIVERED = 'delivered', 'Delivered'
    CANCELLED = 'cancelled', 'Cancelled'
    REJECTED = 'rejected', 'Rejected'


# Valid status transitions
# Chef: pending -> accepted/rejected, accepted -> out_for_delivery, out_for_delivery -> delivered
# Consumer: pending -> cancelled
# Chef can also cancel pending orders
VALID_STATUS_TRANSITIONS = {
    OrderStatus.PENDING: [
        OrderStatus.ACCEPTED,
        OrderStatus.CANCELLED,
        OrderStatus.REJECTED,
    ],
    OrderStatus.ACCEPTED: [
        OrderStatus.OUT_FOR_DELIVERY,
        OrderStatus.CANCELLED,
    ],
    OrderStatus.OUT_FOR_DELIVERY: [
        OrderStatus.DELIVERED,
    ],
    OrderStatus.DELIVERED: [],  # Terminal state
    OrderStatus.CANCELLED: [],  # Terminal state
    OrderStatus.REJECTED: [],   # Terminal state
}


# Who can transition to which status
STATUS_ACTION_PERMISSIONS = {
    OrderStatus.ACCEPTED: 'chef',
    OrderStatus.OUT_FOR_DELIVERY: 'chef',
    OrderStatus.DELIVERED: 'chef',
    OrderStatus.REJECTED: 'chef',
    OrderStatus.CANCELLED: 'both',  # Both chef and consumer can cancel pending orders
}


# Auto-cancel timeout for pending orders (in minutes)
ORDER_PENDING_TIMEOUT_MINUTES = 5


# Fixed delivery fee
DELIVERY_FEE = Decimal('10.00')


# Preparation reminder buffer (minutes before estimated ready time)
PREPARATION_REMINDER_MINUTES = 5


# Notification types
class NotificationType(models.TextChoices):
    ORDER_PLACED = 'order_placed', 'Order Placed'
    ORDER_ACCEPTED = 'order_accepted', 'Order Accepted'
    ORDER_REJECTED = 'order_rejected', 'Order Rejected'
    ORDER_CANCELLED = 'order_cancelled', 'Order Cancelled'
    PREPARATION_REMINDER = 'preparation_reminder', 'Preparation Reminder'
    OUT_FOR_DELIVERY = 'out_for_delivery', 'Out for Delivery'
    DELIVERED = 'delivered', 'Delivered'
