import logging
from celery import Celery
from kombu import Queue

from app.core.config import settings

logger = logging.getLogger("app.workers.celery_app")

# Configure broker and backend based on Redis URL configuration
if settings.REDIS_URL.startswith("mock://"):
    broker_url = "sqla+sqlite:///celerydb.sqlite"
    backend_url = "db+sqlite:///celeryresults.sqlite"
else:
    broker_url = settings.REDIS_URL
    backend_url = settings.REDIS_URL

# Instantiate Celery Application
celery_app = Celery(
    "cloudpilot_tasks",
    broker=broker_url,
    backend=backend_url
)

# Standard Celery Config Options
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    # Configure strict Task Queues mapping to match task queues strategy
    task_queues=[
        Queue("default", routing_key="default.#"),
        Queue("discovery", routing_key="discovery.#"),
        Queue("billing", routing_key="billing.#"),
        Queue("metrics", routing_key="metrics.#"),
        Queue("optimization", routing_key="optimization.#"),
    ],
    task_default_queue="default",
    task_default_exchange="default",
    task_default_routing_key="default.info",
)


@celery_app.task(name="jobs.default.ping")
def ping_task() -> str:
    """Standard heartbeat task checking worker execution readiness."""
    logger.info("Celery heartbeat task triggered successfully.")
    return "pong"
