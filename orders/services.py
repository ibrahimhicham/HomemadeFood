from decimal import Decimal
from datetime import timedelta

from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone
from django.contrib.auth import get_user_model

from rest_framework.exceptions import PermissionDenied

from .models import Order, OrderItem, OrderItemVarietySelection, OrderNotification
from .constants import (
    OrderStatus,
    NotificationType,
    VALID_STATUS_TRANSITIONS,
    STATUS_ACTION_PERMISSIONS,
    ORDER_PENDING_TIMEOUT_MINUTES,
    DELIVERY_FEE,
)
from .utils import (
    broadcast_notification,
    broadcast_order_status_update,
    broadcast_new_order_to_chef,
)
from dishes.models import Dish, DishVarietyOption

User = get_user_model()


class OrderCreateService:
    """Handles order creation with full validation and atomic persistence."""

    def __init__(
        self,
        customer: User,
        chef_id: int,
        items: list[dict],
        delivery_address: str,
        delivery_longitude: Decimal,
        delivery_latitude: Decimal,
        special_instructions: str = None,
    ):
        self.customer = customer
        self.chef_id = chef_id
        self.items = items
        self.delivery_address = delivery_address
        self.delivery_longitude = delivery_longitude
        self.delivery_latitude = delivery_latitude
        self.special_instructions = special_instructions

    def validate(self):
        """Run all pre-creation checks. Raises ValidationError on failure."""
        if not self.items:
            raise ValidationError("At least one item is required.")

        dish_ids = [item['dish_id'] for item in self.items]
        dishes = Dish.objects.filter(id__in=dish_ids).select_related('chef')

        # Check all dishes exist
        found_ids = {d.id for d in dishes}
        missing = set(dish_ids) - found_ids
        if missing:
            raise ValidationError(f"Dishes not found: {missing}")

        # Check all dishes are available
        unavailable = [d.id for d in dishes if not d.is_available]
        if unavailable:
            raise ValidationError(f"The following dishes are unavailable: {unavailable}")

        # Check all dishes belong to the same chef
        chef_ids = {d.chef_id for d in dishes}
        if len(chef_ids) != 1:
            raise ValidationError("All dishes must belong to the same chef.")

        target_chef_id = chef_ids.pop()
        if target_chef_id != self.chef_id:
            raise ValidationError("Chef ID does not match the dishes' chef.")

        # Check chef is online
        chef = User.objects.get(id=self.chef_id)
        if not hasattr(chef, 'chef') or not chef.chef.is_online:
            raise ValidationError("Chef is not currently accepting orders.")

        # Validate variety selections
        for item in self.items:
            dish = next(d for d in dishes if d.id == item['dish_id'])
            for selection in item.get('variety_selections', []):
                section_id = selection.get('section_id')
                option_id = selection.get('option_id')
                if not dish.variety_sections.filter(id=section_id).exists():
                    raise ValidationError(
                        f"Section {section_id} not found for dish {dish.name}"
                    )
                opt = DishVarietyOption.objects.filter(
                    section_id=section_id, id=option_id
                ).first()
                if not opt:
                    raise ValidationError(
                        f"Option {option_id} not found in section {section_id}"
                    )
                if not opt.is_available:
                    raise ValidationError(f"Option {opt.name} is not available")

    @transaction.atomic
    def execute(self) -> Order:
        """Create the order and all related items atomically."""
        self.validate()

        dishes = Dish.objects.filter(
            id__in=[i['dish_id'] for i in self.items]
        ).select_related('chef')
        chef = dishes[0].chef
        chef_name = f"{chef.first_name} {chef.last_name}".strip() or chef.email

        prep_times = [d.preparation_time for d in dishes if d.preparation_time]
        estimated_prep_minutes = max(prep_times) if prep_times else 0

        order = Order.objects.create(
            customer=self.customer,
            chef_id=self.chef_id,
            status=OrderStatus.PENDING,
            delivery_fee=DELIVERY_FEE,
            subtotal=Decimal('0.00'),
            total_amount=DELIVERY_FEE,
            estimated_preparation_minutes=estimated_prep_minutes,
            delivery_address=self.delivery_address,
            delivery_longitude=self.delivery_longitude,
            delivery_latitude=self.delivery_latitude,
            special_instructions=self.special_instructions,
            chef_name_snapshot=chef_name,
        )

        subtotal = Decimal('0.00')
        for item_data in self.items:
            dish = next(d for d in dishes if d.id == item_data['dish_id'])
            unit_price = dish.price
            quantity = item_data['quantity']

            order_item = OrderItem.objects.create(
                order=order,
                dish=dish,
                dish_name_snapshot=dish.name,
                dish_base_price_snapshot=dish.price,
                chef_name_snapshot=chef_name,
                quantity=quantity,
                unit_price=unit_price,
                special_requests=item_data.get('special_requests'),
            )

            item_subtotal = unit_price * quantity
            for sel in item_data.get('variety_selections', []):
                opt = DishVarietyOption.objects.get(id=sel['option_id'])
                OrderItemVarietySelection.objects.create(
                    order_item=order_item,
                    section_name=opt.section.name,
                    option_name=opt.name,
                    option_price_adjustment=opt.price_adjustment,
                )
                item_subtotal += opt.price_adjustment * quantity

            order_item.item_total = item_subtotal
            order_item.save(update_fields=['item_total'])
            subtotal += item_subtotal

        order.subtotal = subtotal
        order.total_amount = subtotal + DELIVERY_FEE
        order.save(update_fields=['subtotal', 'total_amount'])

        # Create DB notification for chef
        OrderNotification.objects.create(
            order=order,
            recipient=order.chef,
            notification_type=NotificationType.ORDER_PLACED,
            message=f"New order #{order.order_id} from {self.customer.first_name} {self.customer.last_name}.",
        )

        # Broadcast WebSocket event to chef
        broadcast_new_order_to_chef(
            chef_id=self.chef_id,
            order_data={
                'order_id': str(order.order_id),
                'customer_name': f'{self.customer.first_name} {self.customer.last_name}',
                'total_amount': str(order.total_amount),
                'items_count': len(self.items),
                'message': f'New order from {self.customer.first_name} {self.customer.last_name}',
                'created_at': timezone.now().isoformat(),
            },
        )

        return order


