# Orders Module — Detailed Implementation Plan

---

## 1. Database Models & Fields

### 1.1 Order Model

| Field | Type | Notes |
|---|---|---|
| `id` | `BigAutoField` (PK) | Internal primary key |
| `order_id` | `UUIDField` | Public-facing identifier, `default=uuid.uuid4`, `editable=False` |
| `customer` | `ForeignKey(User)` | `limit_choices_to={'consumer__isnull': False}`, `related_name='placed_orders'` |
| `chef` | `ForeignKey(User)` | `limit_choices_to={'chef__isnull': False}`, `related_name='received_orders'` |
| `status` | `CharField(max_length=20)` | Choices from `OrderStatus.TextChoices` |
| `subtotal` | `DecimalField(max_digits=10, decimal_places=2)` | Sum of all item totals |
| `delivery_fee` | `DecimalField(max_digits=10, decimal_places=2)` | Fixed at `10.00` |
| `total_amount` | `DecimalField(max_digits=10, decimal_places=2)` | `subtotal + delivery_fee`, auto-calculated in `save()` |
| `estimated_preparation_minutes` | `PositiveIntegerField` | Max of dish `preparation_time` values (parallel prep assumption) |
| `estimated_ready_time` | `DateTimeField(null=True, blank=True)` | `accepted_at + timedelta(minutes=estimated_preparation_minutes)` |
| `created_at` | `DateTimeField` | `default=timezone.now` |
| `updated_at` | `DateTimeField` | `auto_now=True` |
| `accepted_at` | `DateTimeField(null=True, blank=True)` | Timestamp when chef accepted |
| `out_for_delivery_at` | `DateTimeField(null=True, blank=True)` | Timestamp when chef marked out for delivery |
| `delivered_at` | `DateTimeField(null=True, blank=True)` | Timestamp when delivered |
| `cancelled_at` | `DateTimeField(null=True, blank=True)` | Timestamp when cancelled |
| `cancelled_by` | `ForeignKey(User, null=True, blank=True)` | Who cancelled, `related_name='cancelled_orders'` |
| `cancellation_reason` | `TextField(blank=True, null=True)` | Free-text reason |
| `delivery_address` | `TextField` | Full address string |
| `delivery_longitude` | `DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)` | |
| `delivery_latitude` | `DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)` | |
| `estimated_delivery_time` | `DateTimeField(null=True, blank=True)` | |
| `special_instructions` | `TextField(blank=True, null=True)` | Customer notes |
| `chef_name_snapshot` | `CharField(max_length=300)` | Chef's display name at order time |

### 1.2 OrderItem Model

| Field | Type | Notes |
|---|---|---|
| `id` | `BigAutoField` (PK) | |
| `order` | `ForeignKey(Order)` | `related_name='items'` |
| `dish` | `ForeignKey(Dish)` | `on_delete=models.PROTECT` |
| `dish_name_snapshot` | `CharField(max_length=200)` | |
| `dish_base_price_snapshot` | `DecimalField(max_digits=10, decimal_places=2)` | |
| `chef_name_snapshot` | `CharField(max_length=300)` | Redundant with Order-level but useful for denormalized queries |
| `quantity` | `PositiveIntegerField` | Default `1` |
| `unit_price` | `DecimalField(max_digits=10, decimal_places=2)` | Dish price at order time |
| `item_total` | `DecimalField(max_digits=10, decimal_places=2, editable=False)` | `quantity * unit_price + variety adjustments` |
| `special_requests` | `TextField(blank=True, null=True)` | Per-item notes |

### 1.3 OrderItemVarietySelection Model

| Field | Type | Notes |
|---|---|---|
| `id` | `BigAutoField` (PK) | |
| `order_item` | `ForeignKey(OrderItem)` | `related_name='variety_selections'` |
| `section_name` | `CharField(max_length=100)` | Snapshot of `DishVarietySection.name` |
| `option_name` | `CharField(max_length=100)` | Snapshot of `DishVarietyOption.name` |
| `option_price_adjustment` | `DecimalField(max_digits=6, decimal_places=2)` | Snapshot at order time |

### 1.4 OrderNotification Model

| Field | Type | Notes |
|---|---|---|
| `id` | `BigAutoField` (PK) | |
| `order` | `ForeignKey(Order)` | `related_name='notifications'` |
| `recipient` | `ForeignKey(User)` | `related_name='order_notifications'` |
| `notification_type` | `CharField(max_length=30)` | Choices from `NotificationType.TextChoices` |
| `message` | `TextField` | Human-readable message |
| `is_read` | `BooleanField` | Default `False` |
| `created_at` | `DateTimeField` | `default=timezone.now` |

---

## 2. Relationships Between Models

```
User (Consumer) ──< Order (customer FK)
User (Chef)     ──< Order (chef FK)
User            ──< Order (cancelled_by FK, nullable)
User            ──< OrderNotification (recipient FK)

Order           ──< OrderItem (order FK)
OrderItem       ──< Dish (dish FK, PROTECT)
OrderItem       ──< OrderItemVarietySelection (order_item FK)

Order           ──< OrderNotification (order FK)
```

