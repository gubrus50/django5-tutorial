import os
from celery import Celery

# Docs - https://docs.celeryq.dev/en/stable/django/first-steps-with-django.html#using-celery-with-django


os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'my_website.settings')

app = Celery('my_website')

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
app.config_from_object('django.conf:settings', namespace='CELERY')

# Load task modules from all registered Django apps.
app.autodiscover_tasks()

@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')