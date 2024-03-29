from celery.utils.log import get_task_logger
from service.celery import app

logger = get_task_logger("scraper")
queue_name = "main_queue"


def log_info(message, scraper_log=None):
    logger.info(message)
    if scraper_log:
        scraper_log.set_last_message(message)


@app.task(queue_name=queue_name)
def update_ticket_status(ticket_ids=[]):
    print("Task worked")