Key constraints:
- `Order.customer` limited to users with a `Consumer` profile
- `Order.chef` limited to users with a `Chef` profile
- `OrderItem.dish` uses `PROTECT` to prevent deletion of dishes that are part of orders
- `unique_together = ('order', 'dish')` on OrderItem — each dish appears once per order

---

## 3. Field Type Rationale

| Type | Where Used | Why |
|---|---|---|
| `BigAutoField` | All PKs | Django default, supports high volume |
| `UUIDField` | `Order.order_id` | Non-sequential, hard-to-guess public IDs |
| `ForeignKey` | All relationships | Relational integrity, ORM convenience |
| `CharField` | Status, names, snapshots | Fixed/short text, indexable |
| `TextField` | Addresses, instructions, messages | Unbounded text |
| `DecimalField` | All monetary values | Precision for currency |
| `PositiveIntegerField` | Quantities, minutes | Non-negative integers |
| `DateTimeField` | All timestamps | Timezone-aware tracking |
| `BooleanField` | `is_read` | Simple flag |

**No JSONField needed.** Variety selections are normalized into `OrderItemVarietySelection` rows. This keeps queries SQL-friendly and avoids opaque blobs. If future requirements demand arbitrary metadata, add a `metadata JSONField` then.

---

## 4. Enums / Constants

Already defined in `orders/constants.py`:

```python
class OrderStatus(models.TextChoices):
    PENDING = 'pending', 'Pending'
    ACCEPTED = 'accepted', 'Accepted'
    OUT_FOR_DELIVERY = 'out_for_delivery', 'Out for Delivery'
    DELIVERED = 'delivered', 'Delivered'
    CANCELLED = 'cancelled', 'Cancelled'
    REJECTED = 'rejected', 'Rejected'
```

Valid transitions map:

```python
VALID_STATUS_TRANSITIONS = {
    OrderStatus.PENDING:      [ACCEPTED, CANCELLED, REJECTED],
    OrderStatus.ACCEPTED:     [OUT_FOR_DELIVERY, CANCELLED],
    OrderStatus.OUT_FOR_DELIVERY: [DELIVERED],
    OrderStatus.DELIVERED:    [],
    OrderStatus.CANCELLED:    [],
    OrderStatus.REJECTED:     [],
}
```

Actor permissions:

```python
STATUS_ACTION_PERMISSIONS = {
    ACCEPTED:         'chef',
    OUT_FOR_DELIVERY: 'chef',
    DELIVERED:        'chef',
    REJECTED:         'chef',
    CANCELLED:        'both',   # either party can cancel pending
}
```

Other constants:

```python
ORDER_PENDING_TIMEOUT_MINUTES = 5
DELIVERY_FEE = Decimal('10.00')
PREPARATION_REMINDER_MINUTES = 5
```

Notification types:

```python
class NotificationType(models.TextChoices):
    ORDER_PLACED = 'order_placed', 'Order Placed'
    ORDER_ACCEPTED = 'order_accepted', 'Order Accepted'
    ORDER_REJECTED = 'order_rejected', 'Order Rejected'
    ORDER_CANCELLED = 'order_cancelled', 'Order Cancelled'
    PREPARATION_REMINDER = 'preparation_reminder', 'Preparation Reminder'
    OUT_FOR_DELIVERY = 'out_for_delivery', 'Out for Delivery'
    DELIVERED = 'delivered', 'Delivered'
```

---

## 5. Serializer Structure

### 5.1 `OrderItemInputSerializer` (write-only, nested inside order creation)

```python
class OrderItemInputSerializer(serializers.Serializer):
    dish_id = serializers.IntegerField()
    quantity = serializers.IntegerField(min_value=1)
    variety_selections = serializers.ListField(
        child=serializers.DictField(child=serializers.CharField()),
        required=False,
        default=list,
    )
    special_requests = serializers.CharField(required=False, allow_blank=True, allow_null=True)
```

Each dict in `variety_selections` looks like: `{"section_id": 3, "option_id": 7}`.

### 5.2 `OrderCreateSerializer`

```python
class OrderCreateSerializer(serializers.ModelSerializer):
    items = OrderItemInputSerializer(many=True, write_only=True)

    class Meta:
        model = Order
        fields = [
            'order_id', 'chef', 'delivery_address',
            'delivery_longitude', 'delivery_latitude',
            'special_instructions', 'items',
        ]
        read_only_fields = ['order_id']
```

- `customer` is set in the view from `request.user`, not from input.
- `subtotal`, `delivery_fee`, `total_amount`, `status` are computed in the service layer.

### 5.3 `OrderItemReadSerializer` (for responses)

