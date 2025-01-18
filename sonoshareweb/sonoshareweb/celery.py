# sonoshareweb/celery.py

import os
from celery import Celery

# Set the default Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sonoshareweb.settings')

# Create the Celery app
app = Celery('sonoshareweb')

# Read config from Django settings
app.config_from_object('django.conf:settings', namespace='CELERY')

# Load tasks from all registered Django app configs
app.autodiscover_tasks()

@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')
