import os
import django
from django.core.asgi import get_asgi_application

# 1. Set settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HomemadeFood.settings')

# 2. Setup Django
django.setup()

# 3. Get the ASGI application wrapper
django_asgi_app = get_asgi_application()

# 4. Routing configuration (Checks if Channels is used)
try:
    from channels.routing import ProtocolTypeRouter, URLRouter
    from orders.middleware import TokenAuthMiddleware
    # If you have a routing.py file inside your orders app, import it here:
    # from orders.routing import websocket_urlpatterns
    
    application = ProtocolTypeRouter({
        "http": django_asgi_app,
        # "websocket": TokenAuthMiddleware(URLRouter(websocket_urlpatterns)),
    })
except ImportError:
    # Fallback if channels isn't fully configured yet
    application = django_asgi_app