```python
class OrderItemReadSerializer(serializers.ModelSerializer):
    dish_name = serializers.CharField(source='dish_name_snapshot')
    dish_base_price = serializers.CharField(source='dish_base_price_snapshot')
    variety_selections = serializers.SerializerMethodField()

    class Meta:
        model = OrderItem
        fields = [
            'id', 'dish_name', 'dish_base_price', 'quantity',
            'unit_price', 'item_total', 'special_requests', 'variety_selections',
        ]

    def get_variety_selections(self, obj):
        return [
            {
                'section_name': vs.section_name,
                'option_name': vs.option_name,
                'price_adjustment': vs.option_price_adjustment,
            }
            for vs in obj.variety_selections.all()
        ]
```

### 5.4 `OrderListSerializer`

```python
class OrderListSerializer(serializers.ModelSerializer):
    customer_name = serializers.CharField(source='customer.get_full_name', read_only=True)
    chef_name = serializers.CharField(source='chef_name_snapshot')
    items_count = serializers.SerializerMethodField()
    estimated_ready_time = serializers.DateTimeField(read_only=True)

    class Meta:
        model = Order
        fields = [
            'order_id', 'customer_name', 'chef_name', 'status',
            'total_amount', 'created_at', 'items_count', 'estimated_ready_time',
        ]
```

### 5.5 `OrderDetailSerializer`

```python
class OrderDetailSerializer(serializers.ModelSerializer):
    items = OrderItemReadSerializer(many=True, read_only=True)
    customer_name = serializers.CharField(source='customer.get_full_name', read_only=True)
    chef_name = serializers.CharField(source='chef_name_snapshot', read_only=True)

    class Meta:
        model = Order
        fields = [
            'order_id', 'customer', 'customer_name', 'chef', 'chef_name',
            'status', 'subtotal', 'delivery_fee', 'total_amount',
            'estimated_preparation_minutes', 'estimated_ready_time',
            'delivery_address', 'delivery_longitude', 'delivery_latitude',
            'estimated_delivery_time', 'special_instructions',
            'created_at', 'updated_at',
            'accepted_at', 'out_for_delivery_at', 'delivered_at',
            'cancelled_at', 'cancelled_by', 'cancellation_reason',
            'items',
        ]
```

### 5.6 `OrderStatusUpdateSerializer`

```python
class OrderStatusUpdateSerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=OrderStatus.choices)
    cancellation_reason = serializers.CharField(
        required=False, allow_blank=True, allow_null=True,
    )
```

Validated against `VALID_STATUS_TRANSITIONS` and `STATUS_ACTION_PERMISSIONS` in the service layer.

---

## 6. API Endpoint Structure

| Method | Endpoint | View | Auth | Description |
|---|---|---|---|---|
| `POST` | `/api/orders/create/` | `OrderCreateView` | Consumer only | Place a new order |
| `GET` | `/api/orders/` | `OrderListView` | Authenticated | List orders (filtered by role) |
| `GET` | `/api/orders/<uuid:order_id>/` | `OrderDetailView` | Authenticated | Get order details |
| `PATCH` | `/api/orders/<uuid:order_id>/status/` | `OrderStatusUpdateView` | Authenticated | Transition order status |
| `GET` | `/api/orders/notifications/` | `OrderNotificationListView` | Authenticated | List user's order notifications |
| `PATCH` | `/api/orders/notifications/<id>/read/` | `NotificationMarkReadView` | Authenticated | Mark notification as read |
| `POST` | `/api/orders/cancel-expired/` | `CancelExpiredOrdersView` | Admin/Staff (or cron) | Manually trigger auto-cancel |

### URL patterns (`orders/urls.py`):

```python
urlpatterns = [
    path('', views.OrderListView.as_view(), name='order-list'),
    path('create/', views.OrderCreateView.as_view(), name='order-create'),
    path('<uuid:order_id>/', views.OrderDetailView.as_view(), name='order-detail'),
    path('<uuid:order_id>/status/', views.OrderStatusUpdateView.as_view(), name='order-status-update'),
    path('notifications/', views.OrderNotificationListView.as_view(), name='order-notifications'),
    path('notifications/<int:pk>/read/', views.NotificationMarkReadView.as_view(), name='notification-mark-read'),
    path('cancel-expired/', views.CancelExpiredOrdersView.as_view(), name='cancel-expired-orders'),
]
```

### WebSocket Routing (`orders/routing.py`):

```python
from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    re_path(r'ws/orders/$', consumers.OrderConsumer.as_asgi(), name='orders-ws'),
]
```

Clients connect to a single WebSocket endpoint. The consumer subscribes to user-specific and order-specific groups based on the authenticated user.

---

## 7. WebSocket & Real-Time Notifications (Django Channels)

### 7.1 Dependencies

Add to `requirements.txt`:

```
channels>=4.0
channels-redis>=4.0
```

### 7.2 Settings Configuration (`settings.py`)

