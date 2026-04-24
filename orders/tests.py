import json
from decimal import Decimal
from unittest.mock import patch, MagicMock

from django.test import TestCase, TransactionTestCase
from django.contrib.auth import get_user_model
from django.utils import timezone
from channels.testing import WebsocketCommunicator
from channels.layers import get_channel_layer
from asgiref.sync import sync_to_async

from orders.consumers import OrderConsumer
from orders.models import Order, OrderNotification
from orders.constants import OrderStatus, NotificationType
from orders.services import OrderCreateService, OrderStatusService
from orders.utils import (
    broadcast_notification,
    broadcast_order_status_update,
    broadcast_new_order_to_chef,
)

User = get_user_model()


class OrderConsumerTests(TransactionTestCase):
    """Tests for the WebSocket OrderConsumer."""

    async def _create_user(self, email, password, is_chef=False, is_consumer=False):
        """Helper to create a user with optional profile."""
        user = await sync_to_async(User.objects.create_user)(
            email=email,
            password=password,
            first_name=email.split('@')[0],
            last_name='Test',
            phone_number='+1234567890',
        )
        if is_chef:
            from authentication.models import Chef
            await sync_to_async(Chef.objects.create)(user=user, is_online=True)
        if is_consumer:
            from authentication.models import Consumer
            await sync_to_async(Consumer.objects.create)(user=user)
        return user

    async def test_anonymous_user_cannot_connect(self):
        """Anonymous users should be rejected."""
        from django.contrib.auth.models import AnonymousUser

        communicator = WebsocketCommunicator(
            OrderConsumer.as_asgi(),
            '/ws/orders/',
        )
        communicator.scope['user'] = AnonymousUser()
        connected, _ = await communicator.connect()
        self.assertFalse(connected)

    async def test_authenticated_user_can_connect(self):
        """Authenticated users should connect successfully."""
        user = await self._create_user('test@example.com', 'pass123', is_consumer=True)

        communicator = WebsocketCommunicator(
            OrderConsumer.as_asgi(),
            '/ws/orders/',
        )
        communicator.scope['user'] = user
        connected, _ = await communicator.connect()
        self.assertTrue(connected)

        await communicator.disconnect()

    async def test_user_joins_user_group_on_connect(self):
        """User should be added to their user-specific group."""
        user = await self._create_user('test2@example.com', 'pass123', is_consumer=True)

        communicator = WebsocketCommunicator(
            OrderConsumer.as_asgi(),
            '/ws/orders/',
        )
        communicator.scope['user'] = user
        connected, _ = await communicator.connect()
        self.assertTrue(connected)

        # Send a message to the user's group and verify it's received
        channel_layer = get_channel_layer()
        await channel_layer.group_send(
            f'user_{user.id}',
            {
                'type': 'order_notification',
                'data': {'message': 'Test notification'},
            },
        )

        response = await communicator.receive_json_from()
        self.assertEqual(response['type'], 'notification')
        self.assertEqual(response['data']['message'], 'Test notification')

        await communicator.disconnect()

    async def test_subscribe_to_order_group(self):
        """User can subscribe to an order-specific group."""
        user = await self._create_user('test3@example.com', 'pass123', is_consumer=True)

        communicator = WebsocketCommunicator(
            OrderConsumer.as_asgi(),
            '/ws/orders/',
        )
        communicator.scope['user'] = user
        connected, _ = await communicator.connect()
        self.assertTrue(connected)

        # Subscribe to an order
        await communicator.send_json_to({
            'action': 'subscribe_order',
            'order_id': 'abc-123-def',
        })

        response = await communicator.receive_json_from()
        self.assertEqual(response['type'], 'subscribed')
        self.assertEqual(response['order_id'], 'abc-123-def')

        # Send a status update to the order group
        channel_layer = get_channel_layer()
        await channel_layer.group_send(
            'order_abc-123-def',
            {
                'type': 'order_status_update',
                'data': {'order_id': 'abc-123-def', 'status': 'accepted'},
            },
        )

        response = await communicator.receive_json_from()
        self.assertEqual(response['type'], 'status_update')
        self.assertEqual(response['data']['status'], 'accepted')

        await communicator.disconnect()

    async def test_unsubscribe_from_order_group(self):
        """User can unsubscribe from an order-specific group."""
        user = await self._create_user('test4@example.com', 'pass123', is_consumer=True)

        communicator = WebsocketCommunicator(
            OrderConsumer.as_asgi(),
            '/ws/orders/',
        )
        communicator.scope['user'] = user
        connected, _ = await communicator.connect()
        self.assertTrue(connected)

        # Subscribe
        await communicator.send_json_to({
            'action': 'subscribe_order',
            'order_id': 'xyz-789',
        })
        await communicator.receive_json_from()

        # Unsubscribe
        await communicator.send_json_to({
            'action': 'unsubscribe_order',
            'order_id': 'xyz-789',
        })

        response = await communicator.receive_json_from()
        self.assertEqual(response['type'], 'unsubscribed')
        self.assertEqual(response['order_id'], 'xyz-789')

        await communicator.disconnect()

    async def test_receive_new_order_event(self):
        """Chef receives new_order WebSocket event."""
        user = await self._create_user('chef@test.com', 'pass123', is_chef=True)

        communicator = WebsocketCommunicator(
            OrderConsumer.as_asgi(),
            '/ws/orders/',
        )
        communicator.scope['user'] = user
        connected, _ = await communicator.connect()
        self.assertTrue(connected)

        # Simulate new order broadcast
        channel_layer = get_channel_layer()
        await channel_layer.group_send(
            f'user_{user.id}',
            {
                'type': 'order_created',
                'data': {
                    'order_id': 'order-123',
                    'customer_name': 'John Doe',
                    'total_amount': '50.00',
                    'message': 'New order from John Doe',
                },
            },
        )

        response = await communicator.receive_json_from()
        self.assertEqual(response['type'], 'new_order')
        self.assertEqual(response['data']['order_id'], 'order-123')
        self.assertEqual(response['data']['customer_name'], 'John Doe')

        await communicator.disconnect()


