import os
import logging

from utils import is_put_scrape_report, get_attachments, send_email


logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.ERROR,
    format='%(levelname)s: %(asctime)s: %(message)s')


def log_helper(logger, e, event):
    logger.error('## EXCEPTION')
    logger.error(e, exc_info=True)
    logger.error('## ENV VARS')
    logger.error(os.environ)
    logger.error('## EVENT')
    logger.error(event)

def main(event, context):

    if is_put_scrape_report(event):
        attachments = get_attachments()
        try:
            send_email(attachments)
        except Exception as e:
            log_helper(logger, e, event)