```python
INSTALLED_APPS = [
    # ... existing apps ...
    'channels',
    'orders',
]

# ASGI application
ASGI_APPLICATION = 'HomemadeFood.asgi.application'

# Channel layer (Redis for production, in-memory for development)
CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels_redis.core.RedisChannelLayer',
        'CONFIG': {
            'hosts': [('127.0.0.1', 6379)],  # Redis server
        },
    },
}

# Development fallback (no Redis needed)
# CHANNEL_LAYERS = {
#     'default': {
#         'BACKEND': 'channels.layers.InMemoryChannelLayer',
#     },
# }
```

### 7.3 ASGI Configuration (`HomemadeFood/asgi.py`)

```python
import os
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from channels.security.websocket import AllowedHostsOriginValidator
from orders.routing import websocket_urlpatterns

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HomemadeFood.settings')

django_asgi_app = get_asgi_application()

application = ProtocolTypeRouter({
    'http': django_asgi_app,
    'websocket': AllowedHostsOriginValidator(
        AuthMiddlewareStack(
            URLRouter(websocket_urlpatterns)
        )
    ),
})
```

### 7.4 WebSocket Consumer (`orders/consumers.py`)

```python
import json
from channels.generic.websocket import AsyncJsonWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth import get_user_model

User = get_user_model()

class OrderConsumer(AsyncJsonWebsocketConsumer):
    """
    WebSocket consumer for real-time order notifications.
    
    Groups:
    - user_{user_id}: All notifications for this user
    - order_{order_id}: Updates for a specific order (both chef and customer)
    """

    async def connect(self):
        user = self.scope['user']
        
        if user.is_anonymous:
            await self.close()
            return

        self.user_id = user.id
        self.user_group_name = f'user_{self.user_id}'

        # Join user-specific group
        await self.channel_layer.group_add(
            self.user_group_name,
            self.channel_name,
        )
        await self.accept()

    async def disconnect(self, close_code):
        if hasattr(self, 'user_group_name'):
            await self.channel_layer.group_discard(
                self.user_group_name,
                self.channel_name,
            )

    async def receive(self, text_data):
        """
        Client can send messages to acknowledge notifications
        or request order-specific group subscription.
        """
        data = json.loads(text_data)
        action = data.get('action')

        if action == 'subscribe_order':
            order_id = data.get('order_id')
            if order_id:
                order_group = f'order_{order_id}'
                await self.channel_layer.group_add(order_group, self.channel_name)
                await self.send_json({
                    'type': 'subscribed',
                    'order_id': order_id,
                })

        elif action == 'unsubscribe_order':
            order_id = data.get('order_id')
            if order_id:
                order_group = f'order_{order_id}'
                await self.channel_layer.group_discard(order_group, self.channel_name)

    # --- Event handlers (called via channel_layer.group_send) ---

    async def order_notification(self, event):
        """Send a new notification to the client."""
        await self.send_json({
            'type': 'notification',
            'data': event['data'],
        })

    async def order_status_update(self, event):
        """Send order status change to the client."""
        await self.send_json({
            'type': 'status_update',
            'data': event['data'],
        })

    async def order_created(self, event):
        """Notify chef of new order."""
        await self.send_json({
            'type': 'new_order',
            'data': event['data'],
        })
```

### 7.5 Channel Layer Helper (`orders/utils.py`)

```python
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer

channel_layer = get_channel_layer()

def broadcast_notification(user_id: int, notification_data: dict):
    """Send a notification to a specific user's WebSocket connection."""
    async_to_sync(channel_layer.group_send)(
        f'user_{user_id}',
        {
            'type': 'order_notification',
            'data': notification_data,
        },
    )

def broadcast_order_status_update(order_id: str, status_data: dict):
    """Send status update to everyone tracking this order (chef + customer)."""
    async_to_sync(channel_layer.group_send)(
        f'order_{order_id}',
        {
            'type': 'order_status_update',
            'data': status_data,
        },
    )

def broadcast_new_order_to_chef(chef_id: int, order_data: dict):
    """Notify chef of incoming order."""
    async_to_sync(channel_layer.group_send)(
        f'user_{chef_id}',
        {
            'type': 'order_created',
            'data': order_data,
        },
    )
```

### 7.6 Integration with Service Layer

Update `orders/services.py` to broadcast WebSocket events alongside DB notifications:

**In `OrderCreateService.execute()` — after creating order and notification:**

```python
# Existing code:
OrderNotification.objects.create(...)

# Add WebSocket broadcast:
from .utils import broadcast_new_order_to_chef

broadcast_new_order_to_chef(
    chef_id=self.chef_id,
    notification_data={
        'order_id': str(order.order_id),
        'customer_name': f'{self.customer.first_name} {self.customer.last_name}',
        'total_amount': str(order.total_amount),
        'items_count': len(self.items),
        'message': f'New order from {self.customer.first_name} {self.customer.last_name}',
    },
)
```

**In `OrderStatusService._create_notifications()` — after each notification:**

