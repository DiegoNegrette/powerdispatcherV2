from celery.utils.log import get_task_logger
from service.celery import app

logger = get_task_logger("scraper")
queue_name = "main_queue"


@app.task(queue_name=queue_name)
def test_task():
    logger.info("Test Task worked")