class OrderStatusService:
    """Handles order status transitions with validation and notifications."""

    def __init__(
        self,
        order: Order,
        new_status: str,
        user: User,
        cancellation_reason: str = None,
    ):
        self.order = order
        self.new_status = new_status
        self.user = user
        self.cancellation_reason = cancellation_reason

    def validate(self):
        current = self.order.status
        allowed = VALID_STATUS_TRANSITIONS.get(current, [])
        if self.new_status not in allowed:
            raise ValidationError(
                f"Cannot transition from '{current}' to '{self.new_status}'."
            )

        actor = STATUS_ACTION_PERMISSIONS.get(self.new_status)
        if actor == 'chef' and self.order.chef != self.user:
            raise PermissionDenied("Only the assigned chef can perform this action.")
        if actor == 'both' and self.user not in (self.order.chef, self.order.customer):
            raise PermissionDenied(
                "Only the chef or customer can perform this action."
            )

    @transaction.atomic
    def execute(self) -> Order:
        self.validate()

        now = timezone.now()
        status_timestamps = {
            OrderStatus.ACCEPTED: 'accepted_at',
            OrderStatus.OUT_FOR_DELIVERY: 'out_for_delivery_at',
            OrderStatus.DELIVERED: 'delivered_at',
            OrderStatus.CANCELLED: 'cancelled_at',
            OrderStatus.REJECTED: 'cancelled_at',
        }

        ts_field = status_timestamps.get(self.new_status)
        if ts_field:
            setattr(self.order, ts_field, now)

        if self.new_status in (OrderStatus.CANCELLED, OrderStatus.REJECTED):
            self.order.cancelled_by = self.user
            self.order.cancellation_reason = self.cancellation_reason or ''

        self.order.status = self.new_status
        self.order.save()

        if self.new_status == OrderStatus.ACCEPTED:
            self.order.estimated_ready_time = now + timedelta(
                minutes=self.order.estimated_preparation_minutes
            )
            self.order.save(update_fields=['estimated_ready_time'])

        self._create_notifications()
        return self.order

    def _create_notifications(self):
        mapping = {
            OrderStatus.ACCEPTED: (
                self.order.customer,
                NotificationType.ORDER_ACCEPTED,
                f"Your order #{self.order.order_id} has been accepted. "
                f"Estimated ready time: {self.order.estimated_ready_time}.",
            ),
            OrderStatus.REJECTED: (
                self.order.customer,
                NotificationType.ORDER_REJECTED,
                f"Your order #{self.order.order_id} has been rejected. "
                f"Reason: {self.order.cancellation_reason or 'Not specified.'}",
            ),
            OrderStatus.CANCELLED: (
                self.order.chef,
                NotificationType.ORDER_CANCELLED,
                f"Order #{self.order.order_id} was cancelled. "
                f"Reason: {self.order.cancellation_reason or 'Not specified.'}",
            ),
            OrderStatus.OUT_FOR_DELIVERY: (
                self.order.customer,
                NotificationType.OUT_FOR_DELIVERY,
                f"Your order #{self.order.order_id} is out for delivery!",
            ),
            OrderStatus.DELIVERED: (
                self.order.customer,
                NotificationType.DELIVERED,
                f"Your order #{self.order.order_id} has been delivered. Enjoy!",
            ),
        }
        if self.new_status in mapping:
            recipient, n_type, message = mapping[self.new_status]
            OrderNotification.objects.create(
                order=self.order,
                recipient=recipient,
                notification_type=n_type,
                message=message,
            )

            # Broadcast WebSocket notification to recipient
            broadcast_notification(
                user_id=recipient.id,
                notification_data={
                    'notification_type': n_type,
                    'order_id': str(self.order.order_id),
                    'message': message,
                    'created_at': timezone.now().isoformat(),
                },
            )

            # Broadcast status update to order-specific group
            broadcast_order_status_update(
                order_id=str(self.order.order_id),
                status_data={
                    'order_id': str(self.order.order_id),
                    'status': self.new_status,
                    'updated_at': timezone.now().isoformat(),
                    'estimated_ready_time': (
                        self.order.estimated_ready_time.isoformat()
                        if self.order.estimated_ready_time
                        else None
                    ),
                },
            )