```python
# Existing code:
OrderNotification.objects.create(...)

# Add WebSocket broadcasts:
from .utils import broadcast_notification, broadcast_order_status_update

# Send to the notification recipient
broadcast_notification(
    user_id=recipient.id,
    notification_data={
        'notification_type': n_type,
        'order_id': str(self.order.order_id),
        'message': message,
        'created_at': timezone.now().isoformat(),
    },
)

# Also broadcast status change to order-specific group
broadcast_order_status_update(
    order_id=str(self.order.order_id),
    status_data={
        'order_id': str(self.order.order_id),
        'status': self.new_status,
        'updated_at': timezone.now().isoformat(),
        'estimated_ready_time': self.order.estimated_ready_time.isoformat() if self.order.estimated_ready_time else None,
    },
)
```

### 7.7 Frontend WebSocket Client Example

```javascript
// Connect to WebSocket
const ws = new WebSocket('ws://localhost:8000/ws/orders/');

ws.onopen = () => {
  console.log('Connected to orders WebSocket');
  
  // Subscribe to specific order updates
  ws.send(JSON.stringify({
    action: 'subscribe_order',
    order_id: 'abc-123-def',
  }));
};

ws.onmessage = (event) => {
  const message = JSON.parse(event.data);
  
  switch (message.type) {
    case 'notification':
      // Show toast/push notification
      showNotification(message.data.message);
      updateNotificationBadge();
      break;
      
    case 'status_update':
      // Update order status in UI
      updateOrderStatus(message.data.order_id, message.data.status);
      break;
      
    case 'new_order':
      // Chef sees new order in dashboard
      showNewOrderAlert(message.data);
      break;
  }
};

ws.onclose = () => {
  console.log('Disconnected, attempting reconnect...');
  // Implement reconnection logic
};
```

### 7.8 WebSocket Groups Strategy

| Group Name | Who Joins | Purpose |
|---|---|---|
| `user_{user_id}` | All authenticated users on connect | Receive personal notifications (new orders, status updates, cancellations) |
| `order_{order_id}` | Chef + Customer involved in the order | Receive real-time status changes for a specific order |

### 7.9 Fallback Behavior

- If WebSocket connection fails, client falls back to polling `/api/orders/notifications/` every 10 seconds
- All WebSocket events are also persisted as `OrderNotification` records, so polling retrieves missed events
- Client should reconcile both sources to avoid duplicate displays

---

## 8. Permissions Logic

### 8.1 View-level permissions

| View | Permission Class | Additional Check |
|---|---|---|
| `OrderCreateView` | `IsAuthenticated` | `IsConsumer` custom permission |
| `OrderListView` | `IsAuthenticated` | Queryset filtered by role in `get_queryset()` |
| `OrderDetailView` | `IsAuthenticated` | Queryset filtered: consumer sees own orders, chef sees own received orders |
| `OrderStatusUpdateView` | `IsAuthenticated` | Must be the assigned chef (or customer for cancel-only) |
| `OrderNotificationListView` | `IsAuthenticated` | Filtered to `recipient=request.user` |
| `NotificationMarkReadView` | `IsAuthenticated` | Must be the notification recipient |
| `CancelExpiredOrdersView` | `IsAdminUser` or custom `IsStaff` | Admin-only |

### 8.2 Custom permission classes

```python
class IsConsumer(permissions.BasePermission):
    def has_permission(self, request, view):
        return hasattr(request.user, 'consumer')

class IsChef(permissions.BasePermission):
    def has_permission(self, request, view):
        return hasattr(request.user, 'chef')
```

### 8.3 Object-level permission (in `OrderDetailView` / `OrderStatusUpdateView`)

```python
def get_queryset(self):
    user = self.request.user
    if hasattr(user, 'consumer'):
        return Order.objects.filter(customer=user)
    elif hasattr(user, 'chef'):
        return Order.objects.filter(chef=user)
    return Order.objects.none()
```

---

## 9. Validation Rules

### 9.1 Order Creation (`OrderCreateService.validate()`)

1. **At least one item** — `items` list must not be empty.
2. **All dishes exist and are available** — every `dish_id` must reference a `Dish` with `is_available=True`. If any dish is unavailable, reject the entire request with a list of unavailable dish IDs.
3. **All dishes belong to the same chef** — collect `dish.chef_id` for all items; if more than one unique chef, reject with error.
4. **Chef is online** — `chef.is_online` must be `True`. If offline, reject with `"Chef is not currently accepting orders."`
5. **Valid variety selections** — for each item, if `variety_selections` is provided:
   - Each `section_id` must belong to the dish.
   - Each `option_id` must belong to the referenced section and have `is_available=True`.
6. **Quantity > 0** for every item.
7. **Delivery coordinates provided** — `delivery_longitude` and `delivery_latitude` required.

### 9.2 Status Transition (`OrderStatusService.validate_transition()`)

