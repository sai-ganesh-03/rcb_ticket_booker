import logging

# Configure logging with a file path
LOG_FILE_PATH = "/home/sai-ganesh-s/Projects/rcb_ticket_notifier_v3/event_checker.log"

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(module)s - %(funcName)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE_PATH),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)