import os

from celery import Celery
from dotenv import load_dotenv

load_dotenv()

celery_app = Celery(
    "worker",
    broker="amqp://guest:guest@localhost:5672//",
    backend="rpc://",
    include=['src.project.email_service.celery_worker.tasks']
)


celery_app.conf.update(
    SMTP_HOST=os.getenv("SMTP_HOST"),
    SMTP_PORT=int(os.getenv("SMTP_PORT")),
    SMTP_USER=os.getenv("SMTP_USER"),
    SMTP_PASSWORD=os.getenv("SMTP_PASSWORD"),
    result_extended=True,
    task_track_started=True,
    worker_pool='solo',
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    broker_connection_timeout=30
)


celery_app.conf.beat_schedule = {
    'run-every-hour': {
        'task': 'src.project.email_service.celery_worker.tasks.clear_links',
        'schedule': 3600.0,
    },
}

