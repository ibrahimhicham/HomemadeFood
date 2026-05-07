import asyncio
import contextlib

from asgiref.sync import sync_to_async
from channels.testing import WebsocketCommunicator
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from rest_framework.authtoken.models import Token

from HomemadeFood.asgi import application
from authentication.models import Chef, Consumer
from orders.utils import (
    broadcast_new_order_to_chef,
    broadcast_notification,
    broadcast_order_status_update,
)

User = get_user_model()


class Command(BaseCommand):
    help = (
        "Connect multiple token-authenticated websocket clients to /ws/orders/ "
        "and verify routing to user_<id> and order_<id> groups."
    )

    def handle(self, *args, **options):
        try:
            asyncio.run(self._run())
        except AssertionError as exc:
            raise CommandError(str(exc)) from exc

    async def _run(self):
        chef, chef_token = await self._create_user_with_token(
            "ws-chef@example.com", is_chef=True
        )
        customer, customer_token = await self._create_user_with_token(
            "ws-customer@example.com", is_consumer=True
        )
        observer, observer_token = await self._create_user_with_token(
            "ws-observer@example.com", is_consumer=True
        )

        order_id = "ws-order-001"
        chef_socket = await self._connect(chef_token.key)
        customer_socket = await self._connect(customer_token.key)
        observer_socket = await self._connect(observer_token.key)

        try:
            await customer_socket.send_json_to(
                {"action": "subscribe_order", "order_id": order_id}
            )
            await self._expect_message(
                customer_socket,
                {"type": "subscribed", "order_id": order_id},
                "customer subscribe ack",
            )

            await chef_socket.send_json_to(
                {"action": "subscribe_order", "order_id": order_id}
            )
            await self._expect_message(
                chef_socket,
                {"type": "subscribed", "order_id": order_id},
                "chef subscribe ack",
            )

            await sync_to_async(broadcast_new_order_to_chef)(
                chef_id=chef.id,
                order_data={
                    "order_id": order_id,
                    "customer_name": "WebSocket Customer",
                    "total_amount": "42.50",
                    "message": "New order from WebSocket Customer",
                },
            )
            await self._expect_message(
                chef_socket,
                {
                    "type": "new_order",
                    "data": {
                        "order_id": order_id,
                        "customer_name": "WebSocket Customer",
                        "total_amount": "42.50",
                        "message": "New order from WebSocket Customer",
                    },
                },
                "chef new_order event",
            )
            await self._expect_no_message(customer_socket, "customer after new_order")
            await self._expect_no_message(observer_socket, "observer after new_order")

            await sync_to_async(broadcast_notification)(
                user_id=customer.id,
                notification_data={
                    "notification_type": "order_accepted",
                    "order_id": order_id,
                    "message": "Your order was accepted.",
                },
            )
            await self._expect_message(
                customer_socket,
                {
                    "type": "notification",
                    "data": {
                        "notification_type": "order_accepted",
                        "order_id": order_id,
                        "message": "Your order was accepted.",
                    },
                },
                "customer notification",
            )
            await self._expect_no_message(chef_socket, "chef after customer notification")
            await self._expect_no_message(observer_socket, "observer after customer notification")

            await sync_to_async(broadcast_order_status_update)(
                order_id=order_id,
                status_data={
                    "order_id": order_id,
                    "status": "accepted",
                    "updated_at": "2026-05-05T12:00:00Z",
                    "estimated_ready_time": "2026-05-05T12:20:00Z",
                },
            )
            expected_status = {
                "type": "status_update",
                "data": {
                    "order_id": order_id,
                    "status": "accepted",
                    "updated_at": "2026-05-05T12:00:00Z",
                    "estimated_ready_time": "2026-05-05T12:20:00Z",
                },
            }
            await self._expect_message(
                customer_socket, expected_status, "customer status update"
            )
            await self._expect_message(
                chef_socket, expected_status, "chef status update"
            )
            await self._expect_no_message(observer_socket, "observer status update")

            self.stdout.write(self.style.SUCCESS("Websocket routing checks passed."))
            self.stdout.write(
                "Verified: chef-only new_order, customer-only notification, "
                "and order-group status updates only to subscribers."
            )
        finally:
            await self._disconnect(chef_socket)
            await self._disconnect(customer_socket)
            await self._disconnect(observer_socket)

    async def _create_user_with_token(
        self, email: str, *, is_chef: bool = False, is_consumer: bool = False
    ):
        user, _ = await sync_to_async(User.objects.get_or_create)(
            email=email,
            defaults={
                "first_name": email.split("@")[0],
                "last_name": "WS",
                "phone_number": f"+1000000{abs(hash(email)) % 1000000:06d}",
            },
        )
        if is_chef:
            await sync_to_async(Chef.objects.get_or_create)(
                user=user,
                defaults={"is_online": True},
            )
        if is_consumer:
            await sync_to_async(Consumer.objects.get_or_create)(user=user)
        token, _ = await sync_to_async(Token.objects.get_or_create)(user=user)
        return user, token

    async def _connect(self, token: str):
        communicator = WebsocketCommunicator(
            application,
            f"/ws/orders/?token={token}",
        )
        connected, _ = await communicator.connect()
        assert connected, f"websocket failed to connect for token {token}"
        return communicator

    async def _disconnect(self, communicator: WebsocketCommunicator):
        if communicator is None:
            return
        with contextlib.suppress(Exception):
            await communicator.disconnect()

    async def _expect_message(self, communicator, expected: dict, label: str):
        actual = await communicator.receive_json_from(timeout=1)
        assert actual == expected, (
            f"{label} mismatch.\nExpected: {expected}\nActual: {actual}"
        )

    async def _expect_no_message(self, communicator, label: str):
        has_message = not await communicator.receive_nothing(timeout=0.3)
        assert not has_message, f"{label} unexpectedly received a websocket event"