class BroadcastUtilsTests(TransactionTestCase):
    """Tests for the WebSocket broadcast utility functions."""

    async def _create_user(self, email, password, is_chef=False, is_consumer=False):
        """Helper to create a user with optional profile."""
        user = await sync_to_async(User.objects.create_user)(
            email=email,
            password=password,
            first_name=email.split('@')[0],
            last_name='Test',
            phone_number='+1234567890',
        )
        if is_chef:
            from authentication.models import Chef
            await sync_to_async(Chef.objects.create)(user=user, is_online=True)
        if is_consumer:
            from authentication.models import Consumer
            await sync_to_async(Consumer.objects.create)(user=user)
        return user

    async def test_broadcast_notification(self):
        """broadcast_notification sends message to user's group."""
        user = await self._create_user('notify@example.com', 'pass123', is_consumer=True)

        communicator = WebsocketCommunicator(
            OrderConsumer.as_asgi(),
            '/ws/orders/',
        )
        communicator.scope['user'] = user
        connected, _ = await communicator.connect()
        self.assertTrue(connected)

        # Use the broadcast utility
        await sync_to_async(broadcast_notification)(
            user_id=user.id,
            notification_data={
                'notification_type': 'order_accepted',
                'order_id': 'order-456',
                'message': 'Your order was accepted!',
            },
        )

        response = await communicator.receive_json_from()
        self.assertEqual(response['type'], 'notification')
        self.assertEqual(response['data']['message'], 'Your order was accepted!')

        await communicator.disconnect()

    async def test_broadcast_order_status_update(self):
        """broadcast_order_status_update sends message to order group."""
        user = await self._create_user('status@example.com', 'pass123', is_consumer=True)

        communicator = WebsocketCommunicator(
            OrderConsumer.as_asgi(),
            '/ws/orders/',
        )
        communicator.scope['user'] = user
        connected, _ = await communicator.connect()
        self.assertTrue(connected)

        # Subscribe to order group
        await communicator.send_json_to({
            'action': 'subscribe_order',
            'order_id': 'status-order-1',
        })
        await communicator.receive_json_from()

        # Broadcast status update
        await sync_to_async(broadcast_order_status_update)(
            order_id='status-order-1',
            status_data={
                'order_id': 'status-order-1',
                'status': 'out_for_delivery',
            },
        )

        response = await communicator.receive_json_from()
        self.assertEqual(response['type'], 'status_update')
        self.assertEqual(response['data']['status'], 'out_for_delivery')

        await communicator.disconnect()

    async def test_broadcast_new_order_to_chef(self):
        """broadcast_new_order_to_chef sends new_order event to chef."""
        chef = await self._create_user('chef2@example.com', 'pass123', is_chef=True)

        communicator = WebsocketCommunicator(
            OrderConsumer.as_asgi(),
            '/ws/orders/',
        )
        communicator.scope['user'] = chef
        connected, _ = await communicator.connect()
        self.assertTrue(connected)

        # Broadcast new order to chef
        await sync_to_async(broadcast_new_order_to_chef)(
            chef_id=chef.id,
            order_data={
                'order_id': 'new-order-789',
                'customer_name': 'Jane Smith',
                'total_amount': '75.00',
                'message': 'New order from Jane Smith',
            },
        )

        response = await communicator.receive_json_from()
        self.assertEqual(response['type'], 'new_order')
        self.assertEqual(response['data']['order_id'], 'new-order-789')
        self.assertEqual(response['data']['customer_name'], 'Jane Smith')

        await communicator.disconnect()
