"""
ASGI config for rankprice_dashboard project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.1/howto/deployment/asgi/
"""

# rankprice_dashboard/asgi.py
import os
import django
from channels.routing import ProtocolTypeRouter, URLRouter
from django.core.asgi import get_asgi_application
from channels.auth import AuthMiddlewareStack
from django.urls import re_path
from cars.consumers import SyncStatusConsumer

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'rankprice_dashboard.settings')
django.setup()

application = ProtocolTypeRouter({
    "http": get_asgi_application(),
    "websocket": AuthMiddlewareStack(
        URLRouter([
            re_path(r"ws/sync-status/$", SyncStatusConsumer.as_asgi()),
        ])
    ),
})






