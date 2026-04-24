from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer


def broadcast_notification(user_id: int, notification_data: dict):
    """Send a notification to a specific user's WebSocket connection."""
    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        f'user_{user_id}',
        {
            'type': 'order_notification',
            'data': notification_data,
        },
    )


def broadcast_order_status_update(order_id: str, status_data: dict):
    """Send status update to everyone tracking this order (chef + customer)."""
    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        f'order_{order_id}',
        {
            'type': 'order_status_update',
            'data': status_data,
        },
    )


def broadcast_new_order_to_chef(chef_id: int, order_data: dict):
    """Notify chef of incoming order."""
    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        f'user_{chef_id}',
        {
            'type': 'order_created',
            'data': order_data,
        },
    )
