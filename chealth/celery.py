import os
from celery import Celery


CELERY_TASK_LIST = [
    'apps.service_api.fitbit.tasks',
    'apps.service_api.dexcom.tasks',
    'apps.user.tasks',
    'apps.community.tasks',
    'apps.fsucon.tasks',
    'studies.step_up.tasks',
    'studies.plwh_ema.tasks',
]

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'chealth.settings')

app = Celery('chealth', include=CELERY_TASK_LIST)

app.config_from_object('django.conf:settings', namespace='CELERY')

# app.autodiscover_tasks()


@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')
