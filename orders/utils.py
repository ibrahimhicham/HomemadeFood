from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer


def send_to_user_group(user_id: int, event_type: str, data: dict):
    """Send event to a specific user websocket group."""
    channel_layer = get_channel_layer()

    async_to_sync(channel_layer.group_send)(
        f'user_{user_id}',
        {
            'type': event_type,
            'data': data,
        },
    )


def send_to_order_group(order_id: str, event_type: str, data: dict):
    """Send event to order tracking websocket group."""
    channel_layer = get_channel_layer()

    async_to_sync(channel_layer.group_send)(
        f'order_{order_id}',
        {
            'type': event_type,
            'data': data,
        },
    )