from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from django.urls import re_path
from cars.consumers import SyncStatusConsumer

application = ProtocolTypeRouter({
    "http": get_asgi_application(),  
    "websocket": AuthMiddlewareStack(
        URLRouter([
            re_path(r"ws/sync-status/$", SyncStatusConsumer.as_asgi()),
        ])
    ),
})
