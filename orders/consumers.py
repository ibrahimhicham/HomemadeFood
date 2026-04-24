import json
from channels.generic.websocket import AsyncJsonWebsocketConsumer


class OrderConsumer(AsyncJsonWebsocketConsumer):

    async def connect(self):
        user = self.scope['user']
        print(user)

        if user.is_anonymous:
            await self.close()
            return

        self.user_id = user.id
        self.user_group_name = f'user_{self.user_id}'

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
        data = json.loads(text_data)
        action = data.get('action')

        if action == 'subscribe_order':
            order_id = data.get('order_id')
            if order_id:
                group = f'order_{order_id}'
                await self.channel_layer.group_add(group, self.channel_name)

                await self.send_json({
                    'type': 'subscribed',
                    'order_id': order_id,
                })

        elif action == 'unsubscribe_order':
            order_id = data.get('order_id')
            if order_id:
                group = f'order_{order_id}'
                await self.channel_layer.group_discard(group, self.channel_name)

                await self.send_json({
                    'type': 'unsubscribed',
                    'order_id': order_id,
                })

    async def order_notification(self, event):
        await self.send_json({
            'type': 'notification',
            'data': event['data'],
        })

    async def order_status_update(self, event):
        await self.send_json({
            'type': 'status_update',
            'data': event['data'],
        })

    async def order_created(self, event):
        await self.send_json({
            'type': 'new_order',
            'data': event['data'],
        })