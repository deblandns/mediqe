import os
from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'appointment_mediqe.settings')

# config the celery for the application jobs
app = Celery('appointment_mediqe')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()