from urllib.parse import parse_qs
from django.contrib.auth.models import AnonymousUser
from rest_framework.authtoken.models import Token
from channels.db import database_sync_to_async


class TokenAuthMiddleware:
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        scope = dict(scope)

        scope["user"] = AnonymousUser()

        query_string = parse_qs(scope["query_string"].decode())
        token_key = query_string.get("token")

        if token_key:
            token = await self.get_token(token_key[0])
            if token:
                scope["user"] = token.user

        return await self.app(scope, receive, send)

    @database_sync_to_async
    def get_token(self, key):
        try:
            return Token.objects.select_related("user").get(key=key)
        except Token.DoesNotExist:
            return None