1. Look up `VALID_STATUS_TRANSITIONS[current_status]`. If `new_status` not in list, reject.
2. Check `STATUS_ACTION_PERMISSIONS[new_status]`:
   - `'chef'` → requesting user must be the order's chef.
   - `'both'` → requesting user must be either the chef or the customer.
3. If transitioning to `CANCELLED` and user is consumer, `cancellation_reason` is optional but recommended.
4. Terminal states (`DELIVERED`, `CANCELLED`, `REJECTED`) cannot be exited.

---

## 10. Service Layer Methods

Create `orders/services.py`. This is the core business logic, decoupled from views.

### 10.1 `OrderCreateService`

```python
class OrderCreateService:
    """Handles order creation with full validation and atomic persistence."""

    def __init__(self, customer: User, chef_id: int, items: list[dict],
                 delivery_address: str, delivery_longitude: Decimal,
                 delivery_latitude: Decimal, special_instructions: str = None):
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
                    raise ValidationError(f"Section {section_id} not found for dish {dish.name}")
                opt = DishVarietyOption.objects.filter(
                    section_id=section_id, id=option_id
                ).first()
                if not opt:
                    raise ValidationError(f"Option {option_id} not found in section {section_id}")
                if not opt.is_available:
                    raise ValidationError(f"Option {opt.name} is not available")

    @transaction.atomic
    def execute(self) -> Order:
        """Create the order and all related items atomically."""
        self.validate()

        dishes = Dish.objects.filter(id__in=[i['dish_id'] for i in self.items]).select_related('chef')
        chef = dishes[0].chef.user if hasattr(dishes[0].chef, 'user') else dishes[0].chef
        chef_name = f"{chef.first_name} {chef.last_name}"

        prep_times = [d.preparation_time for d in dishes]
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

        OrderNotification.objects.create(
            order=order,
            recipient=order.chef,
            notification_type=NotificationType.ORDER_PLACED,
            message=f"New order #{order.order_id} from {self.customer.first_name} {self.customer.last_name}.",
        )

        return order
```

### 10.2 `OrderStatusService`

```python
class OrderStatusService:
    """Handles order status transitions with validation and notifications."""

    def __init__(self, order: Order, new_status: str, user: User,
                 cancellation_reason: str = None):
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
            raise PermissionDenied("Only the chef or customer can perform this action.")

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
            schedule_preparation_reminder(self.order)

        self._create_notifications()
        return self.order

    def _create_notifications(self):
        mapping = {
            OrderStatus.ACCEPTED: (
                self.order.customer,
                NotificationType.ORDER_ACCEPTED,
                f"Your order #{self.order.order_id} has been accepted. Estimated ready time: {self.order.estimated_ready_time}.",
            ),
            OrderStatus.REJECTED: (
                self.order.customer,
                NotificationType.ORDER_REJECTED,
                f"Your order #{self.order.order_id} has been rejected. Reason: {self.order.cancellation_reason or 'Not specified.'}",
            ),
            OrderStatus.CANCELLED: (
                self.order.chef,
                NotificationType.ORDER_CANCELLED,
                f"Order #{self.order.order_id} was cancelled. Reason: {self.order.cancellation_reason or 'Not specified.'}",
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
```

### 10.3 `CancelExpiredOrdersService`

```python
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
            order.cancellation_reason = 'Auto-cancelled: chef did not respond within 5 minutes.'
            order.save(update_fields=['status', 'cancelled_at', 'cancellation_reason'])

            OrderNotification.objects.create(
                order=order,
                recipient=order.customer,
                notification_type=NotificationType.ORDER_CANCELLED,
                message=f"Order #{order.order_id} was auto-cancelled because the chef did not respond within 5 minutes.",
            )
            count += 1

        return count
```

### 10.4 `schedule_preparation_reminder(order)`

```python
def schedule_preparation_reminder(order: Order):
    """Schedule a reminder notification for the chef 5 minutes before estimated_ready_time."""
    if not order.estimated_ready_time:
        return

    reminder_time = order.estimated_ready_time - timedelta(minutes=PREPARATION_REMINDER_MINUTES)
    delay_seconds = (reminder_time - timezone.now()).total_seconds()

    if delay_seconds <= 0:
        return

    # Production: preparation_reminder_task.apply_async(args=[order.id], countdown=delay_seconds)
    # Development: threading.Timer(delay_seconds, send_preparation_reminder, args=[order.id]).start()
    pass
```

### 10.5 `send_preparation_reminder(order_id)`

```python
def send_preparation_reminder(order_id: int):
    try:
        order = Order.objects.get(id=order_id)
    except Order.DoesNotExist:
        return

    if order.status != OrderStatus.ACCEPTED:
        return

    OrderNotification.objects.create(
        order=order,
        recipient=order.chef,
        notification_type=NotificationType.PREPARATION_REMINDER,
        message=f"Reminder: Order #{order.order_id} should be ready in {PREPARATION_REMINDER_MINUTES} minutes.",
    )
```

