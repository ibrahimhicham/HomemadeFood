"""
ASGI config for HomemadeFood project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.2/howto/deployment/asgi/
"""

import os
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.security.websocket import AllowedHostsOriginValidator

# 1. First, set the settings environment variable
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HomemadeFood.settings')

# 2. Second, initialize Django and load all the application registries
django_asgi_app = get_asgi_application()

# 3. Third, NOW it is completely safe to import your custom middleware and app routes
from orders.middleware import TokenAuthMiddleware
from orders.routing import websocket_urlpatterns

# 4. Finally, declare the Protocol Type Router
application = ProtocolTypeRouter({
    'http': django_asgi_app,
    'websocket': AllowedHostsOriginValidator(
        TokenAuthMiddleware(
            URLRouter(websocket_urlpatterns)
        )
    ),
})
