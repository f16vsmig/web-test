from __future__ import absolute_import

from celery import Celery
import os

from django.conf import settings

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'benchmark.settings')

app = Celery('benchmark')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()

@app.task(bind=True)
def debug_task(self):
    print('Request: {0!r}'.format(self.request))