---

## 11. Signal Usage

**Minimize signals.** Use them only for side-effects that are truly decoupled.

| Signal | Sender | Receiver | Purpose |
|---|---|---|---|
| `post_save` | `Order` | — | **Not needed** — notification created in service layer |
| `post_save` | `Order` | — | **Not needed** — scheduling done in service layer |

**Recommendation: Do NOT use signals for the orders module.** All notifications and side-effects should be explicit in the service layer. This makes the flow traceable, testable, and avoids hidden coupling.

---

## 12. Background Task Usage

Two background tasks are needed:

### 12.1 Auto-cancel expired pending orders

**Production (Celery):**

```python
# orders/tasks.py
from celery import shared_task

@shared_task
def cancel_expired_orders():
    from .services import CancelExpiredOrdersService
    return CancelExpiredOrdersService.execute()
```

Celery beat schedule (`settings.py`):

```python
CELERY_BEAT_SCHEDULE = {
    'cancel-expired-orders-every-minute': {
        'task': 'orders.tasks.cancel_expired_orders',
        'schedule': 60.0,
    },
}
```

**Development (no Celery):** A Django management command called by cron or run manually:

```python
# orders/management/commands/cancel_expired_orders.py
class Command(BaseCommand):
    help = 'Cancel expired pending orders'

    def handle(self, *args, **kwargs):
        count = CancelExpiredOrdersService.execute()
        self.stdout.write(f'Cancelled {count} expired orders.')
```

### 12.2 Preparation reminder

**Production (Celery):**

```python
@shared_task
def preparation_reminder_task(order_id):
    from .services import send_preparation_reminder
    send_preparation_reminder(order_id)
```

Scheduled via `apply_async(countdown=delay_seconds)` in `schedule_preparation_reminder()`.

**Development:** Use `threading.Timer` or skip and rely on the management command.

### 12.3 Recommendation

Start without Celery. Use management commands + cron for auto-cancel. Add Celery when the project scales.

---

## 13. `transaction.atomic` Usage

| Operation | Location | Why |
|---|---|---|
| Order creation | `OrderCreateService.execute()` | Order + OrderItems + VarietySelections + Notification must all succeed or all roll back |
| Status transition | `OrderStatusService.execute()` | Status update + timestamp + notification must be atomic |
| Auto-cancel batch | `CancelExpiredOrdersService.execute()` | Each order update + notification should be atomic |

**Do NOT** wrap read-only operations (list, detail) in atomic blocks.

---

## 14. Pagination & Filtering

### 14.1 Pagination

Use DRF's `PageNumberPagination` with a default of 20 items per page.

```python
# orders/pagination.py
from rest_framework.pagination import PageNumberPagination

class OrderPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100
```

### 14.2 Filtering

Query parameters on `OrderListView`:

| Param | Type | Description |
|---|---|---|
| `status` | `ChoiceField` | Filter by order status |
| `date_from` | `DateField` | Orders from this date onwards |
| `date_to` | `DateField` | Orders up to this date |

Implementation in `OrderListView`:

```python
class OrderListView(generics.ListAPIView):
    serializer_class = OrderListSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = OrderPagination

    def get_queryset(self):
        user = self.request.user
        if hasattr(user, 'consumer'):
            qs = Order.objects.filter(customer=user)
        elif hasattr(user, 'chef'):
            qs = Order.objects.filter(chef=user)
        else:
            return Order.objects.none()

        qs = qs.select_related('chef', 'customer').prefetch_related('items')

        status = self.request.query_params.get('status')
        if status:
            qs = qs.filter(status=status)

        date_from = self.request.query_params.get('date_from')
        if date_from:
            qs = qs.filter(created_at__gte=date_from)

        date_to = self.request.query_params.get('date_to')
        if date_to:
            qs = qs.filter(created_at__lte=date_to)

        return qs.order_by('-created_at')
```

---

## 15. Suggested Folder Structure

```
orders/
├── __init__.py
├── apps.py
├── models.py                  # Order, OrderItem, OrderItemVarietySelection, OrderNotification
├── constants.py               # OrderStatus, NotificationType, DELIVERY_FEE, transitions
├── serializers.py             # All serializers
├── views.py                   # API views
├── urls.py                    # URL routing
├── routing.py                 # WebSocket routing
├── consumers.py               # WebSocket consumers
├── utils.py                   # Channel layer broadcast helpers
├── permissions.py             # IsConsumer, IsChef, IsOrderParticipant
├── services.py                # OrderCreateService, OrderStatusService, CancelExpiredOrdersService
├── pagination.py              # OrderPagination
├── tasks.py                   # Celery tasks (optional, for later)
├── admin.py                   # Admin registration
├── tests/
│   ├── __init__.py
│   ├── test_models.py
│   ├── test_serializers.py
│   ├── test_services.py
│   ├── test_views.py
│   ├── test_permissions.py
│   ├── test_consumers.py      # WebSocket consumer tests
│   └── test_tasks.py
└── management/
    └── commands/
        └── cancel_expired_orders.py
```

