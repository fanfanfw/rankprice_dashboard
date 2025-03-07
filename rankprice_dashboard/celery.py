import os
from celery import Celery

# Pastikan nama project Anda benar, misal "rankprice_dashboard.settings"
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'rankprice_dashboard.settings')

app = Celery('rankprice_dashboard')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()