class CancelExpiredOrdersService:
    """Auto-cancels pending orders older than ORDER_PENDING_TIMEOUT_MINUTES."""

    @staticmethod
    @transaction.atomic
    def execute():
        cutoff = timezone.now() - timedelta(minutes=ORDER_PENDING_TIMEOUT_MINUTES)
        expired_orders = Order.objects.filter(
            status=OrderStatus.PENDING,
            created_at__lte=cutoff,
        )

        count = 0
        for order in expired_orders:
            order.status = OrderStatus.CANCELLED
            order.cancelled_at = timezone.now()
            order.cancellation_reason = (
                'Auto-cancelled: chef did not respond within 5 minutes.'
            )
            order.save(
                update_fields=['status', 'cancelled_at', 'cancellation_reason']
            )

            OrderNotification.objects.create(
                order=order,
                recipient=order.customer,
                notification_type=NotificationType.ORDER_CANCELLED,
                message=(
                    f"Order #{order.order_id} was auto-cancelled because "
                    f"the chef did not respond within 5 minutes."
                ),
            )

            # Broadcast WebSocket notification
            broadcast_notification(
                user_id=order.customer.id,
                notification_data={
                    'notification_type': NotificationType.ORDER_CANCELLED,
                    'order_id': str(order.order_id),
                    'message': (
                        f"Order #{order.order_id} was auto-cancelled because "
                        f"the chef did not respond within 5 minutes."
                    ),
                    'created_at': timezone.now().isoformat(),
                },
            )

            count += 1

        return count
