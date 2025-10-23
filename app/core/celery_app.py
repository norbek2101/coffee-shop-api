from celery import Celery
from celery.schedules import crontab

from app.core.config import settings


def make_celery() -> Celery:
    """Create and configure Celery application for background tasks."""
    celery_app = Celery(
        "coffee_shop_api",
        broker=settings.CELERY_BROKER_URL,
        backend=settings.CELERY_RESULT_BACKEND,
    )
    
    # Basic configuration
    celery_app.conf.update(
        timezone="UTC",
        enable_utc=True,
        task_serializer="json",
        result_serializer="json",
        accept_content=["json"],
    )
    
    # Scheduled task: cleanup unverified users daily at 3 AM UTC
    celery_app.conf.beat_schedule = {
        "daily-cleanup-unverified-users": {
            "task": "app.tasks.cleanup.delete_unverified_users_task",
            "schedule": crontab(hour=3, minute=0),
            "args": (),
        },
    }
    
    return celery_app


# Initialize Celery instance
celery = make_celery()

# Auto-discover tasks in app.tasks module
celery.autodiscover_tasks(["app.tasks"])
