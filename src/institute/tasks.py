import logging

from institute.worker import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(
    name="institute.tasks.send_notification",
    bind=True,
    max_retries=3,
    default_retry_delay=60,
)
def send_notification(self, user_id: str, event: str, payload: dict) -> dict:
    """
    Notification task (placeholder for the Prototype).

    In v2, this task will send emails via SES.
    For now, it only logs — but the infrastructure is ready.
    """
    try:
        logger.info(
            "Processing notification",
            extra={
                "user_id": user_id,
                "event": event,
                "task_id": self.request.id,
            },
        )
        # TODO in the future: integrate with SES
        return {"status": "logged", "user_id": user_id, "event": event}
    except Exception as exc:
        logger.error(
            "Notification failed",
            extra={"user_id": user_id, "event": event, "error": str(exc)},
        )
        raise self.retry(exc=exc) from exc
