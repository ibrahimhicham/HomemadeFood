# WebSocket Endpoints

This project currently defines one WebSocket endpoint.

## 1. Orders WebSocket

- Path: `/ws/orders/`
- Route name: `orders-ws`
- Defined in: [orders/routing.py](C:/Users/Sherif/Desktop/HomemadeFood/orders/routing.py:4)
- Consumer: [orders/consumers.py](C:/Users/Sherif/Desktop/HomemadeFood/orders/consumers.py:5)
- ASGI wiring: [HomemadeFood/asgi.py](C:/Users/Sherif/Desktop/HomemadeFood/HomemadeFood/asgi.py:21)

### Authentication

Authentication is done with a DRF token in the query string, not session auth.

Example:

```text
ws://localhost:8000/ws/orders/?token=<auth_token>
```

Auth middleware: [orders/middleware.py](C:/Users/Sherif/Desktop/HomemadeFood/orders/middleware.py:7)

### Connection Behavior

- Anonymous users are rejected.
- Authenticated users are automatically added to `user_<user_id>`.

### Client Messages

Subscribe to an order group:

```json
{
  "action": "subscribe_order",
  "order_id": "123e4567-e89b-12d3-a456-426614174000"
}
```

Unsubscribe from an order group:

```json
{
  "action": "unsubscribe_order",
  "order_id": "123e4567-e89b-12d3-a456-426614174000"
}
```

### Server Messages

Subscription confirmed:

```json
{
  "type": "subscribed",
  "order_id": "123e4567-e89b-12d3-a456-426614174000"
}
```

Unsubscription confirmed:

```json
{
  "type": "unsubscribed",
  "order_id": "123e4567-e89b-12d3-a456-426614174000"
}
```

Direct notification to a user:

```json
{
  "type": "notification",
  "data": {
    "notification_type": "order_accepted",
    "order_id": "123e4567-e89b-12d3-a456-426614174000",
    "message": "Your order was accepted.",
    "created_at": "2026-05-05T12:00:00Z"
  }
}
```

Order status update to order subscribers:

```json
{
  "type": "status_update",
  "data": {
    "order_id": "123e4567-e89b-12d3-a456-426614174000",
    "status": "accepted",
    "updated_at": "2026-05-05T12:00:00Z",
    "estimated_ready_time": "2026-05-05T12:20:00Z"
  }
}
```

New order event to the chef:

```json
{
  "type": "new_order",
  "data": {
    "order_id": "123e4567-e89b-12d3-a456-426614174000",
    "customer_name": "John Doe",
    "total_amount": "35.98",
    "items_count": 2,
    "message": "New order from John Doe",
    "created_at": "2026-05-05T12:00:00Z"
  }
}
```

### Channel Groups

- `user_<user_id>`: personal notifications and chef new-order events
- `order_<order_id>`: order-specific status updates for subscribed sockets

### Broadcast Sources

- `broadcast_notification(...)`: [orders/utils.py](C:/Users/Sherif/Desktop/HomemadeFood/orders/utils.py:5)
- `broadcast_order_status_update(...)`: [orders/utils.py](C:/Users/Sherif/Desktop/HomemadeFood/orders/utils.py:17)
- `broadcast_new_order_to_chef(...)`: [orders/utils.py](C:/Users/Sherif/Desktop/HomemadeFood/orders/utils.py:29)

### Notes

- Channel layer config is currently in-memory: [HomemadeFood/settings.py](C:/Users/Sherif/Desktop/HomemadeFood/HomemadeFood/settings.py:95)
- Any authenticated user can currently subscribe to any `order_<order_id>` group because the consumer does not enforce order ownership before `group_add`.
