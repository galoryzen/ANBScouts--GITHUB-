import os

from celery import Celery
from src.tasks import *
from dotenv import load_dotenv
load_dotenv()

def make_celery():
    broker = os.getenv("CELERY_BROKER_URL")
    backend = os.getenv("CELERY_RESULT_BACKEND")

    celery = Celery(
        __name__,
        broker=broker,
        backend=backend,
    )
    celery.conf.update(task_ignore_result=True)
    return celery


celery_app = make_celery()