---

## 16. Step-by-Step Implementation Order

### Phase 1: Foundation (Models & Constants)

1. **Review and finalize `constants.py`** — Ensure `OrderStatus`, `VALID_STATUS_TRANSITIONS`, `STATUS_ACTION_PERMISSIONS`, `DELIVERY_FEE`, `NotificationType` are correct.
2. **Review and finalize `models.py`** — Ensure all fields exist. Add missing fields (`subtotal`, `delivery_fee`, `estimated_preparation_minutes`, `estimated_ready_time`, `chef_name_snapshot`, `accepted_at`, `out_for_delivery_at`, `delivered_at`, `cancelled_at`, `cancelled_by`, `cancellation_reason`, `OrderItemVarietySelection`, `OrderNotification`).
3. **Run `makemigrations` and `migrate`** — Verify schema.
4. **Register models in `admin.py`** — With list filters for status, chef, customer, date.

### Phase 2: Service Layer (Business Logic)

5. **Create `services.py`** — Implement `OrderCreateService` with full validation.
6. **Implement `OrderStatusService`** — Status transition validation, timestamp management, notification creation.
7. **Implement `CancelExpiredOrdersService`** — Auto-cancel logic.
8. **Write unit tests for all services** — Test happy path, validation failures, edge cases.

### Phase 3: Serializers

9. **Create all serializers** — `OrderItemInputSerializer`, `OrderCreateSerializer`, `OrderItemReadSerializer`, `OrderListSerializer`, `OrderDetailSerializer`, `OrderStatusUpdateSerializer`.
10. **Write serializer tests** — Test nested input parsing, read-only field mapping, validation errors.

### Phase 4: Views & URLs

11. **Implement `OrderCreateView`** — Use `OrderCreateService` in `perform_create`. Restrict to consumers.
12. **Implement `OrderListView`** — Role-based queryset, pagination, filtering.
13. **Implement `OrderDetailView`** — Role-based access, detail serialization.
14. **Implement `OrderStatusUpdateView`** — Use `OrderStatusService`, restrict to chef/customer.
15. **Implement `OrderNotificationListView`** — List notifications for current user.
16. **Implement `NotificationMarkReadView`** — Mark single notification as read.
17. **Wire up `urls.py`** — All endpoints.
18. **Write view tests** — Auth checks, permission denials, happy path responses.

### Phase 5: WebSocket & Real-Time (Django Channels)

19. **Install `channels` and `channels-redis`** — Add to `requirements.txt`.
20. **Configure `settings.py`** — Add `channels` to `INSTALLED_APPS`, set `ASGI_APPLICATION`, configure `CHANNEL_LAYERS`.
21. **Update `asgi.py`** — Wire up `ProtocolTypeRouter` with WebSocket support.
22. **Create `routing.py`** — Define WebSocket URL patterns.
23. **Create `consumers.py`** — Implement `OrderConsumer` with group management.
24. **Create `utils.py`** — Broadcast helper functions for channel layer.
25. **Integrate WebSocket into services** — Add broadcast calls to `OrderCreateService` and `OrderStatusService`.
26. **Write consumer tests** — Test connect/disconnect, group subscriptions, message broadcasting.
27. **Test end-to-end** — Place order via REST, verify chef receives WebSocket event in real-time.

### Phase 6: Background Tasks

28. **Create `cancel_expired_orders` management command** — Test manually.
29. **(Optional) Set up Celery** — Add `tasks.py`, configure Celery beat.
30. **Test background tasks** — Mock time, verify notifications.

### Phase 7: Permissions & Security

31. **Create `permissions.py`** — `IsConsumer`, `IsChef`, `IsOrderParticipant`.
32. **Audit all views** — Ensure no data leakage between users.
33. **Secure WebSocket connections** — Verify `AuthMiddlewareStack` rejects anonymous users, test group isolation (user A cannot receive user B's notifications).

### Phase 8: Integration & End-to-End Testing

34. **Write integration tests** — Full order flow: create → accept → out_for_delivery → delivered. Also: create → reject, create → cancel, create → auto-cancel.
35. **Test with real API calls** — Use Postman or DRF's `APIClient`.
36. **Test variety selections end-to-end** — Create order with varieties, verify snapshots, verify pricing.
37. **Test WebSocket real-time flow** — Consumer places order → chef receives instant notification → chef accepts → consumer receives status update.
38. **Test WebSocket fallback** — Disconnect WS, verify polling still retrieves missed notifications.

### Phase 9: Polish

39. **Add ordering to list view** — Default `-created_at`.
40. **Add search/filter** — By status, date range.
41. **Document all endpoints** — Update this guide with final API spec.
42. **Load test data fixture** — Create sample orders for development.



--resume f8c4168b-3676-4e71-9ecb-52f00faf3181
