from celery import Celery
from celery.exceptions import CeleryError
from src.backend.core.config import settings
from src.backend.core.utils.date import date_time

__all__ = ("get_celery_client",)


def get_celery_client() -> Celery:
    try:
        celery = Celery(
            "SmartBin",
            broker=settings.celery_broker_url,
            backend=settings.celery_result_backend,
            include=["backend.tasks"],
            config={
                "task_serializer": "json",
                "accept_content": ["json"],
                "result_serializer": "json",
                "timezone": "UTC",
                "enable_utc": True,
                "task_track_started": True,
                "task_time_limit": 3600,
            },
        )
        return celery
    except CeleryError as e:
        raise Exception(f"{date_time()}.Initialization of Celery failed: {e}")